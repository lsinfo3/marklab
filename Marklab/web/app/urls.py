from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import device_api, home, history, login, device, task, docker_image, user_settings


urlpatterns = [
    path('', login.login_view, name='login'),
    path('home/', home.home, name='home'),
    path('history/', history.history, name='history'),
    path('logout/', login.logout_view, name='logout'),
    path('download/<int:task_id>/', task.download_zip, name='download'),
    path('selection/', task.selection, name='selection'),
    path('device/<int:device_id>/', device.device, name='device'),
    path('device/<int:device_id>/task/', task.task, name='task'),
    path('device/<int:device_id>/run_operator_scan/', device.run_operator_scan, name='run_operator_scan'),
    path('upload/<int:device_id>/', device.upload, name='upload'),
    path('task/<int:task_id>/', task.task_detail, name='task_detail'),
    path('task/<int:task_id>/delete/', task.delete_task, name='delete_task'),
    path('task/<int:task_id>/<str:device_id>/rerun/', task.rerun_task, name='rerun_task'),
    path('task/<int:task_id>/stop/', task.stop_task, name='stop_task'),
    path('task/<int:task_id>/preview/', task.preview_task, name='preview_task'),
    path('device/<int:device_id>/docker_image/', docker_image.images, name='docker_image'),
    path('device/<int:device_id>/docker_image/<int:image_id>/delete/', docker_image.delete_image, name='delete_image'),
    path('device/<int:device_id>/docker_image/<int:image_id>/reactivate/', docker_image.reactivate_image, name='reactivate_image'),
    path('device/<int:device_id>/docker_image/<int:image_id>/deactivate/', docker_image.deactivate_image, name='deactivate_image'),
    path('device/<int:device_id>/docker_image/<int:image_id>/publish/', docker_image.publish_image, name='publish_image'),
    path('device/<int:device_id>/docker_image/<int:image_id>/hide/', docker_image.hide_image, name='hide_image'),
    path('settings/', user_settings.settings, name='settings'),
    path('settings/change_password/', user_settings.change_password, name='change_password'),
    path('settings/create_api_key/', user_settings.create_api_key, name='create_api_key'),
    path('settings/delete_api_key/', user_settings.delete_api_key, name='delete_api_key'),

    # User-facing API
    path('api/task', task.task_api, name='task_api'),

    # Device-facing API
    path('device_api/register_device/', device_api.register_device, name='device_api_register_device'),
    path('device_api/modems/', device_api.modems, name='device_api_modems'),
    path('device_api/tinkerforge/', device_api.tinkerforge, name='device_api_tinkerforge'),
    path('device_api/docker_images/', device_api.docker_images, name='device_api_docker_images'),
    path('device_api/health/', device_api.health_check, name='device_api_health'),
    path('device_api/start_next_task/', device_api.start_next_task, name='start_next_task'),
    path('device_api/upload_task_result/', device_api.upload_task_result, name='upload_task_result')
]


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
