from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import Project, ProjectAccess, User
from app.repositories.project_repository import (
    create_project_access,
    create_project_with_owner,
    delete_project,
    get_accessible_projects,
    get_project_access,
    get_project_with_role,
    save_project,
)
from app.repositories.user_repository import get_user_by_login

OWNER_ROLE = "owner"
PARTICIPANT_ROLE = "participant"


def create_project(db: Session, owner: User, name: str, description: str) -> tuple[Project, str]:
    project = create_project_with_owner(db, owner=owner, name=name, description=description)
    return project, OWNER_ROLE


def list_user_projects(db: Session, user: User) -> list[tuple[Project, str]]:
    return get_accessible_projects(db, user)


def get_project_info(db: Session, project_id: int, user: User) -> tuple[Project, str]:
    project_with_role = get_project_with_role(db, project_id=project_id, user=user)
    if project_with_role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return project_with_role


def update_project_info(
    db: Session,
    project_id: int,
    user: User,
    name: str,
    description: str,
) -> tuple[Project, str]:
    project, role = get_project_info(db, project_id=project_id, user=user)
    project.name = name
    project.description = description
    return save_project(db, project), role


def delete_project_as_owner(db: Session, project_id: int, user: User) -> None:
    project, role = get_project_info(db, project_id=project_id, user=user)
    if role != OWNER_ROLE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owner can delete project",
        )

    delete_project(db, project)


def invite_project_participant(
    db: Session,
    project_id: int,
    requester: User,
    invited_login: str,
) -> tuple[ProjectAccess, User]:
    _, requester_role = get_project_info(db, project_id=project_id, user=requester)
    if requester_role != OWNER_ROLE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owner can invite users",
        )

    invited_user = get_user_by_login(db, invited_login)
    if invited_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    existing_access = get_project_access(db, project_id=project_id, user_id=invited_user.id)
    if existing_access is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already has access to this project",
        )

    project_access = create_project_access(
        db,
        project_id=project_id,
        user_id=invited_user.id,
        role=PARTICIPANT_ROLE,
    )
    return project_access, invited_user

