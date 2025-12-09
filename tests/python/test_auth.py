# tests/python/test_auth.py
from flask import g

from scheduler import logic
from scheduler.app import admin_only, login_required
from scheduler.auth import authorization
from scheduler.auth.authorization import require_permission
from scheduler.auth.session import require_jwt
from scheduler.auth.models import SessionUser


def test_superuser_creation(app_context):
    superuser = logic.get_or_create_superuser()
    assert superuser.id == "superuser"
    assert superuser.label == "Superuser"
    assert superuser.addr == "superuser@example.com"
    assert superuser.active is True


def test_login_required(app, client):
    @app.route("/protected")
    @login_required
    def protected():
        return "protected"

    with app.test_request_context():
        g.user = None
        response = client.get("/protected")
        assert response.status_code == 401


def test_admin_only(app, client):
    @app.route("/admin")
    @admin_only
    def admin():
        return "admin only"

    with app.test_request_context():
        g.user = None
        response = client.get("/admin")
        assert response.status_code == 401


def test_require_jwt_uses_existing_user(app, client):
    @app.route("/jwt-protected")
    @require_jwt
    def jwt_protected():
        return "ok"

    with app.test_request_context():
        g.user = SessionUser(username="test", email="test@example.com")
        response = client.get("/jwt-protected")
        assert response.status_code == 200


def test_require_permission_admin_allows(app, client, monkeypatch):
    @app.route("/admin-required")
    @require_permission("admin")
    def admin_required():
        return "ok"

    monkeypatch.setattr(logic, "is_admin", lambda u: True)
    monkeypatch.setattr(
        authorization, "get_user_by_email", lambda email: type("U", (), {"id": "u1", "email": email, "active": True})
    )

    with app.test_request_context():
        g.user = SessionUser(username="test", email="test@example.com")
        response = client.get("/admin-required")
        assert response.status_code == 200


def test_require_permission_admin_blocks(app, client, monkeypatch):
    @app.route("/admin-blocked")
    @require_permission("admin")
    def admin_blocked():
        return "ok"

    monkeypatch.setattr(logic, "is_admin", lambda u: False)
    monkeypatch.setattr(
        authorization, "get_user_by_email", lambda email: type("U", (), {"id": "u1", "email": email, "active": True})
    )

    with app.test_request_context():
        g.user = SessionUser(username="test", email="test@example.com")
        response = client.get("/admin-blocked")
        assert response.status_code == 403
