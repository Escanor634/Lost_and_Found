"""Items management blueprint package."""
from flask import Blueprint

items_bp = Blueprint("items", __name__, url_prefix="/items")

from app.items import routes  # noqa: E402, F401
