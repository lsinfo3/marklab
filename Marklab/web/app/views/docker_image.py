from datetime import datetime
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect
from django.urls import reverse

from ..models import Device, DockerImage, DeviceImage

from ..forms import UploadFileForm

from ..services import delete_docker_image


@login_required(login_url='login')
def images(request, device_id):
    relevant_device = Device.objects.get(id=device_id)

    if not request.user.has_perm(f"app.device.{relevant_device.name}.measure"):
        raise PermissionDenied()

    has_perm_upload_docker_images = request.user.has_perm(f"app.device.{relevant_device.name}.upload_docker_images")

    device_image_ids = DeviceImage.objects.filter(device_id=device_id).values_list('image_id', flat=True)
    docker_images = DockerImage.objects.filter(
        id__in=device_image_ids
    )

    user_images = docker_images.filter(user_id=request.user.id)
    public_images = docker_images.exclude(user_id=request.user.id).filter(is_public=True)

    # order by measurement type and then by name
    user_images = sorted(user_images, key=lambda x: (x.measurement_type, x.name))
    public_images = sorted(public_images, key=lambda x: (x.measurement_type, x.name))

    form = UploadFileForm()

    return render(request, 'docker_images.html',
                  {'device': relevant_device, 'user_images': user_images, 'public_images': public_images, 'form': form, 'has_perm_upload_docker_images': has_perm_upload_docker_images})


@login_required(login_url='login')
def delete_image(request, image_id, device_id):
    relevant_device = Device.objects.get(id=device_id)

    if not request.user.has_perm(f"app.device.{relevant_device.name}.measure") or not request.user.has_perm(f"app.device.{relevant_device.name}.upload_docker_images"):
        raise PermissionDenied()

    try:
        image = DockerImage.objects.get(id=image_id)
        if image.user_id != request.user.id:
            raise PermissionDenied('You are not authorized to delete this image!')

        # remove docker image from device
        device_image = DeviceImage.objects.filter(device_id=device_id, image_id=image_id)

        if not device_image.exists():
            raise Exception('Image not found on device!')

        delete_docker_image(relevant_device, image.name)
        device_image.delete()
        image.delete()
        messages.success(request, f'Image {image.name} deleted successfully!')
    except Exception as e:
        messages.error(request, f'Failed to delete image! {str(e)}')

    return redirect(reverse('docker_image', kwargs={'device_id': device_id}))


@login_required(login_url='login')
def reactivate_image(request, image_id, device_id):
    relevant_device = Device.objects.get(id=device_id)

    if not request.user.has_perm(f"app.device.{relevant_device.name}.measure") or not request.user.has_perm(f"app.device.{relevant_device.name}.upload_docker_images"):
        raise PermissionDenied()

    try:
        image = DockerImage.objects.get(id=image_id)
        if image.user_id != request.user.id:
            raise PermissionDenied('You are not authorized to reactivate this image!')

        image.active = True
        image.change_at = datetime.now()
        image.save()
        messages.success(request, f'Image {image.name} reactivated successfully!')
    except Exception as e:
        messages.error(request, f'Failed to reactivate image! {str(e)}')

    return redirect(reverse('docker_image', kwargs={'device_id': device_id}))


@login_required(login_url='login')
def deactivate_image(request, image_id, device_id):
    relevant_device = Device.objects.get(id=device_id)

    if not request.user.has_perm(f"app.device.{relevant_device.name}.measure") or not request.user.has_perm(f"app.device.{relevant_device.name}.upload_docker_images"):
        raise PermissionDenied()

    try:
        image = DockerImage.objects.get(id=image_id)
        if image.user_id != request.user.id:
            raise PermissionDenied('You are not authorized to deactivate this image!')

        image.active = False
        image.change_at = datetime.now()
        image.save()
        messages.success(request, f'Image {image.name} deactivated successfully!')
    except Exception as e:
        messages.error(request, f'Failed to deactivate image! {str(e)}')

    return redirect(reverse('docker_image', kwargs={'device_id': device_id}))


@login_required(login_url='login')
def publish_image(request, image_id, device_id):
    relevant_device = Device.objects.get(id=device_id)

    if not request.user.has_perm(f"app.device.{relevant_device.name}.measure") or not request.user.has_perm(f"app.device.{relevant_device.name}.upload_docker_images"):
        raise PermissionDenied()

    try:
        image = DockerImage.objects.get(id=image_id)
        if image.user_id != request.user.id:
            raise PermissionDenied('You are not authorized to publish this image!')

        image.is_public = True
        image.change_at = datetime.now()
        image.save()
        messages.success(request, f'Image {image.name} published successfully!')
    except Exception as e:
        messages.error(request, f'Failed to publish image! {str(e)}')

    return redirect(reverse('docker_image', kwargs={'device_id': device_id}))


@login_required(login_url='login')
def hide_image(request, image_id, device_id):
    relevant_device = Device.objects.get(id=device_id)

    if not request.user.has_perm(f"app.device.{relevant_device.name}.measure") or not request.user.has_perm(f"app.device.{relevant_device.name}.upload_docker_images"):
        raise PermissionDenied()

    try:
        image = DockerImage.objects.get(id=image_id)
        if image.user_id != request.user.id:
            raise PermissionDenied('You are not authorized to hide this image!')

        image.is_public = False
        image.change_at = datetime.now()
        image.save()
        messages.success(request, f'Image {image.name} unpublished successfully!')
    except Exception as e:
        messages.error(request, f'Failed to unpublish image! {str(e)}')

    return redirect(reverse('docker_image', kwargs={'device_id': device_id}))
