"""Role-based authorization decorators."""
from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user


def role_required(*allowed_roles):
    """Enforce server-side role check on protected routes.

    Args:
        *allowed_roles: One or more role names permitted to access the route.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for("auth.login"))
            if current_user.role not in allowed_roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """Decorator requiring admin privileges."""
    return role_required("admin")(f)
