# this script is used to run the job on a measurement node
# every x seconds, it will check the job queue and run the job if there is any
# Jobs are stored in the database
# Next job to run is determined by the job status, job creation time, job assignment (by device id)
# it will also update the status accordingly and set the start time
# after finishing the job, the result will be uploaded to the server
# and the result path will be updated in the database as well as the status and end time
import json
import os
import requests

from random import randint
from time import sleep

import sys
sys.path.append("/home/ubuntu/mark")

from core.utils_api import API_URL, REQUEST_HEADERS, REQUEST_HEADERS_NO_JSON, REQUEST_TIMEOUT

from measurement_exec import MeasurementExec
import job_helper

from operator_scan_runner import run_operator_scan

from watchdog.docker_cleanup import docker_cleanup

from dotenv import load_dotenv

load_dotenv(dotenv_path="/home/ubuntu/mark/.env.server")
load_dotenv(dotenv_path="/home/ubuntu/mark/.env.device")


DEVICE_ID = os.getenv("DEVICE_ID")
GPS_UID = os.getenv("GPS_UID")


def get_next_task():
    response = requests.post(f"{API_URL}/start_next_task/", headers=REQUEST_HEADERS, verify=False, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.json()


def upload_result(id, result_path, status):
    try:
        job_helper.log(f"Uploading result to server.")
        home_path = os.getcwd()
        # first archive the result folder
        result_path = os.path.join(home_path, result_path)
        archive_status = job_helper.archive_folder(result_path, result_path)
        if not archive_status:
            raise Exception()
    except Exception as ex:
        job_helper.log(f"Unable to archive result. Skipping copying to server. See logs for more information.")
        return False

    try:
        archive_path = result_path + '.zip'

        files = {
            "metadata": ("metadata", json.dumps({ "id": id, "status": status }), "application/json"),
            "result": ("result.zip", open(archive_path, "rb"), "application/zip")
        }
        response = requests.post(f"{API_URL}/upload_task_result/", headers=REQUEST_HEADERS_NO_JSON, files=files, verify=False, timeout=5*60)
        response.raise_for_status()
        return True
    except Exception as ex:
        job_helper.log(f"Unable to copy result to server. Error: {ex}")
        job_helper.remove_file(archive_path)
        return False

def process_job():
    task_id = None

    try:
        task = get_next_task()
        job = task["job"]

        if job is None:
            has_upcoming_scheduled_task = task["has_upcoming_scheduled_task"]

            if not has_upcoming_scheduled_task:
                # no measurement in queue -> time to scan for operators
                run_operator_scan()

            return

        task_id = task["id"]
        scheduled_task_late = task["scheduled_task_late"]

        # set task status to running
        task_status = 'running'

        job_helper.log(f"Processing job {task_id}.")
        measurement_exec = MeasurementExec(
            job, task_id, GPS_UID
        )
        result_path, status = measurement_exec.run(scheduled_task_late)

        if result_path is None:
            raise ValueError(
                f"Measurement failed. ID: {task_id}. Experiment data removed. If you want to keep the data, set always_save_logs to true.")

        # set task status to completed
        if status:
            task_status = 'completed'
        else:
            task_status = 'failed'

        upload_status = upload_result(task_id, result_path, task_status)

        if upload_status:
            # If the result was uploaded successfully, delete the local copy
            home_path = os.getcwd()
            data_path = os.path.join(home_path, result_path)
            job_helper.remove_folder(data_path)
            job_helper.remove_file(data_path + '.zip')
        else:
            # Otherwise, move the result to failed or success folder
            home_path = os.getcwd()
            if status:
                # move to success folder
                job_helper.move_folder(os.path.join(home_path, result_path), os.path.join(home_path, 'logs/success'))
            else:
                # move to failed folder
                job_helper.move_folder(os.path.join(home_path, result_path), os.path.join(home_path, 'logs/failed'))
            raise ValueError(f"Unable to copy result to server.")

    except Exception as ex:
        task_status = 'failed'
        job_helper.log(f"Error while processing job: {ex}")

    if task_id is not None:
        job_helper.log(f"Job {task_id} finished.")

        # if the task failed, reboot the device
        if task_status == 'failed':
            job_helper.log(f"Rebooting the device in 5 seconds.")
            sleep(5)
            job_helper.log(f"-" * 50)
            os.system("sudo reboot now")
            return

    job_helper.log(f"-" * 50)
    # sleep for 30 seconds before checking for the next job in the queue
    # this is to avoid the device running the job too frequently and to give time for the device to close everything properly
    sleep(30)
    job_helper.log(f"Checking for the next job in the queue after cleaning up.")
    docker_cleanup()
    process_job()


def check_existing_logs(result_path):
    try:
        home_path = os.getcwd()
        processing_path = os.path.join(home_path, result_path)

        if os.path.exists(processing_path) and len(os.listdir(processing_path)) > 0:
            # Foreach folder in processing folder
            # Archive the folder as a .zip and upload it to the server
            # If the upload was successful, remove the zip and the folder
            # Else, save the measurement in the critical folder

            for folder in os.listdir(processing_path):
                folder_path = os.path.join(processing_path, folder)

                if os.path.isdir(folder_path):
                    task_id = folder.split('_')[1]

                    if 'processing' in result_path or 'failed' in result_path:
                        task_status = 'failed'
                    else:
                        task_status = 'completed'

                    file_upload_status = upload_result(task_id, f"{result_path}/{folder}", task_status)

                    # remove the zip and the folder
                    if file_upload_status:
                        job_helper.remove_folder(folder_path)
                        job_helper.remove_file(folder_path + '.zip')
                    else:
                        job_helper.move_folder(folder_path, os.path.join(home_path, 'logs/critical'))
                        job_helper.remove_file(folder_path + '.zip')
                        job_helper.log(
                            f"Unable to upload {folder} to the server. Moving to critical folder. Please check the logs for more information.")

            job_helper.log(f"--------------------------------------------------")
        return True
    except Exception as ex:
        job_helper.log(f"Unable to check existing logs from {result_path}. Error: {ex}")
        return False


def synchronize_folders():
    # check if the is a measurement in processing folder. If so try to upload it to the server or move it to failed
    sync_status = check_existing_logs('logs/processing')
    if not sync_status:
        job_helper.log(
            f"Unable to synchronize logs from processing folder. Please check the logs for more information.")
    sync_status = check_existing_logs('logs/failed')
    if not sync_status:
        job_helper.log(f"Unable to synchronize logs from failed folder. Please check the logs for more information.")
    sync_status = check_existing_logs('logs/success')
    if not sync_status:
        job_helper.log(f"Unable to synchronize logs from success folder. Please check the logs for more information.")


if __name__ == "__main__":
    try:
        # Sleep for a random time between 0 and 60 seconds to avoid all devices running the job at the same time
        sleep(randint(0, 60))

        # synchronize folders
        synchronize_folders()

        # run the job
        process_job()
    except Exception as e:
        job_helper.log(e)
        exit(1)
