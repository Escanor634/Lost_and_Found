"""Pytest configuration and fixtures."""
import pytest
from app import create_app
from app.extensions import db
from config import TestingConfig


@pytest.fixture
def app():
    """Create and configure a Flask application instance for testing."""
    test_app = create_app(TestingConfig)

    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client fixture for HTTP requests."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Test CLI runner fixture for testing Flask commands."""
    return app.test_cli_runner()
