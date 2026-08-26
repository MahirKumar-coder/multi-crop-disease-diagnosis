import io
import base64
import torch
import cv2
import numpy as np
from PIL import Image

class GradCAMVisualizer:
    def __init__(self, model: torch.nn.Module, target_layer: torch.nn.Module):
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None
        self._register_hooks()

    def _register_hooks(self):
        def forward_hook(module, input, output):
            self.activations = output

        def backward_hook(module, grad_in, grad_out):
            self.gradients = grad_out[0]

        self.target_layer.register_forward_hook(forward_hook)
        self.target_layer.register_full_backward_hook(backward_hook)

    def generate_overlay(self, input_tensor: torch.Tensor, class_idx: int, original_image: Image.Image) -> str:
        self.model.eval()
        self.model.zero_grad()

        # Forward pass
        output = self.model(input_tensor)
        target_score = output[0, class_idx]
        
        # Backward pass
        target_score.backward()

        # Global average pool the gradients
        weights = torch.mean(self.gradients, dim=(2, 3), keepdim=True)
        cam = torch.sum(weights * self.activations, dim=1).squeeze(0)

        # ReLU & Normalize
        cam = torch.clamp(cam, min=0).detach().cpu().numpy()
        cam = cv2.resize(cam, original_image.size)
        cam = (cam - np.min(cam)) / (np.max(cam) - np.min(cam) + 1e-8)

        # Color Map Overlay
        heatmap = cv2.applyColorMap(np.uint8(255 * cam), cv2.COLORMAP_JET)
        heatmap = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)
        
        img_np = np.array(original_image)
        overlay = np.uint8(0.6 * img_np + 0.4 * heatmap)

        # Encode to Base64
        overlay_pil = Image.fromarray(overlay)
        buffered = io.BytesIO()
        overlay_pil.save(buffered, format="JPEG", quality=90)
        return "data:image/jpeg;base64," + base64.b64encode(buffered.getvalue()).decode("utf-8")