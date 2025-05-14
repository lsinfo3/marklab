from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from ..models import Device, Task
from ..services import get_devices_sorted_by_name, convert_time_to_readable
from django.db.models import Q

@login_required(login_url='login')
def home(request):
    devices = get_devices_sorted_by_name(Device.objects.all())
    devices = [ device for device in devices if request.user.has_perm(f"app.device.{device.name}.measure")]

    for device in devices:
        if device.last_checkin:
            # calculate time since last check-in for each device
            # if over 1 hour, display in hours, otherwise display in minutes
            device.time_since_checkin = convert_time_to_readable(device.last_checkin)
        else:
            device.time_since_checkin = 'N/A'

        # get task for given device and user
        open_tasks = Task.objects.filter(Q(device=device) & (Q(status='pending') | Q(status='running')))

        # if there are running tasks, set device status to 'processing' (done in template)
        device.processing_task = open_tasks.filter(status='running').count() > 0

        # get open tasks
        device.open_tasks = open_tasks.count()

        open_tasks = open_tasks.exclude(created_user=request.user.id)
        allow_new_task = True
        for task in open_tasks:
            if 'is_scheduled_task' in task.instruction and task.instruction['is_scheduled_task'] and task.status == 'pending':
                allow_new_task = False
                break
        device.allow_new_task = allow_new_task

    return render(request, 'dashboard.html', {'devices': devices})
