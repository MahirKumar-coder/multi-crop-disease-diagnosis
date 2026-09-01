import json
import os
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from typing import Dict, Any, Tuple, Optional


class ModelWithTemperature(nn.Module):
    """
    Applies Temperature Scaling post-processing on model logits:
        calibrated_probs = softmax(logits / T)
    Optimizes T on validation logits to minimize Negative Log-Likelihood (NLL).
    """
    def __init__(self, base_model: Optional[nn.Module] = None, initial_temperature: float = 1.0):
        super(ModelWithTemperature, self).__init__()
        self.base_model = base_model
        self.temperature = nn.Parameter(torch.ones(1) * initial_temperature)

    def forward(self, logits: torch.Tensor) -> torch.Tensor:
        """Scales logits by temperature parameter T."""
        return logits / self.temperature

    def calibrate_temperature(self, val_loader, device: torch.device) -> float:
        """
        Learns optimal temperature T using validation dataset logits.
        """
        if self.base_model is None:
            raise ValueError("Base model must be provided to extract logits for calibration.")

        self.base_model.eval()
        nll_criterion = nn.CrossEntropyLoss()
        
        logits_list = []
        labels_list = []

        print("--> Extracting validation logits for temperature calibration...")
        with torch.no_grad():
            for images, labels in val_loader:
                images = images.to(device)
                logits = self.base_model(images)
                logits_list.append(logits.cpu())
                labels_list.append(labels)

        logits = torch.cat(logits_list).to(device)
        labels = torch.cat(labels_list).to(device)

        # Optimize temperature T using L-BFGS
        optimizer = optim.LBFGS([self.temperature], lr=0.01, max_iter=50)

        def eval_loss():
            optimizer.zero_grad()
            loss = nll_criterion(self.forward(logits), labels)
            loss.backward()
            return loss

        optimizer.step(eval_loss)
        optimal_t = self.temperature.item()
        print(f"✅ Optimal Temperature learned: T = {optimal_t:.4f}")
        return optimal_t

    def save_calibration_config(self, save_path: str = "../models/calibration_config.json"):
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        config = {
            "temperature": round(self.temperature.item(), 4),
            "confidence_threshold": 0.60,
            "method": "Temperature Scaling (Guo et al.)"
        }
        with open(save_path, "w") as f:
            json.dump(config, f, indent=2)
        print(f"Saved calibration config to: {save_path}")


class CalibratedClassifierFilter:
    """
    Inference filter that calibrates raw logits and screens for
    out-of-distribution (OOD), non-leaf, or low-confidence scans (< 60%).
    """
    def __init__(
        self,
        temperature: float = 1.15,
        confidence_threshold: float = 0.60,
        class_mapping_path: Optional[str] = "../data/class_indices.json"
    ):
        self.temperature = max(temperature, 1e-4)
        self.confidence_threshold = confidence_threshold
        self.classes = []

        if class_mapping_path and os.path.exists(class_mapping_path):
            with open(class_mapping_path, "r") as f:
                class_map = json.load(f)
                # Invert mapping: {index: class_name}
                self.classes = [None] * len(class_map)
                for k, v in class_map.items():
                    self.classes[v] = k

    def filter_prediction(
        self,
        raw_logits: np.ndarray,
        top_k: int = 3
    ) -> Dict[str, Any]:
        """
        Takes raw model output logits, applies temperature scaling,
        and evaluates confidence safety triggers.
        """
        # 1. Apply Temperature Scaling: logits / T
        scaled_logits = raw_logits / self.temperature

        # 2. Softmax Normalization
        exp_logits = np.exp(scaled_logits - np.max(scaled_logits))
        calibrated_probs = exp_logits / np.sum(exp_logits)

        # 3. Extract Top-K Hypotheses
        top_indices = np.argsort(calibrated_probs)[::-1][:top_k]
        top_predictions = []

        for idx in top_indices:
            cls_name = self.classes[idx] if idx < len(self.classes) else f"Class_{idx}"
            top_predictions.append({
                "class_id": int(idx),
                "class_name": cls_name,
                "confidence": round(float(calibrated_probs[idx]) * 100, 2)
            })

        primary_prediction = top_predictions[0]
        top_confidence_ratio = primary_prediction["confidence"] / 100.0

        # 4. Out-of-Distribution (OOD) / Low-Confidence Trigger (< 60%)
        is_confident = top_confidence_ratio >= self.confidence_threshold

        if is_confident:
            status_flag = "VALID_DIAGNOSIS"
            warning_message = None
        else:
            status_flag = "UNKNOWN_OR_AMBIGUOUS_SCAN"
            warning_message = (
                f"Low confidence ({primary_prediction['confidence']}% < 60%). "
                "The uploaded image may not be a supported crop leaf, or lighting/symptom clarity is insufficient. "
                "Please capture a clearer, centered photo in good daylight."
            )

        return {
            "is_confident": is_confident,
            "status_flag": status_flag,
            "warning_message": warning_message,
            "primary_prediction": primary_prediction,
            "top_k_predictions": top_predictions,
            "temperature_applied": self.temperature
        }