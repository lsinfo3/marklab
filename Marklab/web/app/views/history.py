import json
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from ..models import Device, Task


@login_required(login_url='login')
def history(request):
    devices = Device.objects.all()
    devices = [ device for device in devices if request.user.has_perm(f"app.device.{device.name}.measure")]

    tasks = Task.objects.filter(device__in=devices)

    user_id = request.user.id
    tasks = tasks.filter(created_user=user_id)
    tasks = tasks.order_by('-created_at')

    for task in tasks:
        task.instruction = str(json.dumps(task.instruction))

    return render(request, 'history.html', {'devices': devices, 'tasks': tasks})