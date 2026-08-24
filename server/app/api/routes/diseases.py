import json
import os
from fastapi import APIRouter, HTTPException, status
from app.schemas.disease_schema import DiseaseDetail, DiseaseListResponse
from app.core.logger import logger

router = APIRouter()

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "remediation_data.json")

def load_remediation_db():
    if not os.path.exists(DATA_PATH):
        logger.error(f"Remediation database file not found at: {DATA_PATH}")
        return{}
    with open(DATA_PATH, "r") as f:
        return json.load(f)

disease_db = load_remediation_db()

@router.get("", response_model=DiseaseListResponse, summary="List all catalogue diseases")
async def get_all_diseases():
    items = [DiseaseDetail(**v) for v in disease_db.values()]
    return DiseaseListResponse(total=len(items), items=items)

@router.get("/{disease_id}", response_model=DiseaseDetail, summary="Get single disease details")
async def get_disease_by_id(disease_id: str):
    if disease_id not in disease_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Disease record '{disease_id}' not found in knowledge database."
        )
    return DiseaseDetail(**disease_db[disease_id])