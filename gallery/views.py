import json
import re
from django.shortcuts import render
from django.http import HttpResponse
from django.templatetags.static import static
from .models import Photo, BusinessInfo

# Populated in Phase 2 (service landing pages). Sitemap + service view read this.
SERVICE_PAGES = {}


def _business_schema(request, info):
    """Build a LocalBusiness (HomeAndConstructionBusiness) JSON-LD dict
    from the real BusinessInfo record — no invented facts."""
    digits = re.sub(r'\D', '', info.phone)
    tel = '+1' + digits[-10:] if len(digits) >= 10 else info.phone
    m = re.match(r'^(.*),\s*(.+),\s*([A-Z]{2})\s*(\d{5})$', info.address)
    if m:
        street, city, state, zipc = m.groups()
    else:
        street, city, state, zipc = info.address, '', '', ''
    return {
        '@context': 'https://schema.org',
        '@type': 'HomeAndConstructionBusiness',
        'name': info.name,
        'url': request.build_absolute_uri('/'),
        'image': request.build_absolute_uri(static('brand/tat-emblem.png')),
        'telephone': tel,
        'email': info.email or None,
        'priceRange': '$$',
        'address': {
            '@type': 'PostalAddress',
            'streetAddress': street,
            'addressLocality': city,
            'addressRegion': state,
            'postalCode': zipc,
            'addressCountry': 'US',
        },
        'areaServed': 'Liberty, NC',
        'openingHours': 'Mo-Fr 09:00-16:00',
        'description': (
            f"{info.name} is a family-owned upholstery shop in Liberty, NC offering "
            f"furniture reupholstery, custom cushions, antique restoration, leather "
            f"repair, and outdoor furniture work by appointment."
        ),
    }


def home(request):
    photos = Photo.objects.all()
    featured = photos.filter(is_featured=True)
    info = BusinessInfo.get()
    schema = _business_schema(request, info)
    return render(request, 'gallery/home.html', {
        'photos': photos,
        'featured_photos': featured,
        'info': info,
        'json_ld': json.dumps(schema, ensure_ascii=False),
        'og_image': request.build_absolute_uri(static('brand/tat-emblem.png')),
        'site_url': request.build_absolute_uri('/'),
    })


def sitemap(request):
    base = request.build_absolute_uri('/')
    urls = [(base, '1.0')]
    for slug in SERVICE_PAGES:
        urls.append((request.build_absolute_uri(f'/services/{slug}/'), '0.8'))
    xml = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for loc, prio in urls:
        xml.append(
            f'  <url><loc>{loc}</loc><changefreq>weekly</changefreq>'
            f'<priority>{prio}</priority></url>'
        )
    xml.append('</urlset>')
    return HttpResponse('\n'.join(xml), content_type='application/xml')
