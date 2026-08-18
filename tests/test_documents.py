from fastapi.testclient import TestClient


def register_and_login(client: TestClient, login: str) -> dict[str, str]:
    password = "strong-password"
    client.post(
        "/auth",
        json={
            "login": login,
            "password": password,
            "repeat_password": password,
        },
    )
    response = client.post("/login", json={"login": login, "password": password})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_project(client: TestClient, headers: dict[str, str]) -> int:
    response = client.post(
        "/projects",
        json={"name": "Documents Project", "description": "Stores documents"},
        headers=headers,
    )
    return int(response.json()["id"])


def test_upload_and_list_project_documents(client: TestClient) -> None:
    owner_headers = register_and_login(client, "owner")
    project_id = create_project(client, owner_headers)

    upload_response = client.post(
        f"/project/{project_id}/documents",
        files={"file": ("requirements.pdf", b"pdf bytes", "application/pdf")},
        headers=owner_headers,
    )
    list_response = client.get(f"/project/{project_id}/documents", headers=owner_headers)
    project_response = client.get(f"/project/{project_id}/info", headers=owner_headers)

    assert upload_response.status_code == 201
    assert upload_response.json()["filename"] == "requirements.pdf"
    assert upload_response.json()["size_bytes"] == 9
    assert list_response.status_code == 200
    assert list_response.json()[0]["filename"] == "requirements.pdf"
    assert project_response.json()["total_documents_size_bytes"] == 9


def test_download_document_requires_project_access(client: TestClient) -> None:
    owner_headers = register_and_login(client, "owner")
    other_headers = register_and_login(client, "other")
    project_id = create_project(client, owner_headers)
    upload_response = client.post(
        f"/project/{project_id}/documents",
        files={"file": ("brief.docx", b"docx bytes", "application/vnd.openxmlformats")},
        headers=owner_headers,
    )
    document_id = upload_response.json()["id"]

    allowed_response = client.get(f"/document/{document_id}", headers=owner_headers)
    forbidden_response = client.get(f"/document/{document_id}", headers=other_headers)

    assert allowed_response.status_code == 200
    assert allowed_response.content == b"docx bytes"
    assert forbidden_response.status_code == 404


def test_update_document_replaces_metadata_and_size(client: TestClient) -> None:
    owner_headers = register_and_login(client, "owner")
    project_id = create_project(client, owner_headers)
    upload_response = client.post(
        f"/project/{project_id}/documents",
        files={"file": ("old.pdf", b"old", "application/pdf")},
        headers=owner_headers,
    )
    document_id = upload_response.json()["id"]

    update_response = client.put(
        f"/document/{document_id}",
        files={"file": ("new.docx", b"new file", "application/vnd.openxmlformats")},
        headers=owner_headers,
    )
    project_response = client.get(f"/project/{project_id}/info", headers=owner_headers)

    assert update_response.status_code == 200
    assert update_response.json()["filename"] == "new.docx"
    assert update_response.json()["size_bytes"] == 8
    assert project_response.json()["total_documents_size_bytes"] == 8


def test_delete_document_removes_metadata_and_size(client: TestClient) -> None:
    owner_headers = register_and_login(client, "owner")
    project_id = create_project(client, owner_headers)
    upload_response = client.post(
        f"/project/{project_id}/documents",
        files={"file": ("delete-me.pdf", b"content", "application/pdf")},
        headers=owner_headers,
    )
    document_id = upload_response.json()["id"]

    delete_response = client.delete(f"/document/{document_id}", headers=owner_headers)
    get_response = client.get(f"/document/{document_id}", headers=owner_headers)
    project_response = client.get(f"/project/{project_id}/info", headers=owner_headers)

    assert delete_response.status_code == 204
    assert get_response.status_code == 404
    assert project_response.json()["total_documents_size_bytes"] == 0


def test_upload_rejects_unsupported_file_type(client: TestClient) -> None:
    owner_headers = register_and_login(client, "owner")
    project_id = create_project(client, owner_headers)

    response = client.post(
        f"/project/{project_id}/documents",
        files={"file": ("notes.txt", b"text", "text/plain")},
        headers=owner_headers,
    )

    assert response.status_code == 415
