from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.models import Project, User
from app.db.session import get_db
from app.services.exceptions import (
    OnlyProjectOwnerAllowedError,
    ProjectAccessAlreadyExistsError,
    ProjectNotFoundError,
    UserNotFoundError,
)
from app.services.project_service import (
    create_project,
    delete_project_as_owner,
    get_project_info,
    invite_project_participant,
    list_user_projects,
    update_project_info,
)

router = APIRouter(tags=["projects"])


class ProjectCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1, max_length=5000)


class ProjectUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1, max_length=5000)


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: str
    total_documents_size_bytes: int
    role: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_project(cls, project: Project, role: str) -> "ProjectResponse":
        return cls(
            id=project.id,
            name=project.name,
            description=project.description,
            total_documents_size_bytes=project.total_documents_size_bytes,
            role=role,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )


class ProjectInviteResponse(BaseModel):
    project_id: int
    user_id: int
    login: str
    role: str


@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project_endpoint(
    payload: ProjectCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectResponse:
    project, role = create_project(
        db,
        owner=current_user,
        name=payload.name,
        description=payload.description,
    )
    return ProjectResponse.from_project(project, role)


@router.get("/projects", response_model=list[ProjectResponse])
def list_projects_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ProjectResponse]:
    projects = list_user_projects(db, current_user)
    return [ProjectResponse.from_project(project, role) for project, role in projects]


@router.get("/project/{project_id}/info", response_model=ProjectResponse)
def get_project_info_endpoint(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectResponse:
    try:
        project, role = get_project_info(db, project_id=project_id, user=current_user)
    except ProjectNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        ) from error

    return ProjectResponse.from_project(project, role)


@router.put("/project/{project_id}/info", response_model=ProjectResponse)
def update_project_info_endpoint(
    project_id: int,
    payload: ProjectUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectResponse:
    try:
        project, role = update_project_info(
            db,
            project_id=project_id,
            user=current_user,
            name=payload.name,
            description=payload.description,
        )
    except ProjectNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        ) from error

    return ProjectResponse.from_project(project, role)


@router.delete("/project/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project_endpoint(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    try:
        delete_project_as_owner(db, project_id=project_id, user=current_user)
    except ProjectNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        ) from error
    except OnlyProjectOwnerAllowedError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owner can delete project",
        ) from error

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/project/{project_id}/invite", response_model=ProjectInviteResponse)
def invite_project_participant_endpoint(
    project_id: int,
    user_login: str = Query(alias="user", min_length=1, max_length=80),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectInviteResponse:
    try:
        project_access, invited_user = invite_project_participant(
            db,
            project_id=project_id,
            requester=current_user,
            invited_login=user_login,
        )
    except ProjectNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        ) from error
    except OnlyProjectOwnerAllowedError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owner can invite users",
        ) from error
    except UserNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        ) from error
    except ProjectAccessAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already has access to this project",
        ) from error

    return ProjectInviteResponse(
        project_id=project_access.project_id,
        user_id=invited_user.id,
        login=invited_user.login,
        role=project_access.role,
    )

