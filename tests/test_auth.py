"""Automated tests for Stage 3: User Authentication and Roles."""
import pytest
from flask import url_for
from werkzeug.security import check_password_hash

from app.extensions import db
from app.models.user import User
from app.auth.decorators import admin_required, role_required


@pytest.fixture
def registered_student(app):
    """Fixture providing a registered student user."""
    user = User(
        name="Diana Prince",
        email="diana@campus.edu",
        role="student",
        status="active",
    )
    user.set_password("StudentPassword123")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def suspended_user(app):
    """Fixture providing a suspended user."""
    user = User(
        name="Suspended Sam",
        email="sam@campus.edu",
        role="student",
        status="suspended",
    )
    user.set_password("SuspendedPassword123")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def admin_account(app):
    """Fixture providing an administrator user."""
    user = User(
        name="Arthur Admin",
        email="arthur@campus.edu",
        role="admin",
        status="active",
    )
    user.set_password("AdminPassword123")
    db.session.add(user)
    db.session.commit()
    return user


# ============================================================================
# REGISTRATION TESTS
# ============================================================================

def test_registration_page_renders(client):
    """Test registration page renders with HTTP 200 and required fields."""
    response = client.get("/auth/register")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Create Account" in html
    assert "Full Name" in html
    assert "Campus Email" in html
    assert "Password" in html
    assert "Confirm Password" in html


def test_registration_successful(client, app):
    """Test successful user registration creates student in DB with hashed password."""
    response = client.post(
        "/auth/register",
        data={
            "name": "Bruce Wayne",
            "email": "bruce@campus.edu",
            "password": "SecurePassword123",
            "password_confirm": "SecurePassword123",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Your account has been created successfully" in html

    # Verify user in database
    with app.app_context():
        user = db.session.execute(
            db.select(User).filter_by(email="bruce@campus.edu")
        ).scalar_one_or_none()
        assert user is not None
        assert user.name == "Bruce Wayne"
        assert user.role == "student"
        assert user.status == "active"
        # Ensure password is not stored plaintext
        assert user.password_hash != "SecurePassword123"
        assert user.check_password("SecurePassword123") is True


def test_registration_normalizes_email(client, app):
    """Test registration normalizes email to lowercase and strips whitespace."""
    response = client.post(
        "/auth/register",
        data={
            "name": "Clark Kent",
            "email": "  CLARK.KENT@Campus.Edu  ",
            "password": "SecurePassword123",
            "password_confirm": "SecurePassword123",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    with app.app_context():
        user = db.session.execute(
            db.select(User).filter_by(email="clark.kent@campus.edu")
        ).scalar_one_or_none()
        assert user is not None
        assert user.email == "clark.kent@campus.edu"


def test_registration_duplicate_email_rejected(client, registered_student):
    """Test that registering an existing email is rejected with helpful message."""
    response = client.post(
        "/auth/register",
        data={
            "name": "Diana Impostor",
            "email": registered_student.email.upper(),  # case-insensitive check
            "password": "AnotherPassword123",
            "password_confirm": "AnotherPassword123",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "An account with this email address already exists" in html


def test_registration_password_mismatch(client):
    """Test that password mismatch fails validation."""
    response = client.post(
        "/auth/register",
        data={
            "name": "Barry Allen",
            "email": "barry@campus.edu",
            "password": "PasswordOne123",
            "password_confirm": "PasswordTwo456",
        },
    )
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Passwords must match" in html


def test_registration_password_too_short(client):
    """Test that passwords shorter than 8 characters are rejected."""
    response = client.post(
        "/auth/register",
        data={
            "name": "Barry Allen",
            "email": "barry@campus.edu",
            "password": "short",
            "password_confirm": "short",
        },
    )
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Password must be at least 8 characters long" in html


def test_registration_cannot_self_assign_admin(client, app):
    """Test that clients cannot grant themselves admin privileges via registration form."""
    response = client.post(
        "/auth/register",
        data={
            "name": "Sneaky Admin",
            "email": "sneaky@campus.edu",
            "password": "Password12345",
            "password_confirm": "Password12345",
            "role": "admin",  # Tampered field
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    with app.app_context():
        user = db.session.execute(
            db.select(User).filter_by(email="sneaky@campus.edu")
        ).scalar_one_or_none()
        assert user is not None
        assert user.role == "student"  # Server strictly enforced student


def test_registration_authenticated_user_redirected(client, registered_student):
    """Test that an already authenticated user visiting /auth/register is redirected."""
    client.post(
        "/auth/login",
        data={"email": registered_student.email, "password": "StudentPassword123"},
    )
    response = client.get("/auth/register")
    assert response.status_code == 302
    assert "/auth/dashboard" in response.headers["Location"]


# ============================================================================
# LOGIN AND LOGOUT TESTS
# ============================================================================

def test_login_page_renders(client):
    """Test login page renders with HTTP 200 and expected fields."""
    response = client.get("/auth/login")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Sign In" in html
    assert "Campus Email" in html
    assert "Password" in html


def test_login_successful(client, registered_student):
    """Test valid credentials successfully establish user session."""
    response = client.post(
        "/auth/login",
        data={
            "email": registered_student.email,
            "password": "StudentPassword123",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert f"Welcome back, {registered_student.name}!" in html
    assert "Log Out" in html


def test_login_invalid_password(client, registered_student):
    """Test incorrect password rejects login without leaking specifics."""
    response = client.post(
        "/auth/login",
        data={
            "email": registered_student.email,
            "password": "WrongPassword999",
        },
    )
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Invalid email or password." in html


def test_login_nonexistent_email(client):
    """Test nonexistent email rejects login with identical generic message."""
    response = client.post(
        "/auth/login",
        data={
            "email": "ghost@campus.edu",
            "password": "SomePassword123",
        },
    )
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Invalid email or password." in html


def test_login_suspended_user_rejected(client, suspended_user):
    """Test that suspended accounts cannot log in."""
    response = client.post(
        "/auth/login",
        data={
            "email": suspended_user.email,
            "password": "SuspendedPassword123",
        },
    )
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Your account has been suspended" in html


def test_login_safe_redirect(client, registered_student):
    """Test that safe internal next URLs are followed, but external open redirects are blocked."""
    # Safe redirect
    resp_safe = client.post(
        "/auth/login?next=/auth/profile",
        data={
            "email": registered_student.email,
            "password": "StudentPassword123",
        },
    )
    assert resp_safe.status_code == 302
    assert resp_safe.headers["Location"] == "/auth/profile"

    # Unsafe external redirect attempt
    client.get("/auth/logout")  # Reset session
    resp_unsafe = client.post(
        "/auth/login?next=https://evil-phishing.com/steal-creds",
        data={
            "email": registered_student.email,
            "password": "StudentPassword123",
        },
    )
    assert resp_unsafe.status_code == 302
    # Should safely fallback to dashboard instead of external site
    assert "/auth/dashboard" in resp_unsafe.headers["Location"]


def test_logout_clears_session(client, registered_student):
    """Test logout clears the session and prevents protected page access."""
    # Log in
    client.post(
        "/auth/login",
        data={
            "email": registered_student.email,
            "password": "StudentPassword123",
        },
    )
    # Log out
    response = client.get("/auth/logout", follow_redirects=True)
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "You have been successfully logged out" in html
    assert "Log In" in html

    # Subsequent access to protected dashboard should redirect to login
    dash_resp = client.get("/auth/dashboard")
    assert dash_resp.status_code == 302
    assert "/auth/login" in dash_resp.headers["Location"]


# ============================================================================
# AUTHORIZATION AND USER PAGES TESTS
# ============================================================================

def test_protected_routes_require_login(client):
    """Test that protected dashboard and profile require authentication."""
    for url in ["/auth/dashboard", "/auth/profile", "/dashboard", "/profile"]:
        resp = client.get(url)
        assert resp.status_code == 302
        assert "/auth/login" in resp.headers["Location"]


def test_dashboard_displays_user_name(client, registered_student):
    """Test student dashboard renders with authenticated user's name."""
    client.post(
        "/auth/login",
        data={
            "email": registered_student.email,
            "password": "StudentPassword123",
        },
    )
    response = client.get("/auth/dashboard")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert f"Welcome, {registered_student.name}!" in html
    assert "Student Portal" in html


def test_profile_displays_user_info_without_password_hash(client, registered_student):
    """Test profile page displays user info and never exposes password hash."""
    client.post(
        "/auth/login",
        data={
            "email": registered_student.email,
            "password": "StudentPassword123",
        },
    )
    response = client.get("/auth/profile")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert registered_student.name in html
    assert registered_student.email in html
    assert registered_student.role in html
    assert registered_student.status in html
    # Password hash must NEVER appear in HTML
    assert registered_student.password_hash not in html


def test_role_required_and_admin_required_decorators(app, client, registered_student, admin_account):
    """Test the @role_required and @admin_required decorators enforce authorization."""
    # Register temporary test routes on the app
    @app.route("/test-admin-only")
    @admin_required
    def test_admin_route():
        return "Admin Secret Area", 200

    @app.route("/test-student-only")
    @role_required("student")
    def test_student_route():
        return "Student Area", 200

    # 1. Unauthenticated request -> redirects to login
    resp_anon = client.get("/test-admin-only")
    assert resp_anon.status_code == 302
    assert "/auth/login" in resp_anon.headers["Location"]

    # 2. Student accessing admin route -> 403 Forbidden
    client.post(
        "/auth/login",
        data={"email": registered_student.email, "password": "StudentPassword123"},
    )
    resp_student_denied = client.get("/test-admin-only")
    assert resp_student_denied.status_code == 403

    # Student accessing student route -> 200 OK
    resp_student_allowed = client.get("/test-student-only")
    assert resp_student_allowed.status_code == 200

    # 3. Admin accessing admin route -> 200 OK
    client.get("/auth/logout")
    client.post(
        "/auth/login",
        data={"email": admin_account.email, "password": "AdminPassword123"},
    )
    resp_admin_allowed = client.get("/test-admin-only")
    assert resp_admin_allowed.status_code == 200
    assert "Admin Secret Area" in resp_admin_allowed.get_data(as_text=True)


def test_user_loader(app, registered_student):
    """Test Flask-Login user_loader with valid, invalid, and nonexistent IDs."""
    from app.extensions import login_manager
    user_loader = login_manager._user_callback

    with app.app_context():
        # Valid ID
        loaded = user_loader(str(registered_student.id))
        assert loaded is not None
        assert loaded.id == registered_student.id

        # Nonexistent ID
        assert user_loader("999999") is None

        # Malformed non-integer ID
        assert user_loader("not-an-id") is None


def test_user_is_active_and_password_helpers():
    """Test User is_active property and password helpers."""
    u_active = User(name="Active User", email="active@campus.edu", status="active")
    assert u_active.is_active is True
    assert u_active.is_admin() is False

    u_suspended = User(name="Suspended User", email="susp@campus.edu", status="suspended")
    assert u_suspended.is_active is False

    # Password setting and checking
    u_active.set_password("MySecretPass999")
    assert u_active.check_password("MySecretPass999") is True
    assert u_active.check_password("WrongPass") is False
    assert u_active.check_password("") is False

    # Empty password rejection
    with pytest.raises(ValueError, match="Password cannot be empty"):
        u_active.set_password("")


def test_profile_ignores_url_spoofing(client, registered_student, admin_account):
    """Test that URL query parameters cannot be used to inspect another user's profile."""
    client.post(
        "/auth/login",
        data={"email": registered_student.email, "password": "StudentPassword123"},
    )
    # Attempt to spoof profile via query params
    response = client.get(f"/auth/profile?user_id={admin_account.id}&id={admin_account.id}")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    # Must display logged-in student, NEVER the target admin
    assert registered_student.email in html
    assert admin_account.email not in html


def test_csrf_protection_enabled_for_unauthorized_post(app):
    """Test CSRF protection blocks requests when CSRF is enabled and token is missing."""
    from config import DevelopmentConfig
    from app import create_app

    # Create app with DevelopmentConfig where WTF_CSRF_ENABLED is True
    csrf_app = create_app(DevelopmentConfig)
    csrf_client = csrf_app.test_client()

    response = csrf_client.post(
        "/auth/register",
        data={
            "name": "No CSRF User",
            "email": "nocsrf@campus.edu",
            "password": "Password123",
            "password_confirm": "Password123",
        },
    )
    # Without valid CSRF token, Flask-WTF returns 400 Bad Request
    assert response.status_code == 400
    assert b"CSRF" in response.data
