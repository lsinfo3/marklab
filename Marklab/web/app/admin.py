from django.contrib import admin
from django.contrib.auth.models import Permission
from .models import Device, Modem, Task, DeviceImage, DockerImage

admin.site.register(Device)
admin.site.register(Modem)
admin.site.register(Task)
admin.site.register(DeviceImage)
admin.site.register(DockerImage)

admin.site.register(Permission)
