import os
import json
import torch
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, transforms
from sklearn.model_selection import StratifiedShuffleSplit

# Standard ImageNet Normalization Constants
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

def get_base_transforms():
    """Deterministic validation/test evaluation pipeline."""
    return transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
    ])

def build_stratified_dataloaders(
    data_dir: str,
    train_transform,
    val_transform=None,
    batch_size: int = 64,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    random_seed: int = 42,
    save_meta_dir: str = "../data"
):
    if val_transform is None:
        val_transform = get_base_transforms()

    # Load dataset index
    raw_dataset = datasets.ImageFolder(root=data_dir)
    targets = raw_dataset.targets
    classes = raw_dataset.classes

    os.makedirs(save_meta_dir, exist_ok=True)
    
    # Save Class-to-Index Map
    class_indices_path = os.path.join(save_meta_dir, "class_indices.json")
    with open(class_indices_path, "w") as f:
        json.dump({cls: idx for idx, cls in enumerate(classes)}, f, indent=2)

    # 1. Stratified Split: Train (70%) vs Temp (30%)
    sss1 = StratifiedShuffleSplit(n_splits=1, test_size=(val_ratio + test_ratio), random_state=random_seed)
    train_idx, temp_idx = next(sss1.split(range(len(targets)), targets))

    temp_targets = [targets[i] for i in temp_idx]
    
    # 2. Stratified Split: Validation (15%) vs Test (15%)
    val_prop_of_temp = val_ratio / (val_ratio + test_ratio)
    sss2 = StratifiedShuffleSplit(n_splits=1, test_size=(1.0 - val_prop_of_temp), random_state=random_seed)
    val_sub_idx, test_sub_idx = next(sss2.split(temp_idx, temp_targets))

    val_idx = [temp_idx[i] for i in val_sub_idx]
    test_idx = [temp_idx[i] for i in test_sub_idx]

    # Save Split Records Artifact
    split_meta = {
        "total_samples": len(targets),
        "num_classes": len(classes),
        "train_samples": len(train_idx),
        "val_samples": len(val_idx),
        "test_samples": len(test_idx)
    }
    with open(os.path.join(save_meta_dir, "split_records.json"), "w") as f:
        json.dump(split_meta, f, indent=2)

    # Instantiate Subsets with respective transforms
    train_ds = Subset(datasets.ImageFolder(root=data_dir, transform=train_transform), train_idx)
    val_ds = Subset(datasets.ImageFolder(root=data_dir, transform=val_transform), val_idx)
    test_ds = Subset(datasets.ImageFolder(root=data_dir, transform=val_transform), test_idx)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=4, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=4, pin_memory=True)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False, num_workers=4, pin_memory=True)

    return train_loader, val_loader, test_loader, classes