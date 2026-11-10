from datetime import datetime, timedelta, timezone

import jwt

from auth.auth import SECRET_KEY, ALGORITHM


def test_register_user(client):

    response = client.post(
        "/users/register",
        json={
            "email": "nuevo@test.com",
            "password": "password123"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == "nuevo@test.com"
    assert data["id"] > 0
    assert "password" not in data
    assert "password_hash" not in data


def test_register_duplicate_email(client):

    response = client.post(
        "/users/register",
        json={
            "email": "nuevo@test.com",
            "password": "password123"
        }
    )

    assert response.status_code == 200

    response = client.post(
        "/users/register",
        json={
            "email": "nuevo@test.com",
            "password": "otra123"
        }
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "El email ya está registrado"
    )


def test_login_success(client, user):

    response = client.post(
        "/users/login",
        json={
            "email": user.email,
            "password": "password123"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"

    token = data["access_token"]

    payload = jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM]
    )

    assert payload["sub"] == str(user.id)


def test_login_wrong_password(client, user):

    response = client.post(
        "/users/login",
        json={
            "email": user.email,
            "password": "password_incorrecta"
        }
    )

    assert response.status_code == 401

    assert response.json()["detail"] == (
        "Email o contraseña incorrectos"
    )


def test_login_nonexistent_user(client):

    response = client.post(
        "/users/login",
        json={
            "email": "noexiste@test.com",
            "password": "password123"
        }
    )

    assert response.status_code == 401

    assert response.json()["detail"] == (
        "Email o contraseña incorrectos"
    )


def test_invalid_token_rejected(
    client,
    auth_headers
):

    headers = {
        "Authorization": "Bearer token_invalido"
    }

    response = client.get(
        "/packages/",
        headers=headers
    )

    assert response.status_code == 401


def test_expired_token_rejected(
    client,
    user
):

    expires_at = (
        datetime.now(timezone.utc)
        - timedelta(minutes=10)
    )

    token = jwt.encode(
        {
            "sub": str(user.id),
            "exp": expires_at
        },
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = client.get(
        "/packages/",
        headers=headers
    )

    assert response.status_code == 401


def test_token_for_nonexistent_user_rejected(
    client
):

    token = jwt.encode(
        {
            "sub": "999999",
            "exp": (
                datetime.now(timezone.utc)
                + timedelta(minutes=10)
            )
        },
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = client.get(
        "/packages/",
        headers=headers
    )

    assert response.status_code == 401


def test_missing_token_rejected(client):

    response = client.get(
        "/packages/"
    )

    assert response.status_code == 401