from django.utils.http import url_has_allowed_host_and_scheme


def safe_return_url(url, fallback="/"):
    """Return url if it's a safe local path, otherwise return fallback."""
    if url and url_has_allowed_host_and_scheme(url, allowed_hosts=None):
        return url
    return fallback
