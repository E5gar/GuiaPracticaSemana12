import logging
import time

from django.conf import settings

logger = logging.getLogger("huancaevent.audit")

CONTENT_SECURITY_POLICY = "; ".join(
    [
        "default-src 'self'",
        "script-src 'self' https://unpkg.com",
        "style-src 'self' https://fonts.googleapis.com",
        "font-src 'self' https://fonts.gstatic.com",
        "img-src 'self' https: data:",
        "media-src 'self' https:",
        "connect-src 'self'",
        "form-action 'self'",
        "base-uri 'self'",
        "frame-ancestors 'none'",
    ]
)


class RequestAuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        started = time.perf_counter()
        response = self.get_response(request)
        elapsed = (time.perf_counter() - started) * 1000
        response["X-Response-Time-Ms"] = f"{elapsed:.1f}"
        if not request.path.startswith("/static/"):
            user = getattr(request, "user", None)
            who = user.username if user is not None and user.is_authenticated else "anonimo"
            logger.info(
                "%s %s status=%s user=%s ip=%s tiempo=%.1fms",
                request.method,
                request.get_full_path(),
                response.status_code,
                who,
                request.META.get("REMOTE_ADDR", "-"),
                elapsed,
            )
        return response

    def process_exception(self, request, exception):
        logger.error("EXCEPCION %s %s %r", request.method, request.path, exception)
        return None


class SessionActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            now = int(time.time())
            if now - request.session.get("last_seen", 0) > 60:
                request.session["last_seen"] = now
                request.session.modified = True
        return self.get_response(request)


class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith("/admin/"):
            return response
        if settings.DEBUG and response.status_code >= 400:
            return response
        response["Content-Security-Policy"] = CONTENT_SECURITY_POLICY
        response["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response["Cross-Origin-Opener-Policy"] = "same-origin"
        return response