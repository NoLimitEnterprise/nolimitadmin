import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import secrets

def landing(request):
    if request.method == 'POST':
        # Basic server-side logging
        ip = request.META.get('REMOTE_ADDR', 'unknown')
        ua = request.META.get('HTTP_USER_AGENT', 'unknown')
        print(f"[CONSENT] IP: {ip} | UA: {ua} | Session: {request.session.session_key}")

        # Generate random slug for this session only
        random_slug = secrets.token_urlsafe(10)  # ~60-bit entropy
        request.session['auth_slug'] = random_slug

        return redirect('dynamic_login', slug=random_slug)

    return render(request, 'landing.html')

def dynamic_login(request, slug):
    # Security check: only allow if this session generated the slug
    if request.session.get('auth_slug') != slug:
        messages.error(request, "Invalid or expired access link. Return to home.")
        return redirect('landing')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Clean up the one-time slug
            del request.session['auth_slug']
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'login.html', {'slug': slug})

@login_required
def dashboard(request):
    return render(request, 'dashboard.html')

@csrf_exempt
@require_POST
def log_fingerprint(request):
    """
    Receives browser fingerprint data via POST and logs it.
    Called automatically from landing page on load.
    """
    try:
        # Since we're using FormData with hidden input, parse as form
        fingerprint_json = request.POST.get('fingerprint')
        if not fingerprint_json:
            return JsonResponse({'error': 'No fingerprint data'}, status=400)

        fingerprint = json.loads(fingerprint_json)

        # Log to Django logger (will go to console/file depending on settings)
        logger.info("[FINGERPRINT] Received from IP: %s", request.META.get('REMOTE_ADDR', 'unknown'))
        logger.info(json.dumps(fingerprint, indent=2))

        # Optional future: save to DB
        # from .models import FingerprintLog
        # FingerprintLog.objects.create(data=fingerprint, ip=request.META.get('REMOTE_ADDR'))

        return JsonResponse({'status': 'logged'}, status=200)
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Fingerprint logging error: {str(e)}")
        return JsonResponse({'error': 'Server error'}, status=500)