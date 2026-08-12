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


def test_create_project_gives_owner_access(client: TestClient) -> None:
    headers = register_and_login(client, "owner")

    response = client.post(
        "/projects",
        json={"name": "Internal Tools", "description": "Dashboard services"},
        headers=headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["name"] == "Internal Tools"
    assert body["description"] == "Dashboard services"
    assert body["role"] == "owner"
    assert body["total_documents_size_bytes"] == 0


def test_list_projects_returns_only_accessible_projects(client: TestClient) -> None:
    owner_headers = register_and_login(client, "owner")
    other_headers = register_and_login(client, "other")
    client.post(
        "/projects",
        json={"name": "Owner Project", "description": "Visible to owner"},
        headers=owner_headers,
    )

    owner_response = client.get("/projects", headers=owner_headers)
    other_response = client.get("/projects", headers=other_headers)

    assert owner_response.status_code == 200
    assert len(owner_response.json()) == 1
    assert other_response.status_code == 200
    assert other_response.json() == []


def test_get_project_info_requires_access(client: TestClient) -> None:
    owner_headers = register_and_login(client, "owner")
    other_headers = register_and_login(client, "other")
    create_response = client.post(
        "/projects",
        json={"name": "Private Project", "description": "Not shared"},
        headers=owner_headers,
    )
    project_id = create_response.json()["id"]

    allowed_response = client.get(f"/project/{project_id}/info", headers=owner_headers)
    forbidden_response = client.get(f"/project/{project_id}/info", headers=other_headers)

    assert allowed_response.status_code == 200
    assert allowed_response.json()["id"] == project_id
    assert forbidden_response.status_code == 404


def test_update_project_info_requires_access(client: TestClient) -> None:
    owner_headers = register_and_login(client, "owner")
    other_headers = register_and_login(client, "other")
    create_response = client.post(
        "/projects",
        json={"name": "Old Name", "description": "Old description"},
        headers=owner_headers,
    )
    project_id = create_response.json()["id"]

    update_response = client.put(
        f"/project/{project_id}/info",
        json={"name": "New Name", "description": "New description"},
        headers=owner_headers,
    )
    forbidden_response = client.put(
        f"/project/{project_id}/info",
        json={"name": "Other Name", "description": "Other description"},
        headers=other_headers,
    )

    assert update_response.status_code == 200
    assert update_response.json()["name"] == "New Name"
    assert update_response.json()["description"] == "New description"
    assert forbidden_response.status_code == 404


def test_delete_project_requires_owner_access(client: TestClient) -> None:
    owner_headers = register_and_login(client, "owner")
    other_headers = register_and_login(client, "other")
    create_response = client.post(
        "/projects",
        json={"name": "Deleted Project", "description": "Can be deleted by owner"},
        headers=owner_headers,
    )
    project_id = create_response.json()["id"]

    forbidden_response = client.delete(f"/project/{project_id}", headers=other_headers)
    delete_response = client.delete(f"/project/{project_id}", headers=owner_headers)
    get_response = client.get(f"/project/{project_id}/info", headers=owner_headers)

    assert forbidden_response.status_code == 404
    assert delete_response.status_code == 204
    assert get_response.status_code == 404


def test_project_endpoints_require_authentication(client: TestClient) -> None:
    response = client.get("/projects")

    assert response.status_code == 401
