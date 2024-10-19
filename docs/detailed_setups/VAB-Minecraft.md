# Setup for VAB-Minecraft

## Installation

1. We have tested on Ubuntu. VAB-Minecraft requires at least 4 GB NVIDIA GPU and NVIDIA GPU driver version >= 530.30.02.

2. Besides [docker](https://www.docker.com/), install [NVIDIA container toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) on your machine.

3. Get pre-built docker image.
    
    - If you have access to docker hub:
        
        ```bash
        docker pull tianjiezhang/vab_minecraft:latest
        ```
    
    - Or you can download from ModelScope.
        
        1. Make sure `git-lfs` is installed.
        
        2. Download from ModelScope:

            ```bash
            git lfs install

            git clone https://www.modelscope.cn/datasets/VisualAgentBench/VAB-Minecraft.git
            ```

        3. Load the docker image from ModelScope dataset.

            ```bash
            docker load -i VAB-Minecraft/vab_minecraft.tar
            ```

4. Download weights of Steve-1 to `data/minecraft`. Please make sure you have access to google drive.
    
    ```bash
    python scripts/minecraft_download.py
    ```

## Get Started

According to your hardware equipment, fill `available_ports` and `available_devices` in the task configuration file `configs/tasks/minecraft.yaml`.

- `available_ports`: Please fill in available ports in your machine. Each concurrent docker container requires 1 port for communication with the task server. Ensure that you provide enough ports to accommodate the expected concurrency.

- `available_devices`: Please fill in GPU IDs and their corresponding capability of concurrency. Each concurrent docker container occupies about **3.3 GB** memory. Ensure that you provide enough GPU memory to accommodate the expected concurrency.

**Note: If you manually shut down the task server and assigner, please ensure you also stop the Minecraft containers to free up the ports!**
