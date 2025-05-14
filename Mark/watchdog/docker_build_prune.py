import docker

client = docker.from_env()


def remove_build_cache():
    status = client.images.prune_builds()
    return status


if __name__ == '__main__':
    # todo: integrate the possibility to check the memory
    remove_build_cache()
