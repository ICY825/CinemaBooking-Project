from app.models import AuditLog
from app.models.enums import UserRole

API = "/api/v1"


def test_customer_and_staff_cannot_manage_accounts(client, make_user, login, cinema):
    for user in (make_user(UserRole.CUSTOMER), make_user(UserRole.STAFF, cinema_id=cinema.id)):
        assert client.get(f"{API}/users", headers=login(user)).status_code == 403


def test_admin_creates_staff_with_cinema_scope_and_audit(client, db, make_user, login, cinema):
    admin = make_user(UserRole.ADMIN)
    headers = login(admin)
    body = {"email": "staff@test.vn", "password": "Staff1234", "full_name": "Thu Ngân", "role": "staff"}

    res = client.post(f"{API}/users", json=body, headers=headers)
    assert res.status_code == 422
    assert res.json()["detail"]["code"] == "CINEMA_REQUIRED"

    res = client.post(f"{API}/users", json={**body, "cinema_id": cinema.id}, headers=headers)
    assert res.status_code == 201, res.text
    assert res.json()["cinema_id"] == cinema.id

    log = db.query(AuditLog).filter_by(action="user.create").one()
    assert log.actor_id == admin.id
    assert log.after["email"] == "staff@test.vn"
    assert "password_hash" not in log.after


def test_admin_list_filters_and_paginates(client, make_user, login):
    admin = make_user(UserRole.ADMIN)
    for _ in range(3):
        make_user(UserRole.CUSTOMER)
    res = client.get(f"{API}/users", params={"role": "customer", "size": 2}, headers=login(admin))
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 3 and len(data["items"]) == 2


def test_update_with_stale_row_version_is_rejected(client, make_user, login):
    admin = make_user(UserRole.ADMIN)
    target = make_user(UserRole.CUSTOMER)
    headers = login(admin)
    version = target.row_version

    res = client.patch(f"{API}/users/{target.id}", json={"full_name": "Tên mới", "row_version": version}, headers=headers)
    assert res.status_code == 200
    assert res.json()["row_version"] == version + 1

    # A second admin still holding the old version must not overwrite the change.
    res = client.patch(f"{API}/users/{target.id}", json={"phone": "0901234567", "row_version": version}, headers=headers)
    assert res.status_code == 409
    assert res.json()["detail"]["code"] == "VERSION_CONFLICT"


def test_disabling_user_revokes_their_session(client, make_user, login):
    admin = make_user(UserRole.ADMIN)
    target = make_user(UserRole.CUSTOMER)
    target_headers = login(target)

    res = client.patch(
        f"{API}/users/{target.id}", json={"is_active": False, "row_version": target.row_version}, headers=login(admin)
    )
    assert res.status_code == 200
    assert client.get(f"{API}/users/me", headers=target_headers).status_code == 401


def test_admin_cannot_lock_out_themselves(client, make_user, login):
    admin = make_user(UserRole.ADMIN)
    res = client.patch(
        f"{API}/users/{admin.id}", json={"role": "customer", "row_version": admin.row_version}, headers=login(admin)
    )
    assert res.status_code == 400
    assert res.json()["detail"]["code"] == "SELF_LOCKOUT"


def test_profile_update_ignores_null_for_required_fields(client, make_user, login):
    user = make_user()
    res = client.patch(
        f"{API}/users/me",
        json={"full_name": None, "phone": "0912345678", "row_version": user.row_version},
        headers=login(user),
    )
    assert res.status_code == 200
    assert res.json()["full_name"] == "Test customer"
    assert res.json()["phone"] == "0912345678"


def test_list_cinemas_is_public_and_hides_deleted(client, db, cinema):
    from datetime import datetime, timezone

    from app.models import Cinema

    db.add(Cinema(name="Old", city="HCM", address="x", deleted_at=datetime.now(timezone.utc)))
    db.commit()
    res = client.get(f"{API}/cinemas")
    assert res.status_code == 200
    assert [c["name"] for c in res.json()] == ["CGV Test"]
