import os
import time
import json
import numpy as np
import onnxruntime as ort
import torch
from typing import Dict, Any

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

    def _initialize_session(self):
        server_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        model_path = getattr(settings, "ONNX_MODEL_PATH", "app/models/efficientnet_plant_disease.onnx")
        class_indices_path = getattr(settings, "CLASS_INDICES_PATH", "app/data/class_indices.json")
        self.model_path = model_path if os.path.isabs(model_path) else os.path.join(server_root, model_path)
        self.class_indices_path = (
            class_indices_path
            if os.path.isabs(class_indices_path)
            else os.path.join(server_root, class_indices_path)
        )
        
        # 1. Initialize ONNX Runtime Session
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = 4
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        
        logger.info(f"Loading ONNX Model from: {self.model_path}")
        self.session = ort.InferenceSession(self.model_path, sess_options=opts, providers=["CPUExecutionProvider"])
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name

        # 2. Initialize Member A's Calibrated Filter (T=1.18, Threshold=60%)
        self.calibrator = CalibratedClassifierFilter(
            temperature=1.18,
            confidence_threshold=0.60,
            class_mapping_path=self.class_indices_path
        )
        logger.info("ONNX Inference Session & Calibrated Classifier initialized.")

    def predict(self, input_tensor: torch.Tensor) -> Dict[str, Any]:
        """
        Executes ONNX forward pass, calculates latency, applies temperature scaling,
        and flags low-confidence/OOD scans.
        """
        np_input = input_tensor.cpu().numpy().astype(np.float32)
        
        start_time = time.perf_counter()
        raw_outputs = self.session.run([self.output_name], {self.input_name: np_input})
        inference_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
        
        raw_logits = raw_outputs[0][0]

        # Apply Temperature Scaling and 60% Safety Filter
        calibrated_result = self.calibrator.filter_prediction(raw_logits, top_k=3)
        calibrated_result["inference_time_ms"] = inference_time_ms

        return calibrated_result

# Singleton instance export
onnx_service = ONNXInferenceService()