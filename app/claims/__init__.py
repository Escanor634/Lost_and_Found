"""Claims blueprint package.

Claims submission and verification routes will be implemented in subsequent stages.
"""
from flask import Blueprint

claims_bp = Blueprint("claims", __name__, url_prefix="/claims")

from app.claims import routes  # noqa: E402, F401
