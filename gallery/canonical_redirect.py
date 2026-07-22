"""301-redirect any non-primary host (e.g. *.railway.app) to the canonical domain.

This tells Google to index ONLY timeaftertimeupholstery.com and avoids
duplicate-content penalties from the Railway preview subdomain.
"""
from django.conf import settings
from django.http import HttpResponsePermanentRedirect
from django.utils.deprecation import MiddlewareMixin


class CanonicalDomainRedirectMiddleware(MiddlewareMixin):
    def process_request(self, request):
        primary = getattr(settings, 'PRIMARY_DOMAIN', None)
        if not primary:
            return None
        host = request.get_host()
        if host and host.lower() != primary.lower():
            # Preserve path + query string
            new_url = f"https://{primary}{request.get_full_path()}"
            return HttpResponsePermanentRedirect(new_url)
        return None
