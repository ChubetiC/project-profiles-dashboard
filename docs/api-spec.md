# API Specification Draft

All successful responses return JSON, except document download endpoints that return file data.

API responses should stay flat where possible. Related entities are referenced by numeric IDs, and nested entities are avoided unless there is a clear reason to include them.

Protected endpoints require:

```http
Authorization: Bearer <jwt_token>
```

## Common Error Format

```json
{
  "detail": "Error message"
}
```

Common status codes:

- `400` invalid request data
- `401` missing or invalid authentication
- `403` authenticated but not allowed
- `404` resource not found
- `409` conflict, for example duplicate login
- `413` file/project storage limit exceeded
- `415` unsupported file type
- `500` unexpected server error

## POST /auth

Create a new user.

Input:

```json
{
  "login": "project_owner",
  "password": "StrongPassword123!",
  "repeat_password": "StrongPassword123!"
}
```

Output:

```json
{
  "id": 1,
  "login": "project_owner"
}
```

Success:

- `201 Created`

Errors:

- `400` passwords do not match or validation failed
- `409` login already exists
- `500` unexpected server error

## POST /login

Log in and receive JWT token.

Input:

```json
{
  "login": "project_owner",
  "password": "StrongPassword123!"
}
```

Output:

```json
{
  "access_token": "jwt-token",
  "token_type": "bearer",
  "expires_in_seconds": 3600
}
```

Success:

- `200 OK`

Errors:

- `401` invalid login or password
- `500` unexpected server error

## POST /projects

Create a project. The current user becomes the project owner.

Input:

```json
{
  "name": "Internal Dashboard",
  "description": "Dashboard for storing project details and documents"
}
```

Output:

```json
{
  "id": 1,
  "name": "Internal Dashboard",
  "description": "Dashboard for storing project details and documents",
  "total_documents_size_bytes": 0,
  "created_at": "<ISO datetime>",
  "updated_at": "<ISO datetime>"
}
```

Success:

- `201 Created`

Errors:

- `401` missing or invalid token
- `400` validation error
- `500` unexpected server error

## GET /projects

Return all projects accessible by the current user.

Output:

```json
[
  {
    "id": 1,
    "name": "Internal Dashboard",
    "description": "Dashboard for storing project details and documents",
    "role": "owner",
    "total_documents_size_bytes": 1048576
  }
]
```

Success:

- `200 OK`

Errors:

- `401` missing or invalid token
- `500` unexpected server error

## GET /project/{project_id}/info

Return project details if the current user has access.

Output:

```json
{
  "id": 1,
  "name": "Internal Dashboard",
  "description": "Dashboard for storing project details and documents",
  "total_documents_size_bytes": 1048576,
  "created_at": "<ISO datetime>",
  "updated_at": "<ISO datetime>"
}
```

Success:

- `200 OK`

Errors:

- `401` missing or invalid token
- `403` user does not have project access
- `404` project not found
- `500` unexpected server error

## PUT /project/{project_id}/info

Update project details. Owner and participant can update.

Input:

```json
{
  "name": "Updated Dashboard",
  "description": "Updated description"
}
```

Output:

```json
{
  "id": 1,
  "name": "Updated Dashboard",
  "description": "Updated description",
  "total_documents_size_bytes": 1048576,
  "created_at": "<ISO datetime>",
  "updated_at": "<ISO datetime>"
}
```

Success:

- `200 OK`

Errors:

- `401` missing or invalid token
- `403` user does not have project access
- `404` project not found
- `500` unexpected server error

## DELETE /project/{project_id}

Delete project and its documents. Only owner can delete.

Output:

No response body.

Success:

- `204 No Content`

Errors:

- `401` missing or invalid token
- `403` user is not project owner
- `404` project not found
- `500` unexpected server error

## GET /project/{project_id}/documents

Return all documents attached to a project.

Output:

```json
[
  {
    "id": 10,
    "project_id": 1,
    "uploaded_by_user_id": 2,
    "filename": "requirements.pdf",
    "content_type": "application/pdf",
    "size_bytes": 1048576,
    "created_at": "<ISO datetime>",
    "updated_at": "<ISO datetime>"
  }
]
```

Success:

- `200 OK`

Errors:

- `401` missing or invalid token
- `403` user does not have project access
- `404` project not found
- `500` unexpected server error

## POST /project/{project_id}/documents

Upload one document to a project.

Initial implementation plan: the API receives the file bytes and uploads them to object storage.

Optional future improvement: use pre-signed upload URLs so the client can upload directly to S3/MinIO-compatible storage. In that version, the API would receive only file metadata, create a pending document record, return an upload URL, and later mark the document as uploaded after an object storage event/handler confirms the upload.

Input:

- `multipart/form-data`
- field name: `file`
- allowed types: `application/pdf`, DOCX MIME type

Output:

```json
{
  "id": 10,
  "project_id": 1,
  "uploaded_by_user_id": 2,
  "filename": "requirements.pdf",
  "content_type": "application/pdf",
  "size_bytes": 1048576,
  "created_at": "<ISO datetime>",
  "updated_at": "<ISO datetime>"
}
```

Success:

- `201 Created`

Errors:

- `401` missing or invalid token
- `403` user does not have project access
- `404` project not found
- `413` project storage limit exceeded
- `415` unsupported file type
- `500` unexpected server error

## GET /document/{document_id}

Download a document if the current user has access to the related project.

Initial implementation plan: the API streams file bytes from object storage to the user.

Optional future improvement: after permission checks, the API returns a pre-signed download URL and the user downloads the file directly from object storage.

Output:

- file bytes

Success:

- `200 OK`

Errors:

- `401` missing or invalid token
- `403` user does not have project access
- `404` document not found
- `500` unexpected server error

## PUT /document/{document_id}

Replace an existing document.

Input:

- `multipart/form-data`
- field name: `file`

Output:

```json
{
  "id": 10,
  "project_id": 1,
  "uploaded_by_user_id": 2,
  "filename": "requirements-v2.pdf",
  "content_type": "application/pdf",
  "size_bytes": 2097152,
  "created_at": "<ISO datetime>",
  "updated_at": "<ISO datetime>"
}
```

Success:

- `200 OK`

Errors:

- `401` missing or invalid token
- `403` user does not have project access
- `404` document not found
- `413` project storage limit exceeded
- `415` unsupported file type
- `500` unexpected server error

## DELETE /document/{document_id}

Delete a document from object storage and database.

Output:

No response body.

Success:

- `204 No Content`

Errors:

- `401` missing or invalid token
- `403` user does not have project access
- `404` document not found
- `500` unexpected server error

## POST /project/{project_id}/invite?user={login}

Grant participant access to another user. Only project owner can invite.

Output:

No response body.

Success:

- `204 No Content`

Errors:

- `401` missing or invalid token
- `403` current user is not project owner
- `404` project or invited user not found
- `500` unexpected server error

## Optional: GET /project/{project_id}/share?with={email}

Generate a join link with a signed token.

Output:

```json
{
  "email": "teammate@example.com",
  "join_url": "http://localhost:8000/join?token=signed-token",
  "token": "signed-token"
}
```

Success:

- `200 OK`

Errors:

- `401` missing or invalid token
- `403` current user is not project owner
- `404` project not found
- `400` invalid email
- `500` unexpected server error
