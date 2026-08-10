from fastapi.testclient import TestClient


def test_register_user_returns_created_user(client: TestClient) -> None:
    # Arrange
    payload = {
        "login": "project_owner",
        "password": "StrongPassword123!",
        "repeat_password": "StrongPassword123!",
    }

    # Act
    response = client.post("/auth", json=payload)

    # Assert
    assert response.status_code == 201
    assert response.json() == {"id": 1, "login": "project_owner"}


def test_register_user_rejects_duplicate_login(client: TestClient) -> None:
    # Arrange
    payload = {
        "login": "project_owner",
        "password": "StrongPassword123!",
        "repeat_password": "StrongPassword123!",
    }
    client.post("/auth", json=payload)

    # Act
    response = client.post("/auth", json=payload)

    # Assert
    assert response.status_code == 409
    assert response.json() == {"detail": "Login already exists"}


def test_login_returns_access_token(client: TestClient) -> None:
    # Arrange
    client.post(
        "/auth",
        json={
            "login": "project_owner",
            "password": "StrongPassword123!",
            "repeat_password": "StrongPassword123!",
        },
    )

    # Act
    response = client.post(
        "/login",
        json={"login": "project_owner", "password": "StrongPassword123!"},
    )

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in_seconds"] == 3600
    assert isinstance(body["access_token"], str)
    assert body["access_token"]


def test_login_rejects_invalid_password(client: TestClient) -> None:
    # Arrange
    client.post(
        "/auth",
        json={
            "login": "project_owner",
            "password": "StrongPassword123!",
            "repeat_password": "StrongPassword123!",
        },
    )

    # Act
    response = client.post(
        "/login",
        json={"login": "project_owner", "password": "WrongPassword123!"},
    )

    # Assert
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid login or password"}
