def _register_and_login(client, email, password="test1234"):
    username = email.split("@")[0]  # email se username derive kar lete hain, unique rahega
    client.post("/auth/register", json={"email": email, "password": password, "username": username})
    response = client.post("/auth/login", data={"username": email, "password": password})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_unauthenticated_upload_rejected(client):
    response = client.post("/api/documents/")
    assert response.status_code == 401


def test_list_documents_empty_for_new_user(client):
    headers = _register_and_login(client, "newuser@example.com")
    response = client.get("/api/documents/", headers=headers)
    assert response.status_code == 200
    assert response.json() == []


def test_reject_unsupported_file_type(client):
    headers = _register_and_login(client, "filetest@example.com")
    response = client.post(
        "/api/documents/",
        headers=headers,
        files={"file": ("test.exe", b"fake content", "application/octet-stream")},
    )
    assert response.status_code == 400