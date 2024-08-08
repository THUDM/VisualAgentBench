import cv2
import gymnasium as gym

class RenderWrapper(gym.Wrapper):
    
    def __init__(self, env, window_name="minecraft"):
        super().__init__(env)
        self.window_name = window_name
    
    def step(self, action):
        obs, reward, terminated, truncated, info = self.env.step(action)
        # bgr_pov = cv2.cvtColor(info['pov'], cv2.COLOR_RGB2BGR)
        # cv2.imshow(self.window_name, bgr_pov)
        # cv2.waitKey(1)
        return obs, reward, terminated, truncated, info

    def reset(self):
        obs, info = self.env.reset()
        # bgr_pov = cv2.cvtColor(info['pov'], cv2.COLOR_RGB2BGR)
        # cv2.imshow(self.window_name, bgr_pov)
        # cv2.waitKey(1)
        return obs, info
    
class RecordWrapper(gym.Wrapper):
    def __init__(self, env):
        super().__init__(env)
        self.frames = []
    
    def step(self, action):
        obs, reward, terminated, truncated, info = self.env.step(action)
        self.frames.append(info['pov'])
        return obs, reward, terminated, truncated, info

    def reset(self):
        obs, info = self.env.reset()
        self.frames.append(info['pov'])
        return obs, info
    
import yaml
import random 
from pathlib import Path
import json
import copy

from jarvis.assets import SPAWN_FILE
with open(SPAWN_FILE, 'r') as f:
    spawn = json.load(f)

seeds = {}
for s in spawn:
    if s['biome'] not in seeds.keys():
        seeds[s['biome']] = []
    seeds[s['biome']].append(s['seed'])

ENV_CONFIG_DIR = Path(__file__).parent.parent / "global_configs" / "envs"
INGREDIENTS_JSON = Path(__file__).parent.parent / "assets" / "ingredients.json"
STEP_REWARDS_JSON = Path(__file__).parent.parent / "assets" / "step_rewards.json"

def recompute_item_reward(item_reward, init_inventory):
    item_reward = copy.deepcopy(item_reward)
    total_reward = sum(item_reward.values())
    for k, v in list(item_reward.items()):
      if k in init_inventory:
          item_reward.pop(k)
    new_total_reward = sum(item_reward.values())
    for k, v in list(item_reward.items()):
        item_reward[k] = item_reward[k] / new_total_reward * total_reward
    return item_reward

def build_env_yaml(env_config):
    with open(ENV_CONFIG_DIR / "jarvis.yaml", 'r') as f:
        env_yaml = yaml.load(f, Loader=yaml.FullLoader)
    # biome -> seed: 12345, close_ended: True
    if env_config["biome"]:
        env_yaml['candidate_preferred_spawn_biome'] = [env_config["biome"]]
        if env_config["biome"] in seeds.keys():
            env_yaml['close_ended'] = True
            env_yaml['seed'] = random.choice(seeds[env_config["biome"]])

    # mobs -> summon_mobs
    if env_config["mobs"]:
        env_yaml['summon_mobs'] = env_config["mobs"]

    # init_inventory -> init_inventory
    if env_config["init_inventory"]:
        for i, (k, v) in enumerate(env_config["init_inventory"].items()):
            if k.isdigit():
                k = int(k)
                env_yaml['init_inventory'][k] = v
            else:
                env_yaml['init_inventory'][i] = {
                    "type": k[10:] if "minecraft:" in k else k,
                    "quantity": v
                }
    
    # init_command -> custom_init_commands
    if "init_command" in env_config and len(env_config["init_command"]) > 0:
        with open(INGREDIENTS_JSON, 'r') as f:
            ingredients = json.load(f)
        env_yaml['custom_init_commands'] += ingredients["clean"]
        for command in env_config["init_command"]:
            if command.startswith("/"):
                env_yaml['custom_init_commands'].append(command)
            else:
                env_yaml['custom_init_commands'] += ingredients[command]

    if "task_name" in env_config:
        filename = f"{env_config['task_name']}.yaml"
    else:
        filename = "demo.yaml"

    with open(ENV_CONFIG_DIR / filename, 'w') as f:
        yaml.dump(env_yaml, f, sort_keys=False)
    
    return env_yaml

def build_reward_dict(task_config):
    with open(STEP_REWARDS_JSON, 'r') as f:
        step_rewards = json.load(f)
    item_reward = {}
    if "minecraft:" + task_config["task"] in step_rewards:
        item_reward = step_rewards["minecraft:" + task_config["task"]]
    item_reward = recompute_item_reward(item_reward, task_config["env"]["init_inventory"])
    return item_reward
