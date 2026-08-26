import numpy as np
import torch
from PIL import Image
import albumentations as A
from albumentations.pytorch import ToTensorV2

IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)

def get_albumentations_train_pipeline(img_size: int = 224) -> A.Compose:
    """
    Advanced in-field augmentation pipeline incorporating optical distortions,
    blur, lighting shifts, and perspective transforms.
    """
    return A.Compose([
        A.Resize(img_size, img_size),
        A.HorizontalFlip(p=0.5),
        A.VerticalFlip(p=0.3),
        A.RandomRotate90(p=0.3),
        A.ShiftScaleRotate(shift_limit=0.1, scale_limit=0.15, rotate_limit=30, p=0.5),
        A.OneOf([
            A.MotionBlur(blur_limit=5, p=0.5),
            A.GaussianBlur(blur_limit=5, p=0.5),
            A.MedianBlur(blur_limit=5, p=0.5),
        ], p=0.4),
        A.OneOf([
            A.OpticalDistortion(distort_limit=0.1, shift_limit=0.1, p=0.5),
            A.GridDistortion(num_steps=5, distort_limit=0.1, p=0.5),
            A.Perspective(scale=(0.05, 0.1), p=0.5),
        ], p=0.3),
        A.OneOf([
            A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2, p=0.7),
            A.CLAHE(clip_limit=2.0, tile_grid_size=(8, 8), p=0.5),
            A.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1, p=0.5),
        ], p=0.6),
        A.CoarseDropout(max_holes=6, max_height=16, max_width=16, fill_value=0, p=0.3),
        A.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ToTensorV2(),
    ])

def get_albumentations_val_pipeline(img_size: int = 224) -> A.Compose:
    """Deterministic validation pipeline."""
    return A.Compose([
        A.Resize(img_size, img_size),
        A.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ToTensorV2(),
    ])

class AlbumentationsDatasetWrapper(torch.utils.data.Dataset):
    """Bridge wrapper to allow ImageFolder images to be processed via Albumentations."""
    def __init__(self, image_folder_subset, transform: A.Compose):
        self.subset = image_folder_subset
        self.transform = transform

    def __len__(self):
        return len(self.subset)

    def __getitem__(self, idx):
        img, label = self.subset[idx]
        if isinstance(img, Image.Image):
            img_np = np.array(img.convert("RGB"))
        else:
            img_np = np.array(img)

        augmented = self.transform(image=img_np)
        return augmented["image"], label