from gallery.models import Photo

def dashboard_context(request):
    """Adds dashboard-wide context variables"""
    if request.user.is_authenticated:
        return {
            'photos_count': Photo.objects.count(),
        }
    return {}