#!/bin/bash
# Railway start script
set -e

# Use /data for persistent storage on Railway (Volume mount)
export DATA_DIR="${DATA_DIR:-/data}"
mkdir -p "$DATA_DIR/media"

# Run migrations
python manage.py migrate --noinput

# Ensure admin user exists AND has the correct password (idempotent — resets each deploy)
python manage.py shell -c "
from django.contrib.auth.models import User
from dashboard.models import SiteConfig
admin, created = User.objects.get_or_create(username='admin', defaults={'email': 'admin@timeaftertime.com'})
admin.is_superuser = True
admin.is_staff = True
admin.is_active = True
admin.set_password('Mhall001!')
admin.save()
print('Admin user ready (password set to Mhall001!)')

# Ensure SiteConfig singleton exists
SiteConfig.get()

# Enforce free-only model: validate every FREE_MODELS id against OpenRouter's
# live API so a retired/phantom id can never ship; coerce any saved non-free
# model back to a known-good free one.
from dashboard.views import FREE_MODELS
import urllib.request, json
FREE_IDS = [m[0] for m in FREE_MODELS]
try:
    _req = urllib.request.Request('https://openrouter.ai/api/v1/models',
        headers={'User-Agent':'tat-boot','HTTP-Referer':'https://timeaftertimeupholstery.com'})
    _data = json.load(urllib.request.urlopen(_req, timeout=20))
    _live = {m['id'] for m in _data.get('data', [])}
    _bad = [i for i in FREE_IDS if i not in _live]
    if _bad:
        print('WARNING: these FREE_MODELS ids are NOT on OpenRouter (will be unusable):', _bad)
    else:
        print('All FREE_MODELS ids verified live on OpenRouter.')
except Exception as e:
    print('WARNING: could not verify FREE_MODELS against OpenRouter:', e)
cfg = SiteConfig.get()
if cfg.openrouter_model not in FREE_IDS:
    cfg.openrouter_model = FREE_IDS[0]
    cfg.save()
    print('Coerced openrouter_model to free:', cfg.openrouter_model)
else:
    print('openrouter_model already free:', cfg.openrouter_model)

print('SiteConfig ready')

# ── Staff user: rhonda (replaces bryan) — idempotent, password set each deploy ──
bryan_qs = User.objects.filter(username='bryan')
if bryan_qs.exists():
    u = bryan_qs.first()
    u.username = 'rhonda'
    u.email = 'rhonda@timeaftertime.com'
    u.set_password('Tat2026!')
    u.is_staff = True
    u.is_active = True
    u.save()
    print('Renamed bryan -> rhonda (password set to Tat2026!)')
else:
    rhonda_qs = User.objects.filter(username='rhonda')
    if rhonda_qs.exists():
        u = rhonda_qs.first()
        u.set_password('Tat2026!')
        u.is_staff = True
        u.is_active = True
        u.save()
        print('Ensured rhonda password (Tat2026!)')
    else:
        u = User.objects.create_user(username='rhonda', email='rhonda@timeaftertime.com', password='Tat2026!')
        u.is_staff = True
        u.is_active = True
        u.save()
        print('Created rhonda (password Tat2026!)')
        "

# Seed BusinessInfo with the correct upholstery details
python manage.py shell -c "
from gallery.models import BusinessInfo
info = BusinessInfo.get()
info.name = 'Time After Time Upholstery'
info.tagline = 'Liberty, NC — Quality Upholstery'
info.phone = '(336) 328-6408'
info.address = '446 North Greensboro Street, Liberty, NC 27298'
info.hours = 'Mon–Fri: 9:00 AM – 4:00 PM'
info.about_text = 'Time After Time Upholstery is Liberty\\'s trusted upholstery shop. We bring worn and beloved furniture back to life — from a single dining chair to a treasured antique sofa passed down through generations. Every piece is personal: we measure, we rebuild, and we stand behind our work with pride.'
info.years_in_business = 10
info.save()
print('BusinessInfo seeded')
"

# Seed the 5 gallery photos sent by the owner (idempotent)
python manage.py shell -c "
import os
from gallery.models import Photo
media_root = '/data/media' if os.path.exists('/data/media') else 'media'
src_dir = os.path.join(os.getcwd(), 'static', 'gallery')
titles = {
    'img_8438c030f577.jpg': 'Antique Chair Restoration',
    'img_2fba6808930e.jpg': 'Custom Reupholstery',
    'img_b7c05a7f0825.jpg': 'Sofa Reupholstery',
    'img_11c5e5b7c8aa.jpg': 'Cushion & Foam Work',
    'img_f6437e7c5385.jpg': 'Completed Piece',
}
cats = ['antique','reupholstery','reupholstery','cushion','other']
descs = [
    'Delicate antique restoration done with care.',
    'Full reupholstery with fresh fabric and foam.',
    'Worn sofa brought back to life.',
    'Custom-cut cushions for a perfect fit.',
    'A finished piece ready for the home.',
]
count = 0
for i, (fname, title) in enumerate(titles.items()):
    src = os.path.join(src_dir, fname)
    if not os.path.exists(src):
        continue
    if Photo.objects.filter(title=title).exists():
        continue
    rel = 'gallery/' + fname
    dst = os.path.join(media_root, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(src, 'rb') as fh:
        data = fh.read()
    from django.core.files.base import ContentFile
    p = Photo(title=title, category=cats[i], description=descs[i], is_featured=(i == 0))
    p.image.save(fname, ContentFile(data), save=True)
    count += 1
print('Seeded', count, 'gallery photos')
"

# Collect static files
python manage.py collectstatic --noinput --clear

# Start server
exec gunicorn config.wsgi --log-file - --bind 0.0.0.0:${PORT:-8080}
