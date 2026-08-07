def test_register_user(client):
    response = client.post(
        "/auth/register",
        json={"email": "alice@example.com", "password": "test1234", "username": "alice"},
    )
    assert response.status_code == 201
    assert response.json()["username"] == "alice"   


def test_login_success(client):
    client.post(
        "/auth/register",
        json={"email": "bob@example.com", "password": "test1234", "username": "bob"},
    )
    response = client.post(
        "/auth/login",
        data={"username": "bob@example.com", "password": "test1234"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_wrong_password(client):
    client.post(
        "/auth/register",
        json={"email": "carol@example.com", "password": "test1234", "username": "carol"},
    )
    response = client.post(
        "/auth/login",
        data={"username": "carol@example.com", "password": "wrongpass"},
    )
    assert response.status_code == 401