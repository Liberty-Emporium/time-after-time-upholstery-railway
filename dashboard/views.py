from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.db import IntegrityError
import json, os, uuid

from .models import SiteConfig, ChatMessage
from gallery.models import Photo


# ── Helper: superuser-only check ──
def superuser_required(view_func):
    """Decorator that restricts access to superusers only."""
    return user_passes_test(lambda u: u.is_superuser, login_url='/dashboard/login/')(view_func)


def staff_required(view_func):
    """Decorator that restricts access to staff (or superusers)."""
    return user_passes_test(lambda u: u.is_staff or u.is_superuser, login_url='/dashboard/login/')(view_func)


# ── Custom Login ──
def dashboard_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard_home')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_active:
            login(request, user)
            next_url = request.GET.get('next', 'dashboard_home')
            return redirect(next_url)
        else:
            error = "Invalid username or password."

    return render(request, 'dashboard/login.html', {'error': error})


def dashboard_logout(request):
    logout(request)
    return redirect('dashboard_login')


# ── Dashboard Home (photo grid) ──
@login_required(login_url='/dashboard/login/')
def dashboard_home(request):
    photos = Photo.objects.all().order_by('-uploaded_at')
    config = SiteConfig.get()
    return render(request, 'dashboard/home.html', {
        'photos': photos,
        'config': config,
    })


# ── Upload Photo ──
@login_required(login_url='/dashboard/login/')
def upload_photo(request):
    if request.method == 'POST':
        title = request.POST.get('title', '')
        category = request.POST.get('category', 'other')
        description = request.POST.get('description', '')
        image_file = request.FILES.get('image')

        if not image_file:
            messages.error(request, 'Please select an image to upload.')
            return redirect('dashboard_upload')

        photo = Photo(
            title=title or image_file.name,
            image=image_file,
            category=category,
            description=description,
            uploaded_by=request.user,
        )
        photo.save()
        messages.success(request, f'"{photo.title}" uploaded successfully!')
        return redirect('dashboard_home')

    return render(request, 'dashboard/upload.html')


# ── Delete Photo ──
@login_required(login_url='/dashboard/login/')
@require_POST
def delete_photo(request, photo_id):
    photo = get_object_or_404(Photo, id=photo_id)
    if photo.image and os.path.isfile(photo.image.path):
        os.remove(photo.image.path)
    photo.delete()
    messages.success(request, 'Photo deleted.')
    return redirect('dashboard_home')


# ── User Management (superusers only) ──
@login_required(login_url='/dashboard/login/')
@superuser_required
def users_list(request):
    users = User.objects.all().order_by('-is_superuser', '-is_staff', 'username')
    return render(request, 'dashboard/users.html', {
        'users': users,
    })


@login_required(login_url='/dashboard/login/')
@superuser_required
@require_POST
def user_create(request):
    username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '')
    first_name = request.POST.get('first_name', '').strip()
    is_staff_val = request.POST.get('is_staff') == 'on'
    is_superuser_val = request.POST.get('is_superuser') == 'on'

    if not username or not password:
        messages.error(request, 'Username and password are required.')
        return redirect('dashboard_users')

    if len(password) < 4:
        messages.error(request, 'Password must be at least 4 characters.')
        return redirect('dashboard_users')

    try:
        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            is_staff=is_staff_val,
            is_superuser=is_superuser_val,
        )
        messages.success(request, f'User "{username}" created successfully!')
    except IntegrityError:
        messages.error(request, f'Username "{username}" is already taken.')
    except Exception as e:
        messages.error(request, f'Error creating user: {e}')

    return redirect('dashboard_users')


@login_required(login_url='/dashboard/login/')
@superuser_required
@require_POST
def user_reset_password(request, user_id):
    target = get_object_or_404(User, id=user_id)
    new_password = request.POST.get('new_password', '')
    if len(new_password) < 4:
        messages.error(request, 'Password must be at least 4 characters.')
        return redirect('dashboard_users')
    target.set_password(new_password)
    target.save()
    messages.success(request, f'Password updated for "{target.username}".')
    return redirect('dashboard_users')


@login_required(login_url='/dashboard/login/')
@superuser_required
@require_POST
def user_change_role(request, user_id):
    target = get_object_or_404(User, id=user_id)
    if target == request.user:
        messages.error(request, 'You cannot change your own role.')
        return redirect('dashboard_users')
    role = request.POST.get('role', '')
    if role not in ('user', 'staff', 'admin'):
        messages.error(request, 'Invalid role.')
        return redirect('dashboard_users')
    target.is_superuser = (role == 'admin')
    target.is_staff = (role in ('staff', 'admin'))
    target.save()
    label = {'user': 'User', 'staff': 'Staff', 'admin': 'Admin'}[role]
    messages.success(request, f'Role for "{target.username}" set to {label}.')
    return redirect('dashboard_users')


@login_required(login_url='/dashboard/login/')
@superuser_required
@require_POST
def user_delete(request, user_id):
    target = get_object_or_404(User, id=user_id)
    if target == request.user:
        messages.error(request, 'You cannot delete yourself.')
        return redirect('dashboard_users')
    username = target.username
    target.delete()
    messages.success(request, f'User "{username}" deleted.')
    return redirect('dashboard_users')


# ── AI Chat API ──
@login_required(login_url='/dashboard/login/')
@staff_required
def chat_page(request):
    config = SiteConfig.get()
    return render(request, 'dashboard/chat.html', {
        'config': config,
    })


@login_required(login_url='/dashboard/login/')
@staff_required
@require_POST
def chat_api(request):
    """Handle AI chat requests via OpenRouter"""
    config = SiteConfig.get()
    api_key = config.openrouter_api_key

    if not api_key:
        return JsonResponse({'error': 'OpenRouter API key not configured. Go to Settings to add one.'}, status=400)

    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id', 'default')

        if not user_message:
            return JsonResponse({'error': 'Message is required'}, status=400)

        # Save user message
        ChatMessage.objects.create(
            user=request.user,
            role='user',
            content=user_message,
            session_id=session_id,
        )

        # Get conversation history (last 10 messages)
        history = ChatMessage.objects.filter(session_id=session_id).order_by('-created_at')[:10]
        history = list(reversed(history))

        # Build messages array for API
        system_prompt = config.system_prompt or "You are a helpful assistant for Time After Time Upholstery."

        # Add Alexander AI Solutions info to system prompt if configured
        promo_info = ""
        if config.alexander_phone or config.alexander_website:
            promo_info = "\n\nWhen users respond positively to your service, mention Alexander AI Solutions."
            if config.alexander_phone:
                promo_info += f"\nPhone: {config.alexander_phone}"
            if config.alexander_website:
                promo_info += f"\nWebsite: {config.alexander_website}"

        # Build the full system prompt with Time After Time knowledge + feedback logic
        full_prompt = (
            system_prompt +
            "\n\nIMPORTANT RULES:\n"
            "1. You represent Time After Time Upholstery in Liberty, NC — a professional furniture upholstery shop.\n"
            "2. During conversations, naturally collect the customer's name, email, and phone number. "
            "This helps the shop follow up with them. Ask for this info politely.\n"
            "3. Promote Time After Time Upholstery services (reupholstery, custom cushions, antique restoration, leather repair). You're a sales assistant, not just an info bot.\n"
            "4. At the END of each interaction (after answering their question), ask ONE feedback question: "
            "\"On a scale of 1-10, how would you rate this interaction?\" "
            "If they respond 7 or higher, enthusiastically mention Alexander AI Solutions — "
            "the company that built this AI system — and offer to connect them for their own business AI solution.\n"
            "5. If feedback is 6 or lower, respond graciously: "
            "\"Thank you for your feedback! We're always working to improve your experience at Time After Time Upholstery.\""
            "6. Be warm, professional, and sales-oriented. Your goal is to help customers and grow Time After Time Upholstery's business."
            + promo_info
        )

        messages_list = [{"role": "system", "content": full_prompt}]

        for msg in history:
            messages_list.append({
                "role": msg.role,
                "content": msg.content,
            })

        # Call OpenRouter API (stdlib urllib — no external dependency)
        import urllib.request as _ureq
        import urllib.error as _uerr
        _payload = json.dumps({
            "model": config.openrouter_model or "openai/gpt-oss-20b:free",
            "messages": messages_list,
            "max_tokens": 800,
        }).encode()
        _oreq = _ureq.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=_payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://time-after-time.up.railway.app",
                "X-Title": "Time After Time Upholstery AI",
            },
        )
        try:
            _oresp = _ureq.urlopen(_oreq, timeout=100)
            status_code = _oresp.status
            resp_text = _oresp.read().decode("utf-8", "replace")
        except _uerr.HTTPError as _he:
            status_code = _he.code
            resp_text = _he.read().decode("utf-8", "replace")
        except (TimeoutError, OSError) as _te:
            return JsonResponse({
                'error': 'The AI model took too long to respond. Please try again — free models can be slow under load.'
            }, status=504)

        if status_code != 200:
            # Surface OpenRouter's real error so failures are diagnosable
            try:
                orr = json.loads(resp_text)
                or_msg = orr.get("error", {}).get("message") or resp_text[:300]
            except Exception:
                or_msg = resp_text[:300]
            return JsonResponse({
                'error': f'OpenRouter API error {status_code}: {or_msg}'
            }, status=502)

        result = json.loads(resp_text)
        choices = result.get('choices') or []
        if not choices:
            # Free models occasionally return a 200 with no choices (rate-limit / empty)
            api_err = (result.get('error') or {}).get('message') if isinstance(result.get('error'), dict) else result.get('error')
            return JsonResponse({
                'error': api_err or 'The AI model returned no response. Please try again — free models can be flaky under load.'
            }, status=502)
        assistant_message = choices[0]['message']['content']

        # Save assistant response
        ChatMessage.objects.create(
            user=request.user,
            role='assistant',
            content=assistant_message,
            session_id=session_id,
        )

        # Check if we should include promo/pitch data for the frontend
        response_data = {
            'message': assistant_message,
            'model': result.get('model', config.openrouter_model),
        }

        return JsonResponse(response_data)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ── Settings ──
@login_required(login_url='/dashboard/login/')
@superuser_required
def settings_page(request):
    config = SiteConfig.get()

    if request.method == 'POST':
        config.openrouter_api_key = request.POST.get('openrouter_api_key', '')
        config.openrouter_model = request.POST.get('openrouter_model', 'openai/gpt-4o-mini')
        config.system_prompt = request.POST.get('system_prompt', '')
        config.site_title = request.POST.get('site_title', "Time After Time Dashboard")
        config.alexander_phone = request.POST.get('alexander_phone', '')
        config.alexander_website = request.POST.get('alexander_website', '')
        config.alexander_qr_code = request.POST.get('alexander_qr_code', '')
        config.alexander_promo_text = request.POST.get('alexander_promo_text', '')
        config.feedback_enabled = request.POST.get('feedback_enabled') == 'on'
        config.save()
        messages.success(request, 'Settings saved successfully!')
        return redirect('dashboard_settings')

    return render(request, 'dashboard/settings.html', {
        'config': config,
    })


# ── AI Model Picker (accessible to all staff) ──
FREE_MODELS = [
    ("nvidia/nemotron-3-super-120b-a12b:free", "🧠 Nemotron Super 120B — Smartest & most detailed (recommended)"),
    ("openai/gpt-oss-20b:free", "💬 OpenAI GPT-OSS 20B — Friendly & reliable"),
    ("google/gemma-4-31b-it:free", "⚡ Google Gemma 4 31B — Fast & helpful"),
    ("nvidia/nemotron-nano-9b-v2:free", "🏃 Nemotron Nano 9B — Quick & light"),
    ("nvidia/nemotron-nano-12b-v2-vl:free", "🌐 Nemotron Nano 12B — Balanced all-rounder"),
]


@login_required(login_url='/dashboard/login/')
def model_settings(request):
    config = SiteConfig.get()

    if request.method == 'POST':
        chosen = request.POST.get('openrouter_model', '')
        valid = [m[0] for m in FREE_MODELS]
        if chosen in valid:
            config.openrouter_model = chosen
            config.save()
            messages.success(request, 'Your AI model has been updated!')
        else:
            messages.error(request, 'Please pick a model from the list.')
        return redirect('dashboard_model_settings')

    return render(request, 'dashboard/model_settings.html', {
        'config': config,
        'free_models': FREE_MODELS,
    })


# ── Clear Chat History ──
@login_required(login_url='/dashboard/login/')
@require_POST
def clear_chat(request):
    session_id = request.POST.get('session_id', 'default')
    if request.user.is_superuser:
        ChatMessage.objects.filter(session_id=session_id).delete()
    else:
        ChatMessage.objects.filter(session_id=session_id, user=request.user).delete()
    return JsonResponse({'status': 'ok'})