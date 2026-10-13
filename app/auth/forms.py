"""Authentication forms using Flask-WTF and WTForms."""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError

from app.extensions import db
from app.models.user import User


class RegistrationForm(FlaskForm):
    """User registration form."""

    name = StringField(
        "Full Name",
        validators=[
            DataRequired(message="Name is required."),
            Length(min=2, max=100, message="Name must be between 2 and 100 characters."),
        ],
        filters=[lambda s: s.strip() if isinstance(s, str) else s],
    )
    email = StringField(
        "Campus Email",
        validators=[
            DataRequired(message="Email is required."),
            Email(message="Please enter a valid email address."),
            Length(max=120, message="Email must not exceed 120 characters."),
        ],
        filters=[lambda s: s.strip().lower() if isinstance(s, str) else s],
    )
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(message="Password is required."),
            Length(min=8, message="Password must be at least 8 characters long."),
        ],
    )
    password_confirm = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(message="Please confirm your password."),
            EqualTo("password", message="Passwords must match."),
        ],
    )
    submit = SubmitField("Create Account")

    def validate_email(self, field):
        """Ensure email is unique across all user accounts."""
        normalized_email = field.data.strip().lower() if field.data else ""
        existing = db.session.execute(
            db.select(User).filter_by(email=normalized_email)
        ).scalar_one_or_none()
        if existing:
            raise ValidationError("An account with this email address already exists.")


class LoginForm(FlaskForm):
    """User login form."""

    email = StringField(
        "Campus Email",
        validators=[
            DataRequired(message="Email is required."),
            Email(message="Please enter a valid email address."),
        ],
        filters=[lambda s: s.strip().lower() if isinstance(s, str) else s],
    )
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(message="Password is required."),
        ],
    )
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Log In")
