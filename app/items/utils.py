"""Utility functions for items management, file validation, and uploads."""
import os
import uuid
from PIL import Image
from flask import current_app
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif"}
ALLOWED_PIL_FORMATS = {"JPEG", "PNG", "WEBP", "GIF"}


def is_allowed_file(filename):
    """Check if file extension is an approved image type."""
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def validate_and_save_image(file_storage, upload_folder=None):
    """Validate image content, format, and size, then save with a safe UUID filename.

    Args:
        file_storage: Werkzeug FileStorage object.
        upload_folder: Target directory (defaults to current_app.config['UPLOAD_FOLDER']).

    Returns:
        tuple (relative_path, error_message):
            - (relative_path, None) on success
            - (None, None) if no file was uploaded
            - (None, error_string) on validation failure
    """
    if not file_storage or not file_storage.filename or file_storage.filename.strip() == "":
        return None, None

    filename = secure_filename(file_storage.filename)
    if not is_allowed_file(filename):
        return None, "Invalid image format. Allowed formats: JPG, PNG, WEBP, GIF."

    # Size validation
    file_storage.seek(0, os.SEEK_END)
    file_size = file_storage.tell()
    file_storage.seek(0)

    max_size = current_app.config.get("MAX_CONTENT_LENGTH", 5 * 1024 * 1024)
    if file_size > max_size:
        return None, f"Image file is too large. Maximum allowed size is {max_size // (1024 * 1024)}MB."

    if file_size == 0:
        return None, "The uploaded image file is empty."

    # Content validation: Inspect binary image headers with Pillow
    try:
        img = Image.open(file_storage)
        img.verify()
        detected_format = (img.format or "").upper()
        if detected_format not in ALLOWED_PIL_FORMATS:
            return None, f"Unsupported image content format: {detected_format}."
    except Exception:
        return None, "Invalid or corrupted image file content."

    # Reset file pointer after verify
    file_storage.seek(0)

    # Generate unguessable safe filename to avoid traversal or script execution
    ext = filename.rsplit(".", 1)[1].lower()
    if ext == "jpeg":
        ext = "jpg"
    safe_filename = f"{uuid.uuid4().hex}.{ext}"

    if upload_folder is None:
        upload_folder = current_app.config.get(
            "UPLOAD_FOLDER",
            os.path.join(current_app.root_path, "static", "uploads"),
        )
    os.makedirs(upload_folder, exist_ok=True)

    dest_path = os.path.join(upload_folder, safe_filename)
    file_storage.save(dest_path)

    return safe_filename, None


def delete_item_image(image_path):
    """Safely delete an uploaded item image file from disk."""
    if not image_path:
        return
    # Guard against directory traversal by taking only the basename
    safe_filename = os.path.basename(image_path)
    upload_folder = current_app.config.get(
        "UPLOAD_FOLDER",
        os.path.join(current_app.root_path, "static", "uploads"),
    )
    full_path = os.path.join(upload_folder, safe_filename)
    if os.path.exists(full_path):
        try:
            os.remove(full_path)
        except OSError:
            pass
