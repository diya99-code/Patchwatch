from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.api.deps import get_current_active_user
from app.core.exceptions import http_404_not_found, http_403_forbidden
from app.database import get_db
from app.models import User, Project, Scan
from app.schemas.project import (
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
    ProjectSummary,
)

router = APIRouter()


def get_user_project(
    project_id: int,
    current_user: User,
    db: Session
) -> Project:
    """
    Get a project owned by the current user or raise 404.
    """
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise http_404_not_found("Project not found")
    
    return project


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Create a new project for the current user.
    """
    db_project = Project(
        name=project_data.name,
        description=project_data.description,
        repository_url=str(project_data.repository_url) if project_data.repository_url else None,
        owner_id=current_user.id,
    )
    
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    return ProjectResponse(
        id=db_project.id,
        name=db_project.name,
        description=db_project.description,
        repository_url=db_project.repository_url,
        owner_id=db_project.owner_id,
        created_at=db_project.created_at.isoformat(),
        updated_at=db_project.updated_at.isoformat(),
    )


@router.get("/", response_model=List[ProjectResponse])
def list_projects(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    List all projects owned by the current user.
    """
    projects = db.query(Project).filter(Project.owner_id == current_user.id).all()
    
    return [
        ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            repository_url=project.repository_url,
            owner_id=project.owner_id,
            created_at=project.created_at.isoformat(),
            updated_at=project.updated_at.isoformat(),
        )
        for project in projects
    ]


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get a specific project owned by the current user.
    """
    project = get_user_project(project_id, current_user, db)
    
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        repository_url=project.repository_url,
        owner_id=project.owner_id,
        created_at=project.created_at.isoformat(),
        updated_at=project.updated_at.isoformat(),
    )


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Update a project owned by the current user.
    """
    project = get_user_project(project_id, current_user, db)
    
    # Update only provided fields
    update_data = project_data.dict(exclude_unset=True)
    
    if "repository_url" in update_data and update_data["repository_url"]:
        update_data["repository_url"] = str(update_data["repository_url"])
    
    for field, value in update_data.items():
        setattr(project, field, value)
    
    db.commit()
    db.refresh(project)
    
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        repository_url=project.repository_url,
        owner_id=project.owner_id,
        created_at=project.created_at.isoformat(),
        updated_at=project.updated_at.isoformat(),
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a project owned by the current user.
    """
    project = get_user_project(project_id, current_user, db)
    
    db.delete(project)
    db.commit()


@router.get("/{project_id}/summary", response_model=ProjectSummary)
def get_project_summary(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get project summary with vulnerability and scan statistics.
    """
    project = get_user_project(project_id, current_user, db)
    
    # Get scan counts and latest scan
    scan_stats = db.query(
        func.count(Scan.id).label("total_scans"),
        func.max(Scan.created_at).label("latest_scan_date"),
        func.sum(Scan.critical_vulns).label("critical_vulns"),
        func.sum(Scan.high_vulns).label("high_vulns"),
        func.sum(Scan.outdated_deps).label("outdated_deps"),
    ).filter(Scan.project_id == project_id).first()
    
    return ProjectSummary(
        id=project.id,
        name=project.name,
        total_scans=scan_stats.total_scans or 0,
        latest_scan_date=scan_stats.latest_scan_date.isoformat() if scan_stats.latest_scan_date else None,
        critical_vulnerabilities=scan_stats.critical_vulns or 0,
        high_vulnerabilities=scan_stats.high_vulns or 0,
        outdated_dependencies=scan_stats.outdated_deps or 0,
    )