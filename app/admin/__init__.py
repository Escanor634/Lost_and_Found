"""Admin blueprint package.

Administrative and moderation routes will be implemented in subsequent stages.
"""
from flask import Blueprint

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
