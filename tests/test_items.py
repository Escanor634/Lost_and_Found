"""Tests for Stage 5: Lost and Found Item Management."""
import io
import os
import shutil
from datetime import date, timedelta
from PIL import Image
import pytest

from app.extensions import db
from app.models.user import User
from app.models.item import Item


@pytest.fixture(autouse=True)
def clean_test_uploads(app):
    """Ensure the test uploads folder exists and is cleaned before and after tests."""
    upload_dir = app.config.get("UPLOAD_FOLDER")
    if upload_dir and os.path.exists(upload_dir):
        shutil.rmtree(upload_dir)
    if upload_dir:
        os.makedirs(upload_dir, exist_ok=True)
    yield
    if upload_dir and os.path.exists(upload_dir):
        shutil.rmtree(upload_dir)


@pytest.fixture
def student(app):
    """Fixture providing an active student user."""
    user = User(
        name="Bruce Wayne",
        email="bruce@campus.edu",
        role="student",
        status="active",
    )
    user.set_password("Gotham1234")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def second_student(app):
    """Fixture providing a second active student user."""
    user = User(
        name="Clark Kent",
        email="clark@campus.edu",
        role="student",
        status="active",
    )
    user.set_password("Metropolis1234")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def admin(app):
    """Fixture providing an active administrator user."""
    user = User(
        name="Alfred Pennyworth",
        email="alfred@campus.edu",
        role="admin",
        status="active",
    )
    user.set_password("AdminSecret123")
    db.session.add(user)
    db.session.commit()
    return user


def login(client, email, password):
    """Helper to authenticate a user."""
    return client.post(
        "/auth/login",
        data={"email": email, "password": password},
        follow_redirects=True,
    )


def create_sample_image(format="PNG"):
    """Helper to generate in-memory dummy image file."""
    img = Image.new("RGB", (120, 120), color="blue")
    buf = io.BytesIO()
    img.save(buf, format=format)
    buf.seek(0)
    return buf


# ============================================================================
# 1. AUTHENTICATION PROTECTION TESTS
# ============================================================================

def test_report_routes_require_login(client):
    """Unauthenticated users must be redirected to login when accessing report views."""
    res_choice = client.get("/items/report")
    assert res_choice.status_code == 302
    assert "/auth/login" in res_choice.headers["Location"]

    res_lost = client.get("/items/report/lost")
    assert res_lost.status_code == 302
    assert "/auth/login" in res_lost.headers["Location"]

    res_found = client.get("/items/report/found")
    assert res_found.status_code == 302
    assert "/auth/login" in res_found.headers["Location"]


def test_my_items_requires_login(client):
    """Unauthenticated access to my-items must redirect to login."""
    res = client.get("/items/my-items")
    assert res.status_code == 302
    assert "/auth/login" in res.headers["Location"]


def test_edit_item_requires_login(client, student):
    """Unauthenticated access to edit an item must redirect to login."""
    item = Item(
        user_id=student.id,
        title="Misplaced Calculator",
        description="TI-84 Plus graphing calculator left in lab.",
        category="Electronics",
        item_type="lost",
        location="Science Lab 204",
        incident_date=date.today(),
        status="open",
    )
    db.session.add(item)
    db.session.commit()

    res = client.get(f"/items/{item.id}/edit")
    assert res.status_code == 302
    assert "/auth/login" in res.headers["Location"]


# ============================================================================
# 2. REPORT CREATION & VALIDATION TESTS
# ============================================================================

def test_report_views_render_for_authenticated_student(client, student):
    """Authenticated student can view report selection and forms."""
    login(client, student.email, "Gotham1234")

    res_choice = client.get("/items/report")
    assert res_choice.status_code == 200
    assert "What would you like to report?" in res_choice.get_data(as_text=True)

    res_lost = client.get("/items/report/lost")
    assert res_lost.status_code == 200
    assert "Report a Lost Item" in res_lost.get_data(as_text=True)

    res_found = client.get("/items/report/found")
    assert res_found.status_code == 200
    assert "Report a Found Item" in res_found.get_data(as_text=True)


def test_invalid_item_type_returns_404(client, student):
    """Reporting an invalid item type must return 404."""
    login(client, student.email, "Gotham1234")
    res = client.get("/items/report/unknown-type")
    assert res.status_code == 404


def test_report_lost_item_success(client, student):
    """Successfully submit a lost item report without photograph."""
    login(client, student.email, "Gotham1234")

    post_data = {
        "title": "Black Hydro Flask Water Bottle",
        "description": "32oz wide mouth black hydroflask with campus sticker.",
        "category": "Bottles & Containers",
        "color": "Matte Black",
        "location": "Main Library 2nd Floor Study Lounge",
        "incident_date": date.today().isoformat(),
    }
    response = client.post("/items/report/lost", data=post_data, follow_redirects=True)
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "Black Hydro Flask Water Bottle" in html
    assert "Main Library 2nd Floor Study Lounge" in html

    # Verify database record
    item = db.session.scalar(db.select(Item).filter_by(title="Black Hydro Flask Water Bottle"))
    assert item is not None
    assert item.user_id == student.id
    assert item.item_type == "lost"
    assert item.status == "open"
    assert item.color == "Matte Black"
    assert item.image_path is None


def test_report_found_item_success(client, student):
    """Successfully submit a found item report."""
    login(client, student.email, "Gotham1234")

    post_data = {
        "title": "Set of Dorm Keys with Green Lanyard",
        "description": "Two brass keys and an electronic fob on green lanyard.",
        "category": "Keys & Lanyards",
        "color": "Green",
        "location": "Campus Center Dining Hall",
        "incident_date": date.today().isoformat(),
    }
    response = client.post("/items/report/found", data=post_data, follow_redirects=True)
    assert response.status_code == 200

    item = db.session.scalar(db.select(Item).filter_by(title="Set of Dorm Keys with Green Lanyard"))
    assert item is not None
    assert item.item_type == "found"
    assert item.user_id == student.id
    assert item.status == "open"


def test_report_validation_future_date_rejected(client, student):
    """Incident date cannot be in the future."""
    login(client, student.email, "Gotham1234")

    future_date = (date.today() + timedelta(days=2)).isoformat()
    post_data = {
        "title": "Blue Umbrella",
        "description": "Navy blue compact folding umbrella.",
        "category": "Clothing & Gear",
        "location": "North Hall Entrance",
        "incident_date": future_date,
    }
    response = client.post("/items/report/lost", data=post_data)
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Incident date cannot be in the future." in html

    # Verify nothing was saved
    assert db.session.scalar(db.select(Item).filter_by(title="Blue Umbrella")) is None


def test_report_validation_missing_required_fields(client, student):
    """Submitting empty or short fields triggers validation errors."""
    login(client, student.email, "Gotham1234")

    post_data = {
        "title": "",
        "description": "shrt",
        "category": "",
        "location": "",
        "incident_date": "",
    }
    response = client.post("/items/report/lost", data=post_data)
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "Please provide a descriptive title" in html
    assert "Description must be between 5 and 2000 characters." in html
    assert "Please select a category." in html


# ============================================================================
# 3. SECURE IMAGE UPLOAD & VALIDATION TESTS
# ============================================================================

def test_report_item_with_valid_image(client, student, app):
    """Valid image upload saves file safely and persists path in database."""
    login(client, student.email, "Gotham1234")

    image_buf = create_sample_image("PNG")
    data = {
        "title": "Silver Dell XPS 13 Laptop",
        "description": "Silver 13-inch laptop in black protective sleeve.",
        "category": "Electronics",
        "color": "Silver",
        "location": "Engineering Hall Room 101",
        "incident_date": date.today().isoformat(),
        "image": (image_buf, "my_laptop.png"),
    }

    response = client.post(
        "/items/report/lost",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert response.status_code == 200

    item = db.session.scalar(db.select(Item).filter_by(title="Silver Dell XPS 13 Laptop"))
    assert item is not None
    assert item.image_path is not None
    assert item.image_path.endswith(".png")
    # Must NOT use original client filename directly
    assert item.image_path != "my_laptop.png"

    # Verify physical file existence in UPLOAD_FOLDER
    saved_path = os.path.join(app.config["UPLOAD_FOLDER"], item.image_path)
    assert os.path.isfile(saved_path)


def test_report_item_with_fake_image_content_rejected(client, student):
    """Text file renamed to .png must be rejected by Pillow content inspection."""
    login(client, student.email, "Gotham1234")

    fake_image_buf = io.BytesIO(b"<!DOCTYPE html><html><body>Malicious payload</body></html>")
    data = {
        "title": "Engineering Textbook",
        "description": "Calculus 9th edition hardback book.",
        "category": "Books & Stationery",
        "location": "Math Building Bench",
        "incident_date": date.today().isoformat(),
        "image": (fake_image_buf, "exploit.png"),
    }

    response = client.post(
        "/items/report/found",
        data=data,
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "Invalid or corrupted image file content." in html
    assert db.session.scalar(db.select(Item).filter_by(title="Engineering Textbook")) is None


def test_report_item_with_unsupported_file_extension(client, student):
    """Executable or text extensions must be rejected by form file validation."""
    login(client, student.email, "Gotham1234")

    text_buf = io.BytesIO(b"Just plain text")
    data = {
        "title": "Spiral Notebook",
        "description": "Yellow lined college spiral notebook.",
        "category": "Books & Stationery",
        "location": "Library Desk",
        "incident_date": date.today().isoformat(),
        "image": (text_buf, "notes.txt"),
    }

    response = client.post(
        "/items/report/lost",
        data=data,
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "Only image files (JPG, PNG, WEBP, GIF) are allowed." in html
    assert db.session.scalar(db.select(Item).filter_by(title="Spiral Notebook")) is None


# ============================================================================
# 4. BROWSE LISTINGS & PAGINATION TESTS
# ============================================================================

def test_browse_catalog_empty_states(client):
    """Browse pages display honest empty states when no items exist."""
    res_lost = client.get("/items/lost")
    assert res_lost.status_code == 200
    assert "No Lost Items Reported Yet" in res_lost.get_data(as_text=True)

    res_found = client.get("/items/found")
    assert res_found.status_code == 200
    assert "No Found Items Reported Yet" in res_found.get_data(as_text=True)


def test_browse_catalog_displays_correct_type(client, student):
    """Lost catalog shows lost items; found catalog shows found items."""
    lost_item = Item(
        user_id=student.id,
        title="Red Backpack",
        description="Red North Face commuter backpack.",
        category="Bags & Backpacks",
        item_type="lost",
        location="Gym Locker Room",
        incident_date=date.today(),
        status="open",
    )
    found_item = Item(
        user_id=student.id,
        title="Black Umbrella",
        description="Found in lobby during rainstorm.",
        category="Clothing & Gear",
        item_type="found",
        location="Student Union Lobby",
        incident_date=date.today(),
        status="open",
    )
    db.session.add_all([lost_item, found_item])
    db.session.commit()

    res_lost = client.get("/items/lost")
    assert res_lost.status_code == 200
    html_lost = res_lost.get_data(as_text=True)
    assert "Red Backpack" in html_lost
    assert "Black Umbrella" not in html_lost

    res_found = client.get("/items/found")
    assert res_found.status_code == 200
    html_found = res_found.get_data(as_text=True)
    assert "Black Umbrella" in html_found
    assert "Red Backpack" not in html_found


def test_browse_pagination(client, student):
    """Browse pages paginate cleanly when exceeding per_page count (9 items)."""
    # Create 12 lost items
    items = [
        Item(
            user_id=student.id,
            title=f"Lost Item #{i}",
            description=f"Detailed description for lost item #{i}",
            category="Other",
            item_type="lost",
            location=f"Location {i}",
            incident_date=date.today(),
            status="open",
        )
        for i in range(1, 13)
    ]
    db.session.add_all(items)
    db.session.commit()

    res_page1 = client.get("/items/lost?page=1")
    assert res_page1.status_code == 200
    html_page1 = res_page1.get_data(as_text=True)
    assert "Page navigation" in html_page1

    res_page2 = client.get("/items/lost?page=2")
    assert res_page2.status_code == 200


# ============================================================================
# 5. ITEM DETAIL & PRIVACY TESTS
# ============================================================================

def test_item_detail_view(client, student):
    """Detail view displays full metadata and reporter's public name."""
    item = Item(
        user_id=student.id,
        title="Sony WH-1000XM4 Headphones",
        description="Black noise cancelling wireless headphones with case.",
        category="Electronics",
        item_type="lost",
        color="Matte Black",
        location="Quiet Study Room B",
        incident_date=date.today(),
        status="open",
    )
    db.session.add(item)
    db.session.commit()

    response = client.get(f"/items/{item.id}")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "Sony WH-1000XM4 Headphones" in html
    assert "Quiet Study Room B" in html
    assert "Matte Black" in html
    # Reporter's name should be displayed
    assert student.name in html
    # Reporter's email MUST NEVER be exposed
    assert student.email not in html


def test_item_detail_nonexistent_returns_404(client):
    """Querying an invalid item ID returns 404."""
    response = client.get("/items/999999")
    assert response.status_code == 404


# ============================================================================
# 6. USER REPORT MANAGEMENT & AUTHORIZATION TESTS
# ============================================================================

def test_my_items_lists_only_own_reports(client, student, second_student):
    """My Items dashboard lists only reports created by current user."""
    item1 = Item(
        user_id=student.id,
        title="Bruce Batarang",
        description="Black gadget misplaced on roof.",
        category="Other",
        item_type="lost",
        location="Science Tower Roof",
        incident_date=date.today(),
        status="open",
    )
    item2 = Item(
        user_id=second_student.id,
        title="Clark Glasses",
        description="Tortoiseshell reading glasses.",
        category="Other",
        item_type="lost",
        location="Daily Planet Campus Office",
        incident_date=date.today(),
        status="open",
    )
    db.session.add_all([item1, item2])
    db.session.commit()

    login(client, student.email, "Gotham1234")
    response = client.get("/items/my-items")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "Bruce Batarang" in html
    assert "Clark Glasses" not in html


def test_owner_can_edit_item_and_status(client, student):
    """Owner can update their item listing details and status."""
    item = Item(
        user_id=student.id,
        title="Apple AirPods Pro Case",
        description="White wireless charging case.",
        category="Electronics",
        item_type="found",
        location="Gym Bench",
        incident_date=date.today(),
        status="open",
    )
    db.session.add(item)
    db.session.commit()

    login(client, student.email, "Gotham1234")

    # GET edit form
    res_get = client.get(f"/items/{item.id}/edit")
    assert res_get.status_code == 200

    # POST updates
    post_data = {
        "title": "Apple AirPods Pro Case (Claimed)",
        "description": "White wireless charging case returned to owner.",
        "category": "Electronics",
        "color": "White",
        "location": "Gym Front Desk",
        "incident_date": date.today().isoformat(),
        "status": "recovered",
    }
    res_post = client.post(f"/items/{item.id}/edit", data=post_data, follow_redirects=True)
    assert res_post.status_code == 200

    db.session.refresh(item)
    assert item.title == "Apple AirPods Pro Case (Claimed)"
    assert item.status == "recovered"
    assert item.location == "Gym Front Desk"


def test_owner_can_remove_photograph(client, student, app):
    """Owner can remove an existing photograph during edit."""
    # Create item with dummy image
    image_buf = create_sample_image("PNG")
    login(client, student.email, "Gotham1234")

    post_data = {
        "title": "Item With Photo",
        "description": "Test item that has a photo attached.",
        "category": "Other",
        "location": "Room 10",
        "incident_date": date.today().isoformat(),
        "image": (image_buf, "photo.png"),
    }
    client.post("/items/report/lost", data=post_data, content_type="multipart/form-data")

    item = db.session.scalar(db.select(Item).filter_by(title="Item With Photo"))
    assert item.image_path is not None
    saved_file = os.path.join(app.config["UPLOAD_FOLDER"], item.image_path)
    assert os.path.isfile(saved_file)

    # Edit and request removal
    edit_data = {
        "title": "Item With Photo",
        "description": "Test item that had a photo attached.",
        "category": "Other",
        "location": "Room 10",
        "incident_date": date.today().isoformat(),
        "status": "open",
        "remove_image": "y",
    }
    res = client.post(f"/items/{item.id}/edit", data=edit_data, follow_redirects=True)
    assert res.status_code == 200

    db.session.refresh(item)
    assert item.image_path is None
    # Previous physical file should be deleted
    assert not os.path.isfile(saved_file)


def test_non_owner_student_cannot_edit_item_forbidden(client, student, second_student):
    """Non-owner student receives 403 Forbidden when attempting to edit another user's item."""
    item = Item(
        user_id=student.id,
        title="Student Private Notebook",
        description="Personal notes.",
        category="Books & Stationery",
        item_type="lost",
        location="Lab",
        incident_date=date.today(),
        status="open",
    )
    db.session.add(item)
    db.session.commit()

    # Login as second student
    login(client, second_student.email, "Metropolis1234")

    # GET must return 403
    res_get = client.get(f"/items/{item.id}/edit")
    assert res_get.status_code == 403

    # POST must also return 403
    res_post = client.post(
        f"/items/{item.id}/edit",
        data={
            "title": "Hacked Title",
            "description": "Tampered description",
            "category": "Books & Stationery",
            "location": "Nowhere",
            "incident_date": date.today().isoformat(),
            "status": "closed",
        },
    )
    assert res_post.status_code == 403

    # Verify database was unchanged
    db.session.refresh(item)
    assert item.title == "Student Private Notebook"


def test_admin_can_edit_any_item(client, admin, student):
    """Administrator is authorized to edit any user's item listing."""
    item = Item(
        user_id=student.id,
        title="Unverified Ring",
        description="Gold ring found on field.",
        category="Other",
        item_type="found",
        location="Soccer Field",
        incident_date=date.today(),
        status="open",
    )
    db.session.add(item)
    db.session.commit()

    login(client, admin.email, "AdminSecret123")

    res_post = client.post(
        f"/items/{item.id}/edit",
        data={
            "title": "Unverified Ring (Admin Reviewed)",
            "description": "Gold ring moved to secure lockbox at safety office.",
            "category": "Other",
            "location": "Campus Safety Office Lockbox",
            "incident_date": date.today().isoformat(),
            "status": "open",
        },
        follow_redirects=True,
    )
    assert res_post.status_code == 200

    db.session.refresh(item)
    assert item.title == "Unverified Ring (Admin Reviewed)"
    assert item.location == "Campus Safety Office Lockbox"


def test_edit_nonexistent_item_returns_404(client, student):
    """Attempting to edit a nonexistent item ID returns 404."""
    login(client, student.email, "Gotham1234")
    res = client.get("/items/999999/edit")
    assert res.status_code == 404
