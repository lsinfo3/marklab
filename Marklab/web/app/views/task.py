from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, HttpResponse, redirect
from django.urls import reverse
from django.http import JsonResponse
from django.db.models import Q
from ..models import Device, Modem, Task, UserAPIKey, DockerImage, DeviceImage
from ..services import reboot_via_ssh
from django.views.decorators.http import require_POST
from datetime import datetime
import os
import io
import time
import json
import zipfile
from django.forms.models import model_to_dict

from rest_framework.decorators import api_view

def to_json_dumps(images):
    images_json_dumps = []
    for image in images:
        image_dict = model_to_dict(image)
        del image_dict["change_at"]
        images_json_dumps.append(image_dict)

    return json.dumps(images_json_dumps)

@login_required(login_url='login')
def task(request, device_id):
    relevant_device = Device.objects.get(id=device_id)

    if not request.user.has_perm(f"app.device.{relevant_device.name}.measure"):
        if request.method == 'POST':
            return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)
        else:
            raise PermissionDenied()

    has_perm_schedule_measurements = request.user.has_perm(f"app.device.{relevant_device.name}.schedule_measurements")

    if request.method == 'POST':
        # create task
        try:
            if not request.body:
                raise Exception('No instruction provided!')

            instruction = parse_json(request.body.decode('utf-8'))

            if not has_perm_schedule_measurements and "is_scheduled_task" in instruction and instruction["is_scheduled_task"]:
                return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)

            samples = instruction.pop('num_samples', 1)

            for i in range(int(samples)):
                create_task(device_id, instruction, request.user.id)
            messages.success(request, 'Task created successfully!')
            redirect_url = reverse('device', kwargs={'device_id': device_id})
            return JsonResponse({'success': True, 'redirect_url': redirect_url})
        except Exception as e:
            # messages.error(request, 'Failed to create a task! Make sure you have entered a valid JSON instruction.')
            return JsonResponse({'success': False, 'message': str(e)})

    modems = Modem.objects.filter(device=relevant_device)
    device_image_ids = DeviceImage.objects.filter(device_id=device_id).values_list('image_id', flat=True)
    docker_images = DockerImage.objects.filter(
        id__in=device_image_ids
    ).filter(
        ((Q(user_id=request.user.id) & Q(is_public=False)) | Q(is_public=True)) & Q(active=True)
    )

    background_images = docker_images.filter(measurement_type='background')
    background_later_images = docker_images.filter(measurement_type='background_later')
    docker_images = docker_images.filter(measurement_type='general')

    docker_images_json_dumps = to_json_dumps(docker_images)
    background_images_json_dumps = to_json_dumps(background_images)
    background_later_images_json_dumps = to_json_dumps(background_later_images)

    # get task for given device and user
    return render(request, 'task.html', {'device': relevant_device, 'modems': modems, 'images': docker_images,
                                         'background_images': background_images, 'background_later_images': background_later_images, 'images_json_dumps': docker_images_json_dumps, 'background_images_json_dumps': background_images_json_dumps, 'background_later_images_json_dumps': background_later_images_json_dumps, 'has_perm_schedule_measurements': has_perm_schedule_measurements})


@api_view(['GET', 'POST'])
def task_api(request):
    api_key = request.headers.get('X-API-KEY')

    if api_key is None or api_key == "":
        return JsonResponse({'success': False, 'message': 'Missing X-API-KEY header'}, status=400)

    try:
        api_key_row = UserAPIKey.objects.get(api_key=api_key)
    except UserAPIKey.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Invalid API key'}, status=401)

    try:
        user = User.objects.get(id=api_key_row.user_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Invalid API key'}, status=401)

    user_id = user.id

    if request.method == 'POST':
        if not request.body:
            return JsonResponse({'success': False, 'message': 'No instruction provided in request body'}, status=400)

        request_body = parse_json(request.body.decode('utf-8'))

        if isinstance(request_body, list):
            instructions = request_body
        else:
            instructions = [request_body]

        for instruction in instructions:
            if not "device_name" in instruction:
                return JsonResponse({'success': False, 'message': 'Device name missing in instruction'}, status=400)

            device_name = instruction["device_name"]
            relevant_device = None

            try:
                relevant_device = Device.objects.get(name=device_name)
            except Device.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Device not found'}, status=404)

            if not user.has_perm(f"app.device.{relevant_device.name}.measure"):
                return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)

            has_perm_schedule_measurements = user.has_perm(f"app.device.{relevant_device.name}.schedule_measurements")

            if not has_perm_schedule_measurements and "is_scheduled_task" in instruction and instruction["is_scheduled_task"]:
                return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)

        task_ids = []

        for instruction in instructions:
            samples = instruction.pop('num_samples', 1)

            for _ in range(int(samples)):
                task_id = create_task(relevant_device.id, instruction, user_id)
                task_ids.append(task_id)

        return JsonResponse({'success': True, 'task_ids': task_ids})
    else:
        return JsonResponse({'success': False, 'message': 'GET not supported yet, to create a task send a POST request with the instruction in the request body'}, status=400)


@login_required(login_url='login')
def task_detail(request, task_id):
    _task = Task.objects.get(id=task_id)

    if not request.user.has_perm(f"app.device.{_task.device.name}.measure"):
        raise PermissionDenied()

    if _task.created_user != request.user.id:
        raise PermissionDenied()

    try:
        instruction = _task.instruction

        # export instruction as json file
        http_response = HttpResponse(json.dumps(instruction), content_type='application/json')
        http_response['Content-Disposition'] = f'attachment; filename={_task.name}.json'

        return http_response
    except Exception as ex:
        messages.error(request, 'Failed to download instruction!')
        return redirect('device', device_id=_task.device_id)


@login_required(login_url='login')
def preview_task(request, task_id):
    _task = Task.objects.get(id=task_id)

    if not request.user.has_perm(f"app.device.{_task.device.name}.measure"):
        raise PermissionDenied()

    if _task.created_user != request.user.id:
        raise PermissionDenied()

    return render(request, 'task_preview.html', {'task': _task, 'device_id': _task.device_id, "ip_type": _task.instruction["modem_configuration"]["ip-type"]})


def create_task(device_id, _instruction, user_id):
    try:
        _task = Task()
        _task.device_id = device_id

        add_tinkerforge_uid(instruction=_instruction, device_id=device_id)
        add_user_location_metadata(instruction=_instruction, user_id=user_id, device_id=device_id)

        _task.instruction = _instruction

        modem = Modem.objects.get(device_id=device_id, name=_instruction.get('modem'))
        modem_port = modem.port

        if not modem_port.__contains__('/dev/'):
            modem_port = '/dev/' + modem_port

        _task.instruction['modem_port'] = modem_port

        if modem.name.__contains__('BG96'):
            _task.instruction['modem_iot'] = True

        _task.name = _task.instruction.get('experiment_name')
        _task.status = 'pending'
        _task.created_user = user_id
        _task.save()
        return _task.id
    except Exception as ex:
        raise Exception('Failed to create task: ' + str(ex))


def parse_json(json_instruction):
    try:
        json_instruction = json.loads(json_instruction)
        return json_instruction
    except Exception as ex:
        raise Exception('Failed to parse JSON instruction: ' + str(ex))


@require_POST
@login_required(login_url='login')
def selection(request):
    device_id = request.POST.get('device_id')  # get device id if available
    if request.method == 'POST':
        relevant_device = Device.objects.get(id=device_id)

        if not request.user.has_perm(f"app.device.{relevant_device.name}.measure"):
            raise PermissionDenied()

        action = request.POST.get('selected_action')

        if action == 'download':
            return selection_download(request, device_id)
        elif action == 'delete':
            return selection_delete(request, device_id)
        else:
            messages.error(request, 'Invalid action.')
            if device_id is None or device_id == '':
                return redirect('history')
            return redirect('device', device_id=device_id)
    else:
        messages.error(request, 'Invalid request method.')
        # reload page
        if device_id is None or device_id == '':
            return redirect('history')
        return redirect('device', device_id=device_id)

def archive_task(task):
    if 'archived' not in task.instruction:
        task.instruction['archived'] = True
    else:
        del task.instruction['archived']
    task.save()

def selection_download(request, device_id):
    try:
        # get task ids from request json
        task_ids = request.POST.get('task_ids')
        task_ids = json.loads(task_ids).get('task_ids')
        in_memory_zip = io.BytesIO()

        tasks = Task.objects.filter(id__in=task_ids)
        # remove tasks that do not have result files
        tasks = [task for task in tasks if task.result_path is not None and task.result_path != '']

        other_users_tasks = [task for task in tasks if task.created_user != request.user.id]

        if len(other_users_tasks) > 0:
            raise PermissionDenied()

        if len(tasks) == 0:
            messages.error(request, 'No results found!')
            if device_id is None or device_id == '':
                return redirect('history')
            return redirect('device', device_id=device_id)

        with zipfile.ZipFile(in_memory_zip, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
            for task in tasks:
                if task.result_path:
                    if os.path.exists(task.result_path):
                        file_name = os.path.basename(task.result_path)
                        zf.write(task.result_path, arcname=file_name)
                    else:
                        raise FileNotFoundError('Result file not found!')

        in_memory_zip.seek(0)
        file_name = f'results_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.zip'
        response = HttpResponse(in_memory_zip.getvalue(), content_type='application/zip')
        response['Content-Disposition'] = 'inline; filename=' + file_name
        return response
    except Task.DoesNotExist:
        messages.error(request, 'One or more tasks could not be found.')
        if device_id is None or device_id == '':
            return redirect('history')
        return redirect('device', device_id=device_id)
    except FileNotFoundError as fnfe:
        messages.error(request, f'Failed to download results. Error: {str(fnfe)}')
        if device_id is None or device_id == '':
            return redirect('history')
        return redirect('device', device_id=device_id)
    except Exception as e:
        messages.error(request, f'Failed to download results. Error: {str(e)}')
        if device_id is None or device_id == '':
            return redirect('history')
        return redirect('device', device_id=device_id)

def selection_delete(request, device_id):
    try:
        task_ids = request.POST.get('task_ids')
        task_ids = json.loads(task_ids).get('task_ids')
        tasks = Task.objects.filter(id__in=task_ids)

        other_users_tasks = [task for task in tasks if task.created_user != request.user.id]

        if len(other_users_tasks) > 0:
            raise PermissionDenied()
    except Task.DoesNotExist:
        messages.error(request, 'One or more tasks could not be found.')
        if device_id is None or device_id == '':
            return redirect('history')
        return redirect('device', device_id=device_id)
    except Exception as e:
        messages.error(request, f'Failed to delete selected. Error: {str(e)}')
        if device_id is None or device_id == '':
            return redirect('history')
        return redirect('device', device_id=device_id)

    for task in tasks:
        if task.status == 'completed' or task.status == 'failed':
            archive_task(task)
        elif task.status != 'pending':
            messages.error(request, f'Failed to delete selected, at least one task is already running.')
            if device_id is None or device_id == '':
                return redirect('history')
            return redirect('device', device_id=device_id)

    try:
        for task in tasks:
            if task.status != 'completed' and task.status != 'failed':
                if task.result_path is not None and task.result_path != '':
                    delete_result(task.result_path)

                task.delete()
    except FileNotFoundError as fnfe:
        messages.error(request, f'Failed to delete selected. Error: {str(fnfe)}')
        if device_id is None or device_id == '':
            return redirect('history')
        return redirect('device', device_id=device_id)

    if device_id is None or device_id == '':
        return redirect('history')
    return redirect('device', device_id=device_id)

@login_required(login_url='login')
def download_zip(request, task_id):
    try:
        relevant_task = Task.objects.get(id=task_id)
        relevant_device = Device.objects.get(id=relevant_task.device_id)

        if not request.user.has_perm(f"app.device.{relevant_device.name}.measure"):
            messages.error(request, 'Permission denied')
            return redirect('device', device_id=relevant_task.device_id)

        if relevant_task.created_user != request.user.id:
            messages.error(request, 'Permission denied')
            return redirect('device', device_id=relevant_task.device_id)

        if relevant_task.result_path is None:
            messages.error(request, 'No result found!')
            return redirect('device', device_id=relevant_task.device_id)
        path = relevant_task.result_path
        file_name = path.split('/')[-1]

        if path is None:
            messages.error(request, 'No result found!')
            return redirect('device', device_id=relevant_task.device_id)

        with open(path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/zip")
            response['Content-Disposition'] = 'inline; filename=' + file_name
            return response
    except Exception as ex:
        messages.error(request, f'Failed to download result!. {str(ex)}')
        return redirect('device', device_id=relevant_task.device_id)


def delete_result(result_path):
    try:
        if os.path.exists(result_path):
            os.remove(result_path)
        else:
            raise FileNotFoundError('Result file not found!')
    except Exception as ex:
        raise FileNotFoundError('Failed to delete result file: ' + str(ex))


@login_required(login_url='login')
def delete_task(request, task_id):
    try:
        relevant_task = Task.objects.get(id=task_id)
        device_id = relevant_task.device_id

        relevant_device = Device.objects.get(id=device_id)

        if not request.user.has_perm(f"app.device.{relevant_device.name}.measure"):
            return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)

        if relevant_task.created_user != request.user.id:
            return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)

        # Archive the task
        if relevant_task.status == 'completed' or relevant_task.status == 'failed':
            archive_task(relevant_task)
            return JsonResponse({'success': True, 'message': 'Task archived successfully!'})

        if relevant_task.status != 'pending' and relevant_task.status != 'scheduled-pending':
            return JsonResponse({'success': False, 'message': 'This task is currently running and cannot be deleted. Please refresh the page.'})

        is_edit = False

        if request.body and request.body != '':
            try:
                body = json.loads(request.body)
                if "is_edit" in body and body["is_edit"]:
                    is_edit = True
            except Exception:
                pass

        # delete result file
        if relevant_task.result_path is not None and relevant_task.result_path != '':
           delete_result(relevant_task.result_path)

        relevant_task.delete()

        if is_edit:
            messages.warning(request, 'Task removed for editing. Closing this tab will discard the task, click "Apply" or "Apply scheduled Task" to save it!')
        else:
            messages.success(request, 'Task deleted successfully!')

        return JsonResponse({'success': True, 'message': 'Task deleted successfully!'})
    except FileNotFoundError as fe:
        messages.error(request, f'{str(fe)}')
        if device_id is None:
            return JsonResponse({'success': False, 'message': str(fe)})
        return JsonResponse({'success': False, 'message': str(fe)})
    except Exception as ex:
        messages.error(request, f'Failed to delete task!. {str(ex)}')
        if device_id is None:
            return JsonResponse({'success': False, 'message': str(ex)})
        return JsonResponse({'success': False, 'message': str(ex)})


@login_required(login_url='login')
def rerun_task(request, task_id, device_id):
    try:
        device_id = int(device_id)
        relevant_task = Task.objects.get(id=task_id)
        device_name = Device.objects.get(id=device_id).name

        existing_device = Device.objects.get(id=relevant_task.device_id)

        if not request.user.has_perm(f"app.device.{existing_device.name}.measure") or not request.user.has_perm(f"app.device.{device_name}.measure"):
            return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)

        has_perm_schedule_measurements = request.user.has_perm(f"app.device.{device_name}.schedule_measurements")
        instruction = relevant_task.instruction

        if not has_perm_schedule_measurements and "is_scheduled_task" in instruction and instruction["is_scheduled_task"]:
            return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)

        if relevant_task.created_user != request.user.id:
            return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)

        # copy task and change status to pending
        new_task = Task()
        new_task.device_id = device_id
        instruction['device_name'] = device_name
        new_task.instruction = instruction

        # Remove all Tinkerforge UIDs before rerun
        for background_task in new_task.instruction["background_tasks"]["tasks"]:
            if background_task["image_name"] != "exp-bricklet-voltage-current":
                continue

            background_task["environment"] = [ variable for variable in background_task["environment"] if not variable.startswith("UID=") ]

        add_tinkerforge_uid(instruction=new_task.instruction, device_id=device_id)
        add_user_location_metadata(instruction=new_task.instruction, user_id=request.user.id, device_id=device_id)

        new_task.name = relevant_task.name
        new_task.status = 'pending'
        new_task.created_user = request.user.id
        new_task.save()
        messages.success(request, 'Task rerun successfully!')
        return JsonResponse({'success': True, 'message': f'Created new task with {relevant_task.name}!'})
    except Exception as ex:
        messages.error(request, f'Failed to rerun task!. {str(ex)}')
        return JsonResponse({'success': False, 'message': str(ex)})


@login_required(login_url='login')
def stop_task(request, task_id):
    try:
        relevant_task = Task.objects.get(id=task_id)
        device = Device.objects.get(id=relevant_task.device_id)

        if not request.user.has_perm(f"app.device.{device.name}.measure"):
            messages.error(request, 'Permission denied')
            return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)

        if relevant_task.created_user != request.user.id:
            return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)

        # reboot device to stop task
        if device.ip_address is None:
            messages.error(request, 'Device IP address is not set!')
            return JsonResponse({'success': False, 'message': 'Device IP address is not set!'})

        if not reboot_via_ssh(device.ip_address):
            # messages.error(request, 'Failed to stop task!')
            return JsonResponse({'success': False, 'message': 'Failed to stop task!'})

        messages.success(request, 'Task stopped successfully!')
        return JsonResponse({'success': True, 'message': 'Task stopped successfully!'})
    except Exception as ex:
        # messages.error(request, f'Failed to stop task!. {str(ex)}')
        return JsonResponse({'success': False, 'message': str(ex)})

def add_tinkerforge_uid(instruction, device_id):
        device = Device.objects.get(id=device_id)

        # Get device UID for every energy measurement
        for task in instruction["background_tasks"]["tasks"]:
            if task["image_name"] != "exp-bricklet-voltage-current":
                continue

            environment = task["environment"]
            has_uid = any(variable.startswith("UID=") for variable in environment)

            new_environment = []

            if has_uid:
                new_environment = environment
            else:
                for variable in environment:
                    if variable.startswith("TF_DEVICE="):
                        tf_device = variable.removeprefix("TF_DEVICE=")

                        if tf_device == "Raspberry Pi":
                            tf_uid = device.tf_uid
                        else:
                            energy_modem = Modem.objects.get(device_id=device_id, name=tf_device)
                            tf_uid = energy_modem.tf_uid

                        new_environment.append(f"UID={tf_uid}")

                    new_environment.append(variable)

            task["environment"] = new_environment

def add_user_location_metadata(instruction, user_id, device_id):
    # Add metadata:
    # User who started the measurement
    user = User.objects.get(id=user_id)
    instruction["user"] = user.username

    # Location of the device
    device = Device.objects.get(id=device_id)
    instruction["location"] = device.location
