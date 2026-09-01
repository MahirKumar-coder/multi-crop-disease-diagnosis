from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class PredictionItem(BaseModel):
    class_id: int
    class_name: str
    confidence: float = Field(..., description="Calibrated confidence score percentage")

class RemediationPlan(BaseModel):
    organic: List[Dict[str, Any]] = []
    chemical: List[Dict[str, Any]] = []
    preventive: List[str] = []

class PredictionResponse(BaseModel):
    # Core Diagnosis Metadata
    predicted_class: str
    crop: str
    disease_name: str
    confidence: float
    is_healthy: bool
    pathogen_type: Optional[str] = None
    severity: Optional[str] = None
    description: Optional[str] = None
    
    # Confidence Calibration & Out-of-Distribution Feedback
    is_confident: bool = Field(..., description="False if calibrated confidence is < 60%")
    status_flag: str = Field(..., description="VALID_DIAGNOSIS or UNKNOWN_OR_AMBIGUOUS_SCAN")
    warning_message: Optional[str] = Field(None, description="Guidance if scan is ambiguous or low confidence")
    
    # Hypotheses & Visual Explainability
    top_3_predictions: List[PredictionItem]
    remediation: Optional[RemediationPlan] = None
    gradcam_heatmap_base64: Optional[str] = None
    
    # Performance & Tracing Metrics
    inference_time_ms: float
    cached: bool = False