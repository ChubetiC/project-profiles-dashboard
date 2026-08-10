from app.db.base import Base
from app.db.models import Document, Project, ProjectAccess, User
from app.db.session import engine

__all__ = ["Document", "Project", "ProjectAccess", "User"]


def init_db() -> None:
    Base.metadata.create_all(bind=engine)

