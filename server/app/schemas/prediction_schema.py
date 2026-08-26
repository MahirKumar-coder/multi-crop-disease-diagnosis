from pydantic import BaseModel
from typing import List, Optional
from app.schemas.disease_schema import RemediationPlan

class PredictionItem(BaseModel):
    class_id: str
    disease_name: str
    crop: str
    confidence: float

class PredictionResponse(BaseModel):
    predicted_class: str
    crop: str
    disease_name: str
    scientific_name: Optional[str] = "N/A"
    confidence: float
    is_healthy: bool
    pathogen_type: str
    severity: str
    description: str
    remediation: RemediationPlan
    top_3_predictions: List[PredictionItem]
    gradcam_heatmap_base64: Optional[str] = None
    cached: bool = False
    image_sha256: Optional[str] = None
