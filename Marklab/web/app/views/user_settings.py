from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.http import HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.crypto import get_random_string
from ..models import UserAPIKey

@login_required(login_url='login')
def settings(request):
    api_keys = UserAPIKey.objects.filter(user_id=request.user.id)

    return render(request, 'settings.html', {'api_keys': api_keys})

@login_required(login_url='login')
def change_password(request):
    if request.method == 'POST':
        new_password = request.POST.get("new_password")
        confirm_new_password = request.POST.get("confirm_new_password")

        if new_password is None or confirm_new_password is None or len(new_password) == 0 or len(confirm_new_password) == 0:
            return HttpResponseBadRequest()

        if new_password != confirm_new_password:
            messages.error(request, 'Passwords do not match!')
            return redirect(reverse('settings'))

        request.user.set_password(new_password)
        request.user.save()
        update_session_auth_hash(request, request.user)

        messages.success(request, 'Password changed successfully!')
        return redirect(reverse('settings'))
    else:
        return HttpResponseBadRequest()


def create_api_key(request):
    if request.method == 'POST':
        api_key = request.POST.get("api_key")

        if api_key is None or api_key == "":
            api_key = get_random_string(length=64)

        api_key_row = UserAPIKey()
        api_key_row.user_id = request.user.id
        api_key_row.api_key = api_key
        api_key_row.save()

        messages.success(request, f'Created new API key')
        return redirect(reverse('settings'))
    else:
        return HttpResponseBadRequest()


def delete_api_key(request):
    if request.method == 'POST':
        api_key = request.POST.get("api_key")

        if api_key is None or api_key == "":
            return HttpResponseBadRequest()

        api_key_rows = UserAPIKey.objects.filter(user_id=request.user.id, api_key=api_key)

        for api_key_row in api_key_rows:
            api_key_row.delete()

        messages.success(request, f'Deleted API key')
        return redirect(reverse('settings'))
    else:
        return HttpResponseBadRequest()
