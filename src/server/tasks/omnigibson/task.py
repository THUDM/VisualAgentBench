from src.server.task import Task, Session
from src.typings import TaskSampleExecutionResult, TaskOutput, SampleIndex, AgentOutputStatus, SampleStatus
from typing import List, Dict, Any
from src.server.tasks.omnigibson.container import Container
from src.server.tasks.omnigibson.prompt import SYSTEM_PROMPT
import os
import asyncio

class OmniGibson(Task):
    def __init__(self, available_ports, available_devices, data_dir, output_dir, max_round, **configs):
        super().__init__(**configs)
        self.vab_source_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vab_omnigibson_src")
        modified_omnigibson_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "modified_omnigibson_src")
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
        Container.modified_omnigibson_src = modified_omnigibson_src
        with open(f"{self.vab_source_path}/task/tasks.txt", "r") as f:
            tasks = f.read()
            self.tasks = eval(tasks)
    
    def get_indices(self) -> List[SampleIndex]:
        return list(range(len(self.tasks)))
    
    async def start_sample(self, index: SampleIndex, session: Session) -> TaskSampleExecutionResult:
        try:
            container = Container(self.tasks[index])
            session.clear()
            session.inject({"role": "user", "content": SYSTEM_PROMPT})
            while True:
                result = await container.execute(session)
                if result.status != SampleStatus.RUNNING:
                    return result
        except Exception as e:
            print(e)
            return TaskSampleExecutionResult(status=SampleStatus.TASK_ERROR)
        finally:
            try:
                container.close()
            except:
                pass

    def calculate_overall(self, results: List[TaskOutput]) -> Dict[str, Any]:
        average_reward = 0
        success_count = 0
        for result in results:
            if result.result:
                if result.result["success"]:
                    success_count += 1
                    average_reward += 1
                else:
                    initial_reward = result.result["initial_reward"]
                    final_reward = result.result["final_reward"]
                    reward = (final_reward - initial_reward) / (1.0 - initial_reward)
                    average_reward += max(0, reward)
        return {
            "success_rate": success_count / len(results),
            "average_reward": average_reward / len(results)
        }


async def main():
    available_ports = [12000, 12001, 12002]
    available_devices = {"0":1, "1":1, "2":1}
    data_dir = "data/omnigibson"
    output_dir = "outputs/omnigibson"
    max_round = 100
    task = OmniGibson(available_ports=available_ports, available_devices=available_devices, max_round=max_round, data_dir=data_dir, output_dir=output_dir, name="OmniGibson-std")
    print(Container.available_devices)
    print(Container.available_ports)
    session = Session()
    res = await task.start_sample(0, session)
    print(res)


if __name__ == "__main__":
    asyncio.run(main())
