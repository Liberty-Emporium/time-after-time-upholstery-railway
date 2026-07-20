import os
from io import BytesIO
from django.db import models
from django.core.files.base import ContentFile
from django.utils import timezone
from django.utils.text import slugify
from PIL import Image, ImageOps

class Photo(models.Model):
    CATEGORY_CHOICES = [
        ('reupholstery', 'Reupholstery'),
        ('cushion', 'Custom Cushion'),
        ('antique', 'Antique Restoration'),
        ('leather', 'Leather Repair'),
        ('outdoor', 'Outdoor & Patio'),
        ('other', 'Other'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    image = models.ImageField(upload_to='gallery/')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    description = models.TextField(blank=True)
    is_featured = models.BooleanField(default=False, help_text="Show on homepage")
    uploaded_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    uploaded_at = models.DateTimeField(default=timezone.now)
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['sort_order', '-uploaded_at']
        verbose_name = 'Photo'
        verbose_name_plural = 'Gallery Photos'

    # Max dimension (long edge) for stored gallery images
    MAX_SIZE = 1600
    JPEG_QUALITY = 82

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) or 'photo'
            self.slug = base
            # Ensure unique slug
            counter = 1
            while Photo.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{base}-{counter}"
                counter += 1

        # Resize / compress the image so any size upload fits the gallery neatly.
        # Only process when a new file has been provided (has content to read).
        if self.image and hasattr(self.image, 'file'):
            self._process_image()

        super().save(*args, **kwargs)

    def _process_image(self):
        """Auto-orient, downsize, and compress the uploaded image to a
        consistent, web-friendly JPEG. Safe to fail — on any error we keep
        the original file so an upload never breaks."""
        try:
            self.image.seek(0)
            img = Image.open(self.image)

            # Respect EXIF orientation (phone photos taken sideways display upright)
            img = ImageOps.exif_transpose(img)

            # Flatten transparency onto white, convert to RGB for JPEG
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1])
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # Downscale only if larger than the max (never upscale)
            if max(img.size) > self.MAX_SIZE:
                img.thumbnail((self.MAX_SIZE, self.MAX_SIZE), Image.LANCZOS)

            # Save to a JPEG buffer
            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=self.JPEG_QUALITY, optimize=True)
            buffer.seek(0)

            # Rename to .jpg and replace the file content in-place (no extra save)
            base_name = os.path.splitext(os.path.basename(self.image.name))[0]
            new_name = f"{base_name}.jpg"
            self.image.save(new_name, ContentFile(buffer.read()), save=False)
        except Exception:
            # If anything goes wrong, fall back to the original upload untouched.
            pass

    def __str__(self):
        return self.title


class BusinessInfo(models.Model):
    name = models.CharField(max_length=200, default="Time After Time Upholstery")
    tagline = models.CharField(max_length=300, blank=True, default="Liberty, NC — Quality Upholstery")
    phone = models.CharField(max_length=20, default="(336) 328-6480")
    address = models.CharField(max_length=300, default="446 North Greensboro Street, Liberty, NC 27298")
    email = models.EmailField(blank=True)
    hours = models.CharField(max_length=200, default="Mon–Fri: 9:00 AM – 4:00 PM")
    about_text = models.TextField(blank=True)
    years_in_business = models.IntegerField(default=10)
    logo = models.ImageField(upload_to='brand/', blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Business Info"

    def save(self, *args, **kwargs):
        self.pk = 1  # Singleton
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return self.name