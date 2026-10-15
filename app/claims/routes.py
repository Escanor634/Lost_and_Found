"""Routes for submitting, reviewing, and tracking ownership claims."""
from datetime import datetime, timezone
from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.item import Item
from app.models.claim import Claim
from app.claims import claims_bp
from app.claims.forms import ClaimForm, ClaimActionForm


@claims_bp.route("/item/<int:item_id>", methods=["GET", "POST"])
@login_required
def submit_claim(item_id):
    """Submit an ownership claim for a found item."""
    item = db.session.get(Item, item_id)
    if not item:
        abort(404)

    # Only found items can be claimed
    if item.item_type != "found":
        flash("Only found items can be claimed.", "danger")
        return redirect(url_for("items.item_detail", item_id=item.id))

    # Only open items can be claimed
    if item.status != "open":
        flash("This item is not currently open for claiming.", "warning")
        return redirect(url_for("items.item_detail", item_id=item.id))

    # Prevent users from claiming items they reported
    if item.user_id == current_user.id:
        flash("You cannot claim an item you reported.", "warning")
        return redirect(url_for("items.item_detail", item_id=item.id))

    # Prevent duplicate active claims (pending or approved) by the same user
    existing_active = db.session.scalar(
        db.select(Claim).filter(
            Claim.item_id == item.id,
            Claim.claimant_id == current_user.id,
            Claim.status.in_(["pending", "approved"]),
        )
    )
    if existing_active:
        flash(
            f"You already have an active claim for this item (Status: {existing_active.status.capitalize()}).",
            "info",
        )
        return redirect(url_for("claims.my_claims"))

    form = ClaimForm()
    if form.validate_on_submit():
        claim = Claim(
            item_id=item.id,
            claimant_id=current_user.id,
            proof_description=form.proof_description.data.strip(),
            status="pending",
        )

        try:
            db.session.add(claim)
            db.session.commit()
            flash(
                f"Your ownership claim for '{item.title}' has been submitted successfully! The reporter will review your proof.",
                "success",
            )
            return redirect(url_for("claims.my_claims"))
        except IntegrityError:
            db.session.rollback()
            flash("An active claim already exists for this item.", "warning")
            return redirect(url_for("items.item_detail", item_id=item.id))
        except Exception:
            db.session.rollback()
            flash("A database error occurred while submitting your claim. Please try again.", "danger")
            return redirect(url_for("items.item_detail", item_id=item.id))

    return render_template("claims/claim_form.html", item=item, form=form)


@claims_bp.route("/<int:claim_id>/approve", methods=["POST"])
@login_required
def approve_claim(claim_id):
    """Approve a pending ownership claim. Only the item owner can approve."""
    form = ClaimActionForm()
    if not form.validate_on_submit():
        flash("Invalid or missing CSRF token. Please try again.", "danger")
        return redirect(request.referrer or url_for("auth.dashboard"))

    claim = db.session.get(Claim, claim_id)
    if not claim:
        abort(404)

    # Critical authorization: only the item owner can approve claims
    # Claimant cannot review their own claim; other students cannot access
    if claim.item.user_id != current_user.id or claim.claimant_id == current_user.id:
        abort(403)

    # Claim must be in pending status
    if claim.status != "pending":
        flash(
            f"This claim has already been {claim.status} and cannot be reviewed again.",
            "warning",
        )
        return redirect(url_for("items.item_detail", item_id=claim.item_id))

    # Item must be open to approve
    if claim.item.status != "open":
        flash("Cannot approve claim: this item is no longer open.", "warning")
        return redirect(url_for("items.item_detail", item_id=claim.item_id))

    # Ensure no other claim has already been approved for this item
    existing_approved = db.session.scalar(
        db.select(Claim).filter(
            Claim.item_id == claim.item_id,
            Claim.status == "approved",
        )
    )
    if existing_approved:
        flash("Another claim has already been approved for this item.", "warning")
        return redirect(url_for("items.item_detail", item_id=claim.item_id))

    try:
        claim.approve(reviewer_id=current_user.id)
        claim.item.status = "recovered"
        claim.item.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        flash(
            f"Claim from {claim.claimant.name} has been approved! The item is now marked as recovered.",
            "success",
        )
    except Exception:
        db.session.rollback()
        flash("A database error occurred while approving the claim. Please try again.", "danger")

    return redirect(url_for("items.item_detail", item_id=claim.item_id))


@claims_bp.route("/<int:claim_id>/reject", methods=["POST"])
@login_required
def reject_claim(claim_id):
    """Reject a pending ownership claim. Only the item owner can reject."""
    form = ClaimActionForm()
    if not form.validate_on_submit():
        flash("Invalid or missing CSRF token. Please try again.", "danger")
        return redirect(request.referrer or url_for("auth.dashboard"))

    claim = db.session.get(Claim, claim_id)
    if not claim:
        abort(404)

    # Critical authorization: only the item owner can reject claims
    # Claimant cannot review their own claim; other students cannot access
    if claim.item.user_id != current_user.id or claim.claimant_id == current_user.id:
        abort(403)

    # Claim must be in pending status
    if claim.status != "pending":
        flash(
            f"This claim has already been {claim.status} and cannot be reviewed again.",
            "warning",
        )
        return redirect(url_for("items.item_detail", item_id=claim.item_id))

    try:
        claim.reject(reviewer_id=current_user.id)
        # Item status remains unchanged so other claims may be reviewed or submitted
        db.session.commit()
        flash(f"Claim from {claim.claimant.name} has been rejected.", "info")
    except Exception:
        db.session.rollback()
        flash("A database error occurred while rejecting the claim. Please try again.", "danger")

    return redirect(url_for("items.item_detail", item_id=claim.item_id))


@claims_bp.route("/my-claims", methods=["GET"])
@login_required
def my_claims():
    """Display ownership claims submitted by the current user."""
    page = request.args.get("page", 1, type=int)
    per_page = 10
    query = (
        db.select(Claim)
        .filter_by(claimant_id=current_user.id)
        .order_by(Claim.created_at.desc())
    )
    pagination = db.paginate(query, page=page, per_page=per_page, error_out=False)
    return render_template("claims/my_claims.html", pagination=pagination)
