import docker
import os
import paramiko
import re
import shutil
import socket

from datetime import datetime
from zipfile import ZipFile

from dotenv import load_dotenv
load_dotenv()

DEVICE_USERNAME = os.getenv('DEVICE_USERNAME')
DEVICE_PASSWORD = os.getenv('DEVICE_PASSWORD')


# region general
def convert_time_to_readable(last_checkin):
    time_since_checkin = datetime.now() - last_checkin
    time_since_checkin = time_since_checkin.total_seconds()
    if time_since_checkin > 3600:
        # convert to integer
        time_since_checkin = int(time_since_checkin)
        time_since_checkin = f'{time_since_checkin // 3600} hour(s) ago'
    else:
        time_since_checkin = int(time_since_checkin)
        time_since_checkin = f'{time_since_checkin // 60} minutes ago'
    return time_since_checkin

device_name_pattern = re.compile(r"(\D*)(\d+)$")

def device_sort_comparison(device):
    match = device_name_pattern.match(device.name)

    if match is None:
        return ("", 0, device.id)
    else:
        return (match.group(1), int(match.group(2)), device.id)

def get_devices_sorted_by_name(devices):
    return sorted(devices, key=device_sort_comparison)
# endregion


# region Device
def handle_zip_file(file):
    try:
        # extract zip file
        with ZipFile(file, 'r') as zip_file:
            if len(zip_file.filelist) == 0:
                raise ValueError("ZIP archive empty")

            # Top level Dockerfile
            if "Dockerfile" in zip_file.namelist():
                output_path = "temp/" + file.name.removesuffix(".zip")
                zip_file.extractall(output_path)
                return output_path

            # Find top level directories
            top_level_directories = {
                file_name.split("/")[0] for file_name in zip_file.namelist()
                if "/" in file_name and not file_name.startswith("__MACOSX")
            }
            if len(top_level_directories) == 0:
                raise ValueError("No Dockerfile and no directories found in ZIP archive")
            elif len(top_level_directories) > 1:
                raise ValueError(f"Multiple top level directories found in ZIP archive: {top_level_directories}")

            zip_file.extractall("temp")
            return "temp/" + next(iter(top_level_directories))
    except Exception as ex:
        raise ValueError(f"Failed to extract ZIP archive. Error: {ex}")


def contains_dockerfile(folder_path):
    for root, dirs, files in os.walk(folder_path):
        if "Dockerfile" in files:
            return True
    return False


def deploy_dockerfile(dir, device, tag):
    upload_status = False
    message = ''
    try:
        # deploy dockerfiles to device
        client = docker.DockerClient(base_url=f"ssh://{DEVICE_USERNAME}@{device.ip_address}")

        if client is None:
            raise ValueError('Failed to connect to device!')

        if not client.ping():
            raise ValueError('Failed to connect to device!')

        # check if Dockerfile exists
        if not contains_dockerfile(dir):
            raise ValueError('Dockerfile not found!')

        # build docker image
        image, build_logs = client.images.build(path=dir, tag=tag, rm=True)
        # check if image is built
        if image is None:
            raise ValueError('Failed to build docker image! \n' + build_logs)

        upload_status = True
    except Exception as ex:
        upload_status = False
        message = f"Failed to deploy dockerfiles to device. Error: {ex}"
    finally:
        # remove temp folder
        try:
            shutil.rmtree(dir)
        except Exception as ex:
            message += f"\nFailed to remove temp folder. Error: {ex}\nAvailable files: "
            message += str(os.listdir("temp"))

    return upload_status, message


def delete_docker_image(device, tag):
    upload_status = False
    message = ''
    try:
        # deploy dockerfiles to device
        client = docker.DockerClient(base_url=f"ssh://{DEVICE_USERNAME}@{device.ip_address}")
        if client is None:
            message = 'Failed to connect to device!'
            raise ValueError('Failed to connect to device!')

        if not client.ping():
            message = 'Failed to connect to device!'
            raise ValueError('Failed to connect to device!')

        # remove docker image
        client.images.remove(image=tag, force=True)
        upload_status = True
    except Exception as ex:
        upload_status = False
        message = f"Failed to delete docker image from device. Error: {ex}"
    finally:
        return upload_status, message


def reboot_via_ssh(ip, username=DEVICE_USERNAME, password=DEVICE_PASSWORD, port=22):
    with paramiko.SSHClient() as ssh:
        ssh.load_system_host_keys()

        try:
            ssh.connect(ip, username=username, password=password, port=port)
            stdin, stdout, stderr = ssh.exec_command("sudo reboot", get_pty=True)
            stdin.write(f"{password}\n")
            stdin.flush()
            return stdout.channel.recv_exit_status() == 0
        except Exception as e:
            # rethrow exception
            raise ValueError(f"Failed to reboot device. Error: {e}")

# endregion
