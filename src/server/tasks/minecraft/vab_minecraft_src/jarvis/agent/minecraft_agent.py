from jarvis.agent.server import Server
from jarvis.assembly.core import translate_inventory, translate_equipment, translate_location
from jarvis.agent.prompts import system_prompt
import os

class Agent(object):

    def __init__(self, args):
        self.args = args
        self.server = Server(args.port)
        self.system_prompt = system_prompt
        self.result_history = []
        self.reward_history = []
        self.action_history = []

    def step(self, obs, info):
        
        image = obs['pov_path']

        if info is not None:
            success = info['success']
            message = info['message']
            num_steps = info['num_steps']
            reward = info['reward']

            if success:
                feedback = f"Your last action \"{self.action_history[-1]}\" has been executed."
            else:
                feedback = f"Your last action \"{self.action_history[-1]}\" can not be executed."

            if message is not None:
                feedback += f" {message}"
        
        else:
            feedback = "No action before."
            num_steps = 0
            reward = 0
            success = True

        self.result_history.append(success)
        self.reward_history.append(reward)

        if len(self.result_history) >= 20 and self.result_history[-15:].count(False) == 15:
            self.server.step(None, None, reward, None, "agent invalid action")
            return False, "The agent has failed 15 times in a row. The task is terminated.", "None ACTION."
        
        if len(self.result_history) >= 20 and len(set(self.action_history[-15:])) == 1:
            self.server.step(None, None, reward, None, "task limit reached")
            return False, "The agent has taken the same action 15 times in a row. The task is terminated.", "None ACTION."
        
        if len(self.result_history) >= 40 and sum(self.reward_history[-30:]) <= 30 * self.reward_history[-30] + 1e-3:
            self.server.step(None, None, reward, None, "task limit reached")
            return False, "The agent has been stuck for 30 steps. The task is terminated.", "None ACTION."

        inventory_text = translate_inventory(obs)
        equipment_text = translate_equipment(obs)
        location_text = translate_location(obs)

        if num_steps % 8 == 4 and num_steps >= 20 and obs['init_command']:
            location_text += "\nTip: If you're having difficulty finding certain mobs or plants, considering teleporting to your spawn point where these resources may be available."
        prompt = f"Feedback on the Action: {feedback}\nYour Inventory: {inventory_text}\nEquipped Item: {equipment_text}\nLocation and Orientation: {location_text}\nVision Input: "

        success, response = self.server.step(prompt, image, reward, self.args.task_name)

        with open(os.path.join(self.args.log_dir, f"{num_steps:03}_prompt.txt"), "w") as f:
            f.write(prompt)
        with open(os.path.join(self.args.log_dir, f"{num_steps:03}_response.txt"), "w") as f:
            f.write(response)
        
        if not success:
            self.server.step(None, None, reward, None, "task error")
            return False, response, None
        
        else:
            if "ACTION" not in response:
                action = "None ACTION."
            else:
                action = response.split('ACTION: ')[-1]
                action = action.split('ACTION:')[-1]
                action = action.replace('\n', '')
                if "```" in action:
                    action = action.split('```')[1]
                if "`" in action and action.count("`") == 2:
                    action = action.split('`')[1]
                if action.startswith('python'):
                    action = action.split('python')[-1]
                if 'execute(' in action:
                    action = 'execute(' + action.split('execute(', 1)[-1]
                elif 'look_up(' in action:
                    action = 'look_up(' + action.split('look_up(', 1)[-1]
                elif 'craft(' in action:
                    action = 'craft(' + action.split('craft(', 1)[-1]
                elif 'smelt(' in action:
                    action = 'smelt(' + action.split('smelt(', 1)[-1]
                elif 'equip(' in action:
                    action = 'equip(' + action.split('equip(', 1)[-1]
                elif 'teleport_to_spawn(' in action:
                    action = 'teleport_to_spawn(' + action.split('teleport_to_spawn(', 1)[-1]
                action = action.split('#')[0]
                action = action.strip()
            
            self.action_history.append(action)
            if "execute(" in action and ("terminate" in action or "task_complete" in action):
                self.server.step(None, None, reward, None, "task failed")
                return False, response, action
        
        return True, response, action
