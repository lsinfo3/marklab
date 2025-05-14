import sys
sys.path.append("/home/ubuntu/mark/watchdog")

from docker_api import DockerAPI
from watchdog_utils import log


def docker_cleanup():
    try:
        docker_container_checker = DockerAPI()
        existing_containers = docker_container_checker.get_existing_containers(all=True)

        for cont in existing_containers:
            status = cont.status
            if status == 'running':
                docker_container_checker.stop_container(cont.name)
                status = docker_container_checker.get_container_status(cont.name)

            if status == 'exited' or status == 'created':
                docker_container_checker.remove_container(cont.name)
    except Exception as ex:
        raise ValueError(ex)


if __name__ == '__main__':
    try:
        docker_cleanup()
    except Exception as e:
        log(f"Error while checking containers: {e}", "docker_cleanup.log")
        exit(1)
