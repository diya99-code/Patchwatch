from typing import Optional
from pydantic import BaseModel, Field, HttpUrl


class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    repository_url: Optional[HttpUrl] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    repository_url: Optional[HttpUrl] = None


class ProjectResponse(ProjectBase):
    id: int
    owner_id: int
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class ProjectSummary(BaseModel):
    id: int
    name: str
    total_scans: int
    latest_scan_date: Optional[str] = None
    critical_vulnerabilities: int
    high_vulnerabilities: int
    outdated_dependencies: int
    
    class Config:
        from_attributes = True