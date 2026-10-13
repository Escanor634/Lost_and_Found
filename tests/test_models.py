"""Tests for database models, relationships, and constraints."""
from datetime import date, datetime, timezone
import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import User, Item, Claim, Notification


@pytest.fixture
def student_user(app):
    """Fixture providing a committed student user."""
    user = User(
        name="Alice Student",
        email="alice@campus.edu",
        password_hash="hashed_pw_alice",
        role="student",
        status="active",
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def admin_user(app):
    """Fixture providing a committed admin user."""
    user = User(
        name="Bob Admin",
        email="bob@campus.edu",
        password_hash="hashed_pw_bob",
        role="admin",
        status="active",
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def sample_item(app, student_user):
    """Fixture providing a committed item."""
    item = Item(
        user_id=student_user.id,
        title="Blue Backpack",
        description="Blue Jansport backpack with notebook inside",
        category="Bags",
        item_type="lost",
        color="Blue",
        location="Library 2nd Floor",
        incident_date=date(2026, 10, 10),
        status="open",
    )
    db.session.add(item)
    db.session.commit()
    return item


# ============================================================================
# USER MODEL TESTS
# ============================================================================

def test_create_user_successful(app, student_user):
    """Test successful user creation and attribute persistence."""
    fetched = db.session.get(User, student_user.id)
    assert fetched is not None
    assert fetched.name == "Alice Student"
    assert fetched.email == "alice@campus.edu"
    assert fetched.role == "student"
    assert fetched.status == "active"
    assert fetched.account_status == "active"
    assert isinstance(fetched.created_at, datetime)


def test_user_defaults(app):
    """Test default values for role, status, and created_at."""
    user = User(
        name="Charlie Test",
        email="charlie@campus.edu",
        password_hash="hashed_pw_charlie",
    )
    db.session.add(user)
    db.session.commit()

    assert user.role == "student"
    assert user.status == "active"
    assert user.created_at is not None


def test_user_email_uniqueness(app, student_user):
    """Test that email uniqueness is strictly enforced."""
    duplicate_user = User(
        name="Duplicate Alice",
        email="alice@campus.edu",
        password_hash="another_hash",
    )
    db.session.add(duplicate_user)
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_user_required_fields(app):
    """Test that missing required fields trigger IntegrityError."""
    # Missing email
    user_no_email = User(name="No Email", password_hash="hash")
    db.session.add(user_no_email)
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()

    # Missing password_hash
    user_no_pw = User(name="No PW", email="nopw@campus.edu")
    db.session.add(user_no_pw)
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_user_valid_roles_and_statuses(app):
    """Test allowed role and status permutations."""
    u1 = User(
        name="Admin User",
        email="admin_role@campus.edu",
        password_hash="hash",
        role="admin",
        status="active",
    )
    u2 = User(
        name="Suspended User",
        email="suspended@campus.edu",
        password_hash="hash",
        role="student",
        account_status="suspended",
    )
    db.session.add_all([u1, u2])
    db.session.commit()
    assert u1.role == "admin"
    assert u2.status == "suspended"


def test_user_invalid_role_rejected():
    """Test that invalid role values are rejected at validation time."""
    with pytest.raises(ValueError, match="Invalid role"):
        User(
            name="Invalid Role",
            email="badrole@campus.edu",
            password_hash="hash",
            role="super_moderator",
        )


def test_user_invalid_status_rejected():
    """Test that invalid account statuses are rejected at validation time."""
    with pytest.raises(ValueError, match="Invalid account status"):
        User(
            name="Invalid Status",
            email="badstatus@campus.edu",
            password_hash="hash",
            status="banned",
        )


def test_user_invalid_email_rejected():
    """Test that malformed email addresses are rejected at validation time."""
    with pytest.raises(ValueError, match="Invalid email"):
        User(
            name="Invalid Email",
            email="not-an-email",
            password_hash="hash",
        )


# ============================================================================
# ITEM MODEL TESTS
# ============================================================================

def test_create_item_successful(app, sample_item):
    """Test successful creation and persistence of Item."""
    fetched = db.session.get(Item, sample_item.id)
    assert fetched is not None
    assert fetched.title == "Blue Backpack"
    assert fetched.category == "Bags"
    assert fetched.item_type == "lost"
    assert fetched.color == "Blue"
    assert fetched.status == "open"
    assert fetched.incident_date == date(2026, 10, 10)
    assert isinstance(fetched.created_at, datetime)
    assert isinstance(fetched.updated_at, datetime)


def test_item_defaults_and_optionals(app, student_user):
    """Test item defaults and optional fields."""
    minimal_item = Item(
        user_id=student_user.id,
        title="Found Keycard",
        description="Blue lanyard with NFC access card",
        category="Cards",
        item_type="found",
        location="Dining Hall",
        incident_date="2026-10-11",
    )
    db.session.add(minimal_item)
    db.session.commit()

    assert minimal_item.status == "open"
    assert minimal_item.color is None
    assert minimal_item.image_path is None
    assert minimal_item.incident_date == date(2026, 10, 11)


def test_item_required_fields(app, student_user):
    """Test that omitting required fields on Item raises IntegrityError."""
    # Missing title
    item_no_title = Item(
        user_id=student_user.id,
        description="Desc",
        category="Tech",
        item_type="lost",
        location="Lab",
        incident_date=date(2026, 10, 1),
    )
    db.session.add(item_no_title)
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_item_valid_types_and_statuses(app, student_user):
    """Test valid types ('lost', 'found') and statuses."""
    item_found = Item(
        user_id=student_user.id,
        title="Found Umbrella",
        description="Black umbrella",
        category="Personal",
        item_type="found",
        location="Gym",
        incident_date=date(2026, 10, 5),
        status="claim_pending",
    )
    db.session.add(item_found)
    db.session.commit()
    assert item_found.item_type == "found"
    assert item_found.status == "claim_pending"


def test_item_invalid_type_rejected(student_user):
    """Test that invalid item_type raises ValueError."""
    with pytest.raises(ValueError, match="Invalid item_type"):
        Item(
            user_id=student_user.id,
            title="Invalid",
            description="Desc",
            category="Misc",
            item_type="stolen",
            location="Campus",
            incident_date=date(2026, 10, 1),
        )


def test_item_invalid_status_rejected(student_user):
    """Test that invalid item status raises ValueError."""
    with pytest.raises(ValueError, match="Invalid item status"):
        Item(
            user_id=student_user.id,
            title="Invalid",
            description="Desc",
            category="Misc",
            item_type="lost",
            location="Campus",
            incident_date=date(2026, 10, 1),
            status="archived",
        )


def test_item_incident_date_validation(student_user):
    """Test that incident_date accepts date, datetime, or ISO string, but rejects invalid types."""
    # datetime input converted to date
    i1 = Item(
        user_id=student_user.id,
        title="Item 1",
        description="Desc",
        category="Misc",
        item_type="lost",
        location="Campus",
        incident_date=datetime(2026, 9, 15, 14, 30),
    )
    assert i1.incident_date == date(2026, 9, 15)

    # Invalid input
    with pytest.raises(ValueError, match="Invalid incident_date"):
        Item(
            user_id=student_user.id,
            title="Item 2",
            description="Desc",
            category="Misc",
            item_type="lost",
            location="Campus",
            incident_date=12345,
        )


def test_item_user_relationship(app, student_user, sample_item):
    """Test bidirectional relationship between User and Item."""
    assert sample_item.user == student_user
    assert sample_item in student_user.items


def test_item_invalid_foreign_key(app):
    """Test that referencing a non-existent user_id raises IntegrityError."""
    orphan_item = Item(
        user_id=99999,
        title="Ghost Item",
        description="Desc",
        category="Misc",
        item_type="lost",
        location="Nowhere",
        incident_date=date(2026, 10, 1),
    )
    db.session.add(orphan_item)
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_cascade_delete_user_removes_items(app, student_user, sample_item):
    """Test that deleting a user cascades to remove their reported items."""
    item_id = sample_item.id
    db.session.delete(student_user)
    db.session.commit()

    assert db.session.get(Item, item_id) is None


# ============================================================================
# CLAIM MODEL TESTS
# ============================================================================

def test_create_claim_successful(app, sample_item):
    """Test creating a claim on an item."""
    claimant = User(
        name="Dave Claimant",
        email="dave@campus.edu",
        password_hash="hash_dave",
    )
    db.session.add(claimant)
    db.session.commit()

    claim = Claim(
        item_id=sample_item.id,
        claimant_id=claimant.id,
        proof_description="I have the receipt and matching serial number #12345.",
    )
    db.session.add(claim)
    db.session.commit()

    assert claim.id is not None
    assert claim.status == "pending"
    assert claim.reviewer_id is None
    assert claim.reviewed_at is None
    assert claim.item == sample_item
    assert claim.claimant == claimant
    assert claim in sample_item.claims
    assert claim in claimant.claims


def test_claim_invalid_status_rejected(sample_item, student_user):
    """Test that invalid claim status raises ValueError."""
    with pytest.raises(ValueError, match="Invalid claim status"):
        Claim(
            item_id=sample_item.id,
            claimant_id=student_user.id,
            proof_description="Proof",
            status="under_review",
        )


def test_claim_review_lifecycle(app, sample_item, admin_user):
    """Test claim approval and rejection workflow methods."""
    claimant = User(
        name="Eve Claimant",
        email="eve@campus.edu",
        password_hash="hash_eve",
    )
    db.session.add(claimant)
    db.session.commit()

    claim = Claim(
        item_id=sample_item.id,
        claimant_id=claimant.id,
        proof_description="Proof description",
    )
    db.session.add(claim)
    db.session.commit()

    # Approve
    claim.approve(reviewer_id=admin_user.id)
    db.session.commit()
    assert claim.status == "approved"
    assert claim.reviewer == admin_user
    assert isinstance(claim.reviewed_at, datetime)

    # Reject
    claim.reject(reviewer_id=admin_user.id)
    db.session.commit()
    assert claim.status == "rejected"

    # Withdraw
    claim.withdraw()
    db.session.commit()
    assert claim.status == "withdrawn"


def test_prevent_duplicate_active_claims_per_user(app, sample_item):
    """Test that a claimant cannot submit multiple active claims on the same item."""
    claimant = User(
        name="Frank Claimant",
        email="frank@campus.edu",
        password_hash="hash_frank",
    )
    db.session.add(claimant)
    db.session.commit()

    claim1 = Claim(
        item_id=sample_item.id,
        claimant_id=claimant.id,
        proof_description="First claim proof",
        status="pending",
    )
    db.session.add(claim1)
    db.session.commit()

    # Attempt second active claim for same user & item
    claim2 = Claim(
        item_id=sample_item.id,
        claimant_id=claimant.id,
        proof_description="Second duplicate claim proof",
        status="pending",
    )
    db.session.add(claim2)
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_allow_new_claim_after_rejection(app, sample_item):
    """Test that a user can submit a new claim if their previous claim was rejected."""
    claimant = User(
        name="Grace Claimant",
        email="grace@campus.edu",
        password_hash="hash_grace",
    )
    db.session.add(claimant)
    db.session.commit()

    old_claim = Claim(
        item_id=sample_item.id,
        claimant_id=claimant.id,
        proof_description="First insufficient proof",
        status="rejected",
    )
    db.session.add(old_claim)
    db.session.commit()

    # Now submit a new pending claim with updated proof
    new_claim = Claim(
        item_id=sample_item.id,
        claimant_id=claimant.id,
        proof_description="New comprehensive proof with receipt",
        status="pending",
    )
    db.session.add(new_claim)
    db.session.commit()
    assert new_claim.id is not None
    assert new_claim.status == "pending"


def test_prevent_multiple_approved_claims_per_item(app, sample_item, admin_user):
    """Test that an item cannot have multiple approved claims simultaneously."""
    u1 = User(name="User 1", email="u1@campus.edu", password_hash="h1")
    u2 = User(name="User 2", email="u2@campus.edu", password_hash="h2")
    db.session.add_all([u1, u2])
    db.session.commit()

    claim1 = Claim(
        item_id=sample_item.id,
        claimant_id=u1.id,
        proof_description="Proof 1",
        status="approved",
        reviewer_id=admin_user.id,
    )
    db.session.add(claim1)
    db.session.commit()

    claim2 = Claim(
        item_id=sample_item.id,
        claimant_id=u2.id,
        proof_description="Proof 2",
        status="approved",
        reviewer_id=admin_user.id,
    )
    db.session.add(claim2)
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_claim_invalid_foreign_keys(app, student_user):
    """Test that invalid item_id or claimant_id raises IntegrityError."""
    # Invalid item_id
    bad_item_claim = Claim(
        item_id=99999,
        claimant_id=student_user.id,
        proof_description="Proof",
    )
    db.session.add(bad_item_claim)
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


# ============================================================================
# NOTIFICATION MODEL TESTS
# ============================================================================

def test_create_notification_successful(app, student_user, sample_item):
    """Test notification creation and alias properties."""
    notification = Notification(
        user_id=student_user.id,
        message="A potential match for your lost item was reported.",
        notification_type="match_found",
        related_item_id=sample_item.id,
    )
    db.session.add(notification)
    db.session.commit()

    assert notification.id is not None
    assert notification.is_read is False
    assert notification.item_id == sample_item.id
    assert notification.related_item_id == sample_item.id
    assert notification.user == student_user
    assert notification.item == sample_item
    assert notification in student_user.notifications


def test_notification_claim_association(app, sample_item, admin_user):
    """Test notification associated with a claim."""
    claimant = User(name="Heidi", email="heidi@campus.edu", password_hash="hash")
    db.session.add(claimant)
    db.session.commit()

    claim = Claim(
        item_id=sample_item.id,
        claimant_id=claimant.id,
        proof_description="Proof",
    )
    db.session.add(claim)
    db.session.commit()

    notification = Notification(
        user_id=claimant.id,
        message="Your claim has been approved by campus admin.",
        notification_type="claim_approved",
        related_claim_id=claim.id,
    )
    db.session.add(notification)
    db.session.commit()

    assert notification.claim == claim
    assert notification.related_claim_id == claim.id


def test_notification_mark_as_read(app, student_user):
    """Test mark_as_read helper method."""
    notification = Notification(
        user_id=student_user.id,
        message="Test alert",
        notification_type="system",
    )
    db.session.add(notification)
    db.session.commit()

    assert notification.is_read is False
    notification.mark_as_read()
    db.session.commit()
    assert notification.is_read is True


def test_notification_invalid_user_fk(app):
    """Test that notification without a valid recipient user fails IntegrityError."""
    orphan_notification = Notification(
        user_id=99999,
        message="Nowhere",
        notification_type="system",
    )
    db.session.add(orphan_notification)
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()
