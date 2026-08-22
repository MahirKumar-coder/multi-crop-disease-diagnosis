import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Multi-Crop Plant Disease & Remediation API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    ALLOWED_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000", "*"]
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10 MB
    ALLOWED_EXTENSIONS: set = {"image/jpeg", "image/png", "image/webp"}
    MODEL_PATH: str = os.getenv("MODEL_PATH", "app/models/efficientnet_plant_disease.pt")

    class Config:
        case_sensitive = True

settings = Settings()