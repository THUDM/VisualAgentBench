from jarvis.assembly.marks import MarkI
from jarvis.stark_tech.env_interface import MinecraftWrapper
from jarvis.assembly.env import RenderWrapper, build_env_yaml, build_reward_dict
from jarvis.assembly.func_call import look_up, teleport

from jarvis.assembly.evaluate import monitor_function, Reward
from jarvis.assembly.base import get_task_config
from jarvis.utils import log
from jarvis.env.prompt_examiner import check_prompt

from functools import partial
import os
from rich import print as rprint
import cv2
import copy

class Env(object):
    
    def __init__(self, args):
        self.args = args

        task_name = args.task_name
        task_config_dict = get_task_config(task_name)
        self.task_config_dict = copy.deepcopy(task_config_dict)
        reward_dict = build_reward_dict(self.task_config_dict)
        self.reward_dict = {}
        for k, v in task_config_dict['task_obj'].items():
            if "minecraft:" in k:
                self.task_config_dict['task_obj'][k.split("minecraft:")[1]] = self.task_config_dict['task_obj'].pop(k)
        for k, v in reward_dict.items():
            if "minecraft:" in k:
                self.reward_dict[k.split("minecraft:")[1]] = v

        task_env_setting = self.task_config_dict['env']
        task_env_setting['task_name'] = task_name
        self.init_command = False
        if 'init_command' in task_config_dict:
            task_env_setting['init_command'] = task_config_dict['init_command']
            if task_config_dict['init_command'] != []:
                self.init_command = True
        task_env_yaml = build_env_yaml(task_env_setting)

        env = MinecraftWrapper(task_name)
        env = RenderWrapper(env)
        env.reset()
        env.maximum_step = 1200000 - 1
        
        mark = MarkI(env=env)
        mark.reset()

        mark.env_yaml = task_env_yaml

        mark.current_task = self.task_config_dict
        mark.record_goals = {}
        mark.record_prompts = {}

        self.env = env
        self.mark = mark
        self.done = False
        self.accumlated_reward = 0
        self.num_steps = 0

        self.reward_model = Reward(self.task_config_dict['task_obj'], self.reward_dict)
        self.spawn_point = None

    def reset(self):
        self.env.reset()
        self.mark.reset()
        self.mark.record_infos = self.mark.post_infos([self.env.step(self.env.noop_action())[-1]])
        self.done = monitor_function(self.task_config_dict['task_obj'], self.mark.record_infos[-1])[0]
        self.accumlated_reward = self.reward_model.monitor_reward(self.mark.record_infos[-1])
        print(self.mark.record_infos)
        rprint(r"[bold blue][INFO]: Current task: [/bold blue]", self.task_config_dict['task'])
        obs = self.mark.record_infos[-1]
        img = obs['pov']
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_path = os.path.join(self.args.log_dir, f"{self.num_steps:03}.png")
        cv2.imwrite(img_path, img)
        obs['pov_path'] = img_path
        obs['init_command'] = self.init_command
        x = obs['player_pos']['x']
        y = obs['player_pos']['y']
        z = obs['player_pos']['z']
        self.spawn_point = (x, y, z)
        return obs

    def step(self, action: str):
        
        self.num_steps += 1
        action = action.strip()
        success, message = False, "Error: invalid action."

        try:
            action = action.replace("Craft(", "craft(").replace("Smelt(", "smelt(").replace("Equip(", "equip(").replace("Teleport_to_spawn(", "teleport_to_spawn(").replace("Look_up(", "look_up(").replace("Execute(", "execute(").replace("Execute(", "execute(")
            action = action.replace("craft (", "craft(").replace("smelt (", "smelt(").replace("equip (", "equip(").replace("teleport_to_spawn (", "teleport_to_spawn(").replace("look_up (", "look_up(").replace("execute (", "execute(")
            if action.startswith("craft(") or action.startswith("smelt(") or action.startswith("equip(") or action.startswith("teleport_to_spawn(") or action.startswith("look_up("):
                func = action.split("(")[0]
                args_str = action.split("(")[1].split(")")[0]
                args_str = args_str.replace(", ", ",")

                if (args_str == "" or args_str == " ") and func != "teleport_to_spawn":
                    success, message = False, f"Error: `{func}` function takes at least one argument."

                else:   
                    args = args_str.split(",")
                    for id, arg in enumerate(args):
                        if "=" in arg:
                            arg = arg.split("=")[1]
                        if (arg.startswith('"') or arg.startswith("'")):
                            arg = arg[1:]
                        if (arg.endswith('"') or arg.endswith("'")):
                            arg = arg[:-1]
                        arg = arg.strip().lower()
                        args[id] = arg

                    if func == "craft":
                        if len(args) == 1:
                            success, message = self.mark.do("craft", target=args[0], target_num=1)
                            if success:
                                message = f"Successfully crafted 1 {args[0]}."
                        elif len(args) == 2:
                            if args[1].isdigit():
                                target_num = int(args[1])
                                if target_num < 1:
                                    success, message = False, "Error: the second argument of `craft` function must be an integer greater than 0."
                                else:
                                    success, message = self.mark.do("craft", target=args[0], target_num=target_num)
                                if success:
                                    message = f"Successfully crafted {args[1]} {args[0]}."
                            else:
                                success, message = False, "Error: the second argument of `craft` function must be an integer."
                        else:
                            success, message = False, "Error: `craft` function takes 1 or 2 arguments."

                    if func == "smelt":
                        if len(args) == 1:
                            success, message = self.mark.do("smelt", target=args[0], target_num=1)
                            if success:
                                message = f"Successfully smelted 1 {args[0]}."
                        elif len(args) == 2:
                            if args[1].isdigit():
                                target_num = int(args[1])
                                if target_num < 1:
                                    success, message = False, "Error: the second argument of `smelt` function must be an integer greater than 0."
                                else:
                                    success, message = self.mark.do("smelt", target=args[0], target_num=target_num)
                                if success:
                                    message = f"Successfully smelted {args[1]} {args[0]}."
                            else:
                                success, message = False, "Error: the second argument of `smelt` function must be an integer."
                        else:
                            success, message = False, "Error: `smelt` function takes 1 or 2 arguments."

                    if func == "equip":
                        if len(args) == 1:
                            success, message = self.mark.do("equip", target_item=args[0])
                            if success:
                                message = f"Successfully equipped {args[0]}."
                        else:
                            success, message = False, "Error: `equip` function takes exactly 1 argument."
                    
                    if func == "look_up":
                        if len(args) == 1:
                            success, message = True, look_up(args[0])
                        else:
                            success, message = False, "Error: `look_up` function takes exactly 1 argument."
                    
                    if func == "teleport_to_spawn":
                        if args_str.strip() == "":
                            success, message = teleport(self.spawn_point[0], self.spawn_point[1], self.spawn_point[2], self.env, self.mark)
                        else:
                            success, message = False, "Error: `teleport_to_spawn` function takes no argument."
                    
            elif action.startswith("execute("):
                args_str = action.split("(")[1].split(")")[0]
                args_str = args_str.strip()
                if '",' not in args_str and "'," not in args_str:
                    if "=" in args_str:
                        args_str = args_str.split("=")[1]
                    if (args_str.startswith('"') or args_str.startswith("'")) and (args_str.endswith('"') or args_str.endswith("'")):
                        args_str = args_str[1:-1]
                        prompt = args_str.strip()
                        flag, prompt_message = check_prompt(prompt)
                        if flag:
                            ret_flag, ret_info = self.mark.do(prompt, reward = float('inf'), monitor_fn = partial(monitor_function, self.task_config_dict['task_obj']), timeout=self.args.steve_step)
                            message = "The executor has attempted to execute the action according to your prompt. You should check whether your intention has been fulfilled."
                            success = True
                        else:
                            success, message = False, prompt_message
                    else:
                        success, message = False, "Error: the `prompt` and `goal_item` argument in `execute` function must be string."
                else:
                    if '",' in args_str:
                        prompt = args_str.split('",')[0]
                        remaining_args = args_str.split('",')[1:]
                    elif "'," in args_str:
                        prompt = args_str.split("',")[0]
                        remaining_args = args_str.split("',")[1:]
                    if "=" in prompt:
                        prompt = prompt.split("=")[1]
                    prompt = prompt.strip()
                    if (prompt.startswith('"') or prompt.startswith("'")):
                        prompt = prompt[1:]
                    prompt = prompt.strip()
                    flag, prompt_message = check_prompt(prompt)
                    if not flag:
                        success, message = False, prompt_message
                    
                    else:
                        if len(remaining_args) == 1 and "'," not in remaining_args[0] and '",' not in remaining_args[0]:
                            success, message = False, "Error: the `execute` function takes 1 or 3 arguments. And the second argument must be a string."
                        
                        else:
                            if len(remaining_args) == 1 and "'," in remaining_args[0]:
                                remaining_args = remaining_args[0].split("',")
                            elif len(remaining_args) == 1 and '",' in remaining_args[0]:
                                remaining_args = remaining_args[0].split('",')
                            args = [arg.strip() for arg in remaining_args]
                            for i, arg in enumerate(args):
                                if "=" in arg:
                                    arg = arg.split("=")[1]
                                if (arg.startswith('"') or arg.startswith("'")):
                                    arg = arg[1:]
                                if (arg.endswith('"') or arg.endswith("'")):
                                    arg = arg[:-1]
                                arg = arg.strip().lower()
                                args[i] = arg
                            if not args[1].isdigit():
                                success, message = False, "Error: the third argument of `execute` function must be an integer."
                            else:
                                pos = self.mark.mark_shell.craft_script.find_in_inventory(self.mark.mark_shell.craft_script.get_labels(), args[0])
                                if pos == None:
                                    count = int(args[1])
                                else:
                                    quantity = 1
                                    if "quantity" in self.mark.mark_shell.craft_script.get_labels()[pos]:
                                        quantity = self.mark.mark_shell.craft_script.get_labels()[pos]['quantity']
                                    count = min(64, int(args[1]) + quantity)
                                ret_flag, ret_info = self.mark.do(prompt, reward = float('inf'), monitor_fn = partial(monitor_function, {args[0]: count}), timeout=self.args.steve_step)
                                if ret_flag:
                                    message = "Your subgoal has been successfully completed by the executor."
                                else:
                                    message = "The executor has reached the maximum number of steps for this turn without completing your subgoal."
                                success = True
            
            else:
                success, message = False, "Error: Invalid function. Please use one of the following functions: `craft`, `smelt`, `equip`, `teleport_to_spawn`, `look_up`, or `execute`."
                if "(" not in action or ")" not in action:
                    success, message = False, "Error: Invalid action. Please use the format of python function: func(args)."
                if action == "None ACTION.":
                    success, message = False, "Error: Invalid output. You should include \"ACTION\" in your output."

        except Exception as e:
            log(self.args, str(e), "red")
            success, message = False, f"Error: Unknown error occurred. Try moving, equipping something else, and then attempting the action again."
        
        self.mark.record_prompts[len(self.mark.record_frames)] = action
        
        obs = self.mark.record_infos[-1]
        self.done = monitor_function(self.task_config_dict['task_obj'], obs)[0]
        self.accumlated_reward = self.reward_model.monitor_reward(obs)
        info = {
            "success": success,
            "message": message,
            "num_steps": self.num_steps,
            "reward": self.accumlated_reward
        }
        img = obs['pov']
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_path = os.path.join(self.args.log_dir, f"{self.num_steps:03}.png")
        cv2.imwrite(img_path, img)
        obs['pov_path'] = img_path
        obs['init_command'] = self.init_command
        return obs, self.accumlated_reward, self.done, info

    def close(self, write_video=False):
        if write_video:
            prompt_list = sorted(self.mark.record_prompts.items())
            current_prompt_idx = 0
            for id, frame in enumerate(self.mark.record_frames):
                if id >= prompt_list[current_prompt_idx][0]:
                    current_prompt_idx += 1
                if current_prompt_idx >= len(prompt_list):
                    break
                frame = frame.copy()
                self.mark.record_frames[id] = cv2.putText(frame, prompt_list[current_prompt_idx][1], (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 1)
                
            self.mark.make_traj_video(f"{self.args.log_dir}/video.mp4")
        self.env.close()
