"""
Disease Detection Service for Smart Shamba Platform
Handles image-based crop disease detection using BloomVisionCNN (EfficientNet-B0).

Pipeline:
    1. ESP32-CAM captures weekly farm images → uploaded via REST endpoint
    2. Image stored on disk with unique URL identifier
    3. BloomVisionCNN runs inference → 6 classes:
       healthy | leaf_blight | rust | aphid_damage | bloom_detected | wilting
    4. Results saved to crop_images table in PostgreSQL
    5. If disease detected → RAG alert pipeline generates actionable advice
"""

import os
import io
import uuid
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------- Image processing ----------
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("Pillow not installed — image processing disabled")

# ---------- PyTorch ----------
try:
    import torch
    from torchvision import transforms
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch/torchvision not available — disease detection disabled")

# ---------- Paths ----------
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
IMAGES_DIR = os.path.join(DATA_DIR, "farm_images")
MODELS_DIR = os.path.join(DATA_DIR, "models")
os.makedirs(IMAGES_DIR, exist_ok=True)

# ---------- Disease classes ----------
DISEASE_CLASSES = [
    "healthy", "leaf_blight", "rust",
    "aphid_damage", "bloom_detected", "wilting",
]

# Classes that indicate a disease (for alerting)
DISEASE_POSITIVE = {"leaf_blight", "rust", "aphid_damage", "wilting"}


class DiseaseDetectionService:
    """
    Crop disease detection from camera images.
    Uses BloomVisionCNN (EfficientNet-B0) for classification.
    """

    def __init__(self, models_dir: str = MODELS_DIR, device: str = "auto"):
        self.models_dir = models_dir
        self.device = torch.device(
            "cuda" if device == "auto" and TORCH_AVAILABLE and torch.cuda.is_available()
            else "cpu"
        ) if TORCH_AVAILABLE else None

        self.vision_model = None
        self._model_loaded = False
        self.model_version = "v1.0"

        # Image transform (EfficientNet-B0 expects 224×224, ImageNet normalization)
        if TORCH_AVAILABLE:
            self.transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225],
                ),
            ])

        logger.info("DiseaseDetectionService initialized")

    # ------------------------------------------------------------------ #
    #  Model loading
    # ------------------------------------------------------------------ #

    def load_model(self) -> bool:
        """Load the BloomVisionCNN model from safetensors or .pt file."""
        if not TORCH_AVAILABLE:
            logger.warning("Cannot load model — PyTorch not available")
            return False

        if self._model_loaded:
            return True

        try:
            from train_model_pytorch import BloomVisionCNN

            # Try safetensors first
            vis_path = os.path.join(self.models_dir, "vision_cnn.safetensors")
            vis_meta = os.path.join(self.models_dir, "vision_cnn_meta.json")

            if os.path.exists(vis_path):
                import json
                try:
                    from safetensors.torch import load_file as st_load
                except ImportError:
                    st_load = None

                meta = {}
                if os.path.exists(vis_meta):
                    with open(vis_meta) as f:
                        meta = json.load(f)

                n_classes = meta.get("n_classes", 6)
                model = BloomVisionCNN(n_classes=n_classes, pretrained=False)

                if st_load:
                    state = st_load(vis_path, device=str(self.device))
                    model.load_state_dict(state)
                else:
                    logger.warning("safetensors not available — trying torch.load")
                    return False

                model = model.to(self.device)
                model.eval()
                self.vision_model = model
                self._model_loaded = True
                self.model_version = meta.get("version", "v1.0")
                logger.info(f"✓ BloomVisionCNN loaded from safetensors (classes={n_classes})")
                return True

            # Try legacy .pt file
            pt_path = os.path.join(self.models_dir, "vision_cnn.pt")
            if os.path.exists(pt_path):
                model = BloomVisionCNN(n_classes=6, pretrained=False)
                ckpt = torch.load(pt_path, map_location=self.device, weights_only=False)
                if isinstance(ckpt, dict) and "state_dict" in ckpt:
                    model.load_state_dict(ckpt["state_dict"])
                else:
                    model.load_state_dict(ckpt)
                model = model.to(self.device)
                model.eval()
                self.vision_model = model
                self._model_loaded = True
                logger.info("✓ BloomVisionCNN loaded from .pt file")
                return True

            # No pre-trained weights — use pretrained EfficientNet backbone (transfer learning ready)
            logger.info("No trained vision_cnn weights found — loading pretrained EfficientNet-B0 backbone")
            model = BloomVisionCNN(n_classes=6, pretrained=True)
            model = model.to(self.device)
            model.eval()
            self.vision_model = model
            self._model_loaded = True
            self.model_version = "v0-pretrained-backbone"
            return True

        except Exception as e:
            logger.error(f"Failed to load vision model: {e}")
            return False

    # ------------------------------------------------------------------ #
    #  Image storage
    # ------------------------------------------------------------------ #

    def save_image(self, image_bytes: bytes, farm_id: int, device_id: str,
                   captured_at: Optional[datetime] = None) -> Dict:
        """
        Save an uploaded image to disk with a unique identifier.

        Returns:
            {
                "image_uid": "farm1-esp32001-20260206T080000",
                "file_path": "data/farm_images/farm_1/2026-02-06_esp32-001.jpg",
                "file_size_bytes": 45312,
                "image_width": 640,
                "image_height": 480,
            }
        """
        if not PIL_AVAILABLE:
            raise RuntimeError("Pillow not installed — cannot process images")

        captured_at = captured_at or datetime.utcnow()

        # Create farm subdirectory
        farm_dir = os.path.join(IMAGES_DIR, f"farm_{farm_id}")
        os.makedirs(farm_dir, exist_ok=True)

        # Generate unique identifiers
        ts_str = captured_at.strftime("%Y%m%dT%H%M%S")
        clean_device = device_id.replace("-", "").replace("_", "")
        image_uid = f"farm{farm_id}-{clean_device}-{ts_str}"

        filename = f"{captured_at.strftime('%Y-%m-%d')}_{device_id}.jpg"
        # Avoid collisions by appending short UUID if file exists
        file_path_abs = os.path.join(farm_dir, filename)
        if os.path.exists(file_path_abs):
            short_id = uuid.uuid4().hex[:6]
            filename = f"{captured_at.strftime('%Y-%m-%d')}_{device_id}_{short_id}.jpg"
            file_path_abs = os.path.join(farm_dir, filename)
            image_uid = f"{image_uid}-{short_id}"

        # Validate and save image
        try:
            img = Image.open(io.BytesIO(image_bytes))
            width, height = img.size
            # Convert to RGB if needed (e.g., RGBA or grayscale)
            if img.mode != "RGB":
                img = img.convert("RGB")
            img.save(file_path_abs, "JPEG", quality=90)
        except Exception as e:
            raise ValueError(f"Invalid image data: {e}")

        # Relative path for DB storage
        rel_path = os.path.relpath(file_path_abs, BASE_DIR)

        return {
            "image_uid": image_uid,
            "file_path": rel_path,
            "file_size_bytes": os.path.getsize(file_path_abs),
            "image_width": width,
            "image_height": height,
        }

    # ------------------------------------------------------------------ #
    #  Disease inference
    # ------------------------------------------------------------------ #

    def detect_disease(self, image_path: str = None,
                       image_bytes: bytes = None) -> Dict:
        """
        Run crop disease detection on an image.

        Args:
            image_path: Path to image file on disk
            image_bytes: Raw image bytes (alternative to path)

        Returns:
            {
                "classification": "leaf_blight",
                "classification_confidence": 0.87,
                "disease_detected": True,
                "all_probabilities": {"healthy": 0.05, "leaf_blight": 0.87, ...},
                "inference_time_ms": 45.2,
                "model_name": "BloomVisionCNN",
                "model_version": "v1.0",
            }
        """
        if not TORCH_AVAILABLE or not PIL_AVAILABLE:
            return {
                "classification": "unknown",
                "classification_confidence": 0.0,
                "disease_detected": False,
                "error": "PyTorch or Pillow not available",
            }

        # Load model if needed
        if not self._model_loaded:
            if not self.load_model():
                return {
                    "classification": "unknown",
                    "classification_confidence": 0.0,
                    "disease_detected": False,
                    "error": "Vision model not available",
                }

        try:
            # Load image
            if image_bytes:
                img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            elif image_path:
                abs_path = image_path if os.path.isabs(image_path) else os.path.join(BASE_DIR, image_path)
                img = Image.open(abs_path).convert("RGB")
            else:
                raise ValueError("Either image_path or image_bytes required")

            # Transform and inference
            start_time = time.time()
            tensor = self.transform(img).unsqueeze(0).to(self.device)

            with torch.no_grad():
                logits = self.vision_model(tensor)
                probs = torch.softmax(logits, dim=-1)[0]
                top_idx = probs.argmax().item()

            inference_ms = (time.time() - start_time) * 1000

            classification = DISEASE_CLASSES[top_idx] if top_idx < len(DISEASE_CLASSES) else f"class_{top_idx}"
            confidence = float(probs[top_idx])
            all_probs = {c: round(float(p), 4) for c, p in zip(DISEASE_CLASSES, probs)}

            return {
                "classification": classification,
                "classification_confidence": round(confidence, 4),
                "disease_detected": classification in DISEASE_POSITIVE,
                "all_probabilities": all_probs,
                "inference_time_ms": round(inference_ms, 1),
                "model_name": "BloomVisionCNN",
                "model_version": self.model_version,
            }

        except Exception as e:
            logger.error(f"Disease detection error: {e}")
            return {
                "classification": "error",
                "classification_confidence": 0.0,
                "disease_detected": False,
                "error": str(e),
            }

    # ------------------------------------------------------------------ #
    #  Combined: save + detect + store results in DB
    # ------------------------------------------------------------------ #

    def process_farm_image(self, image_bytes: bytes, farm_id: int,
                           device_id: str, farmer_id: int,
                           captured_at: Optional[datetime] = None,
                           capture_type: str = "weekly_scheduled") -> Dict:
        """
        Full pipeline: save image → run inference → store results in PostgreSQL.

        Returns:
            {
                "image_uid": "...",
                "classification": "leaf_blight",
                "disease_detected": True,
                "confidence": 0.87,
                "alert_needed": True,
                "crop_image_id": 42,
            }
        """
        captured_at = captured_at or datetime.utcnow()

        # 1. Save image to disk
        save_result = self.save_image(image_bytes, farm_id, device_id, captured_at)

        # 2. Run disease detection
        detection = self.detect_disease(image_bytes=image_bytes)

        # 3. Store in PostgreSQL
        try:
            from database.connection import get_sync_session
            from database.models import CropImage

            with get_sync_session() as session:
                crop_image = CropImage(
                    image_uid=save_result["image_uid"],
                    farm_id=farm_id,
                    device_id=device_id,
                    farmer_id=farmer_id,
                    file_path=save_result["file_path"],
                    file_size_bytes=save_result["file_size_bytes"],
                    mime_type="image/jpeg",
                    image_width=save_result.get("image_width"),
                    image_height=save_result.get("image_height"),
                    captured_at=captured_at,
                    capture_type=capture_type,
                    classification=detection.get("classification"),
                    classification_confidence=detection.get("classification_confidence"),
                    all_probabilities=detection.get("all_probabilities"),
                    disease_detected=detection.get("disease_detected", False),
                    model_name=detection.get("model_name"),
                    model_version=detection.get("model_version"),
                    inference_time_ms=detection.get("inference_time_ms"),
                )
                session.add(crop_image)
                session.commit()
                session.refresh(crop_image)
                crop_image_id = crop_image.id

            logger.info(
                f"✓ Image processed: {save_result['image_uid']} → "
                f"{detection.get('classification')} ({detection.get('classification_confidence', 0):.2%})"
            )
        except Exception as e:
            logger.error(f"Failed to store crop image in DB: {e}")
            crop_image_id = None

        disease_detected = detection.get("disease_detected", False)
        confidence = detection.get("classification_confidence", 0)

        return {
            "image_uid": save_result["image_uid"],
            "file_path": save_result["file_path"],
            "classification": detection.get("classification", "unknown"),
            "classification_confidence": confidence,
            "disease_detected": disease_detected,
            "all_probabilities": detection.get("all_probabilities", {}),
            "inference_time_ms": detection.get("inference_time_ms"),
            "alert_needed": disease_detected and confidence > 0.5,
            "crop_image_id": crop_image_id,
        }

    # ------------------------------------------------------------------ #
    #  Query disease history for a farm
    # ------------------------------------------------------------------ #

    def get_farm_disease_history(self, farm_id: int, limit: int = 20) -> List[Dict]:
        """Get recent disease detection results for a farm."""
        try:
            from database.connection import get_sync_session
            from database.models import CropImage
            from sqlmodel import select
            from sqlalchemy import and_

            with get_sync_session() as session:
                stmt = (
                    select(CropImage)
                    .where(CropImage.farm_id == farm_id)
                    .order_by(CropImage.captured_at.desc())
                    .limit(limit)
                )
                results = session.exec(stmt).all()
                return [
                    {
                        "image_uid": r.image_uid,
                        "captured_at": r.captured_at.isoformat() if r.captured_at else None,
                        "classification": r.classification,
                        "confidence": r.classification_confidence,
                        "disease_detected": r.disease_detected,
                        "capture_type": r.capture_type,
                        "file_path": r.file_path,
                        "alert_sent": r.alert_sent,
                    }
                    for r in results
                ]
        except Exception as e:
            logger.error(f"Error getting disease history: {e}")
            return []

    def get_latest_disease_status(self, farm_id: int) -> Optional[Dict]:
        """Get the most recent disease detection result for a farm."""
        history = self.get_farm_disease_history(farm_id, limit=1)
        return history[0] if history else None

    # ------------------------------------------------------------------ #
    #  Multimodal training sample creation
    # ------------------------------------------------------------------ #

    def create_multimodal_training_sample(
        self,
        farm_id: int,
        farmer_id: int,
        image_uid: str,
        image_path: str,
        classification: str,
        cnn_confidence: float,
        sensor_data: Optional[Dict] = None,
        satellite_data: Optional[Dict] = None,
        label_source: str = "cnn_prediction",
    ) -> Optional[int]:
        """
        Create a labeled multimodal training sample when disease detection
        + soil telemetry + satellite data correlate.

        This feeds the retraining loop: confirmed labeled samples are used
        by train_vision_cnn.py and the multimodal inference service.

        Args:
            farm_id: Farm where image was captured
            farmer_id: Farmer owning the farm
            image_uid: Unique image identifier
            image_path: Path to image file on disk
            classification: CNN classification label
            cnn_confidence: Model confidence score
            sensor_data: Latest IoT sensor readings
            satellite_data: Latest satellite observations
            label_source: How the label was determined

        Returns:
            training sample ID or None
        """
        try:
            from database.connection import get_sync_session
            from database.models import MultimodalTrainingSample

            sensor = sensor_data or {}
            satellite = satellite_data or {}

            # Calculate correlation score: how many data sources are present
            data_sources = 0
            if image_uid:
                data_sources += 1
            if any(sensor.get(k) is not None for k in
                   ['soil_ph', 'soil_moisture_pct', 'soil_nitrogen', 'temperature_c']):
                data_sources += 1
            if any(satellite.get(k) is not None for k in ['ndvi', 'ndwi', 'rainfall_mm']):
                data_sources += 1

            correlation_score = data_sources / 3.0  # 0.33 to 1.0

            sample = MultimodalTrainingSample(
                farm_id=farm_id,
                farmer_id=farmer_id,
                image_uid=image_uid,
                image_path=image_path,
                label=classification,
                label_source=label_source,
                cnn_confidence=cnn_confidence,
                # Soil telemetry
                soil_ph=sensor.get('soil_ph'),
                soil_moisture_pct=sensor.get('soil_moisture_pct'),
                soil_nitrogen=sensor.get('soil_nitrogen'),
                soil_phosphorus=sensor.get('soil_phosphorus'),
                soil_potassium=sensor.get('soil_potassium'),
                temperature_c=sensor.get('temperature_c'),
                humidity_pct=sensor.get('humidity_pct'),
                # Satellite
                ndvi=satellite.get('ndvi'),
                ndwi=satellite.get('ndwi'),
                rainfall_mm=satellite.get('rainfall_mm'),
                land_surface_temp_c=satellite.get('land_surface_temperature_c',
                                                  satellite.get('temperature_mean_c')),
                correlation_score=correlation_score,
            )

            with get_sync_session() as session:
                session.add(sample)
                session.commit()
                session.refresh(sample)
                logger.info(
                    f"✓ Training sample {sample.id}: {classification} "
                    f"(confidence={cnn_confidence:.2%}, correlation={correlation_score:.2f})"
                )
                return sample.id

        except Exception as e:
            logger.error(f"Failed to create training sample: {e}")
            return None

    def get_training_samples(
        self, unused_only: bool = True, min_confidence: float = 0.6,
        min_correlation: float = 0.33, limit: int = 500,
    ) -> List[Dict]:
        """
        Retrieve multimodal training samples for model retraining.

        Args:
            unused_only: Only return samples not yet used in training
            min_confidence: Minimum CNN confidence threshold
            min_correlation: Minimum data source correlation score
            limit: Max samples to return
        """
        try:
            from database.connection import get_sync_session
            from database.models import MultimodalTrainingSample
            from sqlmodel import select

            with get_sync_session() as session:
                stmt = select(MultimodalTrainingSample)
                if unused_only:
                    stmt = stmt.where(MultimodalTrainingSample.used_in_training == False)
                stmt = stmt.where(
                    MultimodalTrainingSample.cnn_confidence.isnot(None)
                ).where(
                    MultimodalTrainingSample.cnn_confidence >= min_confidence
                ).where(
                    MultimodalTrainingSample.correlation_score.isnot(None)
                ).where(
                    MultimodalTrainingSample.correlation_score >= min_correlation
                ).order_by(
                    MultimodalTrainingSample.created_at.desc()
                ).limit(limit)

                samples = session.exec(stmt).all()
                return [
                    {
                        "id": s.id,
                        "image_uid": s.image_uid,
                        "image_path": s.image_path,
                        "label": s.label,
                        "label_source": s.label_source,
                        "cnn_confidence": s.cnn_confidence,
                        "soil_ph": s.soil_ph,
                        "soil_moisture_pct": s.soil_moisture_pct,
                        "soil_nitrogen": s.soil_nitrogen,
                        "ndvi": s.ndvi,
                        "ndwi": s.ndwi,
                        "correlation_score": s.correlation_score,
                        "created_at": s.created_at.isoformat() if s.created_at else None,
                    }
                    for s in samples
                ]
        except Exception as e:
            logger.error(f"Error getting training samples: {e}")
            return []

    def mark_samples_used(self, sample_ids: List[int], epoch: int = 0):
        """Mark training samples as used after a retraining run."""
        try:
            from database.connection import get_sync_session
            from database.models import MultimodalTrainingSample

            with get_sync_session() as session:
                for sid in sample_ids:
                    sample = session.get(MultimodalTrainingSample, sid)
                    if sample:
                        sample.used_in_training = True
                        sample.training_epoch = epoch
                session.commit()
                logger.info(f"Marked {len(sample_ids)} training samples as used (epoch {epoch})")
        except Exception as e:
            logger.error(f"Error marking samples: {e}")


# Quick self-test
if __name__ == "__main__":
    print("🔬 Disease Detection Service — Self Test")
    print("=" * 60)

    svc = DiseaseDetectionService()
    print(f"PIL available: {PIL_AVAILABLE}")
    print(f"PyTorch available: {TORCH_AVAILABLE}")

    # Try loading model
    if TORCH_AVAILABLE:
        ok = svc.load_model()
        print(f"Model loaded: {ok}")

        # Create a dummy test image
        if PIL_AVAILABLE:
            dummy = Image.new("RGB", (224, 224), color=(100, 150, 50))
            buf = io.BytesIO()
            dummy.save(buf, "JPEG")
            dummy_bytes = buf.getvalue()

            result = svc.detect_disease(image_bytes=dummy_bytes)
            print(f"Detection result: {result}")

    print("\n✓ Disease detection service test completed!")
