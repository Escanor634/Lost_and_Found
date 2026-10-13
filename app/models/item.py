"""Item model representing lost and found item reports."""
from datetime import date, datetime, timezone
from sqlalchemy import CheckConstraint
from sqlalchemy.orm import validates

from app.extensions import db


class Item(db.Model):
    """Lost and found item listing."""

    __tablename__ = "items"
    __table_args__ = (
        CheckConstraint("item_type IN ('lost', 'found')", name="check_item_type"),
        CheckConstraint(
            "status IN ('open', 'claim_pending', 'recovered', 'closed')",
            name="check_item_status",
        ),
    )

    VALID_TYPES = ("lost", "found")
    VALID_STATUSES = ("open", "claim_pending", "recovered", "closed")

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False, index=True)
    item_type = db.Column(db.String(20), nullable=False, index=True)
    color = db.Column(db.String(50), nullable=True)
    location = db.Column(db.String(150), nullable=False)
    incident_date = db.Column(db.Date, nullable=False)
    image_path = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="open", index=True)
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user = db.relationship("User", back_populates="items")
    claims = db.relationship(
        "Claim",
        back_populates="item",
        cascade="all, delete-orphan",
        lazy="select",
    )
    notifications = db.relationship(
        "Notification",
        back_populates="item",
        lazy="select",
    )

    @validates("item_type")
    def validate_item_type(self, key, value):
        if value not in self.VALID_TYPES:
            raise ValueError(
                f"Invalid item_type: {value}. Allowed types are: {', '.join(self.VALID_TYPES)}."
            )
        return value

    @validates("status")
    def validate_status(self, key, value):
        if value not in self.VALID_STATUSES:
            raise ValueError(
                f"Invalid item status: {value}. Allowed statuses are: {', '.join(self.VALID_STATUSES)}."
            )
        return value

    @validates("incident_date")
    def validate_incident_date(self, key, value):
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            # Allow ISO formatted date string
            return date.fromisoformat(value)
        raise ValueError(
            f"Invalid incident_date: {value}. Must be a date, datetime, or ISO date string."
        )

    def __repr__(self):
        return f"<Item id={self.id} title='{self.title}' type='{self.item_type}' status='{self.status}'>"
