# VAB-Minecraft

## Get Started

### Install Dependencies

VAB-Minecraft is built upon [JARVIS-1](https://arxiv.org/abs/2311.05997), and this repo includes the necessary parts of JARVIS-1. You can refer to their [repo](https://github.com/CraftJarvis/JARVIS-1?tab=readme-ov-file#install-dependencies) to install necessary dependencies, including the Minecraft environment and the weights of [STEVE-1](https://arxiv.org/abs/2306.00937).

### Usage

- You need to set the environment variable `TMPDIR` and `OPENAI_API_KEY` first.

    ```bash
    export TMPDIR=/tmp
    export OPENAI_API_KEY="sk-******"
    pip install opencv-python coloredlogs psutil daemoniker lxml Pyro4 xmltodict dm-tree einops transformers x_transformers==0.27.1 nltk colorama
    ```

- To evaluate `gpt-4o` with all the 116 tests, run:

    ```bash
    python parellel_test.py
    ```

    The running result of each tests will be shown in `test_results/test_openai.txt`.

- If you want to evaluate `gpt-4o` with a single task, run:

    ```bash
    python main.py --task_name <item_name>
    ```

    `<item_name>` is the name of the object to obtain, like `cake`, `dried_kelp`. See `jarvis/assets/tasks/formated_tasks_v1.3.json` for all 116 test tasks.

## Test Set and Training Set

Our 116 test tasks are in `jarvis/assets/tasks/formated_tasks_v1.3.json`.

For training tasks, the 40 tasks designed by us are in `jarvis/assets/training_tasks.json`,
and we also use 132 tasks from JARVIS-1, located at `jarvis/assets/tasks.json`. All 382 bootstrapped trajectories can be downloaded from [here](TRAINING_SET_LINK).

## Comparison with JARVIS-1

### What we Adopt from JARVIS-1

We use the Minecraft environment setup in JARVIS-1, and adapt 4 types of actions (`craft`, `smelt`, `equip`, and calling STEVE-1) implemented in JARVIS-1. For `craft` and `smelt`, we fix appeared bugs during our testing.

We also utilize 132 tasks from JARVIS-1's offline memory to bootstrap 206 successful trajectories as part of our training set.

### Differences between JARVIS-1

1. Different from JARVIS-1 utilizing large language models (LLMs), we design a new pipeline for large multimodal models (LMMs) as agents.

    - The LMMs can call 6 types of actions: `look_up`, `teleport_to_spawn` and the other 4 from JARVIS-1. The implementations of `look_up` and `teleport_to_spawn` are at `jarvis/assembly/func_call.py`.

    - VAB-Minecraft uses [ReAct](https://arxiv.org/abs/2210.03629) to test LMMs in a multi-turn dialog manner. JARVIS-1 uses a different pipeline of self-check and self-explain.

    - Our implemented pipeline decomposes LMM agent and Minecraft environment. With the information or feedback from Minecraft environment, `jarvis/agent` organizes them into language and image prompts, and sends requests to LMM APIs. `jarvis/env` wraps Minecraft environment, providing necessary information for LMM agents, generating reward signals, and interpreting the language actions from LMM agents.

2. We set up 116 item obtaining tasks with suitable initializing configs to test LMM agents.

3. We newly design 40 training tasks and use `gpt-4-turbo` to bootstrap 176 successful trajectories as another part of our training set.

## Acknowledgement

VAB-Minecraft is built upon several projects related to Minecraft. We are sincerely grateful for their contributions and efforts.

- [JARVIS-1](https://github.com/CraftJarvis/JARVIS-1): We utilize the Minecraft environment setup, action interface, and tasks from JARVIS-1. (See [What we Adopt from JARVIS-1](#What-we-Adopt-from-JARVIS-1))

- [STEVE-1](https://github.com/Shalev-Lifshitz/STEVE-1): This is an instruction-tuned Video Pretraining (VPT) model for Minecraft. One of the actions for LMM agents involves calling STEVE-1.

- [MineRL](https://github.com/minerllabs/minerl): This platform is used for developing agents in the Minecraft environment. The Minecraft environment we use is a hybrid between MineRL and MCP-Reborn.

- [MCP-Reborn](https://github.com/Hexeption/MCP-Reborn): This is a mod coder pack for Minecraft. The Minecraft environment we use is a hybrid between MineRL and MCP-Reborn.