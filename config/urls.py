from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import user_passes_test
from django.views.static import serve


# Wrap admin URLs to only allow superusers
admin.site.login = user_passes_test(
    lambda u: u.is_superuser,
    login_url='/dashboard/login/'
)(admin.site.login)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('dashboard/', include('dashboard.urls')),
    path('', include('gallery.urls')),
]

# Serve user-uploaded media files in BOTH dev and production.
# WhiteNoise only serves STATIC files, not user uploads, so we route /media/
# through Django's serve view. (For high traffic, move to S3/R2 later.)
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]