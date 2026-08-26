import os
import torch
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import classification_report, confusion_matrix
from dataset_loader import build_stratified_dataloaders
from augmentations import get_train_transforms, get_base_transforms
from network import PlantDiseaseClassifier

def evaluate_model(data_dir: str, weights_path: str, output_dir: str = "../models"):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    _, _, test_loader, classes = build_stratified_dataloaders(
        data_dir=data_dir,
        train_transform=get_train_transforms(),
        val_transform=get_base_transforms(),
        batch_size=64
    )

    model = PlantDiseaseClassifier(num_classes=len(classes)).to(device)
    model.load_state_dict(torch.load(weights_path, map_location=device))
    model.eval()

    all_preds, all_labels = [], []
    with torch.no_grad():
        for images, labels in test_loader:
            images = images.to(device)
            outputs = model(images)
            _, preds = torch.max(outputs, 1)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.numpy())

    # Text Metrics Report
    report = classification_report(all_labels, all_preds, target_names=classes, digits=4)
    print("\n--- Test Set Evaluation Report ---")
    print(report)

    with open(os.path.join(output_dir, "evaluation_report.txt"), "w") as f:
        f.write(report)

    # Confusion Matrix Visualization
    cm = confusion_matrix(all_labels, all_preds)
    plt.figure(figsize=(16, 14))
    sns.heatmap(cm, annot=False, cmap="Blues", xticklabels=classes, yticklabels=classes)
    plt.xticks(rotation=90, fontsize=8)
    plt.yticks(fontsize=8)
    plt.title("38-Class Plant Disease Confusion Matrix", fontsize=14)
    plt.xlabel("Predicted Class")
    plt.ylabel("True Class")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "confusion_matrix.png"), dpi=300)
    print("Saved confusion_matrix.png and evaluation_report.txt")