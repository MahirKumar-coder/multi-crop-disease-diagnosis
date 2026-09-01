import os
import torch
import torch.nn as nn
from pathlib import Path
from torchvision.models import efficientnet_b0
from app.core.config import settings
from app.core.logger import logger

class ModelLoaderService:
    _instance = None
    _model = None
    _device = None
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
            cls._instance = super(ModelLoaderService, cls).__new__(cls)
            cls._instance._initialize_model()
        return cls._instance

    def _resolve_model_path(self, raw_path: str) -> str:
        current_dir = Path(__file__).resolve().parent
        candidates = [
            Path(raw_path),
            current_dir / ".." / "models" / Path(raw_path).name,
            current_dir / ".." / "models" / "efficientnet_plant_disease.pt",
            current_dir / ".." / "models" / "best_efficientnet.pt",
            current_dir / ".." / "models" / "best_efficientnet_v2.pt",
            Path("server/app/models") / Path(raw_path).name,
            Path("app/models") / Path(raw_path).name,
            Path("server/app/models/efficientnet_plant_disease.pt"),
            Path("app/models/efficientnet_plant_disease.pt"),
        ]
        for c in candidates:
            if c.exists():
                return str(c.resolve())
        return raw_path

    def _initialize_model(self):
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Loading EfficientNet inference model on device: {self._device}")

        model = efficientnet_b0(weights=None)
        in_features = model.classifier[1].in_features
        model.classifier = nn.Sequential(
            nn.Dropout(p=0.3, inplace=True),
            nn.Linear(in_features, 512),
            nn.BatchNorm1d(512),
            nn.SiLU(),
            nn.Dropout(p=0.3, inplace=True),
            nn.Linear(512, len(self._class_names))
        )

        resolved_path = self._resolve_model_path(getattr(settings, "MODEL_PATH", "app/models/efficientnet_plant_disease.pt"))

        if os.path.exists(resolved_path):
            try:
                state_dict = torch.load(resolved_path, map_location=self._device)
                model.load_state_dict(state_dict)
                logger.info(f"Loaded weights from {resolved_path}")
            except Exception as e:
                logger.warning(f"Failed to load weights from file: {e}, Running with initialized head.")
        else:
            logger.warning(f"Weights file not found at '{resolved_path}'. Running in test mock mode.")

        model.to(self._device)
        model.eval()
        self._model = model

    @property
    def model(self):
        return self._model

    @property
    def device(self):
        return self._device

    @property
    def class_names(self):
        return self._class_names

model_service = ModelLoaderService()