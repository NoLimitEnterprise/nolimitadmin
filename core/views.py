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