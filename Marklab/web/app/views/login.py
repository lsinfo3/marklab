from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.middleware.csrf import get_token

from ..forms import LoginForm


def login_user_for_backend(request):
    # Used for login via postman
    if request.method == 'POST':
        form = LoginForm(request.POST)
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # If authentication is successful, log the user in
            login(request, user)

            # Get CSRF token for the logged-in user
            csrf_token = get_token(request)

            # Return the CSRF token and the user's ID
            return JsonResponse({'csrf_token': csrf_token, 'user_id': user.id})
        else:
            # If authentication fails, return an error message
            return JsonResponse({'error': 'Invalid login credentials'})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    form = LoginForm()
    if request.method == 'POST':
        form = LoginForm(request.POST)
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            error_message = 'Invalid login credentials'
    else:
        error_message = None

    return render(request, 'login.html', {'error_message': error_message, 'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')  # Change 'login' to your login URL
