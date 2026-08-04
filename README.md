# Project Profiles Dashboard

Draft backend project for managing project profiles and attached documents.

Current scope:

- user registration and login
- project creation, update, listing, and deletion
- project document upload, download, update, and deletion
- project access sharing with owner/participant roles

Planned local stack:

- FastAPI
- PostgreSQL
- SQLAlchemy ORM
- MinIO or another S3-compatible object storage
- Docker Compose

Project structure will separate:

- API layer: FastAPI routes and request/response schemas
- service layer: business logic and permission checks
- DB layer: ORM models and database queries
- storage layer: document storage integration

API specification:

- [docs/api-spec.md](docs/api-spec.md)

