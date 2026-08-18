from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.dependencies import get_document_storage
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app


class FakeDocumentStorage:
    def __init__(self) -> None:
        self.files: dict[str, bytes] = {}

    def upload_file(self, storage_key: str, content: bytes, content_type: str) -> None:
        self.files[storage_key] = content

    def download_file(self, storage_key: str) -> bytes:
        return self.files[storage_key]

    def delete_file(self, storage_key: str) -> None:
        self.files.pop(storage_key, None)


@pytest.fixture
def client() -> Generator[TestClient]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db() -> Generator[Session]:
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app = create_app(init_database=False)
    app.dependency_overrides[get_db] = override_get_db
    fake_storage = FakeDocumentStorage()
    app.dependency_overrides[get_document_storage] = lambda: fake_storage

    with TestClient(app) as test_client:
        yield test_client

    Base.metadata.drop_all(bind=engine)
