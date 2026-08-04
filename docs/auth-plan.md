# Auth and Permission Notes

## Authentication Flow

1. User registers with login, password, and repeated password.
2. Password is hashed before storing it in PostgreSQL.
3. User logs in with login and password.
4. If credentials are valid, API returns a JWT access token.
5. JWT is sent to protected endpoints as:

```http
Authorization: Bearer <token>
```

Token lifetime:

- 1 hour

Planned JWT fields:

- `sub`: user login or id
- `exp`: expiration time

## Protected Endpoints

All business endpoints should require JWT:

- project creation/listing/updating/deleting
- document upload/list/download/update/delete
- user invite/share actions

## Project Access Logic

Project permissions are resolved through a user-project access table.

Planned roles:

- `owner`
- `participant`

Rules:

- Owner can view, update, delete, upload documents, update documents, delete documents, and invite users.
- Participant can view and modify project information/documents.
- Participant cannot delete the project.
- Participant cannot invite users unless this requirement changes.

## Common Auth Errors

- `401 Unauthorized`: token is missing, expired, or invalid.
- `403 Forbidden`: user is authenticated but does not have required project permissions.

