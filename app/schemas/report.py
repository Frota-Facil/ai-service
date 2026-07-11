from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class ReportUser(BaseModel):
    id: str
    name: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None


class ReportVehicle(BaseModel):
    id: str
    plate: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    odometer: Optional[int] = None
    status: Optional[str] = None
    type: Optional[str] = None


class ReportRoute(BaseModel):
    id: str
    request_id: str
    status: Optional[str] = None
    description: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ReportTrack(BaseModel):
    id: str
    route_id: str
    latitude: float
    longitude: float
    captured_at: datetime
    image_url: Optional[str] = None
    image_key: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ReportRequest(BaseModel):
    id: str
    user_id: Optional[str] = None
    vehicle_id: Optional[str] = None
    approved_by: Optional[str] = None
    status: str
    predicted_start_date: datetime
    predicted_end_date: datetime
    reason: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ReportRoute(BaseModel):
    id: str
    request_id: str
    status: Optional[str] = None
    description: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ReportTrack(BaseModel):
    id: str
    route_id: str
    x_coordinate: int
    y_coordinate: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class GenerateRouteReportInput(BaseModel):
    route: ReportRoute
    request: Optional[ReportRequest] = None
    vehicle: Optional[ReportVehicle] = None
    user: Optional[ReportUser] = None
    tracks: List[ReportTrack] = Field(default_factory=list)

    extra_context: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class GenerateRouteReportOutput(BaseModel):
    markdown_content: str
