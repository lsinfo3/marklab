import docker
import sys
from datetime import datetime


class DockerAPI:
    def __init__(self):
        self.client = docker.from_env()

    def stop_container(self, container_name):
        container = self.client.containers.get(container_name)
        container.stop()

    def remove_container(self, container_name):
        container = self.client.containers.get(container_name)
        container.remove()

    def get_container_status(self, container_name):
        container = self.client.containers.get(container_name)
        return container.status

    def get_container_id(self, container_name):
        container = self.client.containers.get(container_name)
        return container.id

    def get_container_name(self, container_id):
        container = self.client.containers.get(container_id)
        return container.name

    def get_existing_containers(self, all=False):
        return self.client.containers.list(all=all)


if __name__ == '__main__':
    # todo: logging instead of print
    threshold = 172800  # 2 days

    # get args
    args = sys.argv

    if len(args) == 2:
        if args[1].isdigit():
            threshold = int(args[1])
        else:
            print("Please provide a number (seconds) as argument")
            sys.exit(1)

    docker_container_checker = DockerAPI()
    running_containers = docker_container_checker.get_existing_containers()

    for cont in running_containers:
        start = cont.attrs['State']['StartedAt']
        start = datetime.strptime(start, '%Y-%m-%dT%H:%M:%S.%fZ')
        start = start.timestamp()

        # get current time
        now = datetime.now().timestamp()

        if (now - start) > threshold:
            print(f"Stopping container: {cont.name}. It has been running for {now - start} seconds. Threshold is {threshold} seconds.")
            docker_container_checker.stop_container(cont.name)

