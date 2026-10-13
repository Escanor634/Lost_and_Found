from datetime import datetime, timezone
from flask_login import UserMixin
from sqlalchemy import CheckConstraint
from sqlalchemy.orm import validates
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db


class User(db.Model, UserMixin):
    """User account entity with role and status tracking."""

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('student', 'admin')", name="check_user_role"),
        CheckConstraint("status IN ('active', 'suspended')", name="check_user_status"),
    )

    VALID_ROLES = ("student", "admin")
    VALID_STATUSES = ("active", "suspended")

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="student")
    status = db.Column(db.String(20), nullable=False, default="active")
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    items = db.relationship(
        "Item",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select",
    )
    claims = db.relationship(
        "Claim",
        back_populates="claimant",
        foreign_keys="Claim.claimant_id",
        cascade="all, delete-orphan",
        lazy="select",
    )
    reviewed_claims = db.relationship(
        "Claim",
        back_populates="reviewer",
        foreign_keys="Claim.reviewer_id",
        lazy="select",
    )
    notifications = db.relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __init__(self, **kwargs):
        if "account_status" in kwargs:
            kwargs["status"] = kwargs.pop("account_status")
        super().__init__(**kwargs)

    @property
    def account_status(self):
        """Alias for status."""
        return self.status

    @account_status.setter
    def account_status(self, value):
        self.status = value

    @validates("role")
    def validate_role(self, key, value):
        if value not in self.VALID_ROLES:
            raise ValueError(
                f"Invalid role: {value}. Allowed roles are: {', '.join(self.VALID_ROLES)}."
            )
        return value

    @validates("status")
    def validate_status(self, key, value):
        if value not in self.VALID_STATUSES:
            raise ValueError(
                f"Invalid account status: {value}. Allowed statuses are: {', '.join(self.VALID_STATUSES)}."
            )
        return value

    @validates("email")
    def validate_email(self, key, value):
        if not value or "@" not in value:
            raise ValueError(f"Invalid email address: {value}.")
        return value.strip().lower()

    @property
    def is_active(self):
        """Flask-Login active account check."""
        return self.status == "active"

    def set_password(self, password):
        """Hash and set user password."""
        if not password:
            raise ValueError("Password cannot be empty.")
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify password against stored hash."""
        if not self.password_hash or not password:
            return False
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        """Check if user has administrative privileges."""
        return self.role == "admin"

    def __repr__(self):
        return f"<User id={self.id} email='{self.email}' role='{self.role}'>"
