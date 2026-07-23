import json
import re
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.templatetags.static import static
from django.conf import settings
from .models import Photo, BusinessInfo


# Service landing pages — descriptive SEO copy (general upholstery practice,
# not invented business-specific claims). Linked from the homepage.
SERVICE_PAGES = {
    'reupholstery': {
        'slug': 'reupholstery',
        'h1': 'Furniture Reupholstery in Liberty, NC',
        'meta_title': 'Furniture Reupholstery in Liberty, NC | Time After Time Upholstery',
        'meta_description': 'Sofa, chair, loveseat & sectional reupholstery in Liberty, NC. '
                           'New fabric and foam on the frames you love. Free estimates by appointment. '
                           'Call (336) 328-6408.',
        'intro': 'Breathe new life into worn furniture. We reupholster sofas, chairs, loveseats, '
                 'and sectionals — replacing fabric and foam while keeping the frame you already love. '
                 'From a single dining chair to a full sectional, every piece is measured, rebuilt, and '
                 'finished by hand.',
        'bullets': [
            'Sofas, loveseats, sectionals & chairs',
            'Frame repair and webbing rebuilds',
            'New foam and padding cut to fit',
            'Free, no-obligation estimates by appointment',
        ],
    },
    'custom-cushions': {
        'slug': 'custom-cushions',
        'h1': 'Custom Cushions in Liberty, NC',
        'meta_title': 'Custom Cushions & Foam in Liberty, NC | Time After Time Upholstery',
        'meta_description': 'Custom-cut cushions and replacement foam in Liberty, NC — window seats, '
                           'benches, dinettes, and outdoor. Made to fit your piece. Call (336) 328-6408.',
        'intro': 'Window seats, bench cushions, dinette pads, and replacement foam — cut to fit your '
                 'piece exactly. We rebuild cushions that have gone flat and shape new ones for a clean, '
                 'comfortable seat.',
        'bullets': [
            'Window seat & bench cushions',
            'Replacement foam cut to size',
            'Dinettes and boat seating',
            'Outdoor & weather-resistant foam',
            'Welt, piping, and tie-on options',
        ],
    },
    'antique-restoration': {
        'slug': 'antique-restoration',
        'h1': 'Antique Restoration in Liberty, NC',
        'meta_title': 'Antique Furniture Restoration in Liberty, NC | Time After Time Upholstery',
        'meta_description': 'Careful antique and heirloom furniture restoration in Liberty, NC. Delicate '
                           'reupholstery and repair done with respect for the piece. Call (336) 328-6408.',
        'intro': 'Heirloom and antique pieces deserve care. We handle delicate restoration and '
                 'reupholstery of antique furniture — preserving the character of the original while '
                 'bringing it back to a usable, beautiful state.',
        'bullets': [
            'Antique chairs, settees & settees',
            'Spring and webbing repair',
            'Period-appropriate fabric guidance',
            'Careful, reversible restoration work',
            'Pieces passed down through generations',
        ],
    },
    'leather-repair': {
        'slug': 'leather-repair',
        'h1': 'Leather Repair in Liberty, NC',
        'meta_title': 'Leather Furniture Repair in Liberty, NC | Time After Time Upholstery',
        'meta_description': 'Leather couch and chair repair in Liberty, NC — crack repair, recoloring, '
                           'and conditioning. Bring worn leather back to life. Call (336) 328-6408.',
        'intro': 'Cracked, faded, or scratched leather doesn\'t mean the end. We repair and recolor '
                 'leather furniture — repairing cracks, restoring color, and conditioning the surface '
                 'so your leather looks cared for again.',
        'bullets': [
            'Crack and scratch repair',
            'Color matching & recoloring',
            'Conditioning and protection',
            'Leather sofas, chairs & ottomans',
            'Pet-damage touch-ups',
        ],
    },
    'outdoor-patio': {
        'slug': 'outdoor-patio',
        'h1': 'Outdoor & Patio Upholstery in Liberty, NC',
        'meta_title': 'Outdoor & Patio Cushion Upholstery in Liberty, NC | Time After Time Upholstery',
        'meta_description': 'Weather-resistant outdoor and patio cushions in Liberty, NC. Reupholstery and '
                           'custom cushions built for the elements. Call (336) 328-6408.',
        'intro': 'Keep your patio comfortable. We build weather-resistant cushions and reupholster outdoor '
                 'furniture with fabrics made to stand up to sun and rain — so your outdoor space looks good '
                 'season after season.',
        'bullets': [
            'Weather-resistant outdoor cushions',
            'Patio set reupholstery',
            'Sun- and fade-resistant fabrics',
            'Deep-seat and lounge cushions',
            'Custom sizes for any frame',
        ],
    },
}


def _clean_phone(raw):
    """Return clean +1XXXXXXXXXX from any phone format. Fixes stored asterisks."""
    digits = re.sub(r'[^\d]', '', raw or '')
    if len(digits) >= 10:
        return '+1' + digits[-10:]
    return '+133****6408'  # hard fallback for the business's real number


def _business_schema(request, info):
    """LocalBusiness (HomeAndConstructionBusiness) JSON-LD from real BusinessInfo."""
    tel = _clean_phone(info.phone)
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


def service_page(request, slug):
    svc = SERVICE_PAGES.get(slug)
    if not svc:
        from django.http import Http404
        raise Http404('Unknown service')
    info = BusinessInfo.get()
    page_url = request.build_absolute_uri(request.path)
    # Service JSON-LD referencing the business as provider
    biz = _business_schema(request, info)
    service_schema = {
        '@context': 'https://schema.org',
        '@type': 'Service',
        'name': svc['h1'],
        'serviceType': svc['h1'].split(' in ')[0],
        'url': page_url,
        'areaServed': 'Liberty, NC',
        'provider': biz,
    }
    return render(request, 'gallery/service.html', {
        'svc': svc,
        'info': info,
        'services': SERVICE_PAGES,
        'json_ld': json.dumps(service_schema, ensure_ascii=False),
        'og_image': request.build_absolute_uri(static('brand/tat-emblem.png')),
        'site_url': page_url,
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


def robots_txt(request):
    site = request.build_absolute_uri('/').rstrip('/')
    body = f"User-agent: *\nAllow: /\nSitemap: {site}/sitemap.xml\n"
    return HttpResponse(body, content_type='text/plain')