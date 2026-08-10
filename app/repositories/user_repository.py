from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import User


def get_user_by_login(db: Session, login: str) -> User | None:
    return db.scalar(select(User).where(User.login == login))


def create_user(db: Session, login: str, hashed_password: str) -> User:
    user = User(login=login, hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

