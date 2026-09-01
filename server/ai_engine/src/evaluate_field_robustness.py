import os
import json
import time
import torch
import numpy as np
from PIL import Image
from torchvision import transforms
from sklearn.metrics import classification_report, accuracy_score
import albumentations as A
from albumentations.pytorch import ToTensorV2

from network import DeepFineTunedEfficientNet

IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)

# 1. Clean Baseline Transformation
def get_clean_transform():
    return transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
    ])

# 2. In-Field Perturbation Pipelines (Simulating shadows, blur, and lighting extremes)
def get_shadow_pipeline():
    return A.Compose([
        A.Resize(224, 224),
        A.RandomShadow(p=1.0, num_shadows_lower=1, num_shadows_upper=3, shadow_dimension=5),
        A.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ToTensorV2()
    ])

def get_field_blur_pipeline():
    return A.Compose([
        A.Resize(224, 224),
        A.MotionBlur(blur_limit=7, p=1.0),
        A.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ToTensorV2()
    ])

def get_lighting_soil_glare_pipeline():
    return A.Compose([
        A.Resize(224, 224),
        A.RandomBrightnessContrast(brightness_limit=0.35, contrast_limit=0.35, p=1.0),
        A.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ToTensorV2()
    ])

def get_composite_field_pipeline():
    """Combined worst-case in-field conditions: Shadow + Blur + Color Shift"""
    return A.Compose([
        A.Resize(224, 224),
        A.RandomShadow(p=0.8, num_shadows_lower=1, num_shadows_upper=2),
        A.MotionBlur(blur_limit=5, p=0.6),
        A.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2, p=0.7),
        A.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ToTensorV2()
    ])

# 3. Robustness Evaluation Runner
def evaluate_field_robustness(
    test_dir: str,
    weights_path: str = "../models/checkpoints/best_efficientnet_v2.pt",
    output_report_path: str = "../models/field_robustness_report.json",
    num_samples_per_class: int = 20
):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("=" * 65)
    print(" 🌾 IN-FIELD ROBUSTNESS & OOD VALIDATION BENCHMARK")
    print("=" * 65)
    print(f"Device: {device}")
    print(f"Loading weights from: {weights_path}\n")

    # Load Model
    model = DeepFineTunedEfficientNet(num_classes=38).to(device)
    if os.path.exists(weights_path):
        model.load_state_dict(torch.load(weights_path, map_location=device))
        print("Model checkpoint loaded successfully.")
    else:
        print("Warning: Weights not found, running on initialized model.")
    model.eval()

    # Load Classes
    classes = sorted([d for d in os.listdir(test_dir) if os.path.isdir(os.path.join(test_dir, d))])
    class_to_idx = {cls_name: i for i, cls_name in enumerate(classes)}

    # Collect Balanced Test Samples
    image_paths = []
    ground_truth = []
    for cls_name in classes:
        cls_folder = os.path.join(test_dir, cls_name)
        files = [os.path.join(cls_folder, f) for f in os.listdir(cls_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))][:num_samples_per_class]
        image_paths.extend(files)
        ground_truth.extend([class_to_idx[cls_name]] * len(files))

    print(f"Loaded {len(image_paths)} test images across {len(classes)} classes for evaluation.\n")

    pipelines = {
        "Clean Baseline (Lab Conditions)": None,
        "Variable Shadows": get_shadow_pipeline(),
        "Motion Blur & Camera Shake": get_field_blur_pipeline(),
        "Extreme Sunlight & Glare": get_lighting_soil_glare_pipeline(),
        "Composite In-Field Noise": get_composite_field_pipeline()
    }

    benchmark_results = {}
    clean_tf = get_clean_transform()

    for condition_name, aug_pipe in pipelines.items():
        preds = []
        confidences = []
        latencies = []

        for img_path in image_paths:
            img_pil = Image.open(img_path).convert("RGB")
            
            start_t = time.perf_counter()
            if aug_pipe is None:
                tensor = clean_tf(img_pil).unsqueeze(0).to(device)
            else:
                img_np = np.array(img_pil)
                augmented = aug_pipe(image=img_np)["image"]
                tensor = augmented.unsqueeze(0).to(device)

            with torch.no_grad():
                output = model(tensor)
                probs = torch.softmax(output, dim=1)[0]
                top_conf, pred_idx = torch.max(probs, dim=0)

            latencies.append((time.perf_counter() - start_t) * 1000)
            preds.append(pred_idx.item())
            confidences.append(top_conf.item())

        acc = accuracy_score(ground_truth, preds) * 100
        mean_conf = np.mean(confidences) * 100
        avg_lat = np.mean(latencies)

        benchmark_results[condition_name] = {
            "accuracy_percentage": round(acc, 2),
            "mean_confidence": round(mean_conf, 2),
            "mean_latency_ms": round(avg_lat, 2)
        }

        print(f"[{condition_name}]")
        print(f"  --> Top-1 Accuracy : {acc:.2f}%")
        print(f"  --> Mean Confidence: {mean_conf:.2f}%")
        print(f"  --> Avg Latency    : {avg_lat:.2f} ms\n")

    # Compute Degradation from Clean Baseline
    baseline_acc = benchmark_results["Clean Baseline (Lab Conditions)"]["accuracy_percentage"]
    for condition, data in benchmark_results.items():
        degradation = baseline_acc - data["accuracy_percentage"]
        data["accuracy_drop_from_baseline"] = round(degradation, 2)

    # Save Output Report
    os.makedirs(os.path.dirname(output_report_path), exist_ok=True)
    with open(output_report_path, "w") as f:
        json.dump(benchmark_results, f, indent=2)

    print(f"Robustness degradation report saved to: {output_report_path}")

if __name__ == "__main__":
    TEST_DIR = "../data/test" # Point to your test folder
    if os.path.exists(TEST_DIR):
        evaluate_field_robustness(TEST_DIR)