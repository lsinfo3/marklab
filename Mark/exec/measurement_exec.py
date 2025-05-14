import shutil
import subprocess
import docker
import os
import json

from datetime import datetime
from time import sleep
from experiment_logger import ExperimentLogger as Logger
from find_modem_port import find_modem_port

class MeasurementExec:
    def __init__(
        self, instruction, measurement_id, gps_uid=None
    ):
        self.instruction = instruction
        self.measurement_id = measurement_id
        self.start_time = self.get_current_time()
        self.modem = self.instruction.get('modem')
        self.modem_port = self.instruction.get('modem_port')
        self.modem_iot = self.instruction.get('modem_iot', False)
        self.result_path = f"logs/processing/{self.start_time}_{self.measurement_id}"
        self.create_directory(self.result_path)
        self.logger = Logger(self.instruction.get('experiment_name'), self.instruction.get('device_name'),
                             self.instruction.get('modem'),
                             f"{self.result_path}/{self.instruction.get('experiment_name')}.log")
        self.client = docker.from_env()
        self.device_name = self.instruction.get('device_name')
        self.running_bg_containers = []
        self.running_bg_later_containers = []
        self.always_save_logs = self.instruction.get('always_save_logs', True)
        self.interface = None
        self.ip_host = None
        self.status = True
        self.time_label = None
        self.gps_uid = gps_uid

    @staticmethod
    def get_current_time():
        return datetime.now().strftime("%Y%m%d%H%M%S")

    @staticmethod
    def save_response_to_json(filepath, modem_setup_response):
        with open(filepath, "w") as f:
            json.dump(modem_setup_response, f, indent=4)

    @staticmethod
    def create_directory(path):
        os.makedirs(path, exist_ok=True)

    def log_to_file(self, message):
        with open("job_runner.log", "a") as log_file:
            log_file.write(f"{self.get_current_time()};{message}\n")

    def run_docker_container(self, image_name, network_name=None, privileged=False, volumes=None, environment=None):
        """
        Runs a docker container and returns logs and container object. The container is removed after the logs are retrieved.
        :param image_name: docker image name
        :param network_name: network name
        :param privileged: if true, container is run in privileged mode
        :param volumes: volumes to mount
        :param environment: environment variables
        :return: Log in string format and container object
        """
        try:
            # stop signal is needed to stop container with CTRL+C. This signal is used in some containers to stop gracefully.
            container = self.client.containers.run(image_name, detach=True, network=network_name, privileged=privileged,
                                                   volumes=volumes, environment=environment, stop_signal="SIGINT")

            return container
        except Exception as ex:
            self.logger.log_error(f"Exception in running Docker container: {ex}")
            raise

    def run_log_docker_container(self, _container, _file_log, _name, _image_name, _docker_log_path=None,
                                 _time_label=None):
        """
        Logs a docker container and stops it. It checks if the logs are from stdout or in a file.
        :param _container: A running container object
        :param _file_log: If true, logs are in a file. If false, logs are from stdout.
        :param _name: Name of the task.
        :param _docker_log_path: Path to docker log file in container
        :param _image_name: Docker image name
        :param _time_label: Time label for log file
        :return: Log in string format and container object
        """
        try:

            if _time_label is None:
                _time_label = self.get_current_time()

            # Wait for container to finish
            _container.wait()
            log = None
            if _file_log:
                # Get container logs
                self.save_docker_logs_to_archive(f"{self.result_path}/{_name}",
                                                 f"{self.measurement_id}_{_time_label}_{_name}_{_image_name}.tar",
                                                 _container, _docker_log_path)
            else:
                # Get container logs
                log = _container.logs()
                # Decode logs
                log = log.decode("utf-8")
                self.save_stdout_to_file(log, f"{self.result_path}/{_name}",
                                         f"{self.measurement_id}_{_time_label}_{_name}_{_image_name}.log")

            # Remove container
            _container.remove()
            return log
        except Exception as ex:
            self.logger.log_error(f"Exception occurred while running docker container: {ex}")
            raise

    def save_stdout_to_file(self, log, directory_path, file_name):
        """
        Saves stdout to file.
        :param log: Log in string format
        :param directory_path: Directory path to save file
        :param file_name: file name
        """
        try:
            # Create directory if it does not exist
            self.create_directory(directory_path)

            # Save logs to file
            path = os.path.join(directory_path, file_name)
            with open(path, "w") as f:
                f.write(log)
                f.close()
        except Exception as ex:
            self.logger.log_error(f"Exception occurred while saving stdout to file: {ex}")
            raise Exception(f"Exception occurred while saving stdout to file: {ex}")

    def save_docker_logs_to_archive(self, directory_path, archive_name, container, docker_log_path):
        """
        Saves docker logs to tar archive.
        :param directory_path: Directory path to save file
        :param archive_name: target archive name
        :param container: container object
        :param docker_log_path: path to docker log file in container
        """
        try:
            # Create directory if it does not exist
            self.create_directory(directory_path)

            # Get container logs
            bits, stat = container.get_archive(docker_log_path)

            # Save logs to tar archive
            path = os.path.join(directory_path, archive_name)
            with open(path, "wb") as f:
                for chunk in bits:
                    f.write(chunk)
                f.close()
        except Exception as ex:
            self.logger.log_error(f"Exception occurred while saving docker logs to archive: {ex}")
            raise

    def run_manage_modem(self, time_label, label, environment=None):
        """
        Runs manage-modem container. This container is used to enable/disable the modem.
        :param time_label: Time label for log file
        :param label: Label for log file, if the container is used to enable or disable the modem
        :param environment: Environment variables
        :return: Log in string format
        """
        try:
            # Run manage-modem container
            modem_controller_image_name = "setup-controller-modem"
            modem_controller_container = self.run_docker_container(
                modem_controller_image_name,
                privileged=True,
                environment=environment,
                volumes=[
                    "/var/run/dbus:/var/run/dbus",
                    "/run/udev:/run/udev:ro",
                    "/dev/bus/usb:/dev/bus/usb"
                ])

            # Get logs from container and save to file
            modem_controller_log = self.run_log_docker_container(modem_controller_container, False, "modem-controller",
                                                                 modem_controller_image_name, _time_label=time_label)

            # Check if modem was enabled successfully
            enable_response = modem_controller_log.splitlines()[-1]
            if enable_response.__contains__("ERROR"):
                raise Exception(f"Modem {label} failed. Exiting...")

            return modem_controller_log
        except Exception as ex:
            self.logger.log_error(f"Exception occurred while running manage-modem container: {ex}")
            raise

    def run_setup_modem_act(self, time_label, environment=None):
        """
        Runs setup-modem-act container. This container is used to setup the modem AcT.
        :param time_label: Time label for log file
        :param environment: Environment variables
        :return: Log in string format
        """
        try:
            setup_act_image_name = "setup-modem-act"
            setup_act_container = self.run_docker_container(setup_act_image_name, privileged=True,
                                                            environment=environment,
                                                            volumes=[
                                                                "/var/run/dbus:/var/run/dbus",
                                                                "/run/udev:/run/udev:ro",
                                                                "/dev/bus/usb:/dev/bus/usb"
                                                            ])

            # Save logs to file
            setup_act_log = self.run_log_docker_container(setup_act_container, False, "setup-act", setup_act_image_name,
                                                          _time_label=time_label)

            config_setup_response = setup_act_log.splitlines()[-1]
            if config_setup_response.__contains__("ERROR"):
                raise Exception("Modem ACT setup failed. Exiting...")
            return setup_act_log
        except Exception as ex:
            self.logger.log_error(f"Exception occurred while running setup-modem-act container: {ex}")
            raise

    def run_setup_operator(self, time_label, environment=None):
        """
        Runs setup-operator container. This container is used to setup the operator as well as the data connection.
        :param time_label: Time label for log file
        :param environment: Environment variables
        """
        try:
            # Run setup-operator container
            modem_setup_image_name = "setup-operator-modem"
            modem_setup_container = self.run_docker_container(modem_setup_image_name, "host",
                                                              privileged=True,
                                                              environment=environment,
                                                              volumes=[
                                                                  "/var/run/dbus:/var/run/dbus",
                                                                  "/run/udev:/run/udev:ro",
                                                                  "/dev/bus/usb:/dev/bus/usb"
                                                              ])

            # Save logs to file
            modem_setup_log = self.run_log_docker_container(modem_setup_container, False, "modem-setup",
                                                            modem_setup_image_name, _time_label=time_label)

            modem_setup_response = json.loads(modem_setup_log.split("#RESPONSE#")[1].strip())
            # save response to json file
            self.save_response_to_json(
                f"{self.result_path}/modem-setup/{self.measurement_id}_{time_label}_modem-setup_{modem_setup_image_name}.json",
                modem_setup_response)
            if modem_setup_response['level'] == "ERROR":
                raise Exception("Operator setup failed. Exiting...")

            self.interface = modem_setup_response['message']['interface']
            self.ip_host = modem_setup_response['message']['ip_addr']
        except Exception as ex:
            self.logger.log_error(f"Exception occurred while running setup-operator container: {ex}")
            raise

    def run_scan_operator(self, time_label, environment=None):
        """
        Runs scan-operator container. This container is used to scan for operators.
        :param time_label:
        :param environment:
        """
        try:
            modem_scan_image_name = "scan-operator"
            modem_scan_container = self.run_docker_container(modem_scan_image_name, privileged=True,
                                                             volumes=[
                                                                 "/var/run/dbus:/var/run/dbus"],
                                                             environment=environment)
            # Save logs to file
            modem_scan_log = self.run_log_docker_container(modem_scan_container, False, "modem-scan",
                                                           modem_scan_image_name, _time_label=time_label)
            scan_response = json.loads(modem_scan_log.split("#RESPONSE#")[1].strip())

            # todo: using the scan response, we can check if the operator is available.
            # todo: using the returning list of operators
            if scan_response['level'] == "ERROR":
                # throw exception
                raise Exception("Operator scan failed. Exiting...")

            return scan_response
        except Exception as ex:
            self.logger.log_error(f"Exception occurred while running scan-operator container: {ex}")
            raise

    def run_background_task(self, _background_tasks, _time_label):
        """
        Runs background tasks.
        :param _background_tasks: List of background tasks
        :param _time_label: time label for log file
        :return: List of running containers
        """
        try:
            containers = []
            for task in _background_tasks:
                image_name = task.get('image_name')
                name = task.get('name')
                environment = task.get('environment')

                if environment is None:
                    environment = []

                environment.append(f"MODEM={self.modem}")
                environment.append(f"PC_NAME={self.device_name}")

                if image_name.__contains__("gps") and self.gps_uid is not None:
                    environment.append(f"UID={self.gps_uid}")

                network = task.get('network')
                privileged = task.get('privileged')
                pause = task.get('pause')
                self.logger.log_info(f"Running background task {name}: {image_name}.")

                # run docker container
                container = self.run_docker_container(image_name, network, privileged, environment=environment)

                # save container to dictionary for later stopping
                containers.append([container, task])
                if pause is not None:
                    sleep(pause)

            return containers
        except Exception as ex:
            self.logger.log_error(f"Exception occurred while running background task: {ex}")
            raise

    def run_background_later_task(self, _background_later_tasks, _modem, _interface, _modem_port, _ip_host):
        try:
            containers = []
            for task in _background_later_tasks:
                image_name = task.get('image_name')
                name = task.get('name')
                environment = task.get('environment')

                if environment is None:
                    environment = []

                if _modem is not None:
                    environment.append(f"MODEM={_modem}")

                if _interface is not None:
                    environment.append(f"INTERFACE={_interface}")

                if _modem_port is not None:
                    environment.append(f"PORT={_modem_port}")

                if _ip_host is not None:
                    environment.append(f"IP_HOST={_ip_host}")

                if self.device_name is not None:
                    environment.append(f"PC_NAME={self.device_name}")

                if image_name.__contains__("gps") and self.gps_uid is not None:
                    environment.append(f"UID={self.gps_uid}")

                network = task.get('network')
                privileged = task.get('privileged')
                pause = task.get('pause')
                self.logger.log_info(f"Running background later task {name}: {image_name}.")

                # run docker container
                container = self.run_docker_container(image_name, network, privileged, environment=environment)

                # save container to dictionary for later stopping
                containers.append([container, task])
                if pause is not None:
                    sleep(pause)

            return containers
        except Exception as ex:
            self.logger.log_error(f"Exception occurred while running background later task: {ex}")
            raise

    def log_background_tasks(self, container_info):
        """
        Logs background tasks. Either saves stdout to file or saves docker logs to tar archive.
        :param container_info: running container that should be logged
        """
        try:
            if container_info[1].get('docker_logger'):
                task_name = container_info[1].get('name')
                image_name = container_info[1].get('image_name')
                self.save_docker_logs_to_archive(f"{self.result_path}/{task_name}",
                                                 f"{self.measurement_id}_{self.start_time}_{task_name}_{image_name}.tar",
                                                 container_info[0], container_info[1].get('docker_log_path'))
            else:
                task_name = container_info[1].get('name')
                image_name = container_info[1].get('image_name')
                self.save_stdout_to_file(container_info[0].logs().decode("utf-8"), f"{self.result_path}/{task_name}",
                                         f"{self.measurement_id}_{self.start_time}_{task_name}_{image_name}.log")
        except Exception as ex:
            self.logger.log_error(f"Exception occurred while logging background tasks: {ex}")
            raise

    def stop_running_background_tasks(self, _running_containers):
        """
        Stops background tasks.
        :param _running_containers: List of running containers
        """
        try:
            # stop background tasks in reverse order
            _running_containers.reverse()

            for container_info in _running_containers:
                try:
                    # check if container has pause
                    pause = container_info[1].get('pause')
                    if pause is not None:  # if container has pause, sleep for pause seconds
                        sleep(pause)

                    # stop container
                    self.logger.log_info(
                        f"Stopping background task {container_info[1].get('name')}: {container_info[1].get('image_name')}.")
                    container = container_info[0]
                    container.stop(timeout=120)
                    self.log_background_tasks(container_info)
                    container.remove()
                except Exception as ex:
                    self.logger.log_error(f"Exception occurred while stopping container {container_info[0]}: {ex}")

        except Exception as ex:
            self.logger.log_error(f"Exception occurred while stopping running background tasks: {ex}")
            raise

    def run_modem_configuration(self, _modem, _operator_mode, _apn, _ip_type, _modem_port,
                                _act_mode, _set_band, _gsm_band, _catm1_band, _nbiot_band, _scan_operator=False):
        """
        Runs modem configuration. This includes enabling the modem, scanning for operators and setting up the operator.
        :param _scan_operator:
        :param _modem: Name of the modem
        :param _operator_mode: Operator mode. Either manual, random or any
        :param _apn: APN to use
        :param _ip_type: IP type to use
        :param _act_mode: AcT mode to use
        :param _set_band: If true, set band
        :param _gsm_band: GSM band to use
        :param _catm1_band: CatM1 band to use
        :param _nbiot_band: NB-IoT band to use
        :param _modem_port: Modem port to run at commands
        """
        try:

            self.logger.log_info(f"Enabling modem {_modem}.")
            # manage modem
            self.run_manage_modem(self.time_label, "enable",
                                  environment=[f"MODEM={_modem}", f"MODE=1,1", f"PORT={_modem_port}",
                                               f"PC_NAME={self.device_name}"])

            #if self.modem_iot:
            #    self.logger.log_info(f"Setting up modem AcT.")
            #    self.run_setup_modem_act(self.time_label,
            #                             environment=[f"MODEM={_modem}", f"PORT={_modem_port}", f"BAND={_set_band}",
            #                                          f"ACCESS_TECH={_act_mode}", f"GSMBANDVAL={_gsm_band}",
            #                                          f"CATM1BANDVAL={_catm1_band}", f"CATNB1BANDVAL={_nbiot_band}",
            #                                          f"PC_NAME={self.device_name}"])
            #    sleep(20)

            if _scan_operator:
                self.logger.log_info(f"Scanning for operators.")
                scan_response = self.run_scan_operator(self.time_label,
                                                       environment=[f"MODEM={_modem}", f"PORT={_modem_port}",
                                                                    f"PC_NAME={self.device_name}"])
                sleep(20)

            self.logger.log_info(f"Setting up operator.")
            self.run_setup_operator(self.time_label, environment=[f"MODEM={_modem}", f"PORT={_modem_port}",
                                                                  f"CONNECT_OPERATOR={_operator_mode}", f"APN={_apn}",
                                                                  f"IP_TYPE={_ip_type}", f"PC_NAME={self.device_name}",
                                                                  f"ACCESS_TECH={_act_mode}",
                                                                  f"BAND={_set_band}",
                                                                  f"GSMBANDVAL={_gsm_band}",
                                                                  f"CATM1BANDVAL={_catm1_band}",
                                                                  f"CATNB1BANDVAL={_nbiot_band}"
                                                                  ])

        except Exception as ex:
            self.logger.log_error(f"Exception occurred while running modem configuration: {ex}")
            raise

    def run_measurement_task(self, _measurement_tasks, _modem, _interface, _modem_port, _ip_host):
        """
        Runs measurement tasks. These tasks are run sequentially and represent the actual experiment.
        :param _modem_port: Modem port to run at commands
        :param _measurement_tasks: List of measurement tasks
        :param _modem: Name of the modem
        :param _interface: Interface to use for measurement tasks
        :param _ip_host: IP host to use for measurement tasks
        :return:
        """

        # get measurement tasks
        _tasks = _measurement_tasks.get('tasks')
        # get delay between tasks
        # todo: wird noch nicht im Webinterface angezeigt oder gesetzt
        #_delay = _measurement_tasks.get('pause')

        # run measurement tasks
        for task in _tasks:
            name = task.get('name')
            image_name = task.get('image_name')
            environment = task.get('environment')
            privileged = task.get('privileged')
            network = task.get('network')
            docker_logger = task.get('docker_logger')
            docker_log_path = task.get('docker_log_path')
            pause = task.get('pause', None)

            if environment is None:
                environment = []

            if _modem is not None:
                environment.append(f"MODEM={_modem}")

            if _interface is not None:
                environment.append(f"INTERFACE={_interface}")

            if _modem_port is not None:
                environment.append(f"PORT={_modem_port}")

            if _ip_host is not None:
                environment.append(f"IP_HOST={_ip_host}")

            if self.device_name is not None:
                environment.append(f"PC_NAME={self.device_name}")

            self.logger.log_info(f"Running measurement task {name}: {image_name}.")
            container = self.run_docker_container(image_name, network, privileged, environment=environment)

            # Save logs to file
            self.run_log_docker_container(container, docker_logger, name, image_name, docker_log_path, _time_label=self.time_label)

            if pause is not None:
                self.logger.log_info(f"Waiting {pause} seconds for next task.")
                sleep(pause)

    def stop_background_tasks(self):
        """
        Stops background tasks.
        """
        try:
            self.logger.log_info("Stopping background tasks.")
            self.stop_running_background_tasks(self.running_bg_containers)
            self.stop_running_background_tasks(self.running_bg_later_containers)
        except Exception as ex:
            self.logger.log_error(f"Exception occurred while stopping background tasks: {ex}")
            raise

    def save_instruction_to_folder(self):
        try:
            with open(f"{self.result_path}/instruction.json", "w") as f:
                json.dump(self.instruction, f, indent=4)
                f.close()
        except Exception as ex:
            self.logger.log_error(f"Exception occurred while saving instruction to file: {ex}")
            raise

    def run(self, scheduled_task_late):
        """
        Runs the experiment.
        """
        try:
            self.save_instruction_to_folder()

            if scheduled_task_late:
                self.logger.log_warning("This scheduled task started later than planed.")

            self.logger.log_info("Starting experiment.")
            # get modem configuration
            modem_configuration = self.instruction.get('modem_configuration')
            repeat = self.instruction.get('repeat', 1)
            experiment_pause = self.instruction.get('experiment_pause', 0)

            if modem_configuration is None:
                raise Exception("Modem configuration is missing.")
            operator_mode = modem_configuration.get('operator_mode')
            act_mode = modem_configuration.get('act_mode', "all")
            set_band = modem_configuration.get('set_band', "True")
            gsm_band = modem_configuration.get('gsm_band', "0F")
            catm1_band = modem_configuration.get('catm1_band', "0000000000080000")
            nbiot_band = modem_configuration.get('nbiot_band', "0000000000080000")
            apn = modem_configuration.get('apn')
            ip_type = modem_configuration.get('ip-type')
            operators = modem_configuration.get('operators')
            operator_scan = modem_configuration.get('operator_scan', False)

            if apn is None or ip_type is None or operator_mode is None:
                raise Exception("APN, IP type or operator mode is missing.")

            if operator_mode.casefold() == "manual".casefold() and operators is None:
                raise Exception("Operator list is missing.")

            try:
                self.modem_port = find_modem_port(self.modem)
            except Exception as ex:
                raise Exception(f"Modem port selection failed: {ex}")

            self.logger.log_info(f"Found port {self.modem_port} for modem {self.modem}.")

            # disable modem before starting experiment via bash script in ../watchdog/modem_control.sh <port> <at_command>
            self.logger.log_info(f"Disabling modem {self.modem}.")
            try:
                subprocess.run(
                    ["sudo", "bash", "/home/ubuntu/mark/watchdog/modem_control.sh", self.modem_port, "AT+CFUN=0"],
                    check=True)
            except subprocess.CalledProcessError as ex:
                self.logger.log_warning(f"Not able to disable the modem before measurement. "
                                        f"Exception occurred while disabling modem: {ex}. "
                                        f"It is not essential for the measurement.")
                # raise Exception(f"Exception occurred while disabling modem before starting experiment: {ex}")

            # get measurement tasks
            measurement_tasks = self.instruction.get('measurement_tasks')
            if measurement_tasks is None:
                raise Exception("Measurement tasks are missing.")

            # get background tasks
            background_tasks_config = self.instruction.get('background_tasks')

            # get background later tasks
            background_later_tasks_config = self.instruction.get('background_later_tasks')

            if background_tasks_config is not None:
                background_tasks = background_tasks_config.get('tasks')
                background_tasks_delay = background_tasks_config.get('pause', 0)

                if background_tasks is not None and len(background_tasks) > 0:
                    self.logger.log_info("Running background tasks.")
                    self.running_bg_containers = self.run_background_task(background_tasks, self.get_current_time())

                    if background_tasks_delay > 0:
                        self.logger.log_info(f"Waiting {background_tasks_delay} seconds for background tasks to start.")
                        sleep(background_tasks_delay)

            # run experiment
            for i in range(repeat):
                self.logger.log_info(f"Running experiment {i + 1}/{repeat}.")
                self.time_label = self.get_current_time()

                if operator_mode.casefold() != "random".casefold() and operator_mode.casefold() != "any".casefold():
                    operator_mode = operators[i % len(operators)]

                self.run_modem_configuration(self.modem, operator_mode, apn, ip_type, self.modem_port, act_mode,
                                             set_band,
                                             gsm_band, catm1_band, nbiot_band, operator_scan)

                if background_later_tasks_config is not None:
                    background_later_tasks = background_later_tasks_config.get('tasks')

                    if background_later_tasks is not None and len(background_later_tasks) > 0:
                        self.logger.log_info("Running background later tasks.")
                        self.running_bg_later_containers = self.run_background_later_task(background_later_tasks, self.modem, self.interface, self.modem_port, self.ip_host)

                self.run_measurement_task(measurement_tasks, self.modem, self.interface, self.modem_port, self.ip_host)

                self.logger.log_info(f"Disabling modem {self.modem}.")
                self.run_manage_modem(self.get_current_time(), "disable",
                                      environment=[f"MODEM={self.modem}", f"MODE=0", f"PORT={self.modem_port}",
                                                   f"PC_NAME={self.device_name}"])

                if i < repeat - 1:
                    self.logger.log_info(f"Waiting {experiment_pause} seconds for next experiment.")
                    sleep(experiment_pause)

            self.logger.log_info("Measurement finished.")

            if background_tasks_config is not None:
                self.stop_background_tasks()

            self.logger.log_info("Experiment finished.")
        except (Exception, KeyboardInterrupt) as ex:
            self.logger.log_error(f"Exception occurred while running experiment. {ex}")
            self.status = False

            if self.running_bg_containers is not None:
                for _container in self.running_bg_containers:
                    try:
                        _container[0].stop()
                        self.log_background_tasks(_container)
                        _container[0].remove()
                    except Exception as ex:
                        self.logger.log_error(f"Exception occurred while stopping container: {ex}")

            if self.running_bg_later_containers is not None:
                for _container in self.running_bg_later_containers:
                    try:
                        _container[0].stop()
                        self.log_background_tasks(_container)
                        _container[0].remove()
                    except Exception as ex:
                        self.logger.log_error(f"Exception occurred while stopping container: {ex}")
        finally:
            # save logs to archive if experiment failed
            if not self.always_save_logs and not self.status:
                self.log_to_file(
                    f"Removing logs for experiment {self.measurement_id} because always_save_logs is set to false.")
                if os.path.exists(self.result_path):
                    shutil.rmtree(self.result_path)

                # if experiment failed, return None
                self.result_path = None
            self.client.close()
            self.log_to_file(
                f"Experiment finished for modem {self.modem} on device {self.instruction.get('device_name')}. Measurement id {self.measurement_id}.")
            return self.result_path, self.status
