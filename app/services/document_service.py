from pathlib import PurePath
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import Document, User
from app.repositories.document_repository import (
    create_document,
    delete_document,
    get_document_by_id,
    get_project_documents,
    update_document_metadata,
)
from app.services.exceptions import (
    DocumentNotFoundError,
    ProjectNotFoundError,
    ProjectStorageLimitExceededError,
    UnsupportedFileTypeError,
)
from app.services.project_service import get_project_info
from app.storage.s3_storage import DocumentStorage

SUPPORTED_EXTENSIONS = {".docx", ".pdf"}
DEFAULT_CONTENT_TYPE = "application/octet-stream"


def list_project_documents(db: Session, project_id: int, user: User) -> list[Document]:
    get_project_info(db, project_id=project_id, user=user)
    return get_project_documents(db, project_id=project_id)


def upload_project_document(
    db: Session,
    storage: DocumentStorage,
    project_id: int,
    user: User,
    filename: str,
    content_type: str | None,
    content: bytes,
) -> Document:
    project, _ = get_project_info(db, project_id=project_id, user=user)
    safe_filename = validate_filename(filename)
    safe_content_type = content_type or DEFAULT_CONTENT_TYPE
    validate_supported_file_type(safe_filename)
    ensure_project_storage_limit(project.total_documents_size_bytes, len(content))

    storage_key = build_storage_key(project_id=project_id, filename=safe_filename)
    storage.upload_file(storage_key, content, safe_content_type)
    return create_document(
        db,
        project=project,
        uploaded_by_user_id=user.id,
        filename=safe_filename,
        content_type=safe_content_type,
        storage_key=storage_key,
        size_bytes=len(content),
    )


def download_document(
    db: Session,
    storage: DocumentStorage,
    document_id: int,
    user: User,
) -> tuple[Document, bytes]:
    document = get_accessible_document(db, document_id=document_id, user=user)
    return document, storage.download_file(document.storage_key)


def update_document(
    db: Session,
    storage: DocumentStorage,
    document_id: int,
    user: User,
    filename: str,
    content_type: str | None,
    content: bytes,
) -> Document:
    document = get_accessible_document(db, document_id=document_id, user=user)
    safe_filename = validate_filename(filename)
    safe_content_type = content_type or DEFAULT_CONTENT_TYPE
    validate_supported_file_type(safe_filename)

    current_total_without_document = (
        document.project.total_documents_size_bytes - document.size_bytes
    )
    ensure_project_storage_limit(current_total_without_document, len(content))

    old_storage_key = document.storage_key
    new_storage_key = build_storage_key(project_id=document.project_id, filename=safe_filename)
    storage.upload_file(new_storage_key, content, safe_content_type)
    updated_document = update_document_metadata(
        db,
        document=document,
        filename=safe_filename,
        content_type=safe_content_type,
        storage_key=new_storage_key,
        size_bytes=len(content),
    )
    storage.delete_file(old_storage_key)
    return updated_document


def delete_project_document(
    db: Session,
    storage: DocumentStorage,
    document_id: int,
    user: User,
) -> None:
    document = get_accessible_document(db, document_id=document_id, user=user)
    storage_key = document.storage_key
    delete_document(db, document)
    storage.delete_file(storage_key)


def get_accessible_document(db: Session, document_id: int, user: User) -> Document:
    document = get_document_by_id(db, document_id=document_id)
    if document is None:
        raise DocumentNotFoundError

    try:
        get_project_info(db, project_id=document.project_id, user=user)
    except ProjectNotFoundError as error:
        raise DocumentNotFoundError from error

    return document


def validate_filename(filename: str) -> str:
    safe_filename = PurePath(filename).name
    if not safe_filename:
        raise UnsupportedFileTypeError
    return safe_filename


def validate_supported_file_type(filename: str) -> None:
    suffix = PurePath(filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise UnsupportedFileTypeError


def ensure_project_storage_limit(current_size_bytes: int, added_size_bytes: int) -> None:
    settings = get_settings()
    if current_size_bytes + added_size_bytes > settings.max_project_storage_bytes:
        raise ProjectStorageLimitExceededError


def build_storage_key(project_id: int, filename: str) -> str:
    return f"projects/{project_id}/documents/{uuid4()}-{filename}"
