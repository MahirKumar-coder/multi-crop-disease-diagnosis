import os
import time
import numpy as np
from PIL import Image
import onnxruntime as ort
from app.core.config import settings
from app.core.logger import logger

class ONNXInferenceService:
    _instance = None
    _session = None
    _input_name = None
    _output_name = None

    _class_names = [
        "Apple___Apple_scab", "Apple___Black_rot", "Apple___Cedar_apple_rust", "Apple___healthy",
        "Blueberry___healthy", "Cherry___Powdery_mildew", "Cherry___healthy",
        "Corn___Cercospora_leaf_spot Gray_leaf_spot", "Corn___Common_rust", "Corn___Northern_Leaf_Blight", "Corn___healthy",
        "Grape___Black_rot", "Grape___Esca_(Black_Measles)", "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)", "Grape___healthy",
        "Orange___Haunglongbing_(Citrus_greening)", "Peach___Bacterial_spot", "Peach___healthy",
        "Pepper,_bell___Bacterial_spot", "Pepper,_bell___healthy",
        "Potato___Early_blight", "Potato___Late_blight", "Potato___healthy",
        "Raspberry___healthy", "Soybean___healthy", "Squash___Powdery_mildew",
        "Strawberry___Leaf_scorch", "Strawberry___healthy",
        "Tomato___Bacterial_spot", "Tomato___Early_blight", "Tomato___Late_blight", "Tomato___Leaf_Mold",
        "Tomato___Septoria_leaf_spot", "Tomato___Spider_mites Two-spotted_spider_mite", "Tomato___Target_Spot",
        "Tomato___Tomato_Yellow_Leaf_Curl_Virus", "Tomato___Tomato_mosaic_virus", "Tomato___healthy"
    ]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ONNXInferenceService, cls).__new__(cls)
            cls._instance._initialize_session()
        return cls._instance

    def _initialize_session(self):
        onnx_model_path = os.getenv("ONNX_MODEL_PATH", "app/models/efficientnet_plant_disease.onnx")
        
        # 1. Configure Multi-Threaded CPU Execution Options
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = os.cpu_count() or 4
        opts.inter_op_num_threads = 2
        opts.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

        logger.info(f"Initializing ONNX Runtime session (Threads: {opts.intra_op_num_threads})")

        if os.path.exists(onnx_model_path):
            self._session = ort.InferenceSession(
                onnx_model_path, 
                sess_options=opts, 
                providers=["CPUExecutionProvider"]
            )
            self._input_name = self._session.get_inputs()[0].name
            self._output_name = self._session.get_outputs()[0].name
            logger.info(f"Loaded ONNX model successfully from {onnx_model_path}")
        else:
            logger.warning(f"ONNX model file not found at '{onnx_model_path}'. Running session in fallback mock mode.")
            self._session = None

    @staticmethod
    def preprocess_image(image: Image.Image) -> np.ndarray:
        """Pure NumPy/PIL ImageNet normalization (mean/std) without Torch dependency."""
        img = image.resize((224, 224)).convert("RGB")
        img_arr = np.array(img, dtype=np.float32) / 255.0

        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        img_arr = (img_arr - mean) / std

        # Transpose from (H, W, C) -> (C, H, W) and expand batch dim (1, C, H, W)
        img_arr = np.transpose(img_arr, (2, 0, 1))
        return np.expand_dims(img_arr, axis=0).astype(np.float32)

    @staticmethod
    def softmax(x: np.ndarray) -> np.ndarray:
        exp_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
        return exp_x / np.sum(exp_x, axis=-1, keepdims=True)

    def predict(self, image: Image.Image):
        input_tensor = self.preprocess_image(image)

        if self._session is None:
            # Fallback mock for testing if no model exported yet
            mock_probs = np.random.uniform(0, 1, size=(len(self._class_names),))
            probs = self.softmax(mock_probs)
        else:
            raw_outputs = self._session.run([self._output_name], {self._input_name: input_tensor})[0]
            probs = self.softmax(raw_outputs[0])

        top3_indices = np.argsort(probs)[::-1][:3]
        top3_results = [
            {
                "class_id": self._class_names[idx],
                "confidence": round(float(probs[idx]) * 100, 2)
            }
            for idx in top3_indices
        ]
        return top3_results[0]["class_id"], top3_results[0]["confidence"], top3_results

onnx_service = ONNXInferenceService()