# Setup for VAB-OmniGibson

## Installation

1. We have tested on Ubuntu. VAB-OmniGibson requires **11 GB NVIDIA RTX GPU** and NVIDIA GPU driver version >= 450.80.02. For more detailed requirements, please refer to [Isaac Sim 2022.2.0](https://docs.omniverse.nvidia.com/isaacsim/latest/installation/requirements.html).

2. Besides [docker](https://www.docker.com/), install [NVIDIA container toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) on your machine.

3. Get pre-built docker image.
    
    - If you have access to docker hub:
        
        ```bash
        docker pull tianjiezhang/vab_omnigibson:latest
        ```
    
    - Or you can download from ModelScope.
        
        1. Make sure `git-lfs` is installed.
        
        2. Download from ModelScope:

            ```bash
            git lfs install

            git clone https://www.modelscope.cn/datasets/VisualAgentBench/VAB-OmniGibson-Docker.git
            ```

        3. Load the docker image from ModelScope dataset.

            ```bash
            docker load -i VAB-OmniGibson-Docker/vab_omnigibson.tar
            ```

4. Download datasets of OmniGibson, VAB-OmniGibson test activities, and related scene files. Note that about 25 GB data will be downloaded to `data/omnigibson`, and make sure you have access to google drive. During the download process, `git-lfs` is required, and you will be prompted to accept the OmniGibson user agreement.
    
    ```bash
    git lfs install

    python scripts/omnigibson_download.py
    ```

## Get Started

1. According to your hardware equipment, fill `available_ports` and `available_devices` in the task configuration file `configs/tasks/omnigibson.yaml`.

    - `available_ports`: Please fill in available ports in your machine. Each concurrent docker container requires 1 port for communication with the task server. Ensure that you provide enough ports to accommodate the expected concurrency.

    - `available_devices`: Please fill in GPU IDs and their corresponding capability of concurrency. Each concurrent docker container occupies about **11 GB** memory. Ensure that you provide enough GPU memory to accommodate the expected concurrency.

2. It's recommended to increase the file change watcher for Linux. See [Omniverse guide](https://docs.omniverse.nvidia.com/dev-guide/latest/linux-troubleshooting.html#to-update-the-watcher-limit) for more details.

    - View the current watcher limit: `cat /proc/sys/fs/inotify/max_user_watches`.

    - Update the watcher limit:

        1. Edit `/etc/sysctl.conf` and add `fs.inotify.max_user_watches=524288` line.

        2. Load the new value: `sudo sysctl -p`.

**Note: If you manually shut down the task server and assigner, please ensure you also stop the OmniGibson containers to free up the ports!**
