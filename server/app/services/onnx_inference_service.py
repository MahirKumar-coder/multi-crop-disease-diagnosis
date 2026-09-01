import os
import time
import json
import numpy as np
import onnxruntime as ort
import torch
from typing import Dict, Any
from pathlib import Path

from app.core.config import settings
from app.core.logger import logger
from ai_engine.src.calibration import CalibratedClassifierFilter

class ONNXInferenceService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ONNXInferenceService, cls).__new__(cls)
            cls._instance._initialize_session()
        return cls._instance

    def _resolve_path(self, target_rel_path: str) -> str:
        current_dir = Path(__file__).resolve().parent
        candidates = [
            Path(target_rel_path),
            current_dir / ".." / ".." / target_rel_path,
            current_dir / ".." / "models" / Path(target_rel_path).name,
            current_dir / ".." / "data" / Path(target_rel_path).name,
            Path("server") / target_rel_path,
            Path("server/app/models") / Path(target_rel_path).name,
            Path("app/models") / Path(target_rel_path).name,
            Path("server/app/data") / Path(target_rel_path).name,
            Path("app/data") / Path(target_rel_path).name,
        ]
        for c in candidates:
            if c.exists():
                return str(c.resolve())
        return target_rel_path

    def _initialize_session(self):
        raw_model_path = getattr(settings, "ONNX_MODEL_PATH", "app/models/efficientnet_plant_disease.onnx")
        self.model_path = self._resolve_path(raw_model_path)
        
        raw_class_indices_path = getattr(settings, "CLASS_INDICES_PATH", "app/data/class_indices.json")
        self.class_indices_path = self._resolve_path(raw_class_indices_path)
        
        # 1. Initialize ONNX Runtime Session
        self.session = None
        self.input_name = None
        self.output_name = None
        
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = min(os.cpu_count() or 4, 4)
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        
        if os.path.exists(self.model_path):
            try:
                logger.info(f"Loading ONNX Model from: {self.model_path}")
                self.session = ort.InferenceSession(self.model_path, sess_options=opts, providers=["CPUExecutionProvider"])
                self.input_name = self.session.get_inputs()[0].name
                self.output_name = self.session.get_outputs()[0].name
                logger.info("ONNX Inference Session loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load ONNX session from {self.model_path}: {e}")
                self.session = None
        else:
            logger.warning(f"ONNX Model file not found at {self.model_path}. Will use PyTorch fallback.")

        # 2. Initialize Calibrated Filter (T=1.18, Threshold=60%)
        self.calibrator = CalibratedClassifierFilter(
            temperature=1.18,
            confidence_threshold=0.60,
            class_mapping_path=self.class_indices_path
        )
        logger.info("Calibrated Classifier Filter initialized.")

    def predict(self, input_tensor: torch.Tensor) -> Dict[str, Any]:
        """
        Executes forward pass (ONNX with PyTorch fallback), calculates latency,
        applies temperature scaling, and flags low-confidence/OOD scans.
        """
        start_time = time.perf_counter()
        
        if self.session is not None:
            np_input = input_tensor.cpu().numpy().astype(np.float32)
            raw_outputs = self.session.run([self.output_name], {self.input_name: np_input})
            raw_logits = raw_outputs[0][0]
        else:
            # Fallback to PyTorch model if ONNX session is not active
            from app.services.model_service import model_service
            with torch.no_grad():
                device_tensor = input_tensor.to(model_service.device)
                torch_output = model_service.model(device_tensor)
                raw_logits = torch_output.cpu().numpy()[0]
                
        inference_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Apply Temperature Scaling and 60% Safety Filter
        calibrated_result = self.calibrator.filter_prediction(raw_logits, top_k=3)
        calibrated_result["inference_time_ms"] = inference_time_ms

        return calibrated_result

# Singleton instance export
onnx_service = ONNXInferenceService()