from django.contrib import admin
from .models import Photo, BusinessInfo

@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'is_featured', 'sort_order', 'uploaded_at']
    list_filter = ['category', 'is_featured']
    search_fields = ['title', 'description']
    list_editable = ['sort_order', 'is_featured']
    exclude = ['uploaded_by']
    fieldsets = [
        (None, {'fields': ['title', 'image', 'category', 'description']}),
        ('Display Options', {'fields': ['is_featured', 'sort_order']}),
    ]

    def save_model(self, request, obj, form, change):
        if not obj.pk:  # Only set on creation
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(BusinessInfo)
class BusinessInfoAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Business Details', {'fields': ['name', 'tagline', 'phone', 'address', 'email', 'hours']}),
        ('About Section', {'fields': ['about_text', 'years_in_business', 'logo']}),
    ]