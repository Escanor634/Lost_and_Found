"""Tests for Stage 4: Frontend UI, Navigation States, and Template Rendering."""
import pytest
from app.extensions import db
from app.models.user import User


@pytest.fixture
def auth_user(app):
    """Fixture providing an active student user for UI testing."""
    user = User(
        name="Peter Parker",
        email="peter@campus.edu",
        role="student",
        status="active",
    )
    user.set_password("SpiderPass2026")
    db.session.add(user)
    db.session.commit()
    return user


# ============================================================================
# NAVIGATION & GUEST / AUTHENTICATED STATE TESTS
# ============================================================================

def test_guest_navigation_state(client):
    """Test navbar elements displayed for an unauthenticated visitor."""
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    # Guest should see Login and Register
    assert "Log In" in html
    assert "Register" in html
    assert "Report Item" in html

    # Guest should NOT see private navigation in navbar
    assert "Log Out" not in html
    # Check that private nav items are not in the main navbar links
    assert '<a class="nav-link" href="/auth/dashboard">' not in html
    assert '<a class="nav-link" href="/auth/profile">' not in html


def test_authenticated_navigation_state(client, auth_user):
    """Test navbar elements displayed for an authenticated student."""
    client.post(
        "/auth/login",
        data={"email": auth_user.email, "password": "SpiderPass2026"},
    )
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    # Authenticated user should see user name and private links
    assert auth_user.name in html
    assert "Dashboard" in html
    assert "Profile" in html
    assert "Log Out" in html

    # Authenticated user should NOT see guest auth links in navbar
    assert '<a href="/auth/login"' not in html
    assert '<a href="/auth/register"' not in html


# ============================================================================
# HOMEPAGE UI TESTS
# ============================================================================

def test_homepage_search_preview_and_categories(client):
    """Test homepage includes search bar preview and category chips."""
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    # Search bar preview
    assert "search-preview-box" in html
    assert "Catalog Coming in Stage 6" in html
    assert 'placeholder="Search catalog by keyword' in html

    # Category chips
    assert "Electronics" in html
    assert "IDs &amp; Cards" in html or "IDs & Cards" in html
    assert "Keys &amp; Lanyards" in html or "Keys & Lanyards" in html
    assert "Bags &amp; Wallets" in html or "Bags & Wallets" in html
    assert "Books &amp; Notes" in html or "Books & Notes" in html


def test_homepage_report_actions_active(client):
    """Test that prominent report cards provide active links to reporting pages."""
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "Report a Lost Item" in html
    assert "Report a Found Item" in html
    # Active links to reporting routes
    assert 'href="/items/report/lost"' in html
    assert 'href="/items/report/found"' in html


def test_homepage_how_it_works_steps(client):
    """Test How It Works 3-step section."""
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "1. Report an Item" in html
    assert "2. Claim &amp; Verify" in html or "2. Claim & Verify" in html
    assert "3. Reconnect" in html


def test_shared_layout_accessibility_and_assets(client):
    """Test base layout contains accessibility skip link and static asset links."""
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    # Skip link
    assert 'class="skip-link"' in html
    assert 'href="#main-content"' in html
    assert 'id="main-content"' in html

    # Static CSS and JS assets
    assert "/static/css/style.css" in html
    assert "/static/js/main.js" in html


# ============================================================================
# AUTHENTICATION PAGES UI TESTS
# ============================================================================

def test_login_page_ui(client):
    """Test polished login page layout, input groups, and action buttons."""
    response = client.get("/auth/login")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "Sign In" in html
    assert "Campus Email" in html
    assert "Password" in html
    assert 'method="POST"' in html
    assert "Create an account" in html
    assert "auth-card" in html


def test_registration_page_ui(client):
    """Test polished registration page layout, notices, and form elements."""
    response = client.get("/auth/register")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "Create Account" in html
    assert "Full Name" in html
    assert "Campus Email" in html
    assert "Password" in html
    assert "Confirm Password" in html
    assert 'method="POST"' in html
    assert "Student" in html  # Default membership notice
    assert "Sign in here" in html


def test_form_csrf_rendered_when_csrf_enabled():
    """Test form renders hidden csrf_token tag when CSRF is enabled."""
    from config import DevelopmentConfig
    from app import create_app

    csrf_app = create_app(DevelopmentConfig)
    csrf_client = csrf_app.test_client()

    login_html = csrf_client.get("/auth/login").get_data(as_text=True)
    assert 'name="csrf_token"' in login_html

    reg_html = csrf_client.get("/auth/register").get_data(as_text=True)
    assert 'name="csrf_token"' in reg_html


# ============================================================================
# DASHBOARD & PROFILE UI TESTS
# ============================================================================

def test_dashboard_ui_elements(client, auth_user):
    """Test student dashboard personalized greeting, widgets, and honest placeholders."""
    client.post(
        "/auth/login",
        data={"email": auth_user.email, "password": "SpiderPass2026"},
    )
    response = client.get("/auth/dashboard")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    # Personalized greeting
    assert f"Welcome, {auth_user.name}!" in html
    assert "Student Portal" in html
    assert "breadcrumb" in html

    # Honest status overview cards (zeros, no fake numbers)
    assert "0 Listed" in html
    assert "0 Reported" in html
    assert "0 Active" in html

    # Clearly marked placeholders
    assert "My Item Reports" in html
    assert "Awaiting Stage 5 Activation" in html
    assert "My Active Ownership Claims" in html
    assert "Recent Alerts &amp; Notifications" in html or "Recent Alerts & Notifications" in html

    # Useful links
    assert "My Profile" in html


def test_profile_ui_elements(client, auth_user):
    """Test profile page layout, breadcrumbs, security notice, and navigation."""
    client.post(
        "/auth/login",
        data={"email": auth_user.email, "password": "SpiderPass2026"},
    )
    response = client.get("/auth/profile")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    # Breadcrumb
    assert "breadcrumb" in html
    assert "Account Profile" in html

    # User details
    assert auth_user.name in html
    assert auth_user.email in html
    assert auth_user.role in html
    assert auth_user.status in html

    # Security statement
    assert "Password securely encrypted" in html
    assert auth_user.password_hash not in html

    # Navigation buttons
    assert "Back to Dashboard" in html
    assert "Log Out" in html
