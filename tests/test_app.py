"""Unit and integration tests for application setup and architecture."""
import json
from app import create_app, init_db
from config import TestingConfig, DevelopmentConfig


def test_app_creation_testing_config(app):
    """Test that app creates successfully with TestingConfig."""
    assert app is not None
    assert app.config["TESTING"] is True
    assert app.config["SQLALCHEMY_DATABASE_URI"] == "sqlite:///:memory:"


def test_app_creation_default_config():
    """Test that app creates successfully with development / default config."""
    dev_app = create_app(DevelopmentConfig)
    assert dev_app is not None
    assert dev_app.config["DEBUG"] is True


def test_blueprints_registered(app):
    """Test that all required modular blueprints are registered."""
    expected_blueprints = {"auth", "items", "claims", "notifications", "admin"}
    registered_blueprints = set(app.blueprints.keys())
    assert expected_blueprints.issubset(registered_blueprints)


def test_health_endpoint(client):
    """Test that GET /health returns HTTP 200 with JSON payload."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.is_json
    data = response.get_json()
    assert data["status"] == "healthy"
    assert data["service"] == "campus-lost-and-found"


def test_homepage_renders_correctly(client):
    """Test that homepage renders with HTTP 200 and expected sections."""
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    # Check project title and brand
    assert "Campus Lost &amp; Found" in html or "Campus Lost & Found" in html
    # Check navigation items
    assert "Lost Items" in html
    assert "Found Items" in html
    assert "Report Item" in html
    # Check placeholder sections
    assert "Report an Item" in html
    assert "Recent Lost Items" in html
    assert "Recent Found Items" in html
    assert "How It Works" in html
    # Check Bootstrap 5 is included
    assert "bootstrap" in html.lower()


def test_init_db_cli_command(runner):
    """Test the init-db CLI command execution."""
    result = runner.invoke(args=["init-db"])
    assert result.exit_code == 0
    assert "Initialized database tables successfully." in result.output


def test_init_db_helper_function(app):
    """Test programmatic init_db helper function."""
    init_db(app)


def test_non_existent_route_404(client):
    """Test that non-existent routes return 404."""
    response = client.get("/non-existent-endpoint")
    assert response.status_code == 404


def test_app_creation_production_config(monkeypatch):
    """Test that app creates successfully with production config and custom secret key."""
    monkeypatch.setenv("SECRET_KEY", "custom-render-production-secret-123456789")
    prod_app = create_app("production")
    assert prod_app is not None
    assert prod_app.config["DEBUG"] is False
    assert prod_app.config["SECRET_KEY"] == "custom-render-production-secret-123456789"


def test_render_environment_auto_detection(monkeypatch):
    """Test that setting RENDER environment variable defaults to production config."""
    monkeypatch.delenv("FLASK_CONFIG", raising=False)
    monkeypatch.delenv("FLASK_ENV", raising=False)
    monkeypatch.setenv("RENDER", "true")
    render_app = create_app()
    assert render_app is not None
    assert render_app.config["DEBUG"] is False


def test_fresh_production_health_and_homepage(monkeypatch):
    """Test health endpoint and homepage work properly under production configuration."""
    monkeypatch.setenv("SECRET_KEY", "verification-prod-secret-987654321")
    prod_app = create_app("production")
    test_client = prod_app.test_client()

    health_res = test_client.get("/health")
    assert health_res.status_code == 200
    assert health_res.get_json()["status"] == "healthy"

    home_res = test_client.get("/")
    assert home_res.status_code == 200
    assert "Campus Lost &amp; Found" in home_res.get_data(as_text=True) or "Campus Lost & Found" in home_res.get_data(as_text=True)

