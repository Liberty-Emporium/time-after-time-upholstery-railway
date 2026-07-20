from django.shortcuts import render
from .models import Photo, BusinessInfo

def home(request):
    photos = Photo.objects.all()
    featured = photos.filter(is_featured=True)
    info = BusinessInfo.get()
    return render(request, 'gallery/home.html', {
        'photos': photos,
        'featured_photos': featured,
        'info': info,
    })