# Mark

## Setup

The following steps describe the software setup for a Mark measurement node, starting from an installation of Ubuntu 24.04.

 - Update the system packages:
    ```bash
    sudo apt update
    sudo apt upgrade
    ```
 - If the node and the management server are going to be in different networks, set up a VPN like WireGuard on the management server and the nodes.
 - Create an SSH keypair on the management server if you have not already done so. Then, copy the public key to the node and make sure the server can access the node via SSH without a password.
 - Install the necessary packages:
    ```bash
    sudo apt install curl wget ca-certificates

    # Tinkerforge Brick Daemon
    wget https://download.tinkerforge.com/apt/ubuntu/tinkerforge.gpg -q -O - | sudo tee /etc/apt/trusted.gpg.d/tinkerforge.gpg > /dev/null
    echo "deb https://download.tinkerforge.com/apt/ubuntu noble main" | sudo tee /etc/apt/sources.list.d/tinkerforge.list

    # Docker
    sudo install -m 0755 -d /etc/apt/keyrings
    sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    sudo chmod a+r /etc/apt/keyrings/docker.asc

    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    sudo apt update
    sudo apt install brickd curl docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin python3 python3-pip python3-setuptools python3-dotenv python3-requests python3-psutil python3-pyudev python3-tinkerforge socat virtualenv

    sudo pip3 install --break-system-packages docker
    ```
 - Ensure the Docker service is running and enabled on startup:
    ```bash
    sudo systemctl enable --now docker.service
    ```
 - Add user (default `ubuntu`) to the docker group):
    ```bash
    sudo usermod -aG docker ubuntu
    ```
 - Pin ModemManager package to version 1.20.6 by creating the file `/etc/apt/preferences.d/modemmanager` as superuser with the following contents:
    ```
    Package: modemmanager
    Pin: version 1.20.*
    Pin-Priority: 999
    ```
 - Download and install ModemManager 1.20.6:
    ```bash
    wget https://old-releases.ubuntu.com/ubuntu/pool/main/m/modemmanager/modemmanager_1.20.6-1ubuntu1_arm64.deb
    sudo dpkg -i modemmanager_1.20.6-1ubuntu1_arm64.deb
    ```
 - Ensure the ModemManager service is running and enabled on startup:
    ```bash
    sudo systemctl enable --now ModemManager.service
    ```
 - Increase the system-wide soft/hard nofile limits by editing `/etc/security/limits.conf` as superuser and adding these two lines at the end of the file:
    ```
    * soft nofile 10000
    * hard nofile 10000
    ```
 - Configure the system to crash when RAM is full by adding these two lines to `/etc/sysctl.conf`:
    ```
    vm.panic_on_oom=1
    kernel.panic=10
    ```
 - Load the modified kernel parameters:
    ```bash
    sudo sysctl -p
    ```
 - Copy the `Mark` folder from this repository to `/home/ubuntu/mark`.
 - In that folder, create a `.env.server` file:
    ```bash
    # Marklab URL
    SERVER_URL=https://...

    # Add the key from your Marklab .env file here
    REGISTRATION_KEY=...
    ```
 - Make sure that all modems appear in the output of `sudo mmcli -L`. If one is missing, try rebooting the device.
 - Run two python scripts in order to register the new node and its modems:
    ```bash
    sudo python3 mark/config/settings/config_modem_uid.py
    sudo python3 mark/config/settings/config_modem_mm.py
    ```
    In the event that any of these two scripts fail, you will have to delete the files `/lib/udev/rules.d/78-mm-naming.rules` and `/etc/udev/rules.d/99-ignore*` before trying to run them again.
 - Ensure that the system time zone is correct (replace `Europe/Berlin` with your time zone):
    ```bash
    sudo timedatectl set-timezone Europe/Berlin
    ```
 - Build necessary Docker images (this may take a while):
    ```bash
    sudo docker compose -f mark/config/docker-compose.yml build
    sudo docker rmi $(docker images -f "dangling=true" -q)
 - Synchronize the node's Docker images with the management server:
    ```bash
    sudo python3 mark/config/settings/config_db_images.py
    ```
 - Synchronize the node's Tinkerforge devices with the management server:
    ```bash
    sudo python3 mark/config/settings/config_tf_devices.py
    ```
 - Use `sudo crontab -e` to create these cronjobs for the root user:
    ```bash
    # Checks for a new measurement every minute
    */1 * * * * cd /home/ubuntu/mark/exec/ && /bin/bash job_watchdog.sh

    # Reboots the system daily
    1 0 * * * /bin/bash /home/ubuntu/mark/watchdog/system_rebooter.sh job_runner.py

    # Run regular health checks
    */31 * * * * cd /home/ubuntu/mark/watchdog/ && python3 health_check.py
    ```
 - Reboot the system:
    ```bash
    sudo systemctl reboot
    ```
 - The Mark node is now ready for executing measurements.

## Repository structure

The repository is structured as follows:

- `config/`: Contains the configuration files for a Mark instance. These files are used to set up or update a Mark instance as well as to files for building the Docker images.
- `core/`: Contains the core functionality of Mark. This includes the logic for running AT-Commands, ModemManager, network configuration commands as well as logging and helper functions.
This is the main part of the Mark environment to run measurements and tests.
- `docs/`: Contains the documentation of Mark like figures, examples and other useful information.
- `exec/`: Contains the scripts to run measurements. These scripts are used to run the measurements on the Mark instances.
  - `exec/job_helper.py`: The script contains helper functions to run the measurement tasks.
  - `exec/job_watchdog.sh`: The script checks if a measurement task is in progress and runs the measurement task if not. Additionally, it cleans up the node by stopping unintended running containers.
  - `exec/job_runner.py`: The script run the measurement task on the Mark instances. It contains the logic to check the connectivity to the management server, synchronize not transferred measurement tasks and running new task.
  - `exec/measurement_exec.py`: The script executes the measurement jobs running background jobs first and then general jobs.
- `helper/`: Contains helper scripts for external tools like tinkerforge/brickd.
- `measurements/`: Contains system integrated docker measurement images. Each directory corresponds to a measurement image containing the Dockerfile and the measurement script.
- `setup/`: Contains the setup scripts for setting data connection setup before running the measurements.
- `watchdog/`: Contains the watchdog scripts to monitor the Mark instances, among other things:
  - `watchdog/health_check.py`: The scripts checks the health of the Mark instances by checking the usage of disk usage and connectivity to the management server.
  - `watchdog/system_watchdog.py`: The script is used from `job_watchdog.sh` to check if a measurement node is health to be used for a measurement task.
  - ...
