from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('services/<slug:slug>/', views.service_page, name='service_page'),
    path('sitemap.xml', views.sitemap, name='sitemap'),
]
