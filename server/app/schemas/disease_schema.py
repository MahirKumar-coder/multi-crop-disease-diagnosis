from pydantic import BaseModel
from typing import List, Optional

class RemediationPlan(BaseModel): 
    organic: List[str]
    chemical: List[str]
    preventive: List[str]

class DiseaseDetail(BaseModel):
    id: str
    crop: str
    disease_name: str
    scientific_name: Optional[str] = "N/A"
    is_healthy: bool
    pathogen_type: str
    severity: str
    description: str
    remediation: RemediationPlan

class DiseaseListResponse(BaseModel):
    total: int
    items: List[DiseaseDetail]