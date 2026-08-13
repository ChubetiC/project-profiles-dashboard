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


def test_owner_can_invite_participant(client: TestClient) -> None:
    owner_headers = register_and_login(client, "owner")
    participant_headers = register_and_login(client, "participant")
    create_response = client.post(
        "/projects",
        json={"name": "Shared Project", "description": "Visible after invite"},
        headers=owner_headers,
    )
    project_id = create_response.json()["id"]

    invite_response = client.post(
        f"/project/{project_id}/invite",
        params={"user": "participant"},
        headers=owner_headers,
    )
    participant_projects_response = client.get("/projects", headers=participant_headers)

    assert invite_response.status_code == 200
    assert invite_response.json() == {
        "project_id": project_id,
        "user_id": 2,
        "login": "participant",
        "role": "participant",
    }
    assert participant_projects_response.status_code == 200
    assert participant_projects_response.json()[0]["id"] == project_id
    assert participant_projects_response.json()[0]["role"] == "participant"


def test_participant_can_update_but_cannot_delete_project(client: TestClient) -> None:
    owner_headers = register_and_login(client, "owner")
    participant_headers = register_and_login(client, "participant")
    create_response = client.post(
        "/projects",
        json={"name": "Shared Project", "description": "Before update"},
        headers=owner_headers,
    )
    project_id = create_response.json()["id"]
    client.post(
        f"/project/{project_id}/invite",
        params={"user": "participant"},
        headers=owner_headers,
    )

    update_response = client.put(
        f"/project/{project_id}/info",
        json={"name": "Updated by Participant", "description": "After update"},
        headers=participant_headers,
    )
    delete_response = client.delete(f"/project/{project_id}", headers=participant_headers)

    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Updated by Participant"
    assert update_response.json()["role"] == "participant"
    assert delete_response.status_code == 403


def test_participant_cannot_invite_users(client: TestClient) -> None:
    owner_headers = register_and_login(client, "owner")
    participant_headers = register_and_login(client, "participant")
    register_and_login(client, "third")
    create_response = client.post(
        "/projects",
        json={"name": "Shared Project", "description": "Only owner invites"},
        headers=owner_headers,
    )
    project_id = create_response.json()["id"]
    client.post(
        f"/project/{project_id}/invite",
        params={"user": "participant"},
        headers=owner_headers,
    )

    response = client.post(
        f"/project/{project_id}/invite",
        params={"user": "third"},
        headers=participant_headers,
    )

    assert response.status_code == 403


def test_invite_missing_or_existing_access_returns_error(client: TestClient) -> None:
    owner_headers = register_and_login(client, "owner")
    register_and_login(client, "participant")
    create_response = client.post(
        "/projects",
        json={"name": "Shared Project", "description": "Invite validation"},
        headers=owner_headers,
    )
    project_id = create_response.json()["id"]

    missing_user_response = client.post(
        f"/project/{project_id}/invite",
        params={"user": "missing"},
        headers=owner_headers,
    )
    first_invite_response = client.post(
        f"/project/{project_id}/invite",
        params={"user": "participant"},
        headers=owner_headers,
    )
    duplicate_invite_response = client.post(
        f"/project/{project_id}/invite",
        params={"user": "participant"},
        headers=owner_headers,
    )

    assert missing_user_response.status_code == 404
    assert first_invite_response.status_code == 200
    assert duplicate_invite_response.status_code == 409
