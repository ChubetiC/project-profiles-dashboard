from __future__ import annotations

import argparse
from dataclasses import dataclass
from time import time

import httpx


@dataclass(frozen=True)
class UserCredentials:
    login: str
    password: str


class ApiCheckError(RuntimeError):
    pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a basic end-to-end API check.")
    parser.add_argument("--base-url", default="http://localhost:8000")
    args = parser.parse_args()

    run_id = str(int(time()))
    owner = UserCredentials(login=f"owner_{run_id}", password="strong-password")
    participant = UserCredentials(login=f"participant_{run_id}", password="strong-password")

    with httpx.Client(base_url=args.base_url, timeout=10.0) as client:
        check_health(client)
        register_user(client, owner)
        register_user(client, participant)

        owner_token = login(client, owner)
        owner_headers = auth_headers(owner_token)

        project_id = create_project(client, owner_headers)
        list_projects(client, owner_headers, expected_project_id=project_id)
        invite_participant(client, owner_headers, project_id, participant.login)

        participant_token = login(client, participant)
        participant_headers = auth_headers(participant_token)
        list_projects(client, participant_headers, expected_project_id=project_id)
        update_project_as_participant(client, participant_headers, project_id)

        document_id = upload_document(client, participant_headers, project_id)
        list_documents(client, participant_headers, project_id, expected_document_id=document_id)
        download_document(client, participant_headers, document_id)
        update_document(client, participant_headers, document_id)
        delete_document(client, participant_headers, document_id)

        ensure_participant_cannot_delete_project(client, participant_headers, project_id)
        delete_project_as_owner(client, owner_headers, project_id)

    print("API check passed.")


def check_health(client: httpx.Client) -> None:
    response = client.get("/health")
    assert_status(response, 200)
    print("OK health")


def register_user(client: httpx.Client, credentials: UserCredentials) -> None:
    response = client.post(
        "/auth",
        json={
            "login": credentials.login,
            "password": credentials.password,
            "repeat_password": credentials.password,
        },
    )
    assert_status(response, 201)
    print(f"OK registered {credentials.login}")


def login(client: httpx.Client, credentials: UserCredentials) -> str:
    response = client.post(
        "/login",
        json={"login": credentials.login, "password": credentials.password},
    )
    assert_status(response, 200)
    token = response.json()["access_token"]
    print(f"OK logged in {credentials.login}")
    return str(token)


def create_project(client: httpx.Client, headers: dict[str, str]) -> int:
    response = client.post(
        "/projects",
        json={"name": "API Check Project", "description": "Created by scripts/check_api.py"},
        headers=headers,
    )
    assert_status(response, 201)
    project_id = int(response.json()["id"])
    print(f"OK created project {project_id}")
    return project_id


def list_projects(
    client: httpx.Client,
    headers: dict[str, str],
    expected_project_id: int,
) -> None:
    response = client.get("/projects", headers=headers)
    assert_status(response, 200)
    project_ids = {project["id"] for project in response.json()}
    if expected_project_id not in project_ids:
        raise ApiCheckError(f"Project {expected_project_id} was not listed")
    print("OK listed projects")


def invite_participant(
    client: httpx.Client,
    headers: dict[str, str],
    project_id: int,
    participant_login: str,
) -> None:
    response = client.post(
        f"/project/{project_id}/invite",
        params={"user": participant_login},
        headers=headers,
    )
    assert_status(response, 200)
    print("OK invited participant")


def update_project_as_participant(
    client: httpx.Client,
    headers: dict[str, str],
    project_id: int,
) -> None:
    response = client.put(
        f"/project/{project_id}/info",
        json={
            "name": "API Check Project Updated",
            "description": "Updated by participant during API check",
        },
        headers=headers,
    )
    assert_status(response, 200)
    print("OK updated project as participant")


def upload_document(client: httpx.Client, headers: dict[str, str], project_id: int) -> int:
    response = client.post(
        f"/project/{project_id}/documents",
        files={"file": ("api-check.pdf", b"%PDF-1.4 api check content", "application/pdf")},
        headers=headers,
    )
    assert_status(response, 201)
    document_id = int(response.json()["id"])
    print(f"OK uploaded document {document_id}")
    return document_id


def list_documents(
    client: httpx.Client,
    headers: dict[str, str],
    project_id: int,
    expected_document_id: int,
) -> None:
    response = client.get(f"/project/{project_id}/documents", headers=headers)
    assert_status(response, 200)
    document_ids = {document["id"] for document in response.json()}
    if expected_document_id not in document_ids:
        raise ApiCheckError(f"Document {expected_document_id} was not listed")
    print("OK listed documents")


def download_document(client: httpx.Client, headers: dict[str, str], document_id: int) -> None:
    response = client.get(f"/document/{document_id}", headers=headers)
    assert_status(response, 200)
    if response.content != b"%PDF-1.4 api check content":
        raise ApiCheckError("Downloaded document content did not match uploaded content")
    print("OK downloaded document")


def update_document(client: httpx.Client, headers: dict[str, str], document_id: int) -> None:
    response = client.put(
        f"/document/{document_id}",
        files={
            "file": (
                "api-check-updated.docx",
                b"updated content",
                "application/vnd.openxmlformats",
            )
        },
        headers=headers,
    )
    assert_status(response, 200)
    body = response.json()
    if body["filename"] != "api-check-updated.docx":
        raise ApiCheckError("Updated document filename was not returned")
    print("OK updated document")


def delete_document(client: httpx.Client, headers: dict[str, str], document_id: int) -> None:
    response = client.delete(f"/document/{document_id}", headers=headers)
    assert_status(response, 204)
    print("OK deleted document")


def ensure_participant_cannot_delete_project(
    client: httpx.Client,
    headers: dict[str, str],
    project_id: int,
) -> None:
    response = client.delete(f"/project/{project_id}", headers=headers)
    assert_status(response, 403)
    print("OK participant cannot delete project")


def delete_project_as_owner(client: httpx.Client, headers: dict[str, str], project_id: int) -> None:
    response = client.delete(f"/project/{project_id}", headers=headers)
    assert_status(response, 204)
    print("OK owner deleted project")


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def assert_status(response: httpx.Response, expected_status: int) -> None:
    if response.status_code != expected_status:
        raise ApiCheckError(
            f"{response.request.method} {response.request.url} returned "
            f"{response.status_code}, expected {expected_status}: {response.text}"
        )


if __name__ == "__main__":
    main()
