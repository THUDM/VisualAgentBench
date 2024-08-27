import docker
from docker.types import DeviceRequest
import os
import fcntl
import socket
import time
import random
from src.typings import TaskSampleExecutionResult, TaskOutput, SampleIndex, AgentOutputStatus, SampleStatus

class Container():

    available_ports = []
    available_devices = {}
    output_dir = "outputs/minecraft"
    data_dir = "data/minecraft"
    vab_source_dir = ""
    max_round = 100
    docker_image = ""

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
        # print(self.port, self.device)

        volumes = {
            self.vab_source_dir: {"bind": "/VAB-Minecraft", "mode": "rw"},
            self.output_dir: {"bind": "/minecraft_logs", "mode": "rw"},
            self.data_dir: {"bind": "/VAB-Minecraft/jarvis/steveI/weights", "mode": "rw"}
        }
        environment = {
            "NVIDIA_DRIVER_CAPABILITIES": "compute,utility",
            "TMPDIR": "/tmp",
            "PYTHONPYCACHEPREFIX": "/tmp"
        }
        self.container = self.client.containers.run(
            self.docker_image,
            f"xvfb-run -a python main.py --task_name {task} --port {self.port} --max_round {self.max_round}",
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
            self.container.reload()
            if self.container.status == "exited":
                return TaskSampleExecutionResult(status=SampleStatus.TASK_ERROR)
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
        image_path = image_path.replace("/minecraft_logs", self.output_dir)
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
        message = await session.action()
        print(message)
        if message.status == AgentOutputStatus.AGENT_CONTEXT_LIMIT:
            return TaskSampleExecutionResult(status=SampleStatus.AGENT_CONTEXT_LIMIT)
        elif message.status != AgentOutputStatus.NORMAL:
            return TaskSampleExecutionResult(status=SampleStatus.UNKNOWN)
        message = message.content
        if isinstance(message, tuple):
            message = message[0]
        if "Feedback on the Action: " in message:
            message = message.split("Feedback on the Action: ")[0]
        message = message.replace("Action:", "ACTION:")
        message = message.replace("Observation:", "OBSERVATION:")
        message = message.replace("Thought:", "THOUGHT:")
        message = message.replace("action:", "ACTION:")
        message = message.replace("observation:", "OBSERVATION:")
        message = message.replace("thought:", "THOUGHT:")
        if message.count("ACTION") >= 2:
            message_parts = message.split("ACTION", 2)
            message = "ACTION".join(message_parts[:2])
        if message.count("OBSERVATION") >= 2:
            message_parts = message.split("OBSERVATION", 2)
            message = "OBSERVATION".join(message_parts[:2])
        if "THOUGHT:" in message and "ACTION:" in message:
            thought = message.split("THOUGHT:")[1].split("ACTION:")[0]
            observation = message.split(thought)[0]
            action = message.split(thought)[-1]
            thoughts = thought.split("\n")
            new_thought = ""
            for t in thoughts[:5]:
                if t.strip() != "":
                    if t.startswith("2. "):
                        new_thought += t + "\n"
                        break
                    new_thought += t + "\n"
            message = observation + new_thought + action
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
            time.sleep(12)
            if self.container.status != "exited":
                self.container.stop(timeout=24)
        except:
            pass
        
        self.release_device()
        self.release_port()
