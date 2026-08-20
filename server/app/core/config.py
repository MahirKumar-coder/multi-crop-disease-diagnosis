import os
from pydantic_settings import BaseSettings

class Settings:
    PROJECT_NAME: str = "Multi-Crop Plant Disease & Remediation API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    ALLOWED_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000", "*"]
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024
    ALLOWED_EXTENSIONS: str = {"image/jpeg", "image/png", "image/webp"}
    MODEL_PATH: str = os.getenv("MODEL_PATH", "app/models/efficientnet_plant_disease.pt")

settings = Settings()