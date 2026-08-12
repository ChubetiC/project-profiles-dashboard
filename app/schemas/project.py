from datetime import datetime

from pydantic import BaseModel, Field


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

