"""Forms for claiming items and reviewing ownership claims."""
from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length


class ClaimForm(FlaskForm):
    """Form for submitting an ownership claim on a found item."""

    proof_description = TextAreaField(
        "Proof of Ownership & Verification Details",
        validators=[
            DataRequired(message="Please provide details to verify your ownership of this item."),
            Length(
                min=10,
                max=2000,
                message="Proof description must be between 10 and 2000 characters.",
            ),
        ],
        render_kw={
            "rows": 6,
            "placeholder": (
                "Describe details only the true owner would know:\n"
                "- Why do you believe this item belongs to you?\n"
                "- Specific distinguishing marks, scratches, serial numbers, wallpapers, or passwords\n"
                "- Exact contents or receipt details"
            ),
        },
    )
    submit = SubmitField("Submit Ownership Claim")


class ClaimActionForm(FlaskForm):
    """CSRF-protected form for approving or rejecting a claim."""

    submit = SubmitField("Submit")
