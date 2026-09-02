from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class DiagnosticAuditRecord(BaseModel):
    id: int
    timestamp: str = Field(..., description="ISO 8601 formatted diagnostic timestamp")
    crop: str = Field(..., description="Target plant species")
    disease_name: str = Field(..., description="Diagnosed condition or healthy status")
    confidence: float = Field(..., description="Calibrated confidence percentage")
    is_confident: bool = Field(..., description="Confidence threshold status flag")
    status_flag: str = Field(..., description="VALID_DIAGNOSIS or UNKNOWN_OR_AMBIGUOUS_SCAN")
    latency_ms: float = Field(..., description="Total inference pipeline latency in milliseconds")
    client_ip: Optional[str] = Field(None, description="Anonymized or raw client IP address")

class HistoryListResponse(BaseModel):
    total_records: int
    records: List[DiagnosticAuditRecord]

class HistoryClearResponse(BaseModel):
    message: str
    deleted_count: int