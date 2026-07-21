from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('sitemap.xml', views.sitemap, name='sitemap'),
]
