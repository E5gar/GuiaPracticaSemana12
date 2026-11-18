import re

from django.utils.html import strip_tags
from django.utils.http import url_has_allowed_host_and_scheme

CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
INLINE_SPACES = re.compile(r"[ \t]{2,}")


def sanitize_input(value, multiline=False, lower=False):
    if value is None:
        return ""
    text = CONTROL_CHARS.sub("", str(value))
    text = strip_tags(text)
    if multiline:
        lines = [INLINE_SPACES.sub(" ", line).strip() for line in text.splitlines()]
        text = "\n".join(lines)
    else:
        text = " ".join(text.split())
    text = text.strip()
    if lower:
        text = text.lower()
    return text


def safe_redirect_target(request, default):
    target = request.POST.get("next") or request.GET.get("next")
    if target and url_has_allowed_host_and_scheme(
        target,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return target
    return default