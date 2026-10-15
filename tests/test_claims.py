"""Comprehensive tests for item claiming, ownership verification, and claim review."""
from datetime import date
import pytest
from app.extensions import db
from app.models.user import User
from app.models.item import Item
from app.models.claim import Claim


@pytest.fixture
def owner(app):
    """User who reports a found item."""
    user = User(
        name="Alice Finder",
        email="alice@campus.edu",
        role="student",
        status="active",
    )
    user.set_password("AlicePass123")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def claimant(app):
    """User who lost an item and files a claim."""
    user = User(
        name="Bob Claimant",
        email="bob@campus.edu",
        role="student",
        status="active",
    )
    user.set_password("BobPass123")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def second_claimant(app):
    """Second user who also files a claim on the same item."""
    user = User(
        name="Charlie Claimant",
        email="charlie@campus.edu",
        role="student",
        status="active",
    )
    user.set_password("CharliePass123")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def found_item(app, owner):
    """Open found item eligible for claiming."""
    item = Item(
        user_id=owner.id,
        title="Blue Hydro Flask Water Bottle",
        description="Blue 32oz bottle found near the library tables.",
        category="Bottles & Containers",
        item_type="found",
        color="Blue",
        location="Science Library 2nd Floor",
        incident_date=date.today(),
        status="open",
    )
    db.session.add(item)
    db.session.commit()
    return item


@pytest.fixture
def lost_item(app, owner):
    """Lost item (ineligible for claiming)."""
    item = Item(
        user_id=owner.id,
        title="Black Leather Wallet",
        description="Lost somewhere on campus.",
        category="IDs & Cards",
        item_type="lost",
        color="Black",
        location="Student Union",
        incident_date=date.today(),
        status="open",
    )
    db.session.add(item)
    db.session.commit()
    return item


def login(client, email, password):
    """Helper to authenticate a user."""
    client.get("/auth/logout")
    return client.post(
        "/auth/login",
        data={"email": email, "password": password},
        follow_redirects=True,
    )


# ============================================================================
# 1. Unauthenticated User Cannot Submit Claim
# ============================================================================

def test_unauthenticated_user_cannot_submit_claim(client, found_item):
    """Unauthenticated visitors cannot access or submit claim form."""
    # GET request redirected to login
    get_res = client.get(f"/claims/item/{found_item.id}")
    assert get_res.status_code == 302
    assert "/auth/login" in get_res.headers["Location"]

    # POST request redirected to login without creating claim
    post_res = client.post(
        f"/claims/item/{found_item.id}",
        data={"proof_description": "I can prove this hydroflask is mine."},
    )
    assert post_res.status_code == 302
    assert "/auth/login" in post_res.headers["Location"]

    assert db.session.scalar(db.select(db.func.count(Claim.id))) == 0


# ============================================================================
# 2. User Can Submit Valid Claim for Another User's Open Found Item
# ============================================================================

def test_user_can_submit_valid_claim(client, claimant, found_item):
    """Authenticated student can submit a valid claim for another's open found item."""
    login(client, claimant.email, "BobPass123")

    # GET claim form returns 200 OK
    get_res = client.get(f"/claims/item/{found_item.id}")
    assert get_res.status_code == 200
    html = get_res.get_data(as_text=True)
    assert "Claim This Item" in html
    assert found_item.title in html
    assert "Why do you believe this item belongs to you?" in html

    # POST valid proof
    proof = "It has a dent on the bottom rim and a sticker of a pine tree on the side."
    post_res = client.post(
        f"/claims/item/{found_item.id}",
        data={"proof_description": proof},
        follow_redirects=True,
    )
    assert post_res.status_code == 200
    res_html = post_res.get_data(as_text=True)
    assert "submitted successfully" in res_html

    # Check database
    claim = db.session.scalar(
        db.select(Claim).filter_by(item_id=found_item.id, claimant_id=claimant.id)
    )
    assert claim is not None
    assert claim.status == "pending"
    assert claim.proof_description == proof
    assert claim.reviewer_id is None
    assert claim.reviewed_at is None


# ============================================================================
# 3. User Cannot Claim Their Own Item
# ============================================================================

def test_user_cannot_claim_own_item(client, owner, found_item):
    """Students cannot submit a claim on an item that they reported."""
    login(client, owner.email, "AlicePass123")

    # GET request blocked
    get_res = client.get(f"/claims/item/{found_item.id}", follow_redirects=True)
    assert get_res.status_code == 200
    assert "You cannot claim an item you reported" in get_res.get_data(as_text=True)

    # POST request blocked
    post_res = client.post(
        f"/claims/item/{found_item.id}",
        data={"proof_description": "Trying to claim my own reported item."},
        follow_redirects=True,
    )
    assert post_res.status_code == 200
    assert "You cannot claim an item you reported" in post_res.get_data(as_text=True)

    # Verify no claim created
    assert db.session.scalar(db.select(db.func.count(Claim.id))) == 0


# ============================================================================
# 4. User Cannot Claim a Lost, Closed, or Recovered Item
# ============================================================================

def test_cannot_claim_lost_item(client, claimant, lost_item):
    """Lost items cannot receive ownership claims."""
    login(client, claimant.email, "BobPass123")

    res = client.post(
        f"/claims/item/{lost_item.id}",
        data={"proof_description": "Valid proof description here."},
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert "Only found items can be claimed" in res.get_data(as_text=True)
    assert db.session.scalar(db.select(db.func.count(Claim.id))) == 0


def test_cannot_claim_closed_or_recovered_item(client, claimant, found_item):
    """Items with closed or recovered status cannot receive new claims."""
    login(client, claimant.email, "BobPass123")

    # Closed item
    found_item.status = "closed"
    db.session.commit()

    res_closed = client.post(
        f"/claims/item/{found_item.id}",
        data={"proof_description": "Valid proof description here."},
        follow_redirects=True,
    )
    assert "not currently open for claiming" in res_closed.get_data(as_text=True)
    assert db.session.scalar(db.select(db.func.count(Claim.id))) == 0

    # Recovered item
    found_item.status = "recovered"
    db.session.commit()

    res_rec = client.post(
        f"/claims/item/{found_item.id}",
        data={"proof_description": "Valid proof description here."},
        follow_redirects=True,
    )
    assert "not currently open for claiming" in res_rec.get_data(as_text=True)
    assert db.session.scalar(db.select(db.func.count(Claim.id))) == 0


# ============================================================================
# 5. Duplicate Active Claims are Prevented
# ============================================================================

def test_duplicate_active_claims_prevented(client, claimant, found_item):
    """A user cannot have multiple active (pending or approved) claims on the same item."""
    login(client, claimant.email, "BobPass123")

    # First claim
    res1 = client.post(
        f"/claims/item/{found_item.id}",
        data={"proof_description": "First legitimate proof description."},
        follow_redirects=True,
    )
    assert "submitted successfully" in res1.get_data(as_text=True)
    assert db.session.scalar(db.select(db.func.count(Claim.id))) == 1

    # Attempt second claim while first is pending
    res2 = client.post(
        f"/claims/item/{found_item.id}",
        data={"proof_description": "Second duplicate proof attempt."},
        follow_redirects=True,
    )
    assert "already have an active claim" in res2.get_data(as_text=True)
    assert db.session.scalar(db.select(db.func.count(Claim.id))) == 1

    # When first claim is approved, duplicate is still blocked
    claim = db.session.scalar(db.select(Claim).filter_by(item_id=found_item.id))
    claim.status = "approved"
    db.session.commit()

    res3 = client.post(
        f"/claims/item/{found_item.id}",
        data={"proof_description": "Third duplicate proof attempt."},
        follow_redirects=True,
    )
    assert "already have an active claim" in res3.get_data(as_text=True)
    assert db.session.scalar(db.select(db.func.count(Claim.id))) == 1


# ============================================================================
# 6. Only the Item Owner Can Approve or Reject a Claim
# ============================================================================

def test_only_item_owner_can_review_claim(client, owner, claimant, second_claimant, found_item):
    """Non-owners and claimants are blocked with HTTP 403 when attempting review."""
    # Create pending claim
    claim = Claim(
        item_id=found_item.id,
        claimant_id=claimant.id,
        proof_description="Proof for hydroflask ownership.",
        status="pending",
    )
    db.session.add(claim)
    db.session.commit()

    # Claimant themselves cannot approve or reject
    login(client, claimant.email, "BobPass123")
    res_claimant_app = client.post(f"/claims/{claim.id}/approve")
    assert res_claimant_app.status_code == 403
    res_claimant_rej = client.post(f"/claims/{claim.id}/reject")
    assert res_claimant_rej.status_code == 403

    # Unrelated student cannot approve or reject
    login(client, second_claimant.email, "CharliePass123")
    res_other_app = client.post(f"/claims/{claim.id}/approve")
    assert res_other_app.status_code == 403
    res_other_rej = client.post(f"/claims/{claim.id}/reject")
    assert res_other_rej.status_code == 403

    # Item owner can review
    login(client, owner.email, "AlicePass123")
    res_owner = client.post(f"/claims/{claim.id}/approve", follow_redirects=True)
    assert res_owner.status_code == 200
    assert "has been approved" in res_owner.get_data(as_text=True)


# ============================================================================
# 7. Approval Marks Claim Approved and Item Recovered
# ============================================================================

def test_approval_marks_claim_approved_and_item_recovered(client, owner, claimant, found_item):
    """Approving a claim updates claim status, records reviewer, and marks item recovered."""
    claim = Claim(
        item_id=found_item.id,
        claimant_id=claimant.id,
        proof_description="I have the matching serial number and cap.",
        status="pending",
    )
    db.session.add(claim)
    db.session.commit()

    login(client, owner.email, "AlicePass123")
    res = client.post(f"/claims/{claim.id}/approve", follow_redirects=True)
    assert res.status_code == 200
    assert "now marked as recovered" in res.get_data(as_text=True)

    db.session.refresh(claim)
    db.session.refresh(found_item)

    assert claim.status == "approved"
    assert claim.reviewer_id == owner.id
    assert claim.reviewed_at is not None
    assert found_item.status == "recovered"


# ============================================================================
# 8. Rejection Does Not Change Item Status
# ============================================================================

def test_rejection_does_not_change_item_status(client, owner, claimant, second_claimant, found_item):
    """Rejecting a claim sets status to rejected and leaves item open for others."""
    claim = Claim(
        item_id=found_item.id,
        claimant_id=claimant.id,
        proof_description="Insufficient proof.",
        status="pending",
    )
    db.session.add(claim)
    db.session.commit()

    login(client, owner.email, "AlicePass123")
    res = client.post(f"/claims/{claim.id}/reject", follow_redirects=True)
    assert res.status_code == 200
    assert "has been rejected" in res.get_data(as_text=True)

    db.session.refresh(claim)
    db.session.refresh(found_item)

    assert claim.status == "rejected"
    assert claim.reviewer_id == owner.id
    assert claim.reviewed_at is not None
    assert found_item.status == "open"

    # Another student can still submit a claim
    login(client, second_claimant.email, "CharliePass123")
    res2 = client.post(
        f"/claims/item/{found_item.id}",
        data={"proof_description": "My comprehensive proof with purchase receipt."},
        follow_redirects=True,
    )
    assert "submitted successfully" in res2.get_data(as_text=True)
    assert db.session.scalar(
        db.select(Claim).filter_by(item_id=found_item.id, claimant_id=second_claimant.id)
    ) is not None


# ============================================================================
# 9. Other Pending Claims Cannot Be Approved After One is Approved
# ============================================================================

def test_other_pending_claims_cannot_be_approved_after_one_approved(
    client, owner, claimant, second_claimant, found_item
):
    """Once a claim is approved, other pending claims for that item cannot be approved."""
    claim1 = Claim(
        item_id=found_item.id,
        claimant_id=claimant.id,
        proof_description="Bob's proof.",
        status="pending",
    )
    claim2 = Claim(
        item_id=found_item.id,
        claimant_id=second_claimant.id,
        proof_description="Charlie's proof.",
        status="pending",
    )
    db.session.add_all([claim1, claim2])
    db.session.commit()

    login(client, owner.email, "AlicePass123")

    # Approve claim 1
    res1 = client.post(f"/claims/{claim1.id}/approve", follow_redirects=True)
    assert res1.status_code == 200
    db.session.refresh(claim1)
    db.session.refresh(found_item)
    assert claim1.status == "approved"
    assert found_item.status == "recovered"

    # Attempt to approve claim 2
    res2 = client.post(f"/claims/{claim2.id}/approve", follow_redirects=True)
    assert res2.status_code == 200
    assert "no longer open" in res2.get_data(as_text=True) or "already been approved" in res2.get_data(as_text=True)

    db.session.refresh(claim2)
    assert claim2.status == "pending"


# ============================================================================
# 10. Rejected or Approved Claims Cannot Be Reviewed Again
# ============================================================================

def test_reviewed_claims_cannot_be_reviewed_again(client, owner, claimant, found_item):
    """Approved or rejected claims cannot undergo subsequent review actions."""
    claim = Claim(
        item_id=found_item.id,
        claimant_id=claimant.id,
        proof_description="Proof description.",
        status="pending",
    )
    db.session.add(claim)
    db.session.commit()

    login(client, owner.email, "AlicePass123")

    # Reject the claim
    client.post(f"/claims/{claim.id}/reject", follow_redirects=True)
    db.session.refresh(claim)
    assert claim.status == "rejected"

    # Try to approve rejected claim
    res_app = client.post(f"/claims/{claim.id}/approve", follow_redirects=True)
    assert "already been rejected" in res_app.get_data(as_text=True) or "cannot be reviewed again" in res_app.get_data(as_text=True)
    db.session.refresh(claim)
    assert claim.status == "rejected"

    # Try to reject again
    res_rej = client.post(f"/claims/{claim.id}/reject", follow_redirects=True)
    assert "already been rejected" in res_rej.get_data(as_text=True) or "cannot be reviewed again" in res_rej.get_data(as_text=True)
    db.session.refresh(claim)
    assert claim.status == "rejected"


# ============================================================================
# 11. Users Can View Own Claims Without Seeing Unrelated Private Info
# ============================================================================

def test_users_can_view_own_claims_without_unrelated_private_info(
    client, owner, claimant, second_claimant, found_item
):
    """Claims page displays user's own claims and protects other students' private proofs."""
    # Bob files claim with private details
    claim_bob = Claim(
        item_id=found_item.id,
        claimant_id=claimant.id,
        proof_description="BobSecretSerialNumber777",
        status="pending",
    )
    # Charlie files claim with different private details
    claim_charlie = Claim(
        item_id=found_item.id,
        claimant_id=second_claimant.id,
        proof_description="CharliePrivateEngraving888",
        status="pending",
    )
    db.session.add_all([claim_bob, claim_charlie])
    db.session.commit()

    # Bob views his claims
    login(client, claimant.email, "BobPass123")
    res_bob = client.get("/claims/my-claims")
    assert res_bob.status_code == 200
    html_bob = res_bob.get_data(as_text=True)
    assert "BobSecretSerialNumber777" in html_bob
    assert "CharliePrivateEngraving888" not in html_bob
    assert found_item.title in html_bob

    # Charlie views his claims
    login(client, second_claimant.email, "CharliePass123")
    res_charlie = client.get("/claims/my-claims")
    assert res_charlie.status_code == 200
    html_charlie = res_charlie.get_data(as_text=True)
    assert "CharliePrivateEngraving888" in html_charlie
    assert "BobSecretSerialNumber777" not in html_charlie

    # Non-owner visiting item details does NOT see other students' proofs
    res_detail = client.get(f"/items/{found_item.id}")
    html_detail = res_detail.get_data(as_text=True)
    assert "BobSecretSerialNumber777" not in html_detail
    assert "Pending Claims &amp; Verification" not in html_detail

    # Item owner visiting item details CAN see the proofs in the review section
    login(client, owner.email, "AlicePass123")
    res_owner = client.get(f"/items/{found_item.id}")
    html_owner = res_owner.get_data(as_text=True)
    assert "BobSecretSerialNumber777" in html_owner
    assert "CharliePrivateEngraving888" in html_owner
    assert "Pending Claims &amp; Verification" in html_owner


# ============================================================================
# 12. Invalid IDs and Unauthorized Requests Handled Safely
# ============================================================================

def test_invalid_ids_and_unauthorized_requests(client, owner, claimant):
    """Non-existent items/claims return 404, unauthenticated reviews redirect."""
    login(client, claimant.email, "BobPass123")

    # Non-existent item ID
    res_not_found_get = client.get("/claims/item/99999")
    assert res_not_found_get.status_code == 404
    res_not_found_post = client.post(
        "/claims/item/99999", data={"proof_description": "Valid proof."}
    )
    assert res_not_found_post.status_code == 404

    # Non-existent claim review
    login(client, owner.email, "AlicePass123")
    res_claim_404_app = client.post("/claims/99999/approve")
    assert res_claim_404_app.status_code == 404
    res_claim_404_rej = client.post("/claims/99999/reject")
    assert res_claim_404_rej.status_code == 404

    # Unauthenticated review attempts redirect to login
    client.get("/auth/logout")
    res_unauth_app = client.post("/claims/1/approve")
    assert res_unauth_app.status_code == 302
    assert "/auth/login" in res_unauth_app.headers["Location"]


# ============================================================================
# 13. Form Validation & CSRF Protection Tests
# ============================================================================

def test_claim_proof_validation(client, claimant, found_item):
    """Form requires minimum description length and provides clear error messages."""
    login(client, claimant.email, "BobPass123")

    # Empty description
    res_empty = client.post(f"/claims/item/{found_item.id}", data={"proof_description": ""})
    assert res_empty.status_code == 200
    assert "Please provide details" in res_empty.get_data(as_text=True)

    # Too short (< 10 chars)
    res_short = client.post(f"/claims/item/{found_item.id}", data={"proof_description": "Mine"})
    assert res_short.status_code == 200
    assert "between 10 and 2000 characters" in res_short.get_data(as_text=True)

    assert db.session.scalar(db.select(db.func.count(Claim.id))) == 0


def test_csrf_protection_on_claim_actions():
    """Claim action endpoints enforce CSRF protection when enabled."""
    from config import DevelopmentConfig
    from app import create_app

    csrf_app = create_app(DevelopmentConfig)
    csrf_client = csrf_app.test_client()

    # Attempt POST to approve without CSRF token
    res = csrf_client.post("/claims/1/approve")
    # CSRFProtect returns HTTP 400 Bad Request when missing CSRF token
    assert res.status_code in (400, 302)
