"""Notifications blueprint package.

Notification handling and alert routes will be implemented in subsequent stages.
"""
from flask import Blueprint

notifications_bp = Blueprint("notifications", __name__, url_prefix="/notifications")
