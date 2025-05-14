from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.http import JsonResponse
from django.utils import timezone
from django.utils.crypto import get_random_string

import json
import os
import re

from datetime import datetime, date, timedelta

from rest_framework import status as http_status
from rest_framework.decorators import api_view

from dotenv import load_dotenv
load_dotenv()

REGISTRATION_KEY = os.getenv('REGISTRATION_KEY')

from ..models import Device, DeviceImage, DockerImage, Modem, Task


@api_view(['POST'])
def register_device(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'GET not supported'}, status=400)

    supplied_registration_key = request.headers.get('X-Registration-Key')

    if supplied_registration_key is None or supplied_registration_key == "":
        return JsonResponse({'success': False, 'message': 'Missing X-Registration-Key header'}, status=400)

    if supplied_registration_key != REGISTRATION_KEY:
        return JsonResponse({'success': False, 'message': 'Invalid registration key'}, status=401)

    ip_address = request.data.get('ip_address')

    if ip_address is None:
        return JsonResponse({'success': False, 'message': 'Missing IP address'}, status=400)

    # get all devices from database and get the name. Example: Mark-1, Mark-2, ...
    existing_devices = Device.objects.all()

    new_device_name = "Mark-1"
    new_device_number = 1

    # extract the highest number and increment it by 1
    for existing_device in existing_devices:
        existing_device_name = existing_device.name
        match = re.match(r"(\D*)(\d+)$", existing_device_name)

        if match is None:
            continue

        existing_device_prefix = match.group(1)
        existing_device_number_str = match.group(2)
        existing_device_number = int(existing_device_number_str)

        if existing_device_number + 1 > new_device_number:
            new_device_number = existing_device_number + 1
            new_device_name = f"{existing_device_prefix}{new_device_number}"

    new_device = Device()
    new_device.name = new_device_name
    new_device.location = "University of Würzburg"
    new_device.status = "online"
    new_device.last_checkin = timezone.now()
    new_device.ip_address = ip_address
    new_device.api_key = get_random_string(length=64)
    new_device.save()

    content_type = ContentType.objects.get_for_model(Device)
    permission_measure = Permission.objects.create(
        codename=f"device.{new_device_name}.measure",
        name=f"Create measurements on {new_device_name}",
        content_type=content_type
    )
    permission_measure.save()

    permission_schedule_measurements = Permission.objects.create(
        codename=f"device.{new_device_name}.schedule_measurements",
        name=f"Schedule measurements on {new_device_name}",
        content_type=content_type
    )
    permission_schedule_measurements.save()

    permission_upload_docker_images = Permission.objects.create(
        codename=f"device.{new_device_name}.upload_docker_images",
        name=f"Upload docker images on {new_device_name}",
        content_type=content_type
    )
    permission_upload_docker_images.save()

    return JsonResponse({'success': True, 'device_id': new_device.id, 'api_key': new_device.api_key})


@api_view(['GET', 'POST'])
def modems(request):
    api_key = request.headers.get('X-API-KEY')

    if api_key is None or api_key == "":
        return JsonResponse({'success': False, 'message': 'Missing X-API-KEY header'}, status=400)

    try:
        device = Device.objects.get(api_key=api_key)
    except Device.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Invalid API key'}, status=401)

    try:
        if request.method == 'GET':
            modems = [{
                'name': modem.name,
                'port': modem.port,
                'ability': modem.ability,
                'operators': modem.operators
            } for modem in Modem.objects.filter(device=device)]

            return JsonResponse({'success': True, 'modems': modems})
        elif request.method == 'POST':
            if not isinstance(request.data, list):
                return JsonResponse({'success': False, 'message': 'List of modems expected'}, status=400)

            for modem in request.data:
                if not "name" in modem:
                    return JsonResponse({'success': False, 'message': 'Missing name in modem object'}, status=400)

            for modem in request.data:
                try:
                    db_modem = Modem.objects.get(device=device, name=modem["name"])

                    if "port" in modem:
                        db_modem.port = modem["port"]

                    if "ability" in modem:
                        db_modem.ability = modem["ability"]

                    if "operators" in modem:
                        db_modem.operators = modem["operators"]

                    db_modem.save()
                except Modem.DoesNotExist:
                    db_modem = Modem()
                    db_modem.name = modem["name"]
                    db_modem.device = device
                    db_modem.port = modem["port"]
                    db_modem.ability = modem["ability"]

                    if "operators" in modem:
                        db_modem.operators = modem["operators"]

                    db_modem.save()

            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'message': 'Request method not supported'}, status=400)
    except Exception as ex:
        return JsonResponse({'success': False, 'error': str(ex)}, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def tinkerforge(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'GET not supported'}, status=400)

    try:
        api_key = request.headers.get('X-API-KEY')

        if api_key is None or api_key == "":
            return JsonResponse({'success': False, 'message': 'Missing X-API-KEY header'}, status=400)

        try:
            device = Device.objects.get(api_key=api_key)
        except Device.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Invalid API key'}, status=401)

        tinkerforge_device_name = request.data.get("device")

        if tinkerforge_device_name is None:
            return JsonResponse({'success': False, 'message': 'Missing Tinkerforge device name'}, status=400)

        tinkerforge_uid = request.data.get("uid")

        if tinkerforge_uid is None:
            return JsonResponse({'success': False, 'message': 'Missing Tinkerforge UID'}, status=400)

        if tinkerforge_device_name == "Raspberry_Pi":
            device.tf_uid = tinkerforge_uid
            device.save()
        else:
            try:
                modem = Modem.objects.get(device=device, name=tinkerforge_device_name)
                modem.tf_uid = tinkerforge_uid
                modem.save()
            except Modem.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Modem not found'}, status=404)

        return JsonResponse({'success': True})
    except Exception as ex:
        return JsonResponse({'success': False, 'error': str(ex)}, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def docker_images(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'GET not supported'}, status=400)

    try:
        api_key = request.headers.get('X-API-KEY')

        if api_key is None or api_key == "":
            return JsonResponse({'success': False, 'message': 'Missing X-API-KEY header'}, status=400)

        try:
            device = Device.objects.get(api_key=api_key)
        except Device.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Invalid API key'}, status=401)

        if not isinstance(request.data, list):
            return JsonResponse({'success': False, 'message': 'List of Docker images expected'}, status=400)

        required_fields = ['name', 'label', 'output_type', 'measurement_type', 'active', 'is_public']

        for image in request.data:
            for required_field in required_fields:
                if not required_field in image or image[required_field] is None:
                        return JsonResponse({'success': False, 'message': f'At leat one docker image is missing the required {required_field} property'}, status=400)

        for image in request.data:
            name = image.get('name')
            label = image.get('label')
            output_type = image.get('output_type')
            output_file = image.get('output_file')
            if output_file is None:
                output_file = ""
            measurement_type = image.get('measurement_type')
            active = image.get('active')
            is_public = image.get('is_public')
            env_schema = image.get('env_schema')

            try:
                existing_image = DockerImage.objects.get(name=name)
            except DockerImage.DoesNotExist:
                existing_image = DockerImage()
                existing_image.name = name

            existing_image.label = label
            existing_image.output_type = output_type
            existing_image.output_file = output_file
            existing_image.measurement_type = measurement_type
            existing_image.active = active
            existing_image.is_public = is_public
            existing_image.env_schema = env_schema
            existing_image.save()

            existing_device_images = DeviceImage.objects.filter(device=device, image=existing_image)

            if len(existing_device_images) == 0:
                existing_device_image = DeviceImage()
                existing_device_image.device = device
                existing_device_image.image = existing_image
                existing_device_image.save()

        return JsonResponse({'success': True})
    except Exception as ex:
        return JsonResponse({'success': False, 'error': str(ex)}, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def health_check(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'GET not supported'}, status=400)

    try:
        api_key = request.headers.get('X-API-KEY')

        if api_key is None or api_key == "":
            return JsonResponse({'success': False, 'message': 'Missing X-API-KEY header'}, status=400)

        try:
            device = Device.objects.get(api_key=api_key)
        except Device.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Invalid API key'}, status=401)

        message = request.data.get('message')
        data_status = request.data.get('status')

        # If device is in maintenance mode, do not update status
        if device.status == 'maintenance':
            if data_status == 'maintenance':
                device.status_message += f"\n{message}"
            device.last_checkin = timezone.now()
            device.save()
            return JsonResponse({'success': True, 'message': 'Device is in maintenance mode.'}, status=http_status.HTTP_200_OK)

        # Update device status and last check-in time
        device.status = data_status
        device.last_checkin = timezone.now()
        device.status_message = message
        # Save changes to database
        device.save()

        # Return a success message
        return JsonResponse({'success': True, 'message': 'Successfully updated.'}, status=http_status.HTTP_200_OK)
    except Exception as ex:
        return JsonResponse({'success': False, 'error': str(ex)}, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)


def get_next_task_user(device_id):
    """
    For creating a round robin algorithm, we need to get the next user to assign the task to.
    The next user is determined
    :return: The next user to assign the task to or None if there are no users with pending tasks
    """

    with connection.cursor() as cursor:
        # users with tasks
        query_users = '''
        SELECT DISTINCT created_user, MAX(completed_at) AS completed_at
        FROM task WHERE device_id = %s AND created_user IN (
            SELECT created_user FROM task AS t2
            WHERE t2.status = 'pending' AND device_id = %s)
        GROUP BY created_user
        '''

        # run the query
        cursor.execute(query_users, [device_id, device_id])
        result = cursor.fetchall()
        # if there are no users with tasks, return None
        if result is None or len(result) == 0:
            return None

        # handle user with no completed tasks
        for user in result:
            if user[1] is None:
                return user[0]

        # get the user with the oldest completed task
        user = min(result, key=lambda x: x[1])
        return user[0]


def get_result_path(task, device, user):
    results_folder = os.getenv('RESULTS_FOLDER')

    # Get the current year and month
    date_today = date.today()
    year = date_today.year
    month = date_today.month

    if month < 10:
        month = "0" + str(month)

    user_name = user.username
    device_name = device.name

    task_start_time = task.started_at.strftime("%Y%m%d%H%M%S")
    task_id = task.id

    # ../year/month/user_name/device_name/id.zip
    return f"{results_folder}/{str(year)}/{month}/{user_name}/{device_name}/{task_start_time}_{task_id}.zip"


@api_view(['POST'])
def start_next_task(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'GET not supported'}, status=400)

    try:
        api_key = request.headers.get('X-API-KEY')

        if api_key is None or api_key == "":
            return JsonResponse({'success': False, 'message': 'Missing X-API-KEY header'}, status=400)

        try:
            device = Device.objects.get(api_key=api_key)
        except Device.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Invalid API key'}, status=401)

        # get the next user to assign the task to
        next_user = get_next_task_user(device.id)

        if next_user is None:
            return JsonResponse({'success': True, 'job': None, 'has_upcoming_scheduled_task': False})

        tasks = Task.objects.filter(status='pending', device=device, created_user=next_user).order_by('-created_at')

        if tasks is None or len(tasks) == 0:
            return JsonResponse({'success': True, 'job': None, 'has_upcoming_scheduled_task': False})

        # Check whether there is a scheduled task that is due. Take the task with the earliest date.
        task_information = None
        final_task_id = None
        final_result = None
        final_date_scheduled = date.today()
        final_time_scheduled = datetime.now().time()

        # When this is true, the operator scan will be skipped
        has_upcoming_scheduled_task = False

        for task in tasks:
            task_id = task.id
            instruction = task.instruction

            if 'is_scheduled_task' in instruction and instruction['is_scheduled_task']:
                date_scheduled = instruction['scheduled_task_date_time']['date']
                date_scheduled = datetime.strptime(date_scheduled, '%Y-%m-%d').date()

                time_scheduled = instruction['scheduled_task_date_time']['time']
                time_scheduled = datetime.strptime(time_scheduled, '%H:%M').time()

                datetime_now = datetime.now()
                datetime_scheduled = datetime.combine(date_scheduled, time_scheduled)

                if datetime_scheduled >= datetime_now and datetime_scheduled - datetime_now <= timedelta(hours=1):
                    has_upcoming_scheduled_task = True

                if date_scheduled < final_date_scheduled or date_scheduled == final_date_scheduled and time_scheduled <= final_time_scheduled:
                    task_information = task
                    final_task_id = task_id
                    final_result = instruction
                    final_date_scheduled = date_scheduled
                    final_time_scheduled = time_scheduled

        # Check whether the scheduled task is late
        scheduled_task_late = False
        if final_task_id is not None:
            date_now = date.today()
            time_now = datetime.now().time()
            datetime_now = datetime.combine(date_now, time_now)

            date_scheduled = final_result['scheduled_task_date_time']['date']
            date_scheduled = datetime.strptime(date_scheduled, '%Y-%m-%d').date()

            time_scheduled = final_result['scheduled_task_date_time']['time']
            time_scheduled = datetime.strptime(time_scheduled, '%H:%M').time()

            datetime_scheduled = datetime.combine(date_scheduled, time_scheduled)

            if datetime_now - datetime_scheduled > timedelta(minutes=8):
                scheduled_task_late = True

        # Check whether there is a task that is not scheduled.
        if final_task_id is None:
            for task in tasks:
                task_id = task.id
                instruction = task.instruction
                if 'is_scheduled_task' not in instruction or not instruction['is_scheduled_task']:
                    final_task_id = task_id
                    final_result = instruction

        # If it is a repeating task, check whether a new task should be inserted into the database.
        if final_task_id is not None and 'repeat_scheduled_task' in final_result and final_result['repeat_scheduled_task'] != 'never':
            final_date_time_scheduled = datetime.combine(final_date_scheduled, final_time_scheduled)

            days = 0
            hours = 0
            minutes = 0
            if final_result['repeat_scheduled_task'] == '15-minutes':
                minutes = 15
            elif final_result['repeat_scheduled_task'] == '30-minutes':
                minutes = 30
            elif final_result['repeat_scheduled_task'] == 'hour':
                hours = 1
            elif final_result['repeat_scheduled_task'] == '2-hours':
                hours = 2
            elif final_result['repeat_scheduled_task'] == '4-hours':
                hours = 4
            elif final_result['repeat_scheduled_task'] == '6-hours':
                hours = 6
            elif final_result['repeat_scheduled_task'] == '8-hours':
                hours = 8
            elif final_result['repeat_scheduled_task'] == '12-hours':
                hours = 12
            elif final_result['repeat_scheduled_task'] == 'day':
                days = 1
            elif final_result['repeat_scheduled_task'] == '2-days':
                days = 2
            elif final_result['repeat_scheduled_task'] == 'week':
                days = 7

            new_final_date_time_scheduled = final_date_time_scheduled + timedelta(days=days, hours=hours,
                                                                                  minutes=minutes)
            new_final_date_scheduled = new_final_date_time_scheduled.date()
            new_final_time_scheduled = new_final_date_time_scheduled.time()

            insert_task = False
            increment_repetition_count = False
            if final_result['end_repetition_scheduled_task'] == 'on_date_and_time':
                date_end_repetition = final_result['end_repetition_scheduled_task_date_time']['date']
                date_end_repetition = datetime.strptime(date_end_repetition, '%Y-%m-%d').date()

                time_end_repetition = final_result['end_repetition_scheduled_task_date_time']['time']
                time_end_repetition = datetime.strptime(time_end_repetition, '%H:%M').time()
                if new_final_date_scheduled < date_end_repetition or new_final_date_scheduled == date_end_repetition and new_final_time_scheduled <= time_end_repetition:
                    insert_task = True
            elif final_result['end_repetition_scheduled_task'] == 'num_repetitions':
                if final_result['end_repetition_scheduled_task_repetition_count'] < final_result['end_repetition_scheduled_task_num_repetitions']:
                    insert_task = True
                    increment_repetition_count = True
            else:
                insert_task = True

            if insert_task and task_information is not None:
                inserted_task_instruction = task_information.instruction

                inserted_task_instruction['scheduled_task_date_time']['date'] = str(new_final_date_scheduled)
                inserted_task_instruction['scheduled_task_date_time']['time'] = new_final_time_scheduled.strftime('%H:%M')

                if increment_repetition_count:
                    inserted_task_instruction['end_repetition_scheduled_task_repetition_count'] += 1

                inserted_task = Task()
                inserted_task.device = device
                inserted_task.instruction = inserted_task_instruction
                inserted_task.name = task_information.name
                inserted_task.status = task_information.status
                inserted_task.created_at = datetime.now()
                inserted_task.created_user = task_information.created_user
                inserted_task.save()

        if final_task_id is None:
            return JsonResponse({'success': True, 'job': None, 'has_upcoming_scheduled_task': has_upcoming_scheduled_task})

        final_task = Task.objects.get(id=final_task_id)
        final_task.status = 'running'
        final_task.started_at = timezone.now()
        final_task.save()

        return JsonResponse({
            'success': True, 'job': final_result, 'id': final_task_id,
            'scheduled_task_late': scheduled_task_late, 'has_upcoming_scheduled_task': has_upcoming_scheduled_task
        })
    except Exception as ex:
        return JsonResponse({'success': False, 'error': str(ex)}, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def upload_task_result(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'GET not supported'}, status=400)

    try:
        api_key = request.headers.get('X-API-KEY')

        if api_key is None or api_key == "":
            return JsonResponse({'success': False, 'message': 'Missing X-API-KEY header'}, status=400)

        try:
            device = Device.objects.get(api_key=api_key)
        except Device.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Invalid API key'}, status=401)

        if not 'metadata' in request.FILES or not 'result' in request.FILES:
            return JsonResponse({'success': False, 'message': 'Missing metadata or result'}, status=400)

        metadata = json.load(request.FILES.get('metadata'))

        if not 'id' in metadata or not 'status' in metadata:
            return JsonResponse({'success': False, 'message': 'Missing id or status in metadata'}, status=400)

        id = metadata["id"]
        status = metadata["status"]

        if status != 'completed' and status != 'failed':
            return JsonResponse({'success': False, 'message': 'Invalid target status'}, status=400)

        try:
            task = Task.objects.get(id=id)
        except Task.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Task not found'}, status=404)

        if task.device != device:
            return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)

        if task.status != 'running':
            return JsonResponse({'success': False, 'message': 'Measurement not running yet or already completed'}, status=400)

        try:
            user = User.objects.get(id=task.created_user)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'User not found'}, status=404)

        result_path = get_result_path(task, device, user)
        result_zip = request.FILES.get('result')

        try:
            os.makedirs(os.path.dirname(result_path), exist_ok=True)

            with open(result_path, "wb+") as result_file:
                for chunk in result_zip.chunks():
                    result_file.write(chunk)
        except Exception as ex:
            print(f"Error saving result: {ex}")

        task.status = status
        task.result_path = result_path
        task.completed_at = timezone.now()
        task.save()

        return JsonResponse({'success': True}, status=200)
    except Exception as ex:
        return JsonResponse({'success': False, 'error': str(ex)}, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)
