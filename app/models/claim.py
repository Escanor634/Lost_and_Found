"""Claim model representing ownership claims on lost/found items."""
from datetime import datetime, timezone
from sqlalchemy import CheckConstraint, Index, text
from sqlalchemy.orm import validates

from app.extensions import db


class Claim(db.Model):
    """Claim filed by a user on an item with verification proof."""

    __tablename__ = "claims"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'withdrawn')",
            name="check_claim_status",
        ),
        # Prevent a single user from having multiple active (pending/approved) claims on the same item
        Index(
            "uq_active_claim_user_item",
            "item_id",
            "claimant_id",
            unique=True,
            sqlite_where=text("status IN ('pending', 'approved')"),
        ),
        # Ensure only one claim can be approved per item
        Index(
            "uq_approved_claim_per_item",
            "item_id",
            unique=True,
            sqlite_where=text("status = 'approved'"),
        ),
    )

    VALID_STATUSES = ("pending", "approved", "rejected", "withdrawn")

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(
        db.Integer,
        db.ForeignKey("items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    claimant_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    proof_description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending", index=True)
    reviewer_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    reviewed_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    item = db.relationship("Item", back_populates="claims")
    claimant = db.relationship(
        "User",
        foreign_keys=[claimant_id],
        back_populates="claims",
    )
    reviewer = db.relationship(
        "User",
        foreign_keys=[reviewer_id],
        back_populates="reviewed_claims",
    )
    notifications = db.relationship(
        "Notification",
        back_populates="claim",
        lazy="select",
    )

    @validates("status")
    def validate_status(self, key, value):
        if value not in self.VALID_STATUSES:
            raise ValueError(
                f"Invalid claim status: {value}. Allowed statuses are: {', '.join(self.VALID_STATUSES)}."
            )
        return value

    def approve(self, reviewer_id):
        """Helper to mark claim as approved with reviewer and timestamp."""
        self.status = "approved"
        self.reviewer_id = reviewer_id
        self.reviewed_at = datetime.now(timezone.utc)

    def reject(self, reviewer_id):
        """Helper to mark claim as rejected with reviewer and timestamp."""
        self.status = "rejected"
        self.reviewer_id = reviewer_id
        self.reviewed_at = datetime.now(timezone.utc)

    def withdraw(self):
        """Helper to withdraw a claim."""
        self.status = "withdrawn"

    def __repr__(self):
        return f"<Claim id={self.id} item_id={self.item_id} claimant_id={self.claimant_id} status='{self.status}'>"
