"""Notification model for user updates on claims and items."""
from datetime import datetime, timezone

from app.extensions import db


class Notification(db.Model):
    """Notification entity sent to users."""

    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), nullable=False, index=True)
    item_id = db.Column(
        db.Integer,
        db.ForeignKey("items.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    claim_id = db.Column(
        db.Integer,
        db.ForeignKey("claims.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    is_read = db.Column(db.Boolean, nullable=False, default=False, index=True)
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user = db.relationship("User", back_populates="notifications")
    item = db.relationship("Item", back_populates="notifications")
    claim = db.relationship("Claim", back_populates="notifications")

    def __init__(self, **kwargs):
        if "related_item_id" in kwargs:
            kwargs["item_id"] = kwargs.pop("related_item_id")
        if "related_claim_id" in kwargs:
            kwargs["claim_id"] = kwargs.pop("related_claim_id")
        super().__init__(**kwargs)

    @property
    def related_item_id(self):
        """Alias for item_id."""
        return self.item_id

    @related_item_id.setter
    def related_item_id(self, value):
        self.item_id = value

    @property
    def related_claim_id(self):
        """Alias for claim_id."""
        return self.claim_id

    @related_claim_id.setter
    def related_claim_id(self, value):
        self.claim_id = value

    def mark_as_read(self):
        """Mark notification as read."""
        self.is_read = True

    def __repr__(self):
        return f"<Notification id={self.id} user_id={self.user_id} type='{self.notification_type}' read={self.is_read}>"
