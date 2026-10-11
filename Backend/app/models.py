from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Boolean, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.database import Base


def _now():
    return datetime.now(timezone.utc)


class ScanStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed" 
    FAILED = "failed"
    CANCELLED = "cancelled"


class DependencyType(str, enum.Enum):
    DIRECT = "direct"
    TRANSITIVE = "transitive"
    UNKNOWN = "unknown"


class SeverityLevel(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class RecommendationPriority(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[Optional[str]] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    projects: Mapped[list["Project"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    repository_url: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    owner: Mapped[User] = relationship(back_populates="projects")
    scans: Mapped[list["Scan"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class Scan(Base):
    __tablename__ = "scans"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    status: Mapped[ScanStatus] = mapped_column(SQLEnum(ScanStatus), default=ScanStatus.QUEUED)
    filename: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Summary counts
    total_deps: Mapped[int] = mapped_column(Integer, default=0)
    direct_deps: Mapped[int] = mapped_column(Integer, default=0)
    transitive_deps: Mapped[int] = mapped_column(Integer, default=0)
    outdated_deps: Mapped[int] = mapped_column(Integer, default=0)
    vulnerable_deps: Mapped[int] = mapped_column(Integer, default=0)
    
    # Vulnerability counts by severity
    critical_vulns: Mapped[int] = mapped_column(Integer, default=0)
    high_vulns: Mapped[int] = mapped_column(Integer, default=0)
    medium_vulns: Mapped[int] = mapped_column(Integer, default=0)
    low_vulns: Mapped[int] = mapped_column(Integer, default=0)
    
    # Error information
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    # Celery task information
    task_id: Mapped[Optional[str]] = mapped_column(String(255))

    project: Mapped[Project] = relationship(back_populates="scans")
    dependencies: Mapped[list["Dependency"]] = relationship(
        back_populates="scan", cascade="all, delete-orphan"
    )


class Dependency(Base):
    __tablename__ = "dependencies"

    id: Mapped[int] = mapped_column(primary_key=True)
    scan_id: Mapped[int] = mapped_column(ForeignKey("scans.id"))
    
    # Package information
    package_name: Mapped[str] = mapped_column(String(255), index=True)
    ecosystem: Mapped[str] = mapped_column(String(50))  # npm, pypi, maven, etc.
    
    # Version information
    installed_version: Mapped[str] = mapped_column(String(100))
    declared_constraint: Mapped[Optional[str]] = mapped_column(String(100))
    latest_version: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Dependency metadata
    dependency_type: Mapped[DependencyType] = mapped_column(
        SQLEnum(DependencyType), default=DependencyType.UNKNOWN
    )
    is_outdated: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    scan: Mapped[Scan] = relationship(back_populates="dependencies")
    vulnerabilities: Mapped[list["Vulnerability"]] = relationship(
        back_populates="dependency", cascade="all, delete-orphan"
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(
        back_populates="dependency", cascade="all, delete-orphan"
    )


class Vulnerability(Base):
    __tablename__ = "vulnerabilities"

    id: Mapped[int] = mapped_column(primary_key=True)
    dependency_id: Mapped[int] = mapped_column(ForeignKey("dependencies.id"))
    
    # Vulnerability identification
    advisory_id: Mapped[str] = mapped_column(String(100), index=True)
    ecosystem: Mapped[str] = mapped_column(String(50))
    package_name: Mapped[str] = mapped_column(String(255))
    
    # Vulnerability details
    summary: Mapped[str] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)
    severity: Mapped[SeverityLevel] = mapped_column(
        SQLEnum(SeverityLevel), default=SeverityLevel.UNKNOWN
    )
    
    # Version information
    affected_versions: Mapped[Optional[str]] = mapped_column(Text)  # JSON string
    fixed_versions: Mapped[Optional[str]] = mapped_column(Text)    # JSON string
    
    # Additional metadata
    aliases: Mapped[Optional[str]] = mapped_column(Text)  # JSON string
    references: Mapped[Optional[str]] = mapped_column(Text)  # JSON string
    
    # Timestamps
    published_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    modified_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    detected_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    dependency: Mapped[Dependency] = relationship(back_populates="vulnerabilities")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(primary_key=True)
    dependency_id: Mapped[int] = mapped_column(ForeignKey("dependencies.id"))
    
    # Recommendation details
    recommended_version: Mapped[str] = mapped_column(String(100))
    priority: Mapped[RecommendationPriority] = mapped_column(
        SQLEnum(RecommendationPriority), default=RecommendationPriority.INFO
    )
    reasoning: Mapped[str] = mapped_column(Text)
    
    # Supporting evidence
    fixes_vulnerabilities: Mapped[bool] = mapped_column(Boolean, default=False)
    vulnerability_count: Mapped[int] = mapped_column(Integer, default=0)
    is_breaking_change: Mapped[Optional[bool]] = mapped_column(Boolean)
    
    # Additional metadata
    evidence: Mapped[Optional[str]] = mapped_column(Text)  # JSON string
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    dependency: Mapped[Dependency] = relationship(back_populates="recommendations")


# Legacy models for backward compatibility (to be migrated)
class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[int] = mapped_column(primary_key=True)
    scan_id: Mapped[int] = mapped_column(ForeignKey("scans.id"))
    package: Mapped[str] = mapped_column(String(255))
    version: Mapped[str] = mapped_column(String(64))
    vuln_id: Mapped[str] = mapped_column(String(64))
    summary: Mapped[str] = mapped_column(Text, default="")
    severity: Mapped[str] = mapped_column(String(16), default="UNKNOWN")
    fixed_versions: Mapped[str] = mapped_column(String(255), default="")
    aliases: Mapped[str] = mapped_column(String(255), default="")

    scan: Mapped[Scan] = relationship()  # No back_populates to avoid conflicts
