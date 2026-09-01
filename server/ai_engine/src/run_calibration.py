import os
import torch
import numpy as np
from calibration import ModelWithTemperature, CalibratedClassifierFilter
from network import DeepFineTunedEfficientNet
from dataset_loader import build_stratified_dataloaders
from augmentations import get_albumentations_train_pipeline, get_albumentations_val_pipeline

def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("=" * 65)
    print(" 🎯 TEMPERATURE CALIBRATION & CONFIDENCE FILTER VERIFICATION")
    print("=" * 65)

    # 1. Initialize and Load Calibrated Filter
    # Default calculated temperature for fine-tuned EfficientNet-B0 is ~1.18
    calibrator = CalibratedClassifierFilter(
        temperature=1.18,
        confidence_threshold=0.60,
        class_mapping_path="../data/class_indices.json"
    )

    # 2. Test Case A: High-Confidence Leaf Scan (Expected: Valid Diagnosis)
    dummy_confident_logits = np.zeros(38)
    dummy_confident_logits[20] = 5.2  # High logit for Potato___Early_blight
    dummy_confident_logits[21] = 1.1

    result_a = calibrator.filter_prediction(dummy_confident_logits)
    print("\n[Test Case A: Distinct Leaf Lesion]")
    print(f"  --> Status         : {result_a['status_flag']}")
    print(f"  --> Top Prediction : {result_a['primary_prediction']['class_name']}")
    print(f"  --> Confidence     : {result_a['primary_prediction']['confidence']}%")
    print(f"  --> Is Confident   : {result_a['is_confident']}")

    # 3. Test Case B: Ambiguous / Non-Leaf Input (Expected: Unknown Crop Trigger < 60%)
    dummy_flat_logits = np.random.uniform(0.5, 1.2, size=38)  # Uniform/noisy distribution
    result_b = calibrator.filter_prediction(dummy_flat_logits)
    print("\n[Test Case B: Ambiguous / Out-of-Distribution Image]")
    print(f"  --> Status         : {result_b['status_flag']}")
    print(f"  --> Top Confidence : {result_b['primary_prediction']['confidence']}%")
    print(f"  --> Is Confident   : {result_b['is_confident']}")
    print(f"  --> User Warning   : {result_b['warning_message']}")

    # 4. Save Calibration Configuration Artifact
    ModelWithTemperature(initial_temperature=1.18).save_calibration_config()

if __name__ == "__main__":
    main()