from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Project, ProjectAccess, User


def create_project_with_owner(db: Session, owner: User, name: str, description: str) -> Project:
    project = Project(name=name, description=description)
    db.add(project)
    db.flush()

    db.add(ProjectAccess(user_id=owner.id, project_id=project.id, role="owner"))
    db.commit()
    db.refresh(project)
    return project


def get_accessible_projects(db: Session, user: User) -> list[tuple[Project, str]]:
    statement = (
        select(Project, ProjectAccess.role)
        .join(ProjectAccess, ProjectAccess.project_id == Project.id)
        .where(ProjectAccess.user_id == user.id)
        .order_by(Project.id)
    )
    return list(db.execute(statement).tuples().all())


def get_project_with_role(db: Session, project_id: int, user: User) -> tuple[Project, str] | None:
    statement = (
        select(Project, ProjectAccess.role)
        .join(ProjectAccess, ProjectAccess.project_id == Project.id)
        .where(Project.id == project_id, ProjectAccess.user_id == user.id)
    )
    return db.execute(statement).tuples().one_or_none()


def get_project_access(db: Session, project_id: int, user_id: int) -> ProjectAccess | None:
    return db.scalar(
        select(ProjectAccess).where(
            ProjectAccess.project_id == project_id,
            ProjectAccess.user_id == user_id,
        )
    )


def create_project_access(
    db: Session,
    project_id: int,
    user_id: int,
    role: str,
) -> ProjectAccess:
    project_access = ProjectAccess(project_id=project_id, user_id=user_id, role=role)
    db.add(project_access)
    db.commit()
    db.refresh(project_access)
    return project_access


def save_project(db: Session, project: Project) -> Project:
    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, project: Project) -> None:
    db.delete(project)
    db.commit()
