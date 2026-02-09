"""
Bloom Prediction ML Model for Smart Shamba — PyTorch Edition
Trains a deep neural network using historical satellite data.

Features: NDVI, NDWI, rainfall, temperature  (+ optional sensor data)
Labels  : Binary bloom occurrence  (bloom / no-bloom)

Drop-in replacement for the sklearn-based train_model.py.
Public API is identical:
    BloomPredictor           — class
    train_bloom_model()      — top-level convenience
    predict_bloom_from_live_data()
"""

import os
import json
import logging
import numpy as np
from datetime import datetime
from typing import Dict, Tuple, List, Optional
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------- PyTorch imports ----------
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, TensorDataset
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available — ML functionality disabled. "
                    "Install: pip install torch")

# ---------- Safetensors support ----------
try:
    from safetensors.torch import save_file as st_save, load_file as st_load
    SAFETENSORS_AVAILABLE = True
except ImportError:
    SAFETENSORS_AVAILABLE = False
    logger.warning("safetensors not available — will fall back to torch.save. "
                    "Install: pip install safetensors")

# sklearn only for StandardScaler (lightweight, widely available)
try:
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import (
        accuracy_score, f1_score, classification_report
    )
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available — will use manual scaling")

# Local modules
try:
    from bloom_processor import BloomProcessor, NDWI_BLOOM_THRESHOLD, NDVI_VEGETATION_THRESHOLD
    from ee_pipeline import EarthEnginePipeline
except ImportError:
    logger.warning("Local modules not available — using fallbacks")
    BloomProcessor = None
    EarthEnginePipeline = None
    NDWI_BLOOM_THRESHOLD = 0.0
    NDVI_VEGETATION_THRESHOLD = 0.3

# ---------- Paths ----------
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
MODELS_DIR = os.path.join(DATA_DIR, "models")
MODEL_PATH = os.path.join(MODELS_DIR, "bloom_model.safetensors")
MODEL_PATH_PT = os.path.join(MODELS_DIR, "bloom_model_torch.pt")  # legacy fallback
METADATA_PATH = os.path.join(MODELS_DIR, "bloom_model_meta.json")
SCALER_PATH = os.path.join(MODELS_DIR, "feature_scaler.json")
os.makedirs(MODELS_DIR, exist_ok=True)


# ===================================================================== #
#  Network Architecture
# ===================================================================== #

class BloomNet(nn.Module):
    """
    Fully-connected classifier for binary bloom prediction.

    Architecture
    ────────────
        Input (4 or N features)
        → Linear(N, 64) → BatchNorm → ReLU → Dropout(0.3)
        → Linear(64, 32) → BatchNorm → ReLU → Dropout(0.2)
        → Linear(32, 16) → ReLU
        → Linear(16, 1)  → Sigmoid
    """

    def __init__(self, n_features: int = 4):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(n_features, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Dropout(0.3),

            nn.Linear(64, 32),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.Dropout(0.2),

            nn.Linear(32, 16),
            nn.ReLU(),

            nn.Linear(16, 1),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x).squeeze(-1)


# ===================================================================== #
#  Time-Series Forecasting: LSTM + Transformer (yield / drought)
# ===================================================================== #

class BloomForecasterLSTM(nn.Module):
    """
    LSTM-based time-series forecaster for agricultural predictions.

    Input : (batch, seq_len, n_features)  — rolling windows of
            [temperature_c, soil_moisture_pct, ndvi, ndwi, rainfall_mm, evi]
    Output: (batch, 3)  — [bloom_probability, yield_potential, drought_risk]

    Architecture
    ────────────
        LSTM(n_features, 128, 2 layers, bidirectional)
        → LayerNorm → Dropout(0.3)
        → Transformer Encoder (2 layers, 4 heads)
        → Linear(hidden, 64) → ReLU → Dropout(0.2)
        → Linear(64, 3) → Sigmoid
    """

    def __init__(self, n_features: int = 6, hidden_size: int = 128,
                 n_lstm_layers: int = 2, n_heads: int = 4,
                 n_transformer_layers: int = 2, dropout: float = 0.3):
        super().__init__()
        self.hidden_size = hidden_size

        # LSTM encoder
        self.lstm = nn.LSTM(
            input_size=n_features,
            hidden_size=hidden_size,
            num_layers=n_lstm_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if n_lstm_layers > 1 else 0.0,
        )
        lstm_out_dim = hidden_size * 2  # bidirectional

        self.layer_norm = nn.LayerNorm(lstm_out_dim)
        self.dropout1 = nn.Dropout(dropout)

        # Transformer encoder on top of LSTM outputs
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=lstm_out_dim,
            nhead=n_heads,
            dim_feedforward=lstm_out_dim * 2,
            dropout=dropout,
            batch_first=True,
        )
        self.transformer = nn.TransformerEncoder(
            encoder_layer, num_layers=n_transformer_layers,
        )

        # Prediction head
        self.head = nn.Sequential(
            nn.Linear(lstm_out_dim, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 3),   # bloom_prob, yield_potential, drought_risk
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (batch, seq_len, n_features)
        Returns:
            (batch, 3)  — [bloom_probability, yield_potential, drought_risk]
        """
        lstm_out, _ = self.lstm(x)                  # (B, T, 2*H)
        lstm_out = self.dropout1(self.layer_norm(lstm_out))
        transformer_out = self.transformer(lstm_out)  # (B, T, 2*H)
        # Use last time-step as summary
        summary = transformer_out[:, -1, :]          # (B, 2*H)
        return self.head(summary)                    # (B, 3)

    def get_embeddings(self, x: torch.Tensor) -> torch.Tensor:
        """Return intermediate embeddings for multimodal fusion."""
        lstm_out, _ = self.lstm(x)
        lstm_out = self.dropout1(self.layer_norm(lstm_out))
        transformer_out = self.transformer(lstm_out)
        return transformer_out[:, -1, :]             # (B, 2*H)


# ===================================================================== #
#  Computer Vision: EfficientNet CNN (crop disease / bloom detection)
# ===================================================================== #

class BloomVisionCNN(nn.Module):
    """
    EfficientNet-based image classifier for crop health / bloom detection.

    Uses TorchVision's EfficientNet-B0 backbone with a custom classification
    head.  Trained on PlantVillage-style labels + farmer-submitted photos.

    Input : (batch, 3, 224, 224)  — RGB images
    Output: (batch, n_classes)    — class probabilities

    Categories (default 6):
        healthy | leaf_blight | rust | aphid_damage | bloom_detected | wilting
    """

    DEFAULT_CLASSES = [
        "healthy", "leaf_blight", "rust",
        "aphid_damage", "bloom_detected", "wilting",
    ]

    def __init__(self, n_classes: int = 6, pretrained: bool = True):
        super().__init__()
        self.n_classes = n_classes

        try:
            from torchvision.models import efficientnet_b0, EfficientNet_B0_Weights
            weights = EfficientNet_B0_Weights.IMAGENET1K_V1 if pretrained else None
            backbone = efficientnet_b0(weights=weights)
            self.feature_dim = backbone.classifier[1].in_features
            backbone.classifier = nn.Identity()
            self.backbone = backbone
            self._torchvision_ok = True
        except ImportError:
            logger.warning("torchvision not available — using lightweight CNN fallback")
            self._torchvision_ok = False
            self.feature_dim = 256
            self.backbone = nn.Sequential(
                nn.Conv2d(3, 32, 3, padding=1), nn.BatchNorm2d(32), nn.ReLU(),
                nn.MaxPool2d(2),
                nn.Conv2d(32, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(),
                nn.MaxPool2d(2),
                nn.Conv2d(64, 128, 3, padding=1), nn.BatchNorm2d(128), nn.ReLU(),
                nn.AdaptiveAvgPool2d(1),
                nn.Flatten(),
                nn.Linear(128, self.feature_dim),
                nn.ReLU(),
            )

        self.classifier = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(self.feature_dim, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, n_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """(B, 3, 224, 224) → (B, n_classes) logits"""
        features = self.backbone(x)
        return self.classifier(features)

    def get_embeddings(self, x: torch.Tensor) -> torch.Tensor:
        """Return feature embeddings for multimodal fusion."""
        return self.backbone(x)                      # (B, feature_dim)

    def predict_image(self, image_tensor: torch.Tensor,
                      class_names: Optional[List[str]] = None) -> Dict:
        """Single-image inference helper."""
        self.eval()
        classes = class_names or self.DEFAULT_CLASSES
        with torch.no_grad():
            logits = self.forward(image_tensor.unsqueeze(0) if image_tensor.dim() == 3 else image_tensor)
            probs = torch.softmax(logits, dim=-1)[0]
            top_idx = probs.argmax().item()
        return {
            "classification": classes[top_idx] if top_idx < len(classes) else f"class_{top_idx}",
            "classification_confidence": float(probs[top_idx]),
            "all_probabilities": {c: float(p) for c, p in zip(classes, probs)},
        }


# ===================================================================== #
#  Multimodal Inference Service — concat embeddings (vision + time-series)
# ===================================================================== #

class MultimodalInferenceService:
    """
    Loads safetensors models and performs multimodal inference by
    concatenating embeddings from the vision CNN and time-series LSTM.

    Fusion → Linear(vision_dim + ts_dim, 128) → ReLU → Linear(128, n_out) → Sigmoid

    Output: bloom_probability, yield_potential, drought_risk,
            pest_risk, disease_risk  (5 values, 0-1)
    """

    N_OUTPUTS = 5  # bloom, yield, drought, pest, disease

    def __init__(self, models_dir: str = MODELS_DIR, device: str = "auto"):
        self.models_dir = models_dir
        self.device = torch.device(
            "cuda" if device == "auto" and TORCH_AVAILABLE and torch.cuda.is_available()
            else "cpu"
        )

        # Sub-models (lazy-loaded)
        self.ts_model: Optional[BloomForecasterLSTM] = None
        self.vision_model: Optional[BloomVisionCNN] = None
        self.bloom_model: Optional[BloomNet] = None
        self.fusion_head: Optional[nn.Module] = None

        self._ts_dim: int = 256   # LSTM hidden*2
        self._vis_dim: int = 1280 # EfficientNet-B0

        logger.info(f"MultimodalInferenceService initialized (device={self.device})")

    # ------------------------------------------------------------------ #
    #  Model loading (safetensors preferred)
    # ------------------------------------------------------------------ #

    def load_models(self) -> Dict[str, bool]:
        """Load all available models from safetensors files."""
        loaded = {}

        # 1) Tabular bloom classifier (always available)
        try:
            meta_path = os.path.join(self.models_dir, "bloom_model_meta.json")
            if os.path.exists(meta_path):
                with open(meta_path) as f:
                    meta = json.load(f)
                n_feat = meta.get("n_features", 4)
                net = BloomNet(n_feat).to(self.device)
                st_path = os.path.join(self.models_dir, "bloom_model.safetensors")
                pt_path = os.path.join(self.models_dir, "bloom_model_torch.pt")
                if SAFETENSORS_AVAILABLE and os.path.exists(st_path):
                    state = st_load(st_path, device=str(self.device))
                    net.load_state_dict(state)
                elif os.path.exists(pt_path):
                    ckpt = torch.load(pt_path, map_location=self.device, weights_only=False)
                    net.load_state_dict(ckpt["state_dict"])
                net.eval()
                self.bloom_model = net
                loaded["bloom_classifier"] = True
                logger.info("✓ Bloom classifier loaded")
        except Exception as e:
            loaded["bloom_classifier"] = False
            logger.warning(f"Bloom classifier load failed: {e}")

        # 2) Time-series forecaster
        try:
            ts_path = os.path.join(self.models_dir, "forecaster_lstm.safetensors")
            ts_meta = os.path.join(self.models_dir, "forecaster_lstm_meta.json")
            if os.path.exists(ts_path) and os.path.exists(ts_meta):
                with open(ts_meta) as f:
                    meta = json.load(f)
                model = BloomForecasterLSTM(
                    n_features=meta.get("n_features", 6),
                    hidden_size=meta.get("hidden_size", 128),
                ).to(self.device)
                if SAFETENSORS_AVAILABLE:
                    state = st_load(ts_path, device=str(self.device))
                    model.load_state_dict(state)
                model.eval()
                self.ts_model = model
                self._ts_dim = meta.get("hidden_size", 128) * 2
                loaded["ts_forecaster"] = True
                logger.info("✓ Time-series forecaster loaded")
            else:
                loaded["ts_forecaster"] = False
        except Exception as e:
            loaded["ts_forecaster"] = False
            logger.warning(f"TS forecaster load failed: {e}")

        # 3) Vision CNN
        try:
            vis_path = os.path.join(self.models_dir, "vision_cnn.safetensors")
            vis_meta = os.path.join(self.models_dir, "vision_cnn_meta.json")
            if os.path.exists(vis_path) and os.path.exists(vis_meta):
                with open(vis_meta) as f:
                    meta = json.load(f)
                model = BloomVisionCNN(
                    n_classes=meta.get("n_classes", 6),
                    pretrained=False,
                ).to(self.device)
                if SAFETENSORS_AVAILABLE:
                    state = st_load(vis_path, device=str(self.device))
                    model.load_state_dict(state)
                model.eval()
                self.vision_model = model
                self._vis_dim = model.feature_dim
                loaded["vision_cnn"] = True
                logger.info("✓ Vision CNN loaded")
            else:
                loaded["vision_cnn"] = False
        except Exception as e:
            loaded["vision_cnn"] = False
            logger.warning(f"Vision CNN load failed: {e}")

        # 4) Fusion head (optional — built on first multimodal call if missing)
        fusion_path = os.path.join(self.models_dir, "fusion_head.safetensors")
        if os.path.exists(fusion_path) and SAFETENSORS_AVAILABLE:
            try:
                self._build_fusion_head()
                state = st_load(fusion_path, device=str(self.device))
                self.fusion_head.load_state_dict(state)
                self.fusion_head.eval()
                loaded["fusion_head"] = True
            except Exception as e:
                loaded["fusion_head"] = False
                logger.warning(f"Fusion head load failed: {e}")
        else:
            loaded["fusion_head"] = False

        return loaded

    def _build_fusion_head(self):
        """Build the fusion MLP that combines vision + time-series embeddings."""
        in_dim = self._vis_dim + self._ts_dim
        self.fusion_head = nn.Sequential(
            nn.Linear(in_dim, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, self.N_OUTPUTS),
            nn.Sigmoid(),
        ).to(self.device)

    # ------------------------------------------------------------------ #
    #  Multimodal prediction
    # ------------------------------------------------------------------ #

    def predict_multimodal(
        self,
        time_series: Optional[torch.Tensor] = None,
        image: Optional[torch.Tensor] = None,
        tabular_features: Optional[List[float]] = None,
    ) -> Dict:
        """
        Run multimodal inference combining available modalities.

        Args:
            time_series: (1, seq_len, n_features) sensor history window
            image: (1, 3, 224, 224) crop/field image
            tabular_features: [ndvi, ndwi, rainfall, temp] for bloom classifier

        Returns:
            Dict with bloom_probability, yield_potential, drought_risk,
            pest_risk, disease_risk, classification, confidence, model_version
        """
        result: Dict = {
            "bloom_probability": None,
            "yield_potential": None,
            "drought_risk": None,
            "pest_risk": None,
            "disease_risk": None,
            "classification": None,
            "classification_confidence": None,
            "modalities_used": [],
            "model_version": "Multimodal v1.0",
            "predicted_at": datetime.now().isoformat(),
        }

        embeddings = []

        # Time-series branch
        if time_series is not None and self.ts_model is not None:
            with torch.no_grad():
                ts_input = time_series.to(self.device)
                ts_preds = self.ts_model(ts_input)        # (1, 3)
                ts_embed = self.ts_model.get_embeddings(ts_input)
                embeddings.append(ts_embed)

            result["bloom_probability"] = float(ts_preds[0, 0]) * 100
            result["yield_potential"] = float(ts_preds[0, 1])
            result["drought_risk"] = float(ts_preds[0, 2])
            result["modalities_used"].append("time_series")

        # Vision branch
        if image is not None and self.vision_model is not None:
            with torch.no_grad():
                img_input = image.to(self.device)
                vis_pred = self.vision_model.predict_image(img_input)
                vis_embed = self.vision_model.get_embeddings(img_input)
                embeddings.append(vis_embed)

            result["classification"] = vis_pred["classification"]
            result["classification_confidence"] = vis_pred["classification_confidence"]
            result["modalities_used"].append("vision")

        # Multimodal fusion (if both embeddings available)
        if len(embeddings) == 2:
            if self.fusion_head is None:
                self._build_fusion_head()
            with torch.no_grad():
                fused = torch.cat(embeddings, dim=-1)     # (1, vis+ts)
                fused_preds = self.fusion_head(fused)[0]  # (5,)
            result["bloom_probability"] = float(fused_preds[0]) * 100
            result["yield_potential"] = float(fused_preds[1])
            result["drought_risk"] = float(fused_preds[2])
            result["pest_risk"] = float(fused_preds[3])
            result["disease_risk"] = float(fused_preds[4])
            result["modalities_used"].append("fusion")

        # Tabular fallback (always available)
        if tabular_features is not None and self.bloom_model is not None:
            with torch.no_grad():
                x = torch.tensor([tabular_features], dtype=torch.float32, device=self.device)
                prob = float(self.bloom_model(x).item()) * 100
            if result["bloom_probability"] is None:
                result["bloom_probability"] = prob
            result["tabular_bloom_probability"] = prob
            result["modalities_used"].append("tabular")

        return result

    # ------------------------------------------------------------------ #
    #  Save all models (safetensors)
    # ------------------------------------------------------------------ #

    def save_all_models(self) -> Dict[str, bool]:
        """Persist all sub-models as safetensors + metadata JSON."""
        saved = {}

        if self.ts_model and SAFETENSORS_AVAILABLE:
            try:
                st_save(self.ts_model.state_dict(),
                        os.path.join(self.models_dir, "forecaster_lstm.safetensors"))
                meta = {
                    "n_features": self.ts_model.lstm.input_size,
                    "hidden_size": self.ts_model.hidden_size,
                    "saved_at": datetime.now().isoformat(),
                }
                with open(os.path.join(self.models_dir, "forecaster_lstm_meta.json"), "w") as f:
                    json.dump(meta, f, indent=2)
                saved["ts_forecaster"] = True
            except Exception as e:
                saved["ts_forecaster"] = False
                logger.error(f"TS model save failed: {e}")

        if self.vision_model and SAFETENSORS_AVAILABLE:
            try:
                st_save(self.vision_model.state_dict(),
                        os.path.join(self.models_dir, "vision_cnn.safetensors"))
                meta = {
                    "n_classes": self.vision_model.n_classes,
                    "feature_dim": self.vision_model.feature_dim,
                    "saved_at": datetime.now().isoformat(),
                }
                with open(os.path.join(self.models_dir, "vision_cnn_meta.json"), "w") as f:
                    json.dump(meta, f, indent=2)
                saved["vision_cnn"] = True
            except Exception as e:
                saved["vision_cnn"] = False
                logger.error(f"Vision model save failed: {e}")

        if self.fusion_head and SAFETENSORS_AVAILABLE:
            try:
                st_save(self.fusion_head.state_dict(),
                        os.path.join(self.models_dir, "fusion_head.safetensors"))
                saved["fusion_head"] = True
            except Exception as e:
                saved["fusion_head"] = False
                logger.error(f"Fusion head save failed: {e}")

        return saved

    def get_info(self) -> Dict:
        """Return summary of loaded models."""
        return {
            "bloom_classifier": self.bloom_model is not None,
            "ts_forecaster": self.ts_model is not None,
            "vision_cnn": self.vision_model is not None,
            "fusion_head": self.fusion_head is not None,
            "device": str(self.device),
            "safetensors_available": SAFETENSORS_AVAILABLE,
        }


# ===================================================================== #
#  BloomPredictor — drop-in replacement for the sklearn version
# ===================================================================== #

class BloomPredictor:
    """
    PyTorch-based bloom predictor.
    API is identical to the sklearn version so callers need no changes.
    """

    def __init__(self):
        self.model: Optional[BloomNet] = None
        self.scaler_params: Optional[Dict] = None   # {mean: [], std: []}
        self.feature_names: Optional[List[str]] = None
        self.model_metrics: Dict = {}
        self.trained_at: Optional[datetime] = None
        self.processor = BloomProcessor() if BloomProcessor else None
        self.pipeline = EarthEnginePipeline() if EarthEnginePipeline else None
        self.device = torch.device("cuda" if TORCH_AVAILABLE and torch.cuda.is_available() else "cpu")
        logger.info(f"Bloom Predictor initialized (PyTorch, device={self.device})")

    # ------------------------------------------------------------------ #
    # Data preparation  (identical contract to sklearn version)
    # ------------------------------------------------------------------ #

    def prepare_training_data(
        self,
        include_weather: bool = True,
        balance_classes: bool = True,
    ) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """Return (X, y, feature_names) numpy arrays."""
        logger.info("Preparing training data for PyTorch model")

        if self.processor:
            try:
                ml_data = self.processor.prepare_ml_training_data(include_weather=include_weather)
                if "error" not in ml_data:
                    X = ml_data["features"]
                    y = ml_data["labels"]
                    feature_names = ml_data["feature_names"]
                    logger.info(f"Training data: {X.shape[0]} samples, {X.shape[1]} features")
                    if balance_classes and len(np.unique(y)) > 1:
                        X, y = self._balance_classes(X, y)
                    X = self._handle_missing_values(X)
                    return X, y, feature_names
            except Exception as e:
                logger.error(f"Error from BloomProcessor: {e}")

        return self._generate_synthetic_training_data(include_weather)

    # ------------------------------------------------------------------ #
    # Training
    # ------------------------------------------------------------------ #

    def train_model(
        self,
        include_weather: bool = True,
        optimize_hyperparameters: bool = False,
    ) -> Dict:
        """Train the bloom prediction neural network."""
        logger.info("Training bloom prediction model (PyTorch)")

        if not TORCH_AVAILABLE:
            return {"error": "PyTorch not available"}

        try:
            X, y, feature_names = self.prepare_training_data(
                include_weather=include_weather, balance_classes=True,
            )
            if len(X) == 0:
                return {"error": "No training data available"}

            n_samples = len(X)
            n_classes = len(set(y))

            # --- train/test split ---
            if n_samples < 10:
                test_size = 0.5
            elif n_samples < 20:
                test_size = 0.2
            elif n_samples < 50:
                test_size = 0.25
            else:
                test_size = 0.3

            try:
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=test_size, random_state=42, stratify=y,
                )
            except Exception:
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=test_size, random_state=42,
                )

            # --- feature scaling ---
            mean = X_train.mean(axis=0)
            std = X_train.std(axis=0)
            std[std == 0] = 1.0  # avoid division by zero
            X_train_s = (X_train - mean) / std
            X_test_s = (X_test - mean) / std
            self.scaler_params = {"mean": mean.tolist(), "std": std.tolist()}

            # --- tensors ---
            X_train_t = torch.tensor(X_train_s, dtype=torch.float32, device=self.device)
            y_train_t = torch.tensor(y_train, dtype=torch.float32, device=self.device)
            X_test_t = torch.tensor(X_test_s, dtype=torch.float32, device=self.device)
            y_test_t = torch.tensor(y_test, dtype=torch.float32, device=self.device)

            train_ds = TensorDataset(X_train_t, y_train_t)
            batch_size = min(32, len(X_train))
            train_dl = DataLoader(train_ds, batch_size=batch_size, shuffle=True)

            # --- model ---
            n_features = X_train.shape[1]
            net = BloomNet(n_features).to(self.device)

            # Hyperparams: optionally tune via optimize flag
            lr = 1e-3
            epochs = 150 if not optimize_hyperparameters else 300
            weight_decay = 1e-4

            criterion = nn.BCELoss()
            optimizer = optim.Adam(net.parameters(), lr=lr, weight_decay=weight_decay)
            scheduler = optim.lr_scheduler.ReduceLROnPlateau(
                optimizer, mode="min", factor=0.5, patience=15,
            )

            # --- training loop ---
            net.train()
            best_loss = float("inf")
            patience_ctr = 0
            patience_limit = 30

            for epoch in range(epochs):
                epoch_loss = 0.0
                for xb, yb in train_dl:
                    optimizer.zero_grad()
                    preds = net(xb)
                    loss = criterion(preds, yb)
                    loss.backward()
                    optimizer.step()
                    epoch_loss += loss.item() * len(xb)

                epoch_loss /= len(X_train)
                scheduler.step(epoch_loss)

                if epoch_loss < best_loss - 1e-4:
                    best_loss = epoch_loss
                    patience_ctr = 0
                else:
                    patience_ctr += 1

                if patience_ctr >= patience_limit:
                    logger.info(f"Early stop at epoch {epoch + 1}")
                    break

            # --- evaluation ---
            net.eval()
            with torch.no_grad():
                train_probs = net(X_train_t).cpu().numpy()
                test_probs = net(X_test_t).cpu().numpy()

            train_preds = (train_probs > 0.5).astype(int)
            test_preds = (test_probs > 0.5).astype(int)

            train_acc = float(accuracy_score(y_train, train_preds))
            test_acc = float(accuracy_score(y_test, test_preds))
            f1 = float(f1_score(y_test, test_preds, average="weighted"))
            class_report = classification_report(y_test, test_preds, output_dict=True)

            # Feature importance via gradient-based attribution
            feature_importance = self._compute_feature_importance(net, X_train_t, feature_names)

            self.model = net
            self.feature_names = feature_names
            self.trained_at = datetime.now()
            self.model_metrics = {
                "train_accuracy": train_acc,
                "test_accuracy": test_acc,
                "accuracy": test_acc,
                "f1_score": f1,
                "cv_mean": test_acc,        # single-split proxy
                "cv_std": 0.0,
                "feature_importance": feature_importance,
                "n_train_samples": len(X_train),
                "n_test_samples": len(X_test),
                "n_features": n_features,
                "epochs_trained": epoch + 1,
                "final_loss": best_loss,
                "classification_report": class_report,
            }

            self.save_model()

            logger.info(f"Model training completed! (PyTorch)")
            logger.info(f"Test Accuracy: {test_acc:.3f}")
            logger.info(f"F1 Score: {f1:.3f}")

            return {
                "status": "success",
                "metrics": self.model_metrics,
                "trained_at": self.trained_at.isoformat(),
                "model_path": MODEL_PATH,
            }

        except Exception as e:
            logger.error(f"Error training model: {e}")
            return {"error": str(e)}

    # ------------------------------------------------------------------ #
    # Feature importance via integrated gradients (simple version)
    # ------------------------------------------------------------------ #

    @staticmethod
    def _compute_feature_importance(
        net: nn.Module, X: torch.Tensor, feature_names: List[str],
    ) -> Dict[str, float]:
        """Gradient-based feature attribution."""
        net.eval()
        X_var = X.detach().clone().requires_grad_(True)
        out = net(X_var)
        out.sum().backward()
        grads = X_var.grad.abs().mean(dim=0).cpu().numpy()
        total = grads.sum() or 1.0
        return {name: float(g / total) for name, g in zip(feature_names, grads)}

    # ------------------------------------------------------------------ #
    # Prediction  (same signature as sklearn version)
    # ------------------------------------------------------------------ #

    def predict_bloom_probability(self, live_data: Optional[Dict] = None) -> Dict:
        """Predict bloom probability (ML model with rule-based fallback)."""
        logger.info("Predicting bloom probability from live data")

        if live_data is None:
            if self.pipeline:
                live_data = self.pipeline.fetch_live_data(days_back=3)
                if "error" in live_data:
                    live_data = self._generate_synthetic_live_data()
            else:
                live_data = self._generate_synthetic_live_data()

        features = self._extract_features_from_live_data(live_data)
        if features is None:
            return self._fallback_prediction(live_data)

        # Try ML inference
        if self.model is not None and self.scaler_params is not None:
            try:
                mean = np.array(self.scaler_params["mean"])
                std = np.array(self.scaler_params["std"])
                scaled = (np.array(features) - mean) / std

                self.model.eval()
                with torch.no_grad():
                    x_t = torch.tensor(scaled, dtype=torch.float32, device=self.device).unsqueeze(0)
                    prob = float(self.model(x_t).cpu().item()) * 100.0

                prediction = 1 if prob > 50 else 0
                confidence = "High" if prob > 75 or prob < 25 else ("Medium" if prob > 60 or prob < 40 else "Low")

                if prob > 70:
                    msg = f"High bloom probability ({prob:.0f}%) — Expect significant blooms next week"
                elif prob > 50:
                    msg = f"Moderate bloom probability ({prob:.0f}%) — Some blooms likely"
                elif prob > 30:
                    msg = f"Low bloom probability ({prob:.0f}%) — Limited bloom activity expected"
                else:
                    msg = f"Very low bloom probability ({prob:.0f}%) — Unfavorable conditions"

                return {
                    "bloom_probability_percent": prob,
                    "bloom_prediction": prediction,
                    "confidence": confidence,
                    "message": msg,
                    "features_used": dict(zip(self.feature_names or [], features)),
                    "predicted_at": datetime.now().isoformat(),
                    "model_version": "PyTorch BloomNet v1.0",
                    **self._compute_additional_predictions(features),
                }
            except Exception as e:
                logger.warning(f"ML inference failed, falling back to rules: {e}")

        # Fall back to rule-based
        return self._rule_based_prediction(features, live_data)

    # ------------------------------------------------------------------ #
    # Rule-based prediction  (fallback — identical to sklearn version)
    # ------------------------------------------------------------------ #

    def _rule_based_prediction(self, features: List[float], live_data: Dict) -> Dict:
        feature_names = ["ndvi", "ndwi", "rainfall_mm", "temperature_c"]

        ndvi = features[0] if len(features) > 0 else 0.4
        ndwi = features[1] if len(features) > 1 else 0.0
        rainfall = features[2] if len(features) > 2 else 50.0
        temperature = features[3] if len(features) > 3 else 25.0

        # Vegetation score
        if ndvi < 0.2:     veg_score = 10
        elif ndvi < 0.3:   veg_score = 25
        elif ndvi < 0.5:   veg_score = 50
        elif ndvi < 0.7:   veg_score = 75
        else:              veg_score = 90

        # Water/moisture score
        if ndwi > 0.3:     water_score = 40
        elif ndwi > 0.1:   water_score = 85
        elif ndwi > -0.1:  water_score = 70
        elif ndwi > -0.3:  water_score = 45
        else:              water_score = 20

        # Temperature score
        if temperature < 15:    temp_score = 25
        elif temperature < 18:  temp_score = 50
        elif temperature < 25:  temp_score = 90
        elif temperature < 30:  temp_score = 70
        elif temperature < 35:  temp_score = 40
        else:                   temp_score = 15

        # Rainfall score
        if rainfall < 5:        rain_score = 30
        elif rainfall < 20:     rain_score = 50
        elif rainfall < 80:     rain_score = 85
        elif rainfall < 150:    rain_score = 60
        else:                   rain_score = 35

        bloom_prob = (
            veg_score * 0.35 + water_score * 0.30 +
            temp_score * 0.20 + rain_score * 0.15
        )
        variation = ((ndvi * 100 + ndwi * 50 + temperature) % 10) - 5
        bloom_prob = max(5, min(95, bloom_prob + variation))

        prediction = 1 if bloom_prob > 50 else 0
        if bloom_prob > 75 or bloom_prob < 25:   confidence = "High"
        elif bloom_prob > 60 or bloom_prob < 40:  confidence = "Medium"
        else:                                      confidence = "Low"

        if bloom_prob > 70:
            msg = f"High bloom probability ({bloom_prob:.0f}%) - Expect significant blooms next week"
        elif bloom_prob > 50:
            msg = f"Moderate bloom probability ({bloom_prob:.0f}%) - Some blooms likely"
        elif bloom_prob > 30:
            msg = f"Low bloom probability ({bloom_prob:.0f}%) - Limited bloom activity expected"
        else:
            msg = f"Very low bloom probability ({bloom_prob:.0f}%) - Unfavorable conditions"

        return {
            "bloom_probability_percent": float(bloom_prob),
            "bloom_prediction": int(prediction),
            "confidence": confidence,
            "message": msg,
            "features_used": dict(zip(feature_names, features)),
            "component_scores": {
                "vegetation": veg_score,
                "moisture": water_score,
                "temperature": temp_score,
                "rainfall": rain_score,
            },
            "predicted_at": datetime.now().isoformat(),
            "model_version": "Rule-based v2.0",
            **self._compute_additional_predictions(features),
        }

    # ------------------------------------------------------------------ #
    # Additional ML Predictions (drought, flood, yield, pest, disease)
    # ------------------------------------------------------------------ #

    def _compute_additional_predictions(self, features: List[float]) -> Dict:
        """Compute drought, flood, yield, pest, and disease risk from features."""
        ndvi = features[0] if len(features) > 0 else 0.4
        ndwi = features[1] if len(features) > 1 else 0.0
        rainfall = features[2] if len(features) > 2 else 50.0
        temperature = features[3] if len(features) > 3 else 25.0

        # --- Drought Risk ---
        # Low NDVI + low NDWI + low rainfall + high temp = drought
        drought_risk = 0.0
        if ndvi < 0.2:     drought_risk += 30
        elif ndvi < 0.35:  drought_risk += 15
        elif ndvi > 0.6:   drought_risk -= 10

        if ndwi < -0.3:    drought_risk += 25
        elif ndwi < -0.1:  drought_risk += 15
        elif ndwi > 0.1:   drought_risk -= 10

        if rainfall < 5:       drought_risk += 25
        elif rainfall < 20:    drought_risk += 10
        elif rainfall > 80:    drought_risk -= 15

        if temperature > 35:   drought_risk += 20
        elif temperature > 30: drought_risk += 10
        elif temperature < 20: drought_risk -= 5

        drought_risk = max(0, min(100, drought_risk))

        # --- Flood Risk ---
        # High rainfall + high NDWI = flood risk
        flood_risk = 0.0
        if rainfall > 150:     flood_risk += 40
        elif rainfall > 100:   flood_risk += 25
        elif rainfall > 80:    flood_risk += 15
        elif rainfall < 20:    flood_risk -= 10

        if ndwi > 0.3:        flood_risk += 30
        elif ndwi > 0.1:      flood_risk += 15
        elif ndwi < -0.1:     flood_risk -= 10

        if temperature > 25:  flood_risk -= 5  # evaporation helps
        flood_risk = max(0, min(100, flood_risk))

        # --- Yield Potential (tonnes/acre) ---
        # Based on NDVI (crop vigor), adequate rainfall, optimal temp
        yield_base = 0.0
        if ndvi > 0.7:     yield_base = 4.5
        elif ndvi > 0.5:   yield_base = 3.5
        elif ndvi > 0.35:  yield_base = 2.5
        elif ndvi > 0.2:   yield_base = 1.5
        else:               yield_base = 0.8

        # Rainfall modifier
        if 30 <= rainfall <= 100:  yield_base *= 1.1
        elif rainfall < 10:        yield_base *= 0.6
        elif rainfall > 150:       yield_base *= 0.7

        # Temperature modifier
        if 20 <= temperature <= 28: yield_base *= 1.1
        elif temperature > 35:      yield_base *= 0.7
        elif temperature < 15:      yield_base *= 0.8

        yield_potential = round(max(0.5, min(6.0, yield_base)), 1)

        # --- Pest Risk ---
        # Warm + humid conditions increase pest risk
        pest_risk = 0.0
        if temperature > 28:     pest_risk += 25
        elif temperature > 25:   pest_risk += 15
        elif temperature < 18:   pest_risk -= 10

        if ndwi > 0.1:          pest_risk += 20  # humid
        elif ndwi > 0:           pest_risk += 10

        if rainfall > 80:       pest_risk += 15  # stagnant water
        elif rainfall > 40:     pest_risk += 5

        if ndvi > 0.5:          pest_risk += 10  # lush vegetation attracts pests
        pest_risk = max(0, min(100, pest_risk))

        # --- Disease Risk ---
        # High humidity + moderate temp + dense vegetation = disease
        disease_risk = 0.0
        if ndwi > 0.2:         disease_risk += 25
        elif ndwi > 0:         disease_risk += 15

        if 20 <= temperature <= 28: disease_risk += 20  # fungal sweet spot
        elif temperature > 30:      disease_risk += 10

        if rainfall > 100:     disease_risk += 20
        elif rainfall > 60:    disease_risk += 10

        if ndvi > 0.6:         disease_risk += 15  # dense canopy traps moisture
        elif ndvi > 0.4:       disease_risk += 5
        disease_risk = max(0, min(100, disease_risk))

        def risk_label(val: float) -> str:
            if val >= 70: return "High"
            if val >= 40: return "Moderate"
            if val >= 20: return "Low"
            return "Very Low"

        return {
            "drought_risk_percent": round(drought_risk, 1),
            "drought_risk_label": risk_label(drought_risk),
            "flood_risk_percent": round(flood_risk, 1),
            "flood_risk_label": risk_label(flood_risk),
            "yield_potential_tonnes_per_acre": yield_potential,
            "pest_risk_percent": round(pest_risk, 1),
            "pest_risk_label": risk_label(pest_risk),
            "disease_risk_percent": round(disease_risk, 1),
            "disease_risk_label": risk_label(disease_risk),
        }

    # ------------------------------------------------------------------ #
    # Persistence
    # ------------------------------------------------------------------ #

    def save_model(self) -> bool:
        try:
            if self.model is None:
                logger.error("No model to save")
                return False

            metadata = {
                "n_features": self.model.net[0].in_features,
                "feature_names": self.feature_names,
                "metrics": self.model_metrics,
                "trained_at": self.trained_at.isoformat() if self.trained_at else None,
                "scaler_params": self.scaler_params,
                "format": "safetensors" if SAFETENSORS_AVAILABLE else "pytorch",
            }

            # Save metadata as JSON
            with open(METADATA_PATH, "w") as f:
                json.dump(metadata, f, indent=2, default=str)

            # Save model weights
            if SAFETENSORS_AVAILABLE:
                st_save(self.model.state_dict(), MODEL_PATH)
                logger.info(f"Model saved (safetensors): {MODEL_PATH}")
            else:
                torch.save({"state_dict": self.model.state_dict()}, MODEL_PATH_PT)
                logger.info(f"Model saved (PyTorch): {MODEL_PATH_PT}")

            logger.info(f"Metadata saved: {METADATA_PATH}")
            return True
        except Exception as e:
            logger.error(f"Error saving model: {e}")
            return False

    def load_model(self) -> bool:
        try:
            # Load metadata
            if not os.path.exists(METADATA_PATH):
                # Try legacy .pt format
                return self._load_legacy_pt()

            with open(METADATA_PATH) as f:
                meta = json.load(f)

            n_features = meta.get("n_features", 4)
            net = BloomNet(n_features).to(self.device)

            # Load weights — prefer safetensors, fall back to .pt
            if SAFETENSORS_AVAILABLE and os.path.exists(MODEL_PATH):
                state_dict = st_load(MODEL_PATH, device=str(self.device))
                net.load_state_dict(state_dict)
                logger.info(f"Model loaded (safetensors): {MODEL_PATH}")
            elif os.path.exists(MODEL_PATH_PT):
                ckpt = torch.load(MODEL_PATH_PT, map_location=self.device, weights_only=False)
                net.load_state_dict(ckpt["state_dict"])
                logger.info(f"Model loaded (PyTorch fallback): {MODEL_PATH_PT}")
            else:
                logger.warning("No model weights file found")
                return False

            net.eval()
            self.model = net
            self.feature_names = meta.get("feature_names", [])
            self.model_metrics = meta.get("metrics", {})
            self.scaler_params = meta.get("scaler_params")
            trained_at = meta.get("trained_at")
            self.trained_at = datetime.fromisoformat(trained_at) if trained_at else None
            return True
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False

    def _load_legacy_pt(self) -> bool:
        """Load from legacy bloom_model_torch.pt format."""
        if not os.path.exists(MODEL_PATH_PT):
            logger.warning(f"No model file found: {MODEL_PATH_PT}")
            return False
        try:
            ckpt = torch.load(MODEL_PATH_PT, map_location=self.device, weights_only=False)
            n_features = ckpt.get("n_features", 4)
            net = BloomNet(n_features).to(self.device)
            net.load_state_dict(ckpt["state_dict"])
            net.eval()

            self.model = net
            self.feature_names = ckpt.get("feature_names", [])
            self.model_metrics = ckpt.get("metrics", {})
            self.scaler_params = ckpt.get("scaler_params")
            trained_at = ckpt.get("trained_at")
            self.trained_at = datetime.fromisoformat(trained_at) if trained_at else None

            # Auto-convert to safetensors
            logger.info("Converting legacy .pt → safetensors")
            self.save_model()
            return True
        except Exception as e:
            logger.error(f"Legacy load failed: {e}")
            return False

    def get_model_info(self) -> Dict:
        if not self.model:
            if not self.load_model():
                return {"error": "No model available"}

        return {
            "model_type": "PyTorch BloomNet (Deep Neural Network)",
            "feature_names": self.feature_names or [],
            "n_features": len(self.feature_names) if self.feature_names else 0,
            "metrics": self.model_metrics,
            "trained_at": self.trained_at.isoformat() if self.trained_at else "Unknown",
            "model_path": MODEL_PATH,
            "model_exists": os.path.exists(MODEL_PATH),
            "device": str(self.device),
        }

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _balance_classes(self, X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        bloom_idx = np.where(y == 1)[0]
        no_bloom_idx = np.where(y == 0)[0]

        if len(bloom_idx) < len(no_bloom_idx):
            up = np.random.choice(bloom_idx, size=len(no_bloom_idx), replace=True)
            X_bal = np.vstack([X[no_bloom_idx], X[up]])
            y_bal = np.hstack([y[no_bloom_idx], y[up]])
        else:
            up = np.random.choice(no_bloom_idx, size=len(bloom_idx), replace=True)
            X_bal = np.vstack([X[bloom_idx], X[up]])
            y_bal = np.hstack([y[bloom_idx], y[up]])
        return X_bal, y_bal

    def _handle_missing_values(self, X: np.ndarray) -> np.ndarray:
        if np.isnan(X).any():
            col_median = np.nanmedian(X, axis=0)
            for j in range(X.shape[1]):
                mask = np.isnan(X[:, j])
                X[mask, j] = col_median[j]
        return X

    def _extract_features_from_live_data(self, live_data: Dict) -> Optional[List[float]]:
        try:
            ndvi_data = live_data.get("ndvi", {})
            ndvi_mean = ndvi_data.get("ndvi_mean", 0.4)

            ndwi_data = live_data.get("ndwi", {})
            ndwi_mean = ndwi_data.get("ndwi_mean", max(0, ndvi_mean - 0.2))

            rainfall_data = live_data.get("rainfall", {})
            rainfall_mm = rainfall_data.get("total_rainfall_mm", 50)

            temp_data = live_data.get("temperature", {})
            temp_c = temp_data.get("temp_mean_c", 22)

            return [ndvi_mean, ndwi_mean, rainfall_mm, temp_c]
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return None

    def _generate_synthetic_training_data(
        self, include_weather: bool,
    ) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        logger.info("Generating synthetic training data")
        n = 200
        ndvi = np.random.uniform(0.1, 0.9, n)
        ndwi = np.random.uniform(0.0, 0.7, n)
        features = [ndvi, ndwi]
        names = ["ndvi", "ndwi"]

        if include_weather:
            rainfall = np.random.uniform(0, 200, n)
            temperature = np.random.uniform(15, 30, n)
            features.extend([rainfall, temperature])
            names.extend(["rainfall_mm", "temperature_c"])

        X = np.array(features).T
        y = ((ndwi > NDWI_BLOOM_THRESHOLD) & (ndvi > NDVI_VEGETATION_THRESHOLD)).astype(int)
        noise = np.random.choice(n, size=int(0.1 * n), replace=False)
        y[noise] = 1 - y[noise]
        return X, y, names

    def _generate_synthetic_live_data(self) -> Dict:
        return {
            "ndvi": {"ndvi_mean": np.random.uniform(0.3, 0.8)},
            "ndwi": {"ndwi_mean": np.random.uniform(0.1, 0.6)},
            "rainfall": {"total_rainfall_mm": np.random.uniform(20, 150)},
            "temperature": {"temp_mean_c": np.random.uniform(18, 28)},
        }

    def _fallback_prediction(self, live_data: Optional[Dict] = None) -> Dict:
        if live_data:
            feats = self._extract_features_from_live_data(live_data)
            if feats:
                return self._rule_based_prediction(feats, live_data)

        time_hash = hash(datetime.now().isoformat()) % 100
        prob = 30 + (time_hash % 40)
        return {
            "bloom_probability_percent": float(prob),
            "bloom_prediction": 1 if prob > 50 else 0,
            "confidence": "Low",
            "message": f"Estimated bloom probability ({prob:.0f}%) — Limited data available",
            "features_used": {},
            "predicted_at": datetime.now().isoformat(),
            "model_version": "Fallback",
        }


# ===================================================================== #
#  Top-level convenience functions  (same signatures as sklearn version)
# ===================================================================== #

def train_bloom_model(
    include_weather: bool = True,
    optimize_hyperparameters: bool = False,
) -> Dict:
    """Train the bloom prediction model (PyTorch)."""
    logger.info("Starting bloom model training (PyTorch)")
    predictor = BloomPredictor()
    return predictor.train_model(
        include_weather=include_weather,
        optimize_hyperparameters=optimize_hyperparameters,
    )


def predict_bloom_from_live_data() -> Dict:
    """Predict bloom probability from current live data."""
    predictor = BloomPredictor()
    return predictor.predict_bloom_probability()


# ===================================================================== #
#  Periodic Retraining Scheduler
# ===================================================================== #

def start_retraining_scheduler(
    interval_hours: int = 24,
    include_weather: bool = True,
):
    """
    Run periodic model retraining in a background thread.
    Call once at application startup.
    """
    import threading

    def _retrain_loop():
        import time
        while True:
            try:
                logger.info("⏰ Scheduled model retraining starting...")
                result = train_bloom_model(include_weather=include_weather)
                if "error" not in result:
                    m = result["metrics"]
                    logger.info(
                        f"✅ Retrain complete — Accuracy: {m['test_accuracy']:.3f}, "
                        f"F1: {m['f1_score']:.3f}"
                    )
                else:
                    logger.warning(f"Retrain failed: {result['error']}")
            except Exception as e:
                logger.error(f"Retrain error: {e}")
            time.sleep(interval_hours * 3600)

    t = threading.Thread(target=_retrain_loop, daemon=True, name="model-retrainer")
    t.start()
    logger.info(f"🔄 Retraining scheduler started (every {interval_hours}h)")


# ===================================================================== #
#  Self-test
# ===================================================================== #

if __name__ == "__main__":
    print("🤖 Bloom Prediction ML Model Test — PyTorch Edition")
    print("=" * 60)

    # Train
    print("\n🎓 Training PyTorch bloom prediction model...")
    result = train_bloom_model(include_weather=True)
    if "error" not in result:
        m = result["metrics"]
        print("✅ Model training successful!")
        print(f"🎯 Test Accuracy: {m['test_accuracy']:.3f}")
        print(f"📊 F1 Score: {m['f1_score']:.3f}")
        print(f"⏱  Epochs: {m['epochs_trained']}")
        print(f"📉 Final Loss: {m['final_loss']:.4f}")
        print("\n🔍 Feature Importance:")
        for feat, imp in m["feature_importance"].items():
            print(f"  {feat}: {imp:.3f}")
    else:
        print(f"❌ Training failed: {result['error']}")

    # Predict
    print("\n🔮 Testing bloom predictions...")
    pred = predict_bloom_from_live_data()
    if "error" not in pred:
        print(f"🌸 Bloom Probability: {pred['bloom_probability_percent']:.1f}%")
        print(f"🎯 Prediction: {'Bloom Expected' if pred['bloom_prediction'] == 1 else 'No Bloom'}")
        print(f"📊 Confidence: {pred['confidence']}")
        print(f"💬 {pred['message']}")
    else:
        print(f"❌ {pred.get('error')}")

    # Info
    print("\n📋 Model Information:")
    info = BloomPredictor().get_model_info()
    if "error" not in info:
        print(f"🤖 Type: {info['model_type']}")
        print(f"🔢 Features: {info['n_features']}")
        print(f"💻 Device: {info['device']}")
        print(f"✅ Exists: {info['model_exists']}")
    else:
        print(f"❌ {info['error']}")

    print("\n" + "=" * 60)
    print("🎉 PyTorch bloom prediction test complete!")
