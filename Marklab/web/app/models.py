from django.db import models
from django.utils import timezone


class Device(models.Model):
    name = models.CharField(unique=True, max_length=255)
    location = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20)
    status_message = models.CharField(max_length=255, blank=True, null=True)
    last_checkin = models.DateTimeField(blank=True, null=True)
    ip_address = models.CharField(max_length=25, blank=True, null=True)
    tf_uid = models.CharField(max_length=30, blank=True, null=True)
    api_key = models.CharField(max_length=255)

    class Meta:
        db_table = 'device'


class DeviceImage(models.Model):
    device = models.ForeignKey(Device, models.DO_NOTHING)
    image = models.ForeignKey('DockerImage', models.DO_NOTHING)

    class Meta:
        db_table = 'device_image'


class DockerImage(models.Model):
    name = models.CharField(unique=True, max_length=255)
    label = models.CharField(max_length=255)
    output_type = models.TextField(blank=True, null=True)  # This field type is a guess.
    output_file = models.CharField(max_length=255, blank=True, null=True)
    measurement_type = models.TextField(blank=True, null=True)  # This field type is a guess.
    active = models.BooleanField(blank=True, null=True)
    user_id = models.IntegerField(blank=True, null=True)
    is_public = models.BooleanField(blank=True, null=True)
    change_at = models.DateTimeField(blank=True, null=True)
    env_schema = models.JSONField(blank=True, null=True)

    class Meta:
        db_table = 'docker_image'


class Modem(models.Model):
    name = models.CharField(max_length=255)
    port = models.CharField(max_length=25)
    device = models.ForeignKey(Device, models.DO_NOTHING)
    ability = models.CharField(max_length=255, blank=True, null=True,
                               db_comment='which RATs is supported (comma seperated)')
    tf_uid = models.CharField(max_length=30, blank=True, null=True)
    operators = models.JSONField(default={"message": "No operator scan results available yet.", "available": False})

    class Meta:
        db_table = 'modem'


class Task(models.Model):
    device = models.ForeignKey(Device, models.DO_NOTHING, blank=True, null=True)
    instruction = models.JSONField(blank=True, null=True)
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField(blank=True, null=True, default=timezone.now)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    created_user = models.IntegerField(blank=True, null=True)
    result_path = models.CharField(blank=True, null=True)

    class Meta:
        db_table = 'task'


class UserAPIKey(models.Model):
    user_id = models.IntegerField(blank=True, null=True)
    api_key = models.CharField(max_length=255)

    class Meta:
        db_table = 'user_api_key'
