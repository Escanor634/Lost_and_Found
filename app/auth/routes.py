"""Authentication routes for registration, login, logout, and user dashboard/profile."""
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from app.extensions import db
from app.models.user import User
from app.auth import auth_bp
from app.auth.forms import RegistrationForm, LoginForm
from app.auth.utils import is_safe_url


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Register a new student account."""
    if current_user.is_authenticated:
        return redirect(url_for("auth.dashboard"))

    form = RegistrationForm()
    if form.validate_on_submit():
        normalized_email = form.email.data.strip().lower()

        # Double-check email uniqueness
        existing_user = db.session.execute(
            db.select(User).filter_by(email=normalized_email)
        ).scalar_one_or_none()
        if existing_user:
            flash("An account with this email address already exists.", "danger")
            return render_template("auth/register.html", form=form)

        # Enforce student role on registration - clients can never self-assign roles
        user = User(
            name=form.name.data.strip(),
            email=normalized_email,
            role="student",
            status="active",
        )
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        flash("Your account has been created successfully! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Authenticate and log in an existing user."""
    if current_user.is_authenticated:
        return redirect(url_for("auth.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        normalized_email = form.email.data.strip().lower()
        user = db.session.execute(
            db.select(User).filter_by(email=normalized_email)
        ).scalar_one_or_none()

        if not user or not user.check_password(form.password.data):
            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html", form=form)

        if user.status == "suspended" or not user.is_active:
            flash(
                "Your account has been suspended. Please contact campus administration.",
                "danger",
            )
            return render_template("auth/login.html", form=form)

        login_user(user, remember=form.remember_me.data)
        flash(f"Welcome back, {user.name}!", "success")

        # Safe redirection check
        next_page = request.args.get("next")
        if not next_page or not is_safe_url(next_page):
            next_page = url_for("auth.dashboard")

        return redirect(next_page)

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    """Log out the current authenticated user."""
    logout_user()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for("index"))


@auth_bp.route("/dashboard")
@login_required
def dashboard():
    """Display student dashboard with user's name and activity overview."""
    return render_template("auth/dashboard.html", user=current_user)


@auth_bp.route("/profile")
@login_required
def profile():
    """Display current user's profile information."""
    return render_template("auth/profile.html", user=current_user)
