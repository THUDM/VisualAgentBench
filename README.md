# VisualAgentBench (VAB)

![](./assets/cover.png)

<p align="center">
   <a href="" target="_blank">🌐 Website</a> | <a href="" target="_blank">📃 Paper </a> | <a href="" target="_blank"> 🗂️ VAB Training (Under Construction)
</p>

# VisualAgentBench: Towards Large Multimodal Models as Visual Foundation Agents

**VisualAgentBench (VAB)** is the first benchmark designed to systematically evaluate and develop large multi models (LMMs) as visual foundation agents, which comprises 5 distinct environments across 3 types of representative visual agent tasks (Embodied, GUI, and Visual Design)

https://github.com/user-attachments/assets/4a1a5980-48f9-4a70-a900-e5f58ded69b4

- VAB-OmniGibson (Embodied)
- VAB-Minecraft (Embodied)
- VAB-Mobile (GUI)
- VAB-WebArena-Lite (GUI, based on [WebArena](https://github.com/web-arena-x/webarena) and [VisualWebArena](https://github.com/web-arena-x/visualwebarena))
- VAB-CSS (Visual Design)

Compared to its predecessor [AgentBench](https://github.com/THUDM/AgentBench), VAB highlights visual inputs and the enabling of **Foundation Agent** capability development with training open LLMs/LMMs on trajectories. 

![](./assets/visualagentbench.png)

![](./assets/intro.png)

## Table of Contents

-   [Dataset Summary](#dataset-summary)
-   [Leaderboard](#leaderboard)
-   [Quick Start](#quick-start)
-   [Next Steps](#next-steps)
-   [Citation](#citation)

## Dataset Summary

We offer two splits for each dataset: Testing and Training. Different from its predecessor [AgentBench](https://github.com/THUDM/AgentBench), VAB is accompanied with a trajectory training set for behavior cloning (BC) training, which allows development of more potent visual foundation agents with emerging open LMMs.

![](./assets/statistics.png)

## Leaderboard

Here is the scores on test set results of VAB. All metrics are task Success Rate (SR). Noted that proprietary LMMs are tested with mere **Prompting**, and open LMMs are tested after **Multitask Finetuning** on VAB training set, as they usually fail to follow complicated agent task instructions.

![](./assets/leaderboard.png)

## Quick Start
TODO

## Acknowledgement
This project is heavily built upon the following repositories (to be updated):

* [AgentBench](https://github.com/THUDM/AgentBench): which serves as the backbone framework of this project for efficient and reliable parallel agent evaluation.
* [WebArena](https://github.com/web-arena-x/webarena) and [VisualWebArena](https://github.com/web-arena-x/visualwebarena): which serve as the testing framework and data source for VAB-WebArena-Lite dataset.
* [OmniGibson](https://github.com/StanfordVL/OmniGibson): which serves as the environment for VAB-OmniGibson.
* [JARVIS-1](https://github.com/CraftJarvis/JARVIS-1): VAB-Minecraft's framework is adapted from JARVIS-1's pipeline.
* [STEVE-1](https://github.com/Shalev-Lifshitz/STEVE-1): which serves as the action executor for VAB-Minecraft.

## Citation

```
```
