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

Local development target:

- Python 3.13

Initial checks:

```bash
uv sync --extra dev
uv run --extra dev pytest
uv run --extra dev ruff check .
uv run --extra dev mypy app tests
```

Local Docker services:

- `api`: FastAPI application
- `db`: PostgreSQL database
- `minio`: S3-compatible object storage

Start local infrastructure:

```bash
cp .env.example .env
docker compose up --build
```

Useful local URLs:

- API health check: `http://localhost:8000/health`
- API docs: `http://localhost:8000/docs`
- MinIO console: `http://localhost:9001`
