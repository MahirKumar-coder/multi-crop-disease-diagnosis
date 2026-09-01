import cv2
import torch
import base64
import numpy as np
from PIL import Image
from typing import Optional

from app.services.model_service import model_service
from app.core.logger import logger

class GradCAM: 
    def __init__(self, model, target_layer):
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None
        self._hook_layers()

    def _hook_layers(self):
        def forward_hook(module, input, output):
            self.activations = output

        def backward_hook(module, grad_in, grad_out):
            self.gradients = grad_out[0]

        self.target_layer.register_forward_hook(forward_hook)
        self.target_layer.register_full_backward_hook(backward_hook)

    def generate_heatmap(self, input_tensor: torch.Tensor, class_idx: int, original_img: Image.Image) -> Optional[str]:
        try:
            device = next(self.model.parameters()).device
            tensor_device = input_tensor.to(device)

            self.model.zero_grad()
            output = self.model(tensor_device)
            score = output[0, class_idx]
            score.backward()

            if self.gradients is None or self.activations is None:
                return None

            gradients = self.gradients.data.cpu().numpy()[0]
            activations = self.activations.data.cpu().numpy()[0]

            weights = np.mean(gradients, axis=(1, 2))
            cam = np.zeros(activations.shape[1:], dtype=np.float32)

            for i, w in enumerate(weights):
                cam += w * activations[i]

            cam = np.maximum(cam, 0)
            if np.max(cam) != 0:
                cam = cam / np.max(cam)

            cam = cv2.resize(cam, (original_img.width, original_img.height))
            heatmap = cv2.applyColorMap(np.uint8(255 * cam), cv2.COLORMAP_JET)

            img_np = np.array(original_img)
            if len(img_np.shape) == 3 and img_np.shape[2] == 3:
                img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
            else:
                img_bgr = img_np

            overlay = cv2.addWeighted(img_bgr, 0.6, heatmap, 0.4, 0)

            _, buffer = cv2.imencode(".jpg", overlay)
            base64_str = base64.b64encode(buffer).decode("utf-8")
            return f"data:image/jpeg;base64,{base64_str}"
        except Exception as e:
            logger.error(f"GradCAM generation internal error: {e}")
            return None


class GradCAMService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GradCAMService, cls).__new__(cls)
            cls._instance._gradcam = None
        return cls._instance

    def _get_gradcam(self) -> Optional[GradCAM]:
        if self._gradcam is None:
            try:
                model = model_service.model
                if model is not None and hasattr(model, "features"):
                    target_layer = model.features[-1]
                    self._gradcam = GradCAM(model, target_layer)
            except Exception as e:
                logger.error(f"Failed to initialize GradCAM hook: {e}")
                return None
        return self._gradcam

    def generate_heatmap(self, input_tensor: torch.Tensor, class_idx: int, original_img: Image.Image) -> Optional[str]:
        gc = self._get_gradcam()
        if gc is None:
            return None
        return gc.generate_heatmap(input_tensor, class_idx, original_img)

    def generate_base64_heatmap(self, input_tensor: torch.Tensor, class_idx: int, original_img: Image.Image) -> Optional[str]:
        return self.generate_heatmap(input_tensor, class_idx, original_img)


# Singleton instance export
gradcam_service = GradCAMService()