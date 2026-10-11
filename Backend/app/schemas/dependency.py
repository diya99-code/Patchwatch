from typing import Optional, List
from pydantic import BaseModel

from app.models import DependencyType, SeverityLevel, RecommendationPriority


class VulnerabilityResponse(BaseModel):
    id: int
    advisory_id: str
    ecosystem: str
    package_name: str
    summary: str
    description: Optional[str]
    severity: SeverityLevel
    affected_versions: Optional[str]
    fixed_versions: Optional[str]
    aliases: Optional[str]
    references: Optional[str]
    published_date: Optional[str]
    modified_date: Optional[str]
    detected_at: str
    
    class Config:
        from_attributes = True


class RecommendationResponse(BaseModel):
    id: int
    recommended_version: str
    priority: RecommendationPriority
    reasoning: str
    fixes_vulnerabilities: bool
    vulnerability_count: int
    is_breaking_change: Optional[bool]
    evidence: Optional[str]
    created_at: str
    
    class Config:
        from_attributes = True


class DependencyResponse(BaseModel):
    id: int
    scan_id: int
    package_name: str
    ecosystem: str
    installed_version: str
    declared_constraint: Optional[str]
    latest_version: Optional[str]
    dependency_type: DependencyType
    is_outdated: bool
    created_at: str
    
    class Config:
        from_attributes = True


class DependencyWithVulnerabilities(DependencyResponse):
    vulnerabilities: List[VulnerabilityResponse]
    recommendations: List[RecommendationResponse]
    
    class Config:
        from_attributes = True


class DependencyUpdate(BaseModel):
    package_name: str
    current_version: str
    recommended_version: str
    priority: RecommendationPriority
    reasoning: str
    fixes_vulnerabilities: bool