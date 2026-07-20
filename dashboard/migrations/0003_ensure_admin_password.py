from django.db import migrations


def ensure_users(apps, schema_editor):
    from django.contrib.auth.models import User
    from dashboard.models import SiteConfig

    admin, _ = User.objects.get_or_create(
        username='admin',
        defaults={'email': 'admin@daviscarpets.com'},
    )
    admin.is_superuser = True
    admin.is_staff = True
    admin.is_active = True
    admin.set_password('Mhall2026')
    admin.save()

    bryan, _ = User.objects.get_or_create(
        username='bryan',
        defaults={'email': 'bryan@daviscarpets.com'},
    )
    bryan.is_staff = True
    bryan.is_active = True
    bryan.set_password('davis1946')
    bryan.save()

    SiteConfig.get()


def reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0002_siteconfig_alexander_phone_and_more'),
    ]

    operations = [
        migrations.RunPython(ensure_users, reverse),
    ]
