from fastapi import APIRouter, Query, status
from app.services.history_service import history_service
from app.schemas.history import HistoryListResponse, HistoryClearResponse

router = APIRouter(prefix="/api/history", tags=["Diagnostic History"])

@router.get("", response_model=HistoryListResponse, status_code=status.HTTP_200_OK)
async def get_diagnostic_history(
    limit: int = Query(50, ge=1, le=100, description="Maximum entries to return"),
    offset: int = Query(0, ge=0, description="Pagination offset")
):
    """
    Retrieves chronological diagnostic audit history including timestamp,
    crop, diagnosis, confidence, latency, and status flags.
    """
    data = history_service.get_records(limit=limit, offset=offset)
    return data

@router.delete("", response_model=HistoryClearResponse, status_code=status.HTTP_200_OK)
async def clear_diagnostic_history():
    """
    Purges all historical diagnostic audit records from the system.
    """
    deleted = history_service.clear_records()
    return {
        "message": "Diagnostic history successfully purged.",
        "deleted_count": deleted
    }