"""Authentication utility functions."""
from urllib.parse import urlparse, urljoin
from flask import request


def is_safe_url(target):
    """Ensure redirect URL belongs to the current host and uses safe schemes."""
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc
