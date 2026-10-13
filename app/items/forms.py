"""Forms for reporting and editing lost and found items."""
from datetime import date
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, DateField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, ValidationError

CATEGORY_CHOICES = [
    ("Electronics", "Electronics & Gadgets"),
    ("IDs & Cards", "IDs, Wallets & Cards"),
    ("Keys & Lanyards", "Keys & Lanyards"),
    ("Bags & Backpacks", "Bags, Backpacks & Purses"),
    ("Books & Stationery", "Books, Notebooks & Stationery"),
    ("Clothing & Gear", "Clothing & Personal Gear"),
    ("Bottles & Containers", "Water Bottles & Containers"),
    ("Other", "Other Miscellaneous"),
]

STATUS_CHOICES = [
    ("open", "Open / Active Listing"),
    ("recovered", "Recovered / Resolved"),
    ("closed", "Closed / Cancelled"),
]


class ItemReportForm(FlaskForm):
    """Form for reporting a lost or found item."""

    title = StringField(
        "Item Title",
        validators=[
            DataRequired(message="Please provide a descriptive title for the item."),
            Length(min=3, max=150, message="Title must be between 3 and 150 characters."),
        ],
    )
    description = TextAreaField(
        "Detailed Description",
        validators=[
            DataRequired(message="Please describe the item (markings, brand, contents, condition)."),
            Length(min=5, max=2000, message="Description must be between 5 and 2000 characters."),
        ],
    )
    category = SelectField(
        "Category",
        choices=CATEGORY_CHOICES,
        validators=[DataRequired(message="Please select a category.")],
    )
    color = StringField(
        "Color / Distinctive Marks (Optional)",
        validators=[
            Optional(),
            Length(max=50, message="Color description must not exceed 50 characters."),
        ],
    )
    location = StringField(
        "Campus Location",
        validators=[
            DataRequired(message="Please specify the campus location (e.g. Science Library 2nd Floor)."),
            Length(min=2, max=150, message="Location must be between 2 and 150 characters."),
        ],
    )
    incident_date = DateField(
        "Date Lost / Found",
        validators=[DataRequired(message="Please specify the date of the incident.")],
        default=date.today,
    )
    image = FileField(
        "Photograph (Optional)",
        validators=[
            Optional(),
            FileAllowed(["jpg", "jpeg", "png", "webp", "gif"], "Only image files (JPG, PNG, WEBP, GIF) are allowed."),
        ],
    )
    submit = SubmitField("Submit Report")

    def validate_incident_date(self, field):
        """Ensure the incident date is not set in the future."""
        if field.data and field.data > date.today():
            raise ValidationError("Incident date cannot be in the future.")


class ItemEditForm(ItemReportForm):
    """Form for report owners to update an existing item."""

    status = SelectField(
        "Listing Status",
        choices=STATUS_CHOICES,
        validators=[DataRequired(message="Please select a valid status.")],
    )
    remove_image = BooleanField("Remove current photograph")
    submit = SubmitField("Save Changes")
