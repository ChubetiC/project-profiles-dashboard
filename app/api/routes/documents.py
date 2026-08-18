from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette.responses import Response as StarletteResponse

from app.api.dependencies import get_current_user, get_document_storage
from app.db.models import Document, User
from app.db.session import get_db
from app.services.document_service import (
    delete_project_document,
    download_document,
    list_project_documents,
    update_document,
    upload_project_document,
)
from app.services.exceptions import (
    DocumentNotFoundError,
    ProjectNotFoundError,
    ProjectStorageLimitExceededError,
    UnsupportedFileTypeError,
)
from app.storage.s3_storage import DocumentStorage

router = APIRouter(tags=["documents"])


class DocumentResponse(BaseModel):
    id: int
    project_id: int
    uploaded_by_user_id: int
    filename: str
    content_type: str
    size_bytes: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_document(cls, document: Document) -> "DocumentResponse":
        return cls(
            id=document.id,
            project_id=document.project_id,
            uploaded_by_user_id=document.uploaded_by_user_id,
            filename=document.filename,
            content_type=document.content_type,
            size_bytes=document.size_bytes,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )


@router.get("/project/{project_id}/documents", response_model=list[DocumentResponse])
def list_project_documents_endpoint(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DocumentResponse]:
    try:
        documents = list_project_documents(db, project_id=project_id, user=current_user)
    except ProjectNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        ) from error

    return [DocumentResponse.from_document(document) for document in documents]


@router.post(
    "/project/{project_id}/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_project_document_endpoint(
    project_id: int,
    file: UploadFile = File(),
    db: Session = Depends(get_db),
    storage: DocumentStorage = Depends(get_document_storage),
    current_user: User = Depends(get_current_user),
) -> DocumentResponse:
    try:
        content = await file.read()
        document = upload_project_document(
            db,
            storage=storage,
            project_id=project_id,
            user=current_user,
            filename=file.filename or "",
            content_type=file.content_type,
            content=content,
        )
    except ProjectNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        ) from error
    except UnsupportedFileTypeError as error:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="File type not supported",
        ) from error
    except ProjectStorageLimitExceededError as error:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Project storage limit exceeded",
        ) from error

    return DocumentResponse.from_document(document)


@router.get("/document/{document_id}")
def download_document_endpoint(
    document_id: int,
    db: Session = Depends(get_db),
    storage: DocumentStorage = Depends(get_document_storage),
    current_user: User = Depends(get_current_user),
) -> StarletteResponse:
    try:
        document, content = download_document(
            db,
            storage=storage,
            document_id=document_id,
            user=current_user,
        )
    except DocumentNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        ) from error

    return Response(
        content=content,
        media_type=document.content_type,
        headers={"Content-Disposition": f'attachment; filename="{document.filename}"'},
    )


@router.put("/document/{document_id}", response_model=DocumentResponse)
async def update_document_endpoint(
    document_id: int,
    file: UploadFile = File(),
    db: Session = Depends(get_db),
    storage: DocumentStorage = Depends(get_document_storage),
    current_user: User = Depends(get_current_user),
) -> DocumentResponse:
    try:
        content = await file.read()
        document = update_document(
            db,
            storage=storage,
            document_id=document_id,
            user=current_user,
            filename=file.filename or "",
            content_type=file.content_type,
            content=content,
        )
    except DocumentNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        ) from error
    except UnsupportedFileTypeError as error:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="File type not supported",
        ) from error
    except ProjectStorageLimitExceededError as error:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Project storage limit exceeded",
        ) from error

    return DocumentResponse.from_document(document)


@router.delete("/document/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document_endpoint(
    document_id: int,
    db: Session = Depends(get_db),
    storage: DocumentStorage = Depends(get_document_storage),
    current_user: User = Depends(get_current_user),
) -> Response:
    try:
        delete_project_document(
            db,
            storage=storage,
            document_id=document_id,
            user=current_user,
        )
    except DocumentNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        ) from error

    return Response(status_code=status.HTTP_204_NO_CONTENT)
