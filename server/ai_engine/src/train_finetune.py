import os
import json
import time
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Subset
from torchvision import datasets
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.metrics import f1_score
from tqdm import tqdm

from augmentations import (
    get_albumentations_train_pipeline,
    get_albumentations_val_pipeline,
    AlbumentationsDatasetWrapper
)
from network import DeepFineTunedEfficientNet

def train_and_finetune(
    data_dir: str,
    output_dir: str = "../models/checkpoints",
    epochs: int = 15,
    batch_size: int = 64
):
    os.makedirs(output_dir, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"🚀 Execution started on device: {device}")

    # 1. Dataset & Stratified Split
    raw_ds = datasets.ImageFolder(root=data_dir)
    targets = raw_ds.targets
    classes = raw_ds.classes
    num_classes = len(classes)

    sss = StratifiedShuffleSplit(n_splits=1, test_size=0.20, random_state=42)
    train_idx, val_idx = next(sss.split(range(len(targets)), targets))

    train_subset = Subset(raw_ds, train_idx)
    val_subset = Subset(raw_ds, val_idx)

    train_ds = AlbumentationsDatasetWrapper(train_subset, get_albumentations_train_pipeline())
    val_ds = AlbumentationsDatasetWrapper(val_subset, get_albumentations_val_pipeline())

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=4, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=4, pin_memory=True)

    print(f"Dataset Loaded: {len(train_ds)} train samples, {len(val_ds)} val samples across {num_classes} classes.")

    # 2. Model Initialization
    model = DeepFineTunedEfficientNet(num_classes=num_classes).to(device)
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
    scaler = torch.cuda.amp.GradScaler()

    best_val_f1 = 0.0
    history = []

    # =========================================================================
    # 15-Epoch Training Loop
    # =========================================================================
    for epoch in range(1, epochs + 1):
        epoch_start = time.time()

        if epoch <= 3:
            # Phase 1: Train Head Only
            model.freeze_all()
            optimizer = optim.AdamW(model.model.classifier.parameters(), lr=1e-3, weight_decay=1e-4)
            scheduler = None
            stage_desc = "Phase 1 (Frozen Backbone)"
        else:
            # Phase 2: Deep Fine-Tuning with Differential Learning Rates
            if epoch == 4:
                print("\n🔥 Unfreezing Stages 4-7 and applying Differential Learning Rates (Backbone: 1e-5, Head: 1e-3)...")
                model.unfreeze_stages(from_stage=4)
                param_groups = model.get_parameter_groups(backbone_lr=1e-5, head_lr=1e-3)
                optimizer = optim.AdamW(param_groups)
                scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=(epochs - 3), eta_min=1e-6)
            stage_desc = "Phase 2 (Deep Fine-Tuning)"

        # Training Phase
        model.train()
        train_loss, train_correct, train_total = 0.0, 0, 0

        pbar = tqdm(train_loader, desc=f"Epoch {epoch:02d}/{epochs:02d} [{stage_desc}]")
        for images, labels in pbar:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()

            with torch.cuda.amp.autocast():
                outputs = model(images)
                loss = criterion(outputs, labels)

            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()

            train_loss += loss.item() * images.size(0)
            _, preds = torch.max(outputs, 1)
            train_correct += torch.sum(preds == labels).item()
            train_total += labels.size(0)

            pbar.set_postfix({"loss": f"{loss.item():.4f}"})

        if scheduler:
            scheduler.step()

        train_acc = (train_correct / train_total) * 100
        epoch_loss = train_loss / train_total

        # Validation Phase
        model.eval()
        val_loss, val_correct, val_total = 0.0, 0, 0
        all_val_preds, all_val_targets = [], []

        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                with torch.cuda.amp.autocast():
                    outputs = model(images)
                    loss = criterion(outputs, labels)

                val_loss += loss.item() * images.size(0)
                _, preds = torch.max(outputs, 1)
                val_correct += torch.sum(preds == labels).item()
                val_total += labels.size(0)

                all_val_preds.extend(preds.cpu().numpy())
                all_val_targets.extend(labels.cpu().numpy())

        val_acc = (val_correct / val_total) * 100
        val_f1 = f1_score(all_val_targets, all_val_preds, average="weighted") * 100
        epoch_duration = time.time() - epoch_start

        print(f"📊 Summary Epoch {epoch:02d} | Train Loss: {epoch_loss:.4f} | Train Acc: {train_acc:.2f}% | Val Acc: {val_acc:.2f}% | Val F1: {val_f1:.2f}% ({epoch_duration:.1f}s)")

        # Log metrics record
        log_entry = {
            "epoch": epoch,
            "stage": stage_desc,
            "train_loss": round(epoch_loss, 4),
            "train_acc": round(train_acc, 2),
            "val_loss": round(val_loss / val_total, 4),
            "val_acc": round(val_acc, 2),
            "val_f1": round(val_f1, 2)
        }
        history.append(log_entry)

        # Save Best Model Weights
        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            best_model_path = os.path.join(output_dir, "best_efficientnet_v2.pt")
            torch.save(model.state_dict(), best_model_path)
            print(f"🎯 Saved New Best Checkpoint ({val_acc:.2f}% Acc / {val_f1:.2f}% F1) -> {best_model_path}")

    # Save training curves history
    history_file = os.path.join(output_dir, "training_history_v2.json")
    with open(history_file, "w") as f:
        json.dump(history, f, indent=2)
    print(f"\n✅ Training Completed. Logs saved to: {history_file}")

if __name__ == "__main__":
    DATASET_PATH = "./data/New Plant Diseases Dataset(Augmented)/train"
    train_and_finetune(DATASET_PATH)