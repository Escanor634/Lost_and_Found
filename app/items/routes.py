"""Routes for reporting, browsing, detailing, and editing lost and found items."""
from datetime import datetime, timezone
from flask import render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_required, current_user

from app.extensions import db
from app.models.item import Item
from app.models.claim import Claim
from app.items import items_bp
from app.items.forms import ItemReportForm, ItemEditForm
from app.items.utils import validate_and_save_image, delete_item_image
from app.claims.forms import ClaimActionForm


@items_bp.route("/report", methods=["GET"])
@login_required
def report_choice():
    """Render report type selection page."""
    return render_template("items/report_choice.html")


@items_bp.route("/report/lost", methods=["GET", "POST"])
@login_required
def report_lost():
    """Report a lost item."""
    return _handle_report("lost")


@items_bp.route("/report/found", methods=["GET", "POST"])
@login_required
def report_found():
    """Report a found item."""
    return _handle_report("found")


@items_bp.route("/report/<item_type>", methods=["GET", "POST"])
@login_required
def report_item(item_type):
    """Dynamic entrypoint for reporting lost or found items."""
    if item_type not in ("lost", "found"):
        abort(404)
    return _handle_report(item_type)


def _handle_report(item_type):
    """Common report processing logic."""
    form = ItemReportForm()
    if form.validate_on_submit():
        image_path = None
        if form.image.data:
            image_path, error = validate_and_save_image(form.image.data)
            if error:
                flash(error, "danger")
                return render_template("items/report.html", form=form, item_type=item_type)

        item = Item(
            user_id=current_user.id,
            title=form.title.data.strip(),
            description=form.description.data.strip(),
            category=form.category.data,
            item_type=item_type,
            color=form.color.data.strip() if form.color.data else None,
            location=form.location.data.strip(),
            incident_date=form.incident_date.data,
            image_path=image_path,
            status="open",
        )

        try:
            db.session.add(item)
            db.session.commit()
            flash(
                f"Your {item_type} item report for '{item.title}' has been successfully published!",
                "success",
            )
            return redirect(url_for("items.item_detail", item_id=item.id))
        except Exception:
            db.session.rollback()
            if image_path:
                delete_item_image(image_path)
            flash("A database error occurred while saving your report. Please try again.", "danger")

    return render_template("items/report.html", form=form, item_type=item_type)


@items_bp.route("/lost", methods=["GET"])
def lost_items():
    """Browse catalog of lost items."""
    page = request.args.get("page", 1, type=int)
    per_page = 9
    query = (
        db.select(Item)
        .filter_by(item_type="lost")
        .order_by(Item.incident_date.desc(), Item.created_at.desc())
    )
    pagination = db.paginate(query, page=page, per_page=per_page, error_out=False)
    return render_template("items/browse.html", pagination=pagination, item_type="lost")


@items_bp.route("/found", methods=["GET"])
def found_items():
    """Browse catalog of found items."""
    page = request.args.get("page", 1, type=int)
    per_page = 9
    query = (
        db.select(Item)
        .filter_by(item_type="found")
        .order_by(Item.incident_date.desc(), Item.created_at.desc())
    )
    pagination = db.paginate(query, page=page, per_page=per_page, error_out=False)
    return render_template("items/browse.html", pagination=pagination, item_type="found")


@items_bp.route("/<int:item_id>", methods=["GET"])
def item_detail(item_id):
    """View details of a specific item report."""
    item = db.session.get(Item, item_id)
    if not item:
        abort(404)

    user_claim = None
    if current_user.is_authenticated:
        user_claim = db.session.scalar(
            db.select(Claim).filter(
                Claim.item_id == item.id,
                Claim.claimant_id == current_user.id,
                Claim.status.in_(["pending", "approved"]),
            )
        )

    action_form = ClaimActionForm()
    return render_template(
        "items/detail.html",
        item=item,
        user_claim=user_claim,
        action_form=action_form,
    )


@items_bp.route("/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
def edit_item(item_id):
    """Allow report creator or administrator to edit an existing report."""
    item = db.session.get(Item, item_id)
    if not item:
        abort(404)

    # Enforce strict server-side ownership authorization
    if item.user_id != current_user.id and not current_user.is_admin():
        abort(403)

    form = ItemEditForm(obj=item)
    if form.validate_on_submit():
        # Handle photograph removal
        if form.remove_image.data and item.image_path:
            delete_item_image(item.image_path)
            item.image_path = None

        # Handle photograph replacement
        if form.image.data:
            new_path, error = validate_and_save_image(form.image.data)
            if error:
                flash(error, "danger")
                return render_template("items/edit.html", form=form, item=item)
            if item.image_path:
                delete_item_image(item.image_path)
            item.image_path = new_path

        # Update fields
        item.title = form.title.data.strip()
        item.description = form.description.data.strip()
        item.category = form.category.data
        item.color = form.color.data.strip() if form.color.data else None
        item.location = form.location.data.strip()
        item.incident_date = form.incident_date.data
        item.status = form.status.data
        item.updated_at = datetime.now(timezone.utc)

        try:
            db.session.commit()
            flash("Listing updated successfully.", "success")
            return redirect(url_for("items.item_detail", item_id=item.id))
        except Exception:
            db.session.rollback()
            flash("Failed to update listing due to a database error.", "danger")

    return render_template("items/edit.html", form=form, item=item)


@items_bp.route("/my-items", methods=["GET"])
@login_required
def my_items():
    """Display all reports created by the authenticated user."""
    page = request.args.get("page", 1, type=int)
    per_page = 10
    query = (
        db.select(Item)
        .filter_by(user_id=current_user.id)
        .order_by(Item.created_at.desc())
    )
    pagination = db.paginate(query, page=page, per_page=per_page, error_out=False)
    return render_template("items/my_items.html", pagination=pagination)
