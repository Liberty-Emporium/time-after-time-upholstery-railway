from django.contrib import admin
from .models import SiteConfig, ChatMessage


@admin.register(SiteConfig)
class SiteConfigAdmin(admin.ModelAdmin):
    fieldsets = [
        ('OpenRouter AI', {'fields': ['openrouter_api_key', 'openrouter_model', 'system_prompt']}),
        ('Dashboard', {'fields': ['site_title']}),
    ]

    def has_add_permission(self, request):
        # Singleton - only 1 config
        return not SiteConfig.objects.exists()


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['role', 'user', 'content_preview', 'session_id', 'created_at']
    list_filter = ['role', 'session_id']
    search_fields = ['content']
    readonly_fields = ['user', 'role', 'content', 'session_id', 'created_at']

    def content_preview(self, obj):
        return obj.content[:80] + '...' if len(obj.content) > 80 else obj.content
    content_preview.short_description = 'Message'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False