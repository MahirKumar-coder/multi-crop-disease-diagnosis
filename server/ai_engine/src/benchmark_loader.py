import os
import time
import shutil
import numpy as np
from PIL import Image
import torch
from torch.utils.data import DataLoader, Subset
from torchvision import datasets

from augmentations import (
    get_train_transforms,
    get_albumentations_train_pipeline,
    AlbumentationsDatasetWrapper
)

def create_mock_dataset(path="./mock_benchmark_dataset", num_images=200):
    """Creates a temporary mock dataset folder for benchmarking."""
    os.makedirs(os.path.join(path, "train/class_a"), exist_ok=True)
    os.makedirs(os.path.join(path, "train/class_b"), exist_ok=True)
    
    # Save dummy images
    for i in range(num_images):
        img_np = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
        img = Image.fromarray(img_np)
        class_dir = "class_a" if i % 2 == 0 else "class_b"
        img.save(os.path.join(path, "train", class_dir, f"img_{i}.jpg"))
    print(f"Created temporary mock dataset with {num_images} images.")

def run_loader_benchmark(dataset_path="./mock_benchmark_dataset", num_batches=10, batch_size=32):
    # Verify dataset exists or create mock
    is_mock = False
    train_dir = os.path.join(dataset_path, "train")
    if not os.path.exists(train_dir):
        dataset_path = "./mock_benchmark_dataset"
        create_mock_dataset(dataset_path)
        is_mock = True

    train_dir = os.path.join(dataset_path, "train")
    raw_dataset = datasets.ImageFolder(root=train_dir)
    
    # 1. Baseline PyTorch Data Loader
    pytorch_transformed_ds = datasets.ImageFolder(root=train_dir, transform=get_train_transforms())
    pytorch_loader = DataLoader(
        pytorch_transformed_ds, 
        batch_size=batch_size, 
        shuffle=True, 
        num_workers=2, 
        pin_memory=True
    )

    # 2. Upgraded Albumentations Data Loader
    subset = Subset(raw_dataset, list(range(len(raw_dataset))))
    albu_dataset = AlbumentationsDatasetWrapper(subset, get_albumentations_train_pipeline())
    albu_loader = DataLoader(
        albu_dataset, 
        batch_size=batch_size, 
        shuffle=True, 
        num_workers=2, 
        pin_memory=True
    )

    print("\nWarmup loaders...")
    # Warmup
    for loader in [pytorch_loader, albu_loader]:
        for i, (images, _) in enumerate(loader):
            if i >= 2:
                break

    # Benchmark PyTorch Loader
    print("Benchmarking PyTorch baseline loader...")
    start_time = time.perf_counter()
    images_count = 0
    batches_processed = 0
    
    for epoch in range(2): # 2 passes to get stable reads
        for images, _ in pytorch_loader:
            images_count += images.size(0)
            batches_processed += 1
            if batches_processed >= num_batches:
                break
        if batches_processed >= num_batches:
            break
            
    pytorch_time = time.perf_counter() - start_time
    pytorch_throughput = images_count / pytorch_time

    # Benchmark Albumentations Loader
    print("Benchmarking Albumentations upgraded loader...")
    start_time = time.perf_counter()
    images_count = 0
    batches_processed = 0
    
    for epoch in range(2):
        for images, _ in albu_loader:
            images_count += images.size(0)
            batches_processed += 1
            if batches_processed >= num_batches:
                break
        if batches_processed >= num_batches:
            break
            
    albu_time = time.perf_counter() - start_time
    albu_throughput = images_count / albu_time

    # Output report
    print("\n" + "="*50)
    print("       DATA LOADER THROUGHPUT BENCHMARK")
    print("="*50)
    print(f"Batch Size Configured       : {batch_size}")
    print(f"Total Batches Evaluated     : {num_batches}")
    print(f"Total Images Processed      : {images_count}")
    print("-"*50)
    print(f"PyTorch Baseline Throughput : {pytorch_throughput:.2f} images/sec")
    print(f"Albumentations Throughput   : {albu_throughput:.2f} images/sec")
    print(f"Throughput Ratio (Albu/PT)  : {albu_throughput / pytorch_throughput:.2f}x")
    print("="*50)

    # Clean up mock dataset if created
    if is_mock and os.path.exists(dataset_path):
        shutil.rmtree(dataset_path)
        print("Removed temporary mock dataset.")

if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "./mock_benchmark_dataset"
    run_loader_benchmark(dataset_path=path, num_batches=15, batch_size=32)
