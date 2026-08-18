from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Document, Project


def create_document(
    db: Session,
    project: Project,
    uploaded_by_user_id: int,
    filename: str,
    content_type: str,
    storage_key: str,
    size_bytes: int,
) -> Document:
    document = Document(
        project_id=project.id,
        uploaded_by_user_id=uploaded_by_user_id,
        filename=filename,
        content_type=content_type,
        storage_key=storage_key,
        size_bytes=size_bytes,
    )
    project.total_documents_size_bytes += size_bytes
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def get_project_documents(db: Session, project_id: int) -> list[Document]:
    statement = select(Document).where(Document.project_id == project_id).order_by(Document.id)
    return list(db.scalars(statement).all())


def get_document_by_id(db: Session, document_id: int) -> Document | None:
    return db.get(Document, document_id)


def update_document_metadata(
    db: Session,
    document: Document,
    filename: str,
    content_type: str,
    storage_key: str,
    size_bytes: int,
) -> Document:
    project = document.project
    project.total_documents_size_bytes = (
        project.total_documents_size_bytes - document.size_bytes + size_bytes
    )
    document.filename = filename
    document.content_type = content_type
    document.storage_key = storage_key
    document.size_bytes = size_bytes
    db.commit()
    db.refresh(document)
    return document


def delete_document(db: Session, document: Document) -> None:
    document.project.total_documents_size_bytes -= document.size_bytes
    db.delete(document)
    db.commit()
