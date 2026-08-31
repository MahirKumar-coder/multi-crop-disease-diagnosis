import io
import base64
import torch
import cv2
import numpy as np
from PIL import Image

class GuidedBackpropReLUModel:
    def __init__(self, model):
        self.model = model
        self.hooks = []
        self._register_hooks()

    def _register_hooks(self):
        def backward_hook(module, grad_in, grad_out):
            # For Guided Backpropagation, we only propagate positive gradients
            if isinstance(grad_in[0], torch.Tensor):
                modified_grad = torch.clamp(grad_in[0], min=0.0)
                return (modified_grad,)
            return grad_in

        # Register hooks on all ReLU and SiLU (Activation) layers
        for module in self.model.modules():
            if isinstance(module, (torch.nn.ReLU, torch.nn.SiLU)):
                self.hooks.append(module.register_full_backward_hook(backward_hook))

    def remove_hooks(self):
        for hook in self.hooks:
            hook.remove()

    def generate_gradients(self, input_tensor: torch.Tensor, class_idx: int) -> np.ndarray:
        input_tensor.requires_grad = True
        self.model.zero_grad()
        output = self.model(input_tensor)
        target_score = output[0, class_idx]
        target_score.backward()
        
        # Return gradients of the input image
        return input_tensor.grad.detach().cpu().numpy()[0]

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
        
        # 1. Standard Grad-CAM
        self.model.zero_grad()
        output = self.model(input_tensor)
        target_score = output[0, class_idx]
        target_score.backward()

        weights = torch.mean(self.gradients, dim=(2, 3), keepdim=True)
        cam = torch.sum(weights * self.activations, dim=1).squeeze(0)
        cam = torch.clamp(cam, min=0).detach().cpu().numpy()
        cam = cv2.resize(cam, original_image.size)
        cam = (cam - np.min(cam)) / (np.max(cam) - np.min(cam) + 1e-8)

        # 2. Guided Backpropagation (for crisper lesion boundaries)
        # Clone tensor and enable gradients
        gb_input = input_tensor.clone().detach()
        gb_model = GuidedBackpropReLUModel(self.model)
        gb_grads = gb_model.generate_gradients(gb_input, class_idx)
        gb_model.remove_hooks()

        # Transpose from (C, H, W) -> (H, W, C)
        gb_grads = np.transpose(gb_grads, (1, 2, 0))
        gb_grads = (gb_grads - np.min(gb_grads)) / (np.max(gb_grads) - np.min(gb_grads) + 1e-8)

        # 3. Guided Grad-CAM (element-wise multiplication)
        guided_cam = gb_grads * cam[:, :, np.newaxis]
        guided_cam = (guided_cam - np.min(guided_cam)) / (np.max(guided_cam) - np.min(guided_cam) + 1e-8)
        
        # Take max across channels to get grayscale boundaries
        guided_cam_gray = np.uint8(255 * np.max(guided_cam, axis=-1))
        guided_cam_gray = cv2.resize(guided_cam_gray, original_image.size)

        # 4. Mix Original with Heatmap and Guided Boundaries
        heatmap = cv2.applyColorMap(np.uint8(255 * cam), cv2.COLORMAP_JET)
        heatmap = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)
        
        img_np = np.array(original_image)
        base_overlay = np.uint8(0.6 * img_np + 0.4 * heatmap)

        # Add guided boundary highlights in bright white-green
        highlight_mask = guided_cam_gray > 40  # threshold for active boundary outlines
        overlay = base_overlay.copy()
        
        # Enhance borders slightly on the overlay image
        for c in range(3):
            overlay[highlight_mask, c] = np.uint8(
                0.7 * base_overlay[highlight_mask, c] + 
                0.3 * (255 if c == 1 else guided_cam_gray[highlight_mask])
            )

        # Encode to Base64
        overlay_pil = Image.fromarray(overlay)
        buffered = io.BytesIO()
        overlay_pil.save(buffered, format="JPEG", quality=90)
        return "data:image/jpeg;base64," + base64.b64encode(buffered.getvalue()).decode("utf-8")