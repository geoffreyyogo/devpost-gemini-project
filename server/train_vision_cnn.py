#!/usr/bin/env python3
"""
BloomVisionCNN Training Pipeline — Crop Disease Detection
==========================================================

Trains the EfficientNet-B0 based BloomVisionCNN on plant disease datasets.

Supports:
  - PlantVillage (54K images, 38 classes → mapped to 6)
  - PlantDoc (2.6K real-world images, 27 classes → mapped to 6)
  - Corn/Maize Leaf Disease (4K images, 4 classes → mapped)
  - Crop Diseases Classification (87K images, multi-crop)
  - Custom ESP32-CAM field images (data/farm_images/)

Training phases:
  Phase 1: Pre-train on PlantVillage + PlantDoc (freeze backbone)
  Phase 2: Unfreeze top layers, fine-tune on merged data (lower LR)
  Phase 3: Domain adaptation on ESP32-CAM field images

Usage:
  python train_vision_cnn.py --data-dir ../data/datasets --epochs 30
  python train_vision_cnn.py --data-dir ../data/datasets --phase 2 --resume
  python train_vision_cnn.py --data-dir ../data/farm_images --phase 3 --resume

Expected directory structure (after Kaggle download + extract):
  data/datasets/
    PlantVillage/         ← kaggle: emmarex/plantdisease
      Pepper__bell___healthy/
      Corn_(maize)___Common_rust_/
      ...
    PlantDoc/             ← kaggle: nirmalsankalana/plantdoc-dataset
      train/
      test/
    CornDisease/          ← kaggle: smaranjitghose/corn-or-maize-leaf-disease-dataset
      Blight/
      Common_Rust/
      ...
    CropDiseases/         ← kaggle: mexwell/crop-diseases-classification
      train/
      valid/
"""

import os
import sys
import json
import shutil
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from collections import Counter

import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ── PyTorch ──────────────────────────────────────────────────────────
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset, ConcatDataset, WeightedRandomSampler

from torchvision import transforms
from torchvision.datasets import ImageFolder

try:
    from safetensors.torch import save_file as st_save, load_file as st_load
    SAFETENSORS = True
except ImportError:
    st_save = None  # type: ignore[assignment]
    st_load = None  # type: ignore[assignment]
    SAFETENSORS = False

# Import our model
sys.path.insert(0, str(Path(__file__).parent))
from train_model_pytorch import BloomVisionCNN

# ═══════════════════════════════════════════════════════════════════════
#  CLASS MAPPING — Map external dataset labels → our 6 output classes
# ═══════════════════════════════════════════════════════════════════════

# Our target classes (same as BloomVisionCNN.DEFAULT_CLASSES)
TARGET_CLASSES = [
    "healthy",        # 0 — no disease
    "leaf_blight",    # 1 — bacterial/fungal blight
    "rust",           # 2 — rust diseases
    "aphid_damage",   # 3 — insect/pest damage
    "bloom_detected", # 4 — flowering stage (from satellite/visual)
    "wilting",        # 5 — water stress / wilting / nutrient deficiency
]

CLASS_TO_IDX = {c: i for i, c in enumerate(TARGET_CLASSES)}

# ─── PlantVillage class mapping ────────────────────────────────────
# PlantVillage has 38 classes across 14 crops.  We map them to our 6.
PLANTVILLAGE_MAP = {
    # Healthy classes → healthy (0)
    "Apple___healthy": "healthy",
    "Blueberry___healthy": "healthy",
    "Cherry_(including_sour)___healthy": "healthy",
    "Corn_(maize)___healthy": "healthy",
    "Grape___healthy": "healthy",
    "Orange___Haunglongbing_(Citrus_greening)": "wilting",  # systemic disease → wilting
    "Peach___healthy": "healthy",
    "Pepper,_bell___healthy": "healthy",
    "Pepper__bell___healthy": "healthy",
    "Potato___healthy": "healthy",
    "Raspberry___healthy": "healthy",
    "Soybean___healthy": "healthy",
    "Squash___Powdery_mildew": "leaf_blight",  # fungal → blight
    "Strawberry___healthy": "healthy",
    "Tomato___healthy": "healthy",

    # Blight-family → leaf_blight (1)
    "Apple___Apple_scab": "leaf_blight",
    "Apple___Black_rot": "leaf_blight",
    "Apple___Cedar_apple_rust": "rust",
    "Cherry_(including_sour)___Powdery_mildew": "leaf_blight",
    "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot": "leaf_blight",
    "Corn_(maize)___Northern_Leaf_Blight": "leaf_blight",
    "Grape___Black_rot": "leaf_blight",
    "Grape___Esca_(Black_Measles)": "leaf_blight",
    "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)": "leaf_blight",
    "Peach___Bacterial_spot": "leaf_blight",
    "Pepper,_bell___Bacterial_spot": "leaf_blight",
    "Pepper__bell___Bacterial_spot": "leaf_blight",
    "Potato___Early_blight": "leaf_blight",
    "Potato___Late_blight": "leaf_blight",
    "Strawberry___Leaf_scorch": "leaf_blight",
    "Tomato___Bacterial_spot": "leaf_blight",
    "Tomato___Early_blight": "leaf_blight",
    "Tomato___Late_blight": "leaf_blight",
    "Tomato___Leaf_Mold": "leaf_blight",
    "Tomato___Septoria_leaf_spot": "leaf_blight",
    "Tomato___Target_Spot": "leaf_blight",

    # Rust → rust (2)
    "Corn_(maize)___Common_rust_": "rust",
    "Corn_(maize)___Common_rust": "rust",

    # Insect / pest damage → aphid_damage (3)
    "Tomato___Spider_mites Two-spotted_spider_mite": "aphid_damage",
    "Tomato___Spider_mites_Two-spotted_spider_mite": "aphid_damage",

    # Viral / systemic / wilting → wilting (5)
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus": "wilting",
    "Tomato___Tomato_mosaic_virus": "wilting",
}

# ─── Corn/Maize Disease dataset mapping ─────────────────────────────
CORN_DISEASE_MAP = {
    "Blight": "leaf_blight",
    "Common_Rust": "rust",
    "Common_Rust_": "rust",
    "Gray_Leaf_Spot": "leaf_blight",
    "Healthy": "healthy",
    "healthy": "healthy",
}

# ─── Fallback: keyword-based mapping for unrecognized class names ───
def map_class_by_keywords(class_name: str) -> str:
    """Map unknown class name to our taxonomy using keywords."""
    name_lower = class_name.lower().replace("_", " ").replace("-", " ")

    if "healthy" in name_lower or "normal" in name_lower:
        return "healthy"
    if "blight" in name_lower or "scab" in name_lower or "spot" in name_lower:
        return "leaf_blight"
    if "mildew" in name_lower or "mold" in name_lower or "rot" in name_lower:
        return "leaf_blight"
    if "rust" in name_lower:
        return "rust"
    if "aphid" in name_lower or "mite" in name_lower or "insect" in name_lower:
        return "aphid_damage"
    if "worm" in name_lower or "borer" in name_lower or "beetle" in name_lower:
        return "aphid_damage"
    if "wilt" in name_lower or "curl" in name_lower or "mosaic" in name_lower:
        return "wilting"
    if "virus" in name_lower or "yellow" in name_lower or "deficien" in name_lower:
        return "wilting"
    if "bloom" in name_lower or "flower" in name_lower:
        return "bloom_detected"

    # Default to leaf_blight for any unrecognized disease
    return "leaf_blight"


# ═══════════════════════════════════════════════════════════════════════
#  DATASET CLASSES
# ═══════════════════════════════════════════════════════════════════════

class MappedImageFolder(Dataset):
    """
    Wraps torchvision.ImageFolder but remaps class labels to our 6-class
    taxonomy using the provided mapping dictionary.
    """

    def __init__(self, root: str, transform=None,
                 class_map: Optional[Dict[str, str]] = None,
                 dataset_name: str = "unknown"):
        self.dataset_name = dataset_name
        self.transform = transform
        self.class_map = class_map or {}

        # Use ImageFolder to discover classes and images
        self._inner = ImageFolder(root, transform=transform)

        # Build label remapping: original_idx → target_idx
        self._label_map = {}
        self._unmapped = set()
        for orig_name, orig_idx in self._inner.class_to_idx.items():
            if orig_name in self.class_map:
                target_name = self.class_map[orig_name]
            else:
                target_name = map_class_by_keywords(orig_name)
                self._unmapped.add(orig_name)

            if target_name in CLASS_TO_IDX:
                self._label_map[orig_idx] = CLASS_TO_IDX[target_name]
            else:
                self._label_map[orig_idx] = CLASS_TO_IDX["leaf_blight"]  # safe default

        if self._unmapped:
            logger.info(f"  [{dataset_name}] Auto-mapped {len(self._unmapped)} classes by keyword: "
                        f"{list(self._unmapped)[:10]}…")

        # Count per target class
        counts = Counter()
        for _, orig_label in self._inner.samples:
            counts[self._label_map[orig_label]] += 1
        self.class_counts = counts

        logger.info(f"  [{dataset_name}] {len(self._inner)} images → "
                    f"{dict(sorted({TARGET_CLASSES[k]: v for k, v in counts.items()}.items()))}")

    def __len__(self):
        return len(self._inner)

    def __getitem__(self, idx):
        img, orig_label = self._inner[idx]
        return img, self._label_map[orig_label]


# ═══════════════════════════════════════════════════════════════════════
#  DATA TRANSFORMS
# ═══════════════════════════════════════════════════════════════════════

def get_transforms(phase: str = "train") -> transforms.Compose:
    """
    Image transforms for training and validation.

    Training: random augmentations (flip, rotation, color jitter, perspective)
    Validation: deterministic (resize + center crop + normalize)
    """
    if phase == "train":
        return transforms.Compose([
            transforms.RandomResizedCrop(224, scale=(0.7, 1.0)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomVerticalFlip(p=0.3),
            transforms.RandomRotation(20),
            transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2, hue=0.05),
            transforms.RandomPerspective(distortion_scale=0.2, p=0.3),
            transforms.RandomGrayscale(p=0.05),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
            transforms.RandomErasing(p=0.15, scale=(0.02, 0.15)),
        ])
    else:
        return transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ])


# ═══════════════════════════════════════════════════════════════════════
#  DATASET DISCOVERY & LOADING
# ═══════════════════════════════════════════════════════════════════════

def discover_datasets(data_dir: str) -> Dict[str, str]:
    """
    Auto-discover extracted Kaggle datasets in the data directory.
    Looks for known folder patterns.
    """
    data_path = Path(data_dir)
    found = {}

    # PlantVillage — look for the characteristic class folders
    for candidate in ["PlantVillage", "plantvillage", "plantdisease",
                       "New Plant Diseases Dataset(Augmented)",
                       "plant_disease", "PlantVillage-Dataset"]:
        p = data_path / candidate
        if p.is_dir():
            # Check for sub-structure: might be nested
            for sub in [p, p / "train", p / "color", p / "segmented"]:
                if sub.is_dir() and any(sub.iterdir()):
                    # Verify it has class folders (not just random files)
                    subdirs = [d for d in sub.iterdir() if d.is_dir()]
                    if len(subdirs) >= 5:
                        found["PlantVillage"] = str(sub)
                        break
            if "PlantVillage" in found:
                break

    # PlantDoc
    for candidate in ["PlantDoc", "plantdoc", "plantdoc-dataset"]:
        p = data_path / candidate
        if p.is_dir():
            for sub in [p / "train", p]:
                subdirs = [d for d in sub.iterdir() if d.is_dir()] if sub.is_dir() else []
                if len(subdirs) >= 5:
                    found["PlantDoc"] = str(sub)
                    break

    # Corn/Maize Disease
    for candidate in ["CornDisease", "corn-or-maize-leaf-disease-dataset",
                       "Corn_Disease", "corn_disease", "maize_disease"]:
        p = data_path / candidate
        if p.is_dir():
            subdirs = [d for d in p.iterdir() if d.is_dir()]
            if len(subdirs) >= 2:
                found["CornDisease"] = str(p)

    # Crop Diseases Classification (large merged dataset)
    for candidate in ["CropDiseases", "crop-diseases-classification",
                       "Crop_Diseases"]:
        p = data_path / candidate
        if p.is_dir():
            for sub in [p / "train", p]:
                subdirs = [d for d in sub.iterdir() if d.is_dir()] if sub.is_dir() else []
                if len(subdirs) >= 5:
                    found["CropDiseases"] = str(sub)
                    break

    # ESP32-CAM field images (your own data for Phase 3)
    farm_dir = data_path / "farm_images"
    if farm_dir.is_dir():
        subdirs = [d for d in farm_dir.iterdir() if d.is_dir()]
        if subdirs:
            found["FieldImages"] = str(farm_dir)

    return found


def load_datasets(data_dir: str, phase: str = "train") -> Tuple[Dataset, Dataset]:
    """
    Load and merge all discovered datasets with class mapping.
    Returns (train_dataset, val_dataset).
    """
    transform_train = get_transforms("train")
    transform_val = get_transforms("val")

    found = discover_datasets(data_dir)
    if not found:
        raise FileNotFoundError(
            f"No datasets found in {data_dir}.\n"
            f"Expected subdirectories: PlantVillage/, PlantDoc/, CornDisease/, CropDiseases/\n"
            f"Download from Kaggle and extract into {data_dir}/"
        )

    logger.info(f"Discovered {len(found)} dataset(s): {list(found.keys())}")

    train_sets = []
    val_sets = []

    for name, path in found.items():
        class_map = {
            "PlantVillage": PLANTVILLAGE_MAP,
            "PlantDoc": {},          # keyword-based auto-mapping
            "CornDisease": CORN_DISEASE_MAP,
            "CropDiseases": {},      # keyword-based auto-mapping
            "FieldImages": {},       # should follow our 6-class folder structure
        }.get(name, {})

        try:
            # Check if dataset has train/test split
            train_path = Path(path) / "train"
            test_path = Path(path) / "test"
            val_path = Path(path) / "valid"

            if train_path.is_dir() and (test_path.is_dir() or val_path.is_dir()):
                train_ds = MappedImageFolder(str(train_path), transform_train, class_map, name)
                val_dir = str(val_path) if val_path.is_dir() else str(test_path)
                val_ds = MappedImageFolder(val_dir, transform_val, class_map, f"{name}_val")
            else:
                # Single directory — split 85/15
                full_ds = MappedImageFolder(path, transform_train, class_map, name)
                n_total = len(full_ds)
                n_val = max(1, int(n_total * 0.15))
                n_train = n_total - n_val
                train_ds, val_ds_raw = torch.utils.data.random_split(
                    full_ds, [n_train, n_val],
                    generator=torch.Generator().manual_seed(42)
                )
                # Replace val transform (random_split shares the parent transform)
                val_ds = ValSubset(val_ds_raw, transform_val)

            train_sets.append(train_ds)
            val_sets.append(val_ds)
        except Exception as e:
            logger.warning(f"Failed to load {name}: {e}")

    if not train_sets:
        raise RuntimeError("No datasets could be loaded successfully.")

    train_combined = ConcatDataset(train_sets) if len(train_sets) > 1 else train_sets[0]
    val_combined = ConcatDataset(val_sets) if len(val_sets) > 1 else val_sets[0]

    logger.info(f"Combined: {len(train_combined)} train + {len(val_combined)} val images")
    return train_combined, val_combined


class ValSubset(Dataset):
    """Wraps a Subset with a different transform for validation."""
    def __init__(self, subset, transform):
        self.subset = subset
        self.transform = transform

    def __len__(self):
        return len(self.subset)

    def __getitem__(self, idx):
        # Get the inner dataset's sample
        inner_idx = self.subset.indices[idx]
        ds = self.subset.dataset
        # Get raw image path and label
        img_path, orig_label = ds._inner.samples[inner_idx]
        from PIL import Image
        img = Image.open(img_path).convert("RGB")
        if self.transform:
            img = self.transform(img)
        label = ds._label_map[orig_label]
        return img, label


# ═══════════════════════════════════════════════════════════════════════
#  TRAINING ENGINE
# ═══════════════════════════════════════════════════════════════════════

def make_weighted_sampler(dataset: Dataset, n_classes: int = 6) -> WeightedRandomSampler:
    """
    Create a weighted random sampler to handle class imbalance.
    PlantVillage has ~2K per class but rust/aphid are underrepresented in our mapping.
    """
    labels = []
    for i in range(len(dataset)):  # type: ignore[arg-type]
        _, label = dataset[i]
        labels.append(label)

    label_counts = Counter(labels)
    total = len(labels)
    class_weights = {cls: total / (n_classes * count) for cls, count in label_counts.items()}
    sample_weights = [class_weights[l] for l in labels]

    return WeightedRandomSampler(
        weights=sample_weights,
        num_samples=len(sample_weights),
        replacement=True,
    )


def train_one_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    optimizer: optim.Optimizer,
    device: torch.device,
    epoch: int,
) -> float:
    """Train for one epoch, return average loss."""
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    for batch_idx, (images, labels) in enumerate(dataloader):
        images, labels = images.to(device), labels.to(device)

        optimizer.zero_grad()
        logits = model(images)
        loss = criterion(logits, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * images.size(0)
        preds = logits.argmax(dim=1)
        correct += (preds == labels).sum().item()
        total += labels.size(0)

        if (batch_idx + 1) % 50 == 0:
            logger.info(f"  Epoch {epoch+1} | Batch {batch_idx+1} | "
                        f"Loss: {loss.item():.4f} | Acc: {correct/total:.3f}")

    return running_loss / total


@torch.no_grad()
def evaluate(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> Tuple[float, float, Dict]:
    """Evaluate model, return (loss, accuracy, per_class_metrics)."""
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0
    all_preds = []
    all_labels = []

    for images, labels in dataloader:
        images, labels = images.to(device), labels.to(device)
        logits = model(images)
        loss = criterion(logits, labels)

        running_loss += loss.item() * images.size(0)
        preds = logits.argmax(dim=1)
        correct += (preds == labels).sum().item()
        total += labels.size(0)
        all_preds.extend(preds.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())

    avg_loss = running_loss / total
    accuracy = correct / total

    # Per-class metrics
    from sklearn.metrics import classification_report
    report: Dict = classification_report(  # type: ignore[assignment]
        all_labels, all_preds,
        target_names=TARGET_CLASSES,
        output_dict=True,
        zero_division=0,
    )

    return avg_loss, accuracy, report


def train_vision_model(
    data_dir: str,
    output_dir: str = "../data/models",
    phase: int = 1,
    epochs: int = 30,
    batch_size: int = 32,
    lr: float = 1e-3,
    resume: bool = False,
    device_str: str = "auto",
) -> Dict:
    """
    Train BloomVisionCNN on plant disease datasets.

    Phase 1: Freeze EfficientNet backbone, train classifier head only
    Phase 2: Unfreeze top layers, fine-tune with lower LR
    Phase 3: Full fine-tune on field images (domain adaptation)
    """
    device = torch.device(
        "cuda" if device_str == "auto" and torch.cuda.is_available() else "cpu"
    )
    logger.info(f"Device: {device}  |  Phase: {phase}  |  Epochs: {epochs}")

    # ── Load data ──
    train_ds, val_ds = load_datasets(data_dir, "train")

    # Weighted sampler for class imbalance
    # Skip for ConcatDataset (too slow to iterate), use standard shuffle
    use_sampler = not isinstance(train_ds, ConcatDataset)

    train_loader = DataLoader(
        train_ds, batch_size=batch_size, shuffle=not use_sampler,
        sampler=make_weighted_sampler(train_ds) if use_sampler else None,
        num_workers=2, pin_memory=True, drop_last=True,
    )
    val_loader = DataLoader(
        val_ds, batch_size=batch_size, shuffle=False,
        num_workers=2, pin_memory=True,
    )

    # ── Model ──
    model = BloomVisionCNN(n_classes=6, pretrained=True).to(device)

    # Resume from checkpoint
    checkpoint_path = os.path.join(output_dir, "vision_cnn.safetensors")
    pt_path = os.path.join(output_dir, "vision_cnn_checkpoint.pt")
    start_epoch = 0

    if resume:
        if SAFETENSORS and os.path.exists(checkpoint_path):
            state = st_load(checkpoint_path, device=str(device))
            model.load_state_dict(state)
            logger.info(f"✓ Resumed from {checkpoint_path}")
        elif os.path.exists(pt_path):
            ckpt = torch.load(pt_path, map_location=device, weights_only=False)
            model.load_state_dict(ckpt["model_state"])
            start_epoch = ckpt.get("epoch", 0)
            logger.info(f"✓ Resumed from {pt_path} (epoch {start_epoch})")

    # ── Freeze strategy ──
    if phase == 1:
        # Freeze entire backbone, train classifier only
        for param in model.backbone.parameters():
            param.requires_grad = False
        trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
        logger.info(f"Phase 1: Backbone frozen. Trainable params: {trainable:,}")
        optimizer = optim.Adam(model.classifier.parameters(), lr=lr, weight_decay=1e-4)

    elif phase == 2:
        # Unfreeze top ~30% of backbone layers
        all_params = list(model.backbone.parameters())
        freeze_until = int(len(all_params) * 0.7)
        for i, param in enumerate(all_params):
            param.requires_grad = (i >= freeze_until)
        trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
        logger.info(f"Phase 2: Top 30% unfrozen. Trainable params: {trainable:,}")
        optimizer = optim.Adam([
            {"params": model.classifier.parameters(), "lr": lr},
            {"params": [p for p in model.backbone.parameters() if p.requires_grad],
             "lr": lr * 0.1},  # lower LR for backbone
        ], weight_decay=1e-4)

    else:  # phase 3
        # Full fine-tune (all params trainable)
        for param in model.parameters():
            param.requires_grad = True
        trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
        logger.info(f"Phase 3: All params trainable: {trainable:,}")
        optimizer = optim.Adam(model.parameters(), lr=lr * 0.01, weight_decay=1e-4)

    # ── Loss + scheduler ──
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
    scheduler = optim.lr_scheduler.CosineAnnealingWarmRestarts(optimizer, T_0=10, T_mult=2)

    # ── Training loop ──
    best_val_acc = 0.0
    best_val_loss = float("inf")
    history = {"train_loss": [], "val_loss": [], "val_acc": []}

    for epoch in range(start_epoch, start_epoch + epochs):
        train_loss = train_one_epoch(model, train_loader, criterion, optimizer, device, epoch)
        val_loss, val_acc, class_report = evaluate(model, val_loader, criterion, device)
        scheduler.step()

        current_lr = optimizer.param_groups[0]["lr"]
        logger.info(
            f"Epoch {epoch+1}/{start_epoch+epochs} | "
            f"Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | "
            f"Val Acc: {val_acc:.3f} | LR: {current_lr:.6f}"
        )

        history["train_loss"].append(train_loss)
        history["val_loss"].append(val_loss)
        history["val_acc"].append(val_acc)

        # Save best model
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_val_loss = val_loss

            # Save safetensors
            os.makedirs(output_dir, exist_ok=True)
            if SAFETENSORS:
                st_save(model.state_dict(), checkpoint_path)
            # Also save PyTorch checkpoint with optimizer state (for resume)
            torch.save({
                "model_state": model.state_dict(),
                "optimizer_state": optimizer.state_dict(),
                "epoch": epoch + 1,
                "val_acc": val_acc,
                "val_loss": val_loss,
                "phase": phase,
            }, pt_path)

            logger.info(f"  ★ Best model saved (acc={val_acc:.3f})")

    # ── Final evaluation ──
    logger.info("\n" + "=" * 60)
    logger.info("FINAL EVALUATION")
    logger.info("=" * 60)

    # Reload best model
    if SAFETENSORS and os.path.exists(checkpoint_path):
        state = st_load(checkpoint_path, device=str(device))
        model.load_state_dict(state)
    elif os.path.exists(pt_path):
        ckpt = torch.load(pt_path, map_location=device, weights_only=False)
        model.load_state_dict(ckpt["model_state"])

    val_loss, val_acc, class_report = evaluate(model, val_loader, criterion, device)

    logger.info(f"Best Val Accuracy: {best_val_acc:.4f}")
    logger.info(f"Best Val Loss:     {best_val_loss:.4f}")
    logger.info("\nPer-class metrics:")
    for cls_name in TARGET_CLASSES:
        if cls_name in class_report:
            m = class_report[cls_name]
            logger.info(f"  {cls_name:20s}  P={m['precision']:.3f}  R={m['recall']:.3f}  "
                        f"F1={m['f1-score']:.3f}  N={m['support']}")

    # ── Save metadata ──
    meta = {
        "model_type": "BloomVisionCNN",
        "backbone": "EfficientNet-B0",
        "n_classes": 6,
        "classes": TARGET_CLASSES,
        "input_size": [3, 224, 224],
        "phase": phase,
        "epochs_trained": epochs,
        "best_val_accuracy": best_val_acc,
        "best_val_loss": best_val_loss,
        "classification_report": class_report,
        "history": history,
        "datasets_used": list(discover_datasets(data_dir).keys()),
        "trained_at": datetime.now().isoformat(),
        "device": str(device),
        "torch_version": torch.__version__,
    }

    meta_path = os.path.join(output_dir, "vision_cnn_meta.json")
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2, default=str)
    logger.info(f"\nMetadata saved to {meta_path}")

    return meta


# ═══════════════════════════════════════════════════════════════════════
#  CLI ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Train BloomVisionCNN on plant disease datasets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Phase 1: Train classifier head on PlantVillage (backbone frozen)
  python train_vision_cnn.py --data-dir ../data/datasets --phase 1 --epochs 20

  # Phase 2: Fine-tune top layers (resume from Phase 1)
  python train_vision_cnn.py --data-dir ../data/datasets --phase 2 --epochs 15 --resume --lr 0.0005

  # Phase 3: Domain adaptation on ESP32-CAM images
  python train_vision_cnn.py --data-dir ../data/farm_images --phase 3 --epochs 10 --resume --lr 0.0001

Dataset setup:
  1. Download from Kaggle:
     kaggle datasets download -d emmarex/plantdisease -p ../data/datasets/
     kaggle datasets download -d nirmalsankalana/plantdoc-dataset -p ../data/datasets/
     kaggle datasets download -d smaranjitghose/corn-or-maize-leaf-disease-dataset -p ../data/datasets/
     kaggle datasets download -d mexwell/crop-diseases-classification -p ../data/datasets/

  2. Extract:
     cd ../data/datasets && unzip "*.zip"

  3. Train:
     python train_vision_cnn.py --data-dir ../data/datasets --phase 1
        """,
    )

    parser.add_argument("--data-dir", type=str, default="../data/datasets",
                        help="Root directory containing dataset folders")
    parser.add_argument("--output-dir", type=str, default="../data/models",
                        help="Directory to save trained model")
    parser.add_argument("--phase", type=int, default=1, choices=[1, 2, 3],
                        help="Training phase (1=freeze backbone, 2=fine-tune top, 3=full)")
    parser.add_argument("--epochs", type=int, default=30,
                        help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=32,
                        help="Training batch size")
    parser.add_argument("--lr", type=float, default=1e-3,
                        help="Learning rate")
    parser.add_argument("--resume", action="store_true",
                        help="Resume from previous checkpoint")
    parser.add_argument("--device", type=str, default="auto",
                        choices=["auto", "cpu", "cuda"],
                        help="Device to train on")

    args = parser.parse_args()

    result = train_vision_model(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        phase=args.phase,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        resume=args.resume,
        device_str=args.device,
    )

    print(f"\n✓ Training complete! Best accuracy: {result['best_val_accuracy']:.4f}")
