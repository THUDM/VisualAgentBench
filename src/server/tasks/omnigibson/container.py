import docker
from docker.types import DeviceRequest
import os
import fcntl
import socket
import time
import random
from src.typings import TaskSampleExecutionResult, TaskOutput, SampleIndex, AgentOutputStatus, SampleStatus

ICD_PATH_1 = "/usr/share/vulkan/icd.d/nvidia_icd.json"
ICD_PATH_2 = "/etc/vulkan/icd.d/nvidia_icd.json"
LAYERS_PATH_1 = "/usr/share/vulkan/icd.d/nvidia_layers.json"
LAYERS_PATH_2 = "/usr/share/vulkan/implicit_layer.d/nvidia_layers.json"
LAYERS_PATH_3 = "/etc/vulkan/implicit_layer.d/nvidia_layers.json"
EGL_VENDOR_PATH = "/usr/share/glvnd/egl_vendor.d/10_nvidia.json"

class Container():

    available_ports = []    # [12000, 12001, 12002, 12003, 12004, 12005, 12006, 12007]
    available_devices = {}    # {"0":1, "1":1, "2":1, "3":1, "4":1, "5":1, "6":1, "7":1}
    output_dir = "outputs/omnigibson"
    data_dir = "data/omnigibson"
    vab_source_dir = ""
    modified_omnigibson_src = ""
    max_round = 100

    def use_port(self):
        time.sleep(random.random())
        for port in self.available_ports:
            port_lock_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmp", f"port_{port}.lock")
            try:
                port_lock_file = open(port_lock_file, "w")
                fcntl.flock(port_lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
                self.port_lock_file = port_lock_file
                return port
            except IOError:
                if port_lock_file:
                    port_lock_file.close()
                continue
        return -1

    def release_port(self):
        if self.port_lock_file:
            fcntl.flock(self.port_lock_file, fcntl.LOCK_UN)
            self.port_lock_file.close()
            self.port_lock_file = None

    def use_device(self):
        time.sleep(random.random())
        for device, cnt in self.available_devices.items():
            for i in range(cnt):
                device_lock_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmp", f"gpu_{device}_{i}.lock")
                try:
                    device_lock_file = open(device_lock_file, "w")
                    fcntl.flock(device_lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    self.device_lock_file = device_lock_file
                    return device, i
                except IOError:
                    if device_lock_file:
                        device_lock_file.close()
                    continue
        return -1, -1

    def release_device(self):
        if self.device_lock_file:
            fcntl.flock(self.device_lock_file, fcntl.LOCK_UN)
            self.device_lock_file.close()
            self.device_lock_file = None


    def __init__(self, task):
        self.client = docker.from_env()
        self.device_lock_file = None
        self.port_lock_file = None
        self.port = self.use_port()
        if self.port == -1:
            raise Exception("All ports are not available.")
        self.device, self.device_task_index = self.use_device()
        if self.device == -1:
            raise Exception("All devices are at full capacity now.")
        device_request = DeviceRequest(capabilities=[["gpu"]], device_ids=[f"{self.device}"])
        icd_path = None
        layers_path = None
        if os.path.exists(ICD_PATH_1):
            icd_path = ICD_PATH_1
        elif os.path.exists(ICD_PATH_2):
            icd_path = ICD_PATH_2
        else:
            raise Exception(
                "Missing nvidia_icd.json file. Typical paths:\n"
                "- /usr/share/vulkan/icd.d/nvidia_icd.json or\n"
                "- /etc/vulkan/icd.d/nvidia_icd.json\n"
                "You can google nvidia_icd.json for your distro to find the correct path.\n"
                "Consider updating your driver to 525 if you cannot find the file.\n"
                "To continue update the ICD_PATH_1 at the top of the `src/server/tasks/omnigibson/container.py` file and retry.\n"
            )
        if os.path.exists(LAYERS_PATH_1):
            layers_path = LAYERS_PATH_1
        elif os.path.exists(LAYERS_PATH_2):
            layers_path = LAYERS_PATH_2
        elif os.path.exists(LAYERS_PATH_3):
            layers_path = LAYERS_PATH_3
        else:
            raise Exception(
                "Missing nvidia_layers.json file. Typical paths:\n"
                "- /usr/share/vulkan/icd.d/nvidia_layers.json\n"
                "- /usr/share/vulkan/implicit_layer.d/nvidia_layers.json\n"
                "- /etc/vulkan/implicit_layer.d/nvidia_layers.json\n"
                "You can google nvidia_layers.json for your distro to find the correct path.\n"
                "Consider updating your driver to 525 if you cannot find the file.\n"
                "To continue update the LAYERS_PATH_1 at the top of the `src/server/tasks/omnigibson/container.py` file and retry.\n"
            )
        if not os.path.exists(EGL_VENDOR_PATH):
            raise Exception(
                f"Missing EGL_VENDOR_PATH file.\n"
                "(default path: /usr/share/glvnd/egl_vendor.d/10_nvidia.json)\n"
                "To continue update the EGL_VENDOR_PATH at the top of the `src/server/tasks/omnigibson/container.py` file and retry.\n"
            )

        volumes = {
            icd_path: {"bind": "/etc/vulkan/icd.d/nvidia_icd.json"},
            layers_path: {"bind": "/etc/vulkan/implicit_layer.d/nvidia_layers.json"},
            EGL_VENDOR_PATH: {"bind": "/usr/share/glvnd/egl_vendor.d/10_nvidia.json"},
            f"{self.data_dir}/datasets": {"bind": "/data"},
            f"{self.data_dir}/isaac-sim/cache/kit": {"bind": "/isaac-sim/kit/cache/Kit", "mode": "rw"},
            f"{self.data_dir}/isaac-sim/cache/ov": {"bind": "/root/.cache/ov", "mode": "rw"},
            f"{self.data_dir}/isaac-sim/cache/pip": {"bind": "/root/.cache/pip", "mode": "rw"},
            f"{self.data_dir}/isaac-sim/cache/glcache": {"bind": "/root/.cache/nvidia/GLCache", "mode": "rw"},
            f"{self.data_dir}/isaac-sim/cache/computecache": {"bind": "/root/.nv/ComputeCache", "mode": "rw"},
            f"{self.data_dir}/isaac-sim/logs": {"bind": "/root/.nvidia-omniverse/logs", "mode": "rw"},
            f"{self.data_dir}/isaac-sim/config": {"bind": "/root/.nvidia-omniverse/config", "mode": "rw"},
            f"{self.data_dir}/isaac-sim/data": {"bind": "/root/.local/share/ov/data", "mode": "rw"},
            f"{self.data_dir}/isaac-sim/documents": {"bind": "/root/Documents", "mode": "rw"},
            f"{self.data_dir}/GoogleNews-vectors-negative300.bin": {"bind": "/GoogleNews-vectors-negative300.bin", "mode": "rw"},
            f"{self.data_dir}/activity_definitions": {"bind": "/micromamba/envs/omnigibson/lib/python3.7/site-packages/bddl/activity_definitions", "mode": "rw"},
            f"{self.modified_omnigibson_src}/inside.py": {"bind": "/omnigibson-src/omnigibson/object_states/inside.py", "mode": "rw"},
            f"{self.modified_omnigibson_src}/on_top.py": {"bind": "/omnigibson-src/omnigibson/object_states/on_top.py", "mode": "rw"},
            f"{self.modified_omnigibson_src}/under.py": {"bind": "/omnigibson-src/omnigibson/object_states/under.py", "mode": "rw"},
            f"{self.modified_omnigibson_src}/next_to.py": {"bind": "/omnigibson-src/omnigibson/object_states/next_to.py", "mode": "rw"},
            f"{self.modified_omnigibson_src}/vision_sensor.py": {"bind": "/omnigibson-src/omnigibson/sensors/vision_sensor.py", "mode": "rw"},
            f"{self.modified_omnigibson_src}/behavior_task.py": {"bind": "/omnigibson-src/omnigibson/tasks/behavior_task.py", "mode": "rw"},
            self.vab_source_dir: {"bind": "/VAB-OmniGibson-code", "mode": "rw"},
            self.output_dir: {"bind": "/og_logs", "mode": "rw"}
        }
        environment = {
            "OMNIGIBSON_HEADLESS": "1"
        }
        self.container = self.client.containers.run(
            "vab-omnigibson:latest",
            f"python main.py --task {task[0]} --scene {task[1]} --port {self.port} --max_round {self.max_round}",
            environment=environment,
            volumes=volumes,
            detach=True,
            stdin_open=True,
            tty=True,
            auto_remove=True,
            device_requests = [device_request],
            ports = {f"{self.port}/tcp": self.port}
        )

        self.initial_reward = None
        self.final_reward = None


    async def execute(self, session):
        while True:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect(("localhost", self.port))
                data = s.recv(8192)
                if not data:
                    s.close()
                    continue
                else:
                    break
            except:
                time.sleep(4)
            
        data = data.decode()
        reward = float(data.split("<RREWARD>")[-1].split("</RREWARD>")[0])
        if self.initial_reward == None:
            self.initial_reward = reward
        if "<DDONE>" in data and "</DDONE>" in data:
            done_message = data.split("<DDONE>")[-1].split("</DDONE>")[0]
            self.final_reward = reward
            if "task limit reached" in done_message:
                s.sendall("okay".encode())
                return TaskSampleExecutionResult(status=SampleStatus.TASK_LIMIT_REACHED, result={"success": False, "initial_reward": self.initial_reward, "final_reward": self.final_reward})
            elif "agent invalid action" in done_message:
                s.sendall("okay".encode())
                return TaskSampleExecutionResult(status=SampleStatus.AGENT_INVALID_ACTION, result={"success": False, "initial_reward": self.initial_reward, "final_reward": self.final_reward})
            elif "task error" in done_message:
                s.sendall("okay".encode())
                return TaskSampleExecutionResult(status=SampleStatus.TASK_ERROR, result={"success": False, "initial_reward": self.initial_reward, "final_reward": self.final_reward})
            elif "task failed" in done_message:
                s.sendall("okay".encode())
                return TaskSampleExecutionResult(status=SampleStatus.COMPLETED, result={"success": False, "initial_reward": self.initial_reward, "final_reward": self.final_reward})
            elif "task completed successfully" in done_message:
                s.sendall("okay".encode())
                return TaskSampleExecutionResult(status=SampleStatus.COMPLETED, result={"success": True, "initial_reward": self.initial_reward, "final_reward": self.final_reward})
        image_path = data.split("<IIMAGE>")[-1].split("</IIMAGE>")[0]
        text_prompt = data.split(f"<IIMAGE>{image_path}</IIMAGE>")[0]
        image_path = image_path.replace("/og_logs", self.output_dir)
        session.inject(
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": text_prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_path}",
                            "detail": "high"
                        }
                    }
                ]
            }
        )
        print(text_prompt)
        message = await session.action()
        print(message)
        if message.status == AgentOutputStatus.AGENT_CONTEXT_LIMIT:
            return TaskSampleExecutionResult(status=SampleStatus.AGENT_CONTEXT_LIMIT)
        elif message.status != AgentOutputStatus.NORMAL:
            return TaskSampleExecutionResult(status=SampleStatus.UNKNOWN)
        message = message.content
        if isinstance(message, tuple):
            message = message[0]
        if "Action Feedback:" in message:
            message = message.split("Action Feedback:")[0]
        if message.count("ACTION") >= 2:
            message_parts = message.split("ACTION", 2)
            message = "ACTION".join(message_parts[:2])
        if message.count("OBSERVATION") >= 2:
            message_parts = message.split("OBSERVATION", 2)
            message = "OBSERVATION".join(message_parts[:2])
        if "\n<|end_of_text|>" in message:
            message = message.split("\n<|end_of_text|>")[0]
        if "<|end_of_text|>" in message:
            message = message.split("<|end_of_text|>")[0]
        s.sendall(message.encode())
        session.history[-1].content = message
        session.history[-2].content = [
            {"type": "text", "text": text_prompt + "Omitted.\n"}
        ]
        return TaskSampleExecutionResult(status=SampleStatus.RUNNING)


    def close(self):
        try:
            time.sleep(4)
            self.container.stop(timeout=24)
        except:
            pass
        
        self.release_device()
        self.release_port()
