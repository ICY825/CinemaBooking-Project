import re

from app.api.v1 import auth as auth_api
from tests.conftest import PASSWORD

API = "/api/v1"


def test_register_login_me(client):
    res = client.post(
        f"{API}/auth/register",
        json={"email": "An@Example.com", "password": "Secret123", "full_name": "Nguyễn Văn An"},
    )
    assert res.status_code == 201, res.text
    assert res.json()["email"] == "an@example.com"
    assert res.json()["role"] == "customer"

    tokens = client.post(f"{API}/auth/login", json={"email": "an@example.com", "password": "Secret123"}).json()
    me = client.get(f"{API}/users/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert me.status_code == 200
    assert me.json()["full_name"] == "Nguyễn Văn An"
    assert "password_hash" not in me.json()


def test_register_rejects_duplicate_email_and_weak_password(client, make_user):
    make_user(email="dup@test.vn")
    res = client.post(f"{API}/auth/register", json={"email": "DUP@test.vn", "password": "Secret123", "full_name": "Dup"})
    assert res.status_code == 409
    assert res.json()["detail"]["code"] == "EMAIL_TAKEN"

    res = client.post(f"{API}/auth/register", json={"email": "x@test.vn", "password": "onlyletters", "full_name": "Xx"})
    assert res.status_code == 422


def test_login_wrong_password_and_disabled_account(client, make_user):
    user = make_user()
    res = client.post(f"{API}/auth/login", json={"email": user.email, "password": "wrong-pass1"})
    assert res.status_code == 401
    assert res.json()["detail"]["code"] == "INVALID_CREDENTIALS"

    res = client.post(f"{API}/auth/login", json={"email": "nobody@test.vn", "password": PASSWORD})
    assert res.status_code == 401

    disabled = make_user(is_active=False)
    res = client.post(f"{API}/auth/login", json={"email": disabled.email, "password": PASSWORD})
    assert res.status_code == 403


def test_protected_route_requires_valid_access_token(client, make_user):
    assert client.get(f"{API}/users/me").status_code == 401
    assert client.get(f"{API}/users/me", headers={"Authorization": "Bearer garbage"}).status_code == 401

    user = make_user()
    tokens = client.post(f"{API}/auth/login", json={"email": user.email, "password": PASSWORD}).json()
    # A refresh token must not be accepted as an access token.
    res = client.get(f"{API}/users/me", headers={"Authorization": f"Bearer {tokens['refresh_token']}"})
    assert res.status_code == 401


def test_refresh_then_logout_revokes_all_tokens(client, make_user):
    user = make_user()
    tokens = client.post(f"{API}/auth/login", json={"email": user.email, "password": PASSWORD}).json()

    new = client.post(f"{API}/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert new.status_code == 200
    headers = {"Authorization": f"Bearer {new.json()['access_token']}"}

    assert client.post(f"{API}/auth/logout", headers=headers).status_code == 204
    assert client.get(f"{API}/users/me", headers=headers).status_code == 401
    assert client.post(f"{API}/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 401


def test_forgot_and_reset_password_link_works_once(client, make_user, monkeypatch):
    sent = []
    monkeypatch.setattr(auth_api, "send_email", lambda to, subject, body: sent.append((to, body)))
    user = make_user()

    assert client.post(f"{API}/auth/forgot-password", json={"email": "unknown@test.vn"}).status_code == 202
    assert sent == []  # same response, but nothing sent for unknown emails

    assert client.post(f"{API}/auth/forgot-password", json={"email": user.email}).status_code == 202
    assert len(sent) == 1 and sent[0][0] == user.email
    token = re.search(r"token=(\S+)", sent[0][1]).group(1)

    res = client.post(f"{API}/auth/reset-password", json={"token": token, "new_password": "NewPass123"})
    assert res.status_code == 204
    res = client.post(f"{API}/auth/reset-password", json={"token": token, "new_password": "Other1234"})
    assert res.status_code == 400

    assert client.post(f"{API}/auth/login", json={"email": user.email, "password": "NewPass123"}).status_code == 200
    assert client.post(f"{API}/auth/login", json={"email": user.email, "password": PASSWORD}).status_code == 401


def test_change_password_requires_current_password(client, make_user, login):
    user = make_user()
    headers = login(user)
    body = {"current_password": "wrong", "new_password": "NewPass123"}
    assert client.post(f"{API}/users/me/change-password", json=body, headers=headers).status_code == 400

    body["current_password"] = PASSWORD
    assert client.post(f"{API}/users/me/change-password", json=body, headers=headers).status_code == 204
    # Every session is signed out after a password change.
    assert client.get(f"{API}/users/me", headers=headers).status_code == 401


def test_json_responses_declare_utf8_charset(client, make_user, login):
    # Without it Windows PowerShell 5.1 decodes responses as Latin-1 and garbles Vietnamese.
    res = client.get(f"{API}/users/me", headers=login(make_user()))
    assert res.headers["content-type"] == "application/json; charset=utf-8"
