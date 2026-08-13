from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.models import Project, User
from app.db.session import get_db
from app.schemas.project import (
    ProjectCreateRequest,
    ProjectInviteResponse,
    ProjectResponse,
    ProjectUpdateRequest,
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


def to_project_response(project: Project, role: str) -> ProjectResponse:
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        total_documents_size_bytes=project.total_documents_size_bytes,
        role=role,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


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
    return to_project_response(project, role)


@router.get("/projects", response_model=list[ProjectResponse])
def list_projects_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ProjectResponse]:
    projects = list_user_projects(db, current_user)
    return [to_project_response(project, role) for project, role in projects]


@router.get("/project/{project_id}/info", response_model=ProjectResponse)
def get_project_info_endpoint(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectResponse:
    project, role = get_project_info(db, project_id=project_id, user=current_user)
    return to_project_response(project, role)


@router.put("/project/{project_id}/info", response_model=ProjectResponse)
def update_project_info_endpoint(
    project_id: int,
    payload: ProjectUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectResponse:
    project, role = update_project_info(
        db,
        project_id=project_id,
        user=current_user,
        name=payload.name,
        description=payload.description,
    )
    return to_project_response(project, role)


@router.delete("/project/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project_endpoint(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    delete_project_as_owner(db, project_id=project_id, user=current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/project/{project_id}/invite", response_model=ProjectInviteResponse)
def invite_project_participant_endpoint(
    project_id: int,
    user_login: str = Query(alias="user", min_length=1, max_length=80),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectInviteResponse:
    project_access, invited_user = invite_project_participant(
        db,
        project_id=project_id,
        requester=current_user,
        invited_login=user_login,
    )
    return ProjectInviteResponse(
        project_id=project_access.project_id,
        user_id=invited_user.id,
        login=invited_user.login,
        role=project_access.role,
    )

