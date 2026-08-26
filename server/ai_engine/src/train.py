import os
import torch
import torch.nn as nn
import torch.optim as optim
from tqdm import tqdm
from dataset_loader import build_stratified_dataloaders
from augmentations import get_train_transforms, get_base_transforms
from network import PlantDiseaseClassifier

def run_training(data_dir: str, save_dir: str = "../models/checkpoints"):
    os.makedirs(save_dir, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training on device: {device}")

    # Build DataLoaders
    train_loader, val_loader, _, _ = build_stratified_dataloaders(
        data_dir=data_dir,
        train_transform=get_train_transforms(),
        val_transform=get_base_transforms(),
        batch_size=64
    )

    model = PlantDiseaseClassifier(num_classes=38).to(device)
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
    best_val_acc = 0.0

    # ==========================================
    # PHASE 1: Warmup Classifier Head (3 Epochs)
    # ==========================================
    print("\n--- PHASE 1: Training Classification Head ---")
    model.freeze_backbone()
    optimizer = optim.Adam(model.backbone.classifier.parameters(), lr=1e-3)

    for epoch in range(1, 4):
        model.train()
        running_loss, correct, total = 0.0, 0, 0
        for images, labels in tqdm(train_loader, desc=f"Phase 1 - Epoch {epoch}/3"):
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * images.size(0)
            _, preds = torch.max(outputs, 1)
            correct += torch.sum(preds == labels)
            total += labels.size(0)

        train_acc = correct.double() / total
        print(f"Phase 1 - Epoch {epoch} | Loss: {running_loss/total:.4f} | Train Acc: {train_acc*100:.2f}%")

    # ==========================================
    # PHASE 2: Deep Fine-Tuning (7 Epochs)
    # ==========================================
    print("\n--- PHASE 2: Unfreezing Deep Layers & Fine-Tuning ---")
    model.unfreeze_top_blocks(num_blocks_to_unfreeze=3)
    
    # Differential Learning Rates
    optimizer = optim.AdamW([
        {"params": model.backbone.features.parameters(), "lr": 1e-4},
        {"params": model.backbone.classifier.parameters(), "lr": 5e-4}
    ], weight_decay=1e-4)

    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=7)
    scaler = torch.cuda.amp.GradScaler()

    for epoch in range(1, 8):
        model.train()
        running_loss, correct, total = 0.0, 0, 0
        for images, labels in tqdm(train_loader, desc=f"Phase 2 - Epoch {epoch}/7"):
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()

            with torch.cuda.amp.autocast():
                outputs = model(images)
                loss = criterion(outputs, labels)

            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()

            running_loss += loss.item() * images.size(0)
            _, preds = torch.max(outputs, 1)
            correct += torch.sum(preds == labels)
            total += labels.size(0)

        scheduler.step()

        # Validation Run
        model.eval()
        val_correct, val_total = 0, 0
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                _, preds = torch.max(outputs, 1)
                val_correct += torch.sum(preds == labels)
                val_total += labels.size(0)

        val_acc = (val_correct.double() / val_total).item()
        print(f"Phase 2 - Epoch {epoch}/7 | Val Acc: {val_acc*100:.2f}%")

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            save_path = os.path.join(save_dir, "best_efficientnet.pt")
            torch.save(model.state_dict(), save_path)
            print(f"Saved Checkpoint to {save_path} ({best_val_acc*100:.2f}%)")

if __name__ == "__main__":
    DATA_PATH = "path/to/dataset"  # Point to raw or augmented Kaggle directory
    run_training(DATA_PATH)