from src.server.task import Task, Session
from src.typings import TaskSampleExecutionResult, TaskOutput, SampleIndex, AgentOutputStatus, SampleStatus
from typing import List, Dict, Any
from src.server.tasks.minecraft.container import Container
from src.server.tasks.minecraft.prompt import SYSTEM_PROMPT
import os
import json
import asyncio

class Minecraft(Task):
    def __init__(self, available_ports, available_devices, data_dir, output_dir, max_round, docker_image, **configs):
        super().__init__(**configs)
        self.vab_source_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vab_minecraft_src")
        Container.available_devices = available_devices
        Container.available_ports = available_ports
        os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmp"), exist_ok=True)
        for port in available_ports:
            port_lock_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmp", f"port_{port}.lock")
            if not os.path.exists(port_lock_file):
                open(port_lock_file, "w").close()
        for device, cnt in available_devices.items():
            for i in range(cnt):
                device_lock_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmp", f"gpu_{device}_{i}.lock")
                if not os.path.exists(device_lock_file):
                    open(device_lock_file, "w").close()
        Container.data_dir = os.path.join(os.getcwd(), data_dir)
        Container.output_dir = os.path.join(os.getcwd(), output_dir)
        if not os.path.exists(Container.output_dir):
            os.makedirs(Container.output_dir)
        Container.max_round = max_round
        Container.vab_source_dir = self.vab_source_path
        Container.docker_image = docker_image
        with open(f"{self.vab_source_path}/jarvis/assets/tasks/formated_tasks_v1.3.json", "r") as f:
            tasks = json.load(f)
        self.tasks = [t["task"] for t in tasks]
    
    def get_indices(self) -> List[SampleIndex]:
        return list(range(len(self.tasks)))
    
    async def start_sample(self, index: SampleIndex, session: Session) -> TaskSampleExecutionResult:
        try:
            container = Container(self.tasks[index])
            session.clear()
            session.inject({"role": "system", "content": SYSTEM_PROMPT})
            while True:
                result = await container.execute(session)
                if result.status != SampleStatus.RUNNING:
                    return result
        except Exception as e:
            import traceback
            traceback.print_exc()
            return TaskSampleExecutionResult(status=SampleStatus.TASK_ERROR, result={"error": e})
        finally:
            try:
                container.close()
            except:
                pass

    def calculate_overall(self, results: List[TaskOutput]) -> Dict[str, Any]:
        average_reward = 0
        success_count = 0
        for result in results:
            if isinstance(result.result, Dict) and "success" in result.result:
                if result.result["success"]:
                    success_count += 1
                    average_reward += 1
                else:
                    final_reward = result.result["final_reward"]
                    average_reward += max(0, final_reward)
        return {
            "total_count": len(results),
            "success_count": success_count,
            "success_rate": success_count / len(results),
            "average_reward": average_reward / len(results)
        }


async def main():
    available_ports = [11000, 11001, 11002]
    available_devices = {"9":6, "1":6, "2":6}
    data_dir = "data/minecraft"
    output_dir = "outputs/minecraft"
    max_round = 100
    docker_image = "tianjiezhang/vab_minecraft:latest"
    task = Minecraft(available_ports=available_ports, available_devices=available_devices, max_round=max_round, data_dir=data_dir, output_dir=output_dir, docker_image=docker_image, name="Minecraft")
    print(Container.available_devices)
    print(Container.available_ports)
    session = Session()
    res = await task.start_sample(89, session)
    print(res)


if __name__ == "__main__":
    asyncio.run(main())
