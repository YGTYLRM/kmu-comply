from typing import Any, Optional
from pydantic import BaseModel
from .enums import AnalysisStep, JobStatus


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    chromadb: str
    embedding_model: str
    version: str = "0.1.0"


class AnalyzeResponse(BaseModel):
    job_id: str
    status: JobStatus
    message: str


class StepProgress(BaseModel):
    step: AnalysisStep
    status: JobStatus
    message: Optional[str] = None
    duration_seconds: Optional[float] = None


class StatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    current_step: Optional[AnalysisStep] = None
    steps: list[StepProgress]
    error: Optional[str] = None


class ProfileValidationResponse(BaseModel):
    valid: bool
    errors: list[str]
    warnings: list[str]
    enriched_profile: Optional[dict[str, Any]] = None


class RegulationInfo(BaseModel):
    id: str
    name: str
    description: str
    document_count: int
    last_updated: Optional[str] = None


class RegulationsListResponse(BaseModel):
    regulations: list[RegulationInfo]
