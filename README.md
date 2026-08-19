# Project Profiles Dashboard

FastAPI backend for managing project profiles, shared access, and attached project
documents.

The service lets users register, log in, create projects, invite participants, and
manage PDF/DOCX documents stored in S3-compatible object storage.

## Features

- User registration and login
- Password hashing with bcrypt
- JWT authentication for protected endpoints
- Project create/list/read/update/delete
- Owner and participant project roles
- Owner-only project delete and invite permissions
- PDF/DOCX document upload, list, download, update, and delete
- Document metadata stored in PostgreSQL
- Document bytes stored in MinIO locally
- Project-level document size tracking
- Automated tests, linting, type checking, and GitHub Actions CI
- Manual end-to-end API check script

## Tech Stack

- Python 3.13
- FastAPI
- Pydantic
- SQLAlchemy ORM
- PostgreSQL
- MinIO/S3-compatible object storage
- Docker Compose
- uv
- pytest
- Ruff
- mypy
- GitHub Actions

## Architecture

The code is split by responsibility:

- `app/api/routes`: FastAPI route handlers and API request/response models
- `app/services`: business logic and service-layer errors
- `app/repositories`: database query/write helpers
- `app/db/models`: SQLAlchemy ORM models
- `app/storage`: S3/MinIO storage integration
- `tests`: automated endpoint and service-flow tests
- `scripts`: manual API verification scripts
- `docs`: API specification and auth notes

Dependency direction is kept simple:

```text
API routes -> services -> repositories/storage -> database/object storage
```

Services raise plain service exceptions. API routes translate those exceptions into
HTTP responses.

## Data Model

Main entities:

- `User`: account login and password hash
- `Project`: project name, description, and total document size
- `ProjectAccess`: user-project relationship with role
- `Document`: file metadata and storage key

Access rules:

- `owner`: can view, update, delete, invite users, and manage documents
- `participant`: can view/update project info and manage documents, but cannot delete the project or invite users

## Local Setup

Create local environment file:

```bash
cp .env.example .env
```

Start local services:

```bash
docker compose up --build
```

Useful local URLs:

- API health check: `http://localhost:8000/health`
- API docs: `http://localhost:8000/docs`
- MinIO console: `http://localhost:9001`

Stop local services:

```bash
docker compose down
```

Reset local database and object storage volumes:

```bash
docker compose down -v
```

## Development Checks

Install dependencies:

```bash
uv sync --extra dev
```

Run tests:

```bash
uv run --extra dev pytest
```

Run linting:

```bash
uv run --extra dev ruff check .
```

Run type checking:

```bash
uv run --extra dev mypy app tests scripts
```

GitHub Actions runs tests, Ruff, and mypy on pull requests and pushes to `main`.

## Manual API Check

With the Docker Compose app running, execute:

```bash
uv run --extra dev python scripts/check_api.py
```

The script verifies:

- health check
- user registration and login
- project creation
- project sharing
- participant project update
- document upload/list/download/update/delete
- participant project delete restriction
- owner project deletion

To run against another deployed URL:

```bash
uv run --extra dev python scripts/check_api.py --base-url http://server-url
```

## Swagger Demo Flow

Open:

```text
http://localhost:8000/docs
```

Suggested demo:

1. `POST /auth`: register owner user
2. `POST /auth`: register participant user
3. `POST /login`: log in as owner
4. Authorize with `Bearer <access_token>`
5. `POST /projects`: create project
6. `POST /project/{project_id}/invite?user=<login>`: invite participant
7. `POST /login`: log in as participant
8. Authorize with participant token
9. `PUT /project/{project_id}/info`: update project as participant
10. `POST /project/{project_id}/documents`: upload PDF/DOCX document
11. `GET /project/{project_id}/documents`: list documents
12. `GET /document/{document_id}`: download document
13. `DELETE /project/{project_id}` as participant: confirm `403 Forbidden`

## API Specification

Full endpoint details are documented in:

- [docs/api-spec.md](docs/api-spec.md)
- [docs/auth-plan.md](docs/auth-plan.md)

## Current Limitations

- Database schema is created automatically on startup for local development.
- Alembic migrations are not included yet.
- Local object storage uses MinIO; AWS S3 can use the same S3-compatible storage layer.
- Upload/download currently pass file bytes through the API. Pre-signed URLs are a possible future improvement.
- Email invite/share links are documented as optional but not implemented.
