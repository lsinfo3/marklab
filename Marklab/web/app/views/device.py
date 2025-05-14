import json
from datetime import datetime, date
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.http import HttpResponseBadRequest, JsonResponse
from ..models import Device, Modem, Task, DockerImage, DeviceImage

from ..forms import UploadFileForm

from ..services import get_devices_sorted_by_name, handle_zip_file, deploy_dockerfile, convert_time_to_readable


def filter_tasks_according_to_date(tasks, start_date, end_date):
    tasks_copy = list(tasks)
    tasks = []

    if start_date == "":
        start_date = date.min
    else:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        start_date = start_date.date()
    end_date = datetime.strptime(end_date, "%Y-%m-%d")
    end_date = end_date.date()
    for task in tasks_copy:
        task_created_at = task.created_at.date()
        if start_date <= task_created_at <= end_date:
            tasks.append(task)

    return tasks


def filter_tasks_according_to_status(tasks, status):
    if status == "all":
        return tasks
    else:
        tasks_copy = list(tasks)
        tasks = []
        for task in tasks_copy:
            if status in task.status:
                tasks.append(task)

        return tasks


@login_required(login_url='login')
def device(request, device_id):
    relevant_device = Device.objects.get(id=device_id)

    if not request.user.has_perm(f"app.device.{relevant_device.name}.measure"):
        raise PermissionDenied()

    has_perm_upload_docker_images = request.user.has_perm(f"app.device.{relevant_device.name}.upload_docker_images")

    modems = Modem.objects.filter(device=relevant_device)
    # get task for given device and user
    tasks = Task.objects.filter(device=relevant_device)

    # get open tasks
    open_tasks = (tasks.filter(status='pending') | tasks.filter(status='running'))
    if open_tasks.filter(status='running').count() > 0:
        relevant_device.status = 'processing'
    open_tasks = open_tasks.count()

    r_tasks = tasks.filter(created_user=request.user.id)
    r_tasks = r_tasks.order_by('-created_at')

    relevant_device.time_since_checkin = convert_time_to_readable(relevant_device.last_checkin)
    if relevant_device.time_since_checkin == 'N/A' or relevant_device.time_since_checkin.__contains__('hour'):
        relevant_device.status = 'unknown'

    form = UploadFileForm()

    for task in r_tasks:
        # Remove all Tinkerforge UIDs from the JSON provided for copying
        for background_task in task.instruction["background_tasks"]["tasks"]:
            if background_task["image_name"] != "exp-bricklet-voltage-current":
                continue

            background_task["environment"] = [ variable for variable in background_task["environment"] if not variable.startswith("UID=") ]

        if 'is_scheduled_task' in task.instruction and task.instruction['is_scheduled_task']:
            if 'repeat_scheduled_task' in task.instruction and task.instruction['repeat_scheduled_task']:
                task.repeat_scheduled_task = task.instruction['repeat_scheduled_task'].replace('-', ' ')

                task.end_repetition_scheduled_task = task.instruction['end_repetition_scheduled_task']
                if task.instruction['end_repetition_scheduled_task'] == 'on_date_and_time':
                    date_repetition_end = task.instruction['end_repetition_scheduled_task_date_time']['date']
                    date_repetition_end = datetime.strptime(date_repetition_end, '%Y-%m-%d')
                    task.repetition_end_date = date_repetition_end.strftime('%d.%m.%Y')
                    task.repetition_end_time = task.instruction['end_repetition_scheduled_task_date_time']['time']
                elif task.instruction['end_repetition_scheduled_task'] == 'num_repetitions':
                    task.repetition_count = task.instruction['end_repetition_scheduled_task_repetition_count']
                    task.num_repetitions = task.instruction['end_repetition_scheduled_task_num_repetitions']
            else:
                task.repeat_scheduled_task = 'never'

            if task.status == 'pending':
                task.status = 'scheduled-pending'
            elif task.status == 'running':
                task.status = 'scheduled-running'
            elif task.status == 'failed':
                task.status = 'scheduled-failed'
            else:
                task.status = 'scheduled-completed'

            date_scheduled = task.instruction['scheduled_task_date_time']['date']
            date_scheduled = datetime.strptime(date_scheduled, '%Y-%m-%d')
            task.date = date_scheduled.strftime('%d.%m.%Y')
            task.time = task.instruction['scheduled_task_date_time']['time']

    devices = Device.objects.all()

    tasks = tasks.exclude(created_user=request.user.id)
    allow_new_task = True
    for task in tasks:
        if 'is_scheduled_task' in task.instruction and task.instruction['is_scheduled_task'] and task.status == 'pending':
            allow_new_task = False
            break

    all_tasks = Task.objects.filter(status='pending')
    all_tasks = all_tasks.exclude(created_user=request.user.id)

    for task in all_tasks:
        if 'is_scheduled_task' in task.instruction and task.instruction['is_scheduled_task'] and task.status == 'pending':
            devices = devices.exclude(id=task.device.id)

    devices = get_devices_sorted_by_name(devices)
    devices = [ device for device in devices if request.user.has_perm(f"app.device.{device.name}.measure")]

    r_tasks_copy = list(r_tasks)
    r_tasks = []
    scheduled_tasks = []
    archived_tasks = []
    for task in r_tasks_copy:
        if 'is_scheduled_task' in task.instruction and task.instruction['is_scheduled_task'] and task.status == 'scheduled-pending':
            task.instruction = str(json.dumps(task.instruction))
            scheduled_tasks.append(task)
        elif (task.status == 'completed' or task.status == 'scheduled-completed' or task.status == 'failed' or task.status == 'scheduled-failed') and 'archived' in task.instruction:
            task.instruction = str(json.dumps(task.instruction))
            archived_tasks.append(task)
        else:
            task.instruction = str(json.dumps(task.instruction))
            r_tasks.append(task)

    num_tasks = len(r_tasks)
    num_archived_tasks = len(archived_tasks)
    num_scheduled_tasks = len(scheduled_tasks)

    switch_tasks_table = request.GET.get("switchTasksTable")
    selected_table = "tasksTable"
    if switch_tasks_table is not None:
        if switch_tasks_table == "showArchivedTasksTable":
            r_tasks = archived_tasks
            selected_table = "archivedTasksTable"
        elif switch_tasks_table == "showScheduledTasksTable":
            r_tasks = scheduled_tasks
            selected_table = "scheduledTasksTable"

    start_date = request.GET.get("task_table_filter_start_date")
    end_date = request.GET.get("task_table_filter_end_date")
    # Filter the tasks. Only the tasks between the start and end date should be selected.
    if start_date is not None and end_date is not None:
        r_tasks = filter_tasks_according_to_date(r_tasks, start_date, end_date)

    status = request.GET.get("filter_task_status_select")
    if status is not None:
        if selected_table != "scheduledTasksTable":
            if selected_table != "archivedTasksTable" or status == "completed" or status == "failed":
                r_tasks = filter_tasks_according_to_status(r_tasks, status)

    return render(request, 'device.html', {'device': relevant_device, 'modems': modems, 'tasks': r_tasks, 'selected_table': selected_table, 'num_tasks': num_tasks, 'num_archived_tasks': num_archived_tasks, 'num_scheduled_tasks': num_scheduled_tasks, 'form': form, 'open_tasks': open_tasks, 'devices': devices, 'allow_new_task': allow_new_task, 'has_perm_upload_docker_images': has_perm_upload_docker_images})


@login_required(login_url='login')
def upload(request, device_id):
    relevant_device = Device.objects.get(id=device_id)

    if not request.user.has_perm(f"app.device.{relevant_device.name}.measure") or not request.user.has_perm(f"app.device.{relevant_device.name}.upload_docker_images"):
        return JsonResponse({'Error': 'Permission denied'}, status=403)

    if request.method == 'POST':
        context = {}
        form = UploadFileForm(request.POST, request.FILES)
        context['form'] = form
        if form.is_valid():
            try:
                # handle zip file
                tag = form.cleaned_data['tag']
                tag = tag.lower()
                label = form.cleaned_data['label']

                # check if tag or label already exists in database for given device
                device_images = DeviceImage.objects.filter(device=device_id)
                images = DockerImage.objects.filter(id__in=device_images.values('image_id'))

                if images.filter(name=tag).exists():
                    return JsonResponse({'Error': 'Name is already used. Use another name.'}, status=400)

                if images.filter(label=label).exists():
                    return JsonResponse({'Error': 'Label is already used. Use another label.'}, status=400)

                # check if docker image should be available for all users
                is_public = form.cleaned_data['availability']

                user_id = request.user.id
                # background or general
                measurement_type = form.cleaned_data['measurement_type']

                # check if the logging information will be stored in extra files or not
                # this is important to decide where to export the measured data - in stdout or in file
                docker_logger = form.cleaned_data['docker_logger']
                output_type = 'stdout'
                if docker_logger:
                    output_type = 'file'

                # path of directory, where data is stored
                output_file = form.cleaned_data['docker_path']

                # handle zip file
                file_path = handle_zip_file(request.FILES['file'])

                # deploy dockerfile to device
                d_status, message = deploy_dockerfile(file_path, relevant_device, tag)

                if d_status:
                    # write to database
                    docker_image = DockerImage(name=tag, label=label, output_type=output_type,
                                               output_file=output_file, active=True, user_id=user_id,
                                               measurement_type=measurement_type, is_public=is_public,
                                               change_at=datetime.now())
                    docker_image.save()

                    # save to device_image
                    device_image = DeviceImage(device_id=device_id, image_id=docker_image.id)
                    device_image.save()

                    messages.success(request, 'File uploaded successfully!')
                    return JsonResponse({'success': True})
                else:
                    return JsonResponse({'Error': f'Failed to upload docker image! Error: {message}'}, status=400)
            except Exception as ex:
                return JsonResponse({'Error': str(ex)}, status=400)
        else:
            errors = {field: form.errors[field][0] for field in form.errors}
            return JsonResponse(errors, status=400)

@login_required(login_url='login')
def run_operator_scan(request, device_id):
    relevant_device = Device.objects.get(id=device_id)

    if not request.user.has_perm(f"app.device.{relevant_device.name}.measure"):
        raise PermissionDenied()

    if request.method == 'POST':
        modem_name = request.POST.get("modem")
        modem = Modem.objects.get(device=relevant_device, name=modem_name)

        modem.operators["manual_scan"] = True
        modem.save()

        messages.success(request, f"Operator scan started on {modem_name}!")
        return redirect('device', device_id=device_id)
    else:
        return HttpResponseBadRequest()
