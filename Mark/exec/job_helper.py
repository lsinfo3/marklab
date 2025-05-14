import os
import shutil
from datetime import datetime


def get_current_time():
    return datetime.now().strftime("%Y%m%d%H%M%S")


def log(_message):
    file = os.path.abspath(__file__)
    with open(f"{os.path.dirname(file)}/job_runner.log", "a") as f:
        f.write(f"{get_current_time()};{_message}\n")


def archive_folder(local_path, archive_path):
    """
    Archive a folder.
    :param local_path: local path of the folder to archive
    :param archive_path: local path of the archive
    :return: True if the folder was archived successfully, False otherwise
    """
    try:
        shutil.make_archive(archive_path, 'zip', local_path)
        return True
    except Exception as e:
        log(f"Error while archiving folder: {e}")
        return False


def move_folder(_source, _destination):
    try:

        if not os.path.exists(_destination):
            os.makedirs(_destination)

        shutil.move(_source, _destination)
        return True
    except Exception as ex:
        log(f"Unable to move folder. Error: {ex}")
        return False


def remove_folder(_path):
    try:
        shutil.rmtree(_path)
        return True
    except Exception as ex:
        log(f"Unable to remove folder. Error: {ex}")
        return False


def remove_file(_path):
    try:
        os.remove(_path)
        return True
    except Exception as ex:
        log(f"Unable to remove file. Error: {ex}")
        return False
