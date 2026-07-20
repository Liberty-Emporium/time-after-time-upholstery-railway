from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.dashboard_login, name='dashboard_login'),
    path('logout/', views.dashboard_logout, name='dashboard_logout'),
    path('', views.dashboard_home, name='dashboard_home'),
    path('upload/', views.upload_photo, name='dashboard_upload'),
    path('delete/<int:photo_id>/', views.delete_photo, name='dashboard_delete'),
    path('chat/', views.chat_page, name='dashboard_chat'),
    path('chat/api/', views.chat_api, name='dashboard_chat_api'),
    path('chat/clear/', views.clear_chat, name='dashboard_clear_chat'),
    path('settings/', views.settings_page, name='dashboard_settings'),
    path('ai-model/', views.model_settings, name='dashboard_model_settings'),
    path('users/', views.users_list, name='dashboard_users'),
    path('users/create/', views.user_create, name='dashboard_user_create'),
    path('users/<int:user_id>/delete/', views.user_delete, name='dashboard_user_delete'),
    path('users/<int:user_id>/password/', views.user_reset_password, name='dashboard_user_password'),
]