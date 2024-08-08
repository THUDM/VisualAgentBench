import os
import yaml
from utils.server import Server

class Agent(object):

    def __init__(self, args):
        self.args = args
        task_json = yaml.load(open("task/task_goal.json", "r"), Loader=yaml.FullLoader)
        self.task_goal = task_json[args.task]
        self.action_history = []
        self.result_history = []
        self.reward_history = []
        self.msg_history = []
        self.summary = ""
        self.server = Server(args.port)

        self.log_dir = args.log_dir
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def step(self, obs):
        
        image = obs['image']
        grasped_obj = obs['grasped_obj']
        rooms = obs['rooms']
        current_room = obs['current_room']
        reward = obs['reward']
        done = obs['done']
        num_step = obs['num_step']
        result = obs['return']
        msg = obs['message']

        self.result_history.append(result)
        self.msg_history.append(msg)
        self.reward_history.append(reward)

        if len(self.result_history) >= 10 and len(set(self.result_history[-8:])) == 1 and self.result_history == False:
            self.server.step(None, None, reward, None, None, "agent invalid action")
            return False, "None", "None"
        
        if len(self.action_history) >= 40 and self.reward_history[-1] <= self.reward_history[-2] and self.reward_history[-1] <= self.reward_history[-10] and \
            self.reward_history[-1] <= self.reward_history[-9] and self.reward_history[-1] <= self.reward_history[-11]:
            self.server.step(None, None, reward, None, None, "task limit reached")
            return False, "None", "None"
        
        if len(self.action_history) >= 30 and len(set(self.reward_history[-5:])) == 1 and self.reward_history[-1] <= self.reward_history[0]:
            self.server.step(None, None, reward, None, None, "task limit reached")
            return False, "None", "None"
        
        task_goal = self.task_goal

        action_feedback = ""
        if len(self.action_history) >= 1:
            action_feedback = f"The last action is `{self.action_history[-1]}`, the feedback is \"{msg}\"."
        else:
            action_feedback = "None actions before."
        
        if grasped_obj == None:
            at_hand_obj = "None."
        else:
            at_hand_obj = f"{grasped_obj}."

        reachable_rooms = ""
        for room in rooms:
            if room != rooms[-1]:
                reachable_rooms += f"{room}, "
            else:
                reachable_rooms += f"{room}."
        if reachable_rooms == "":
            reachable_rooms = "None."

        prompt = f"Action Feedback: {action_feedback}\nAt Hand Object: {at_hand_obj}\nCurrent Room: {current_room}.\nVision Input: "
        
        success, response = self.server.step(prompt, image, reward, task_goal, reachable_rooms)
        
        step_dir = os.path.join(self.log_dir, f"{num_step:03}")
        if not os.path.exists(step_dir):
            os.makedirs(step_dir)
        
        with open(os.path.join(step_dir, "prompt.txt"), 'w') as f:
            f.write(prompt)
        with open(os.path.join(step_dir, "response.txt"), 'w') as f:
            f.write(response)

        if not success:
            self.server.step(None, None, reward, None, None, "task error")
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
                if "python" in action:
                    action = action.split('python')[-1]
                if "`" in action and "```" not in action:
                    action = action.split("`")[1]
                action = action.split("#")[0]
                action = action.strip()
            self.action_history.append(action)

            if len(self.result_history) >= 4 and len(set(self.result_history[-3:])) == 1 and len(set(self.action_history[-4:])) == 1 \
                and "turn" not in self.action_history[-1]:
                    self.server.step(None, None, reward, None, None, "task limit reached")
                    return False, response, action
            
            if len(self.result_history) >= 6 and len(set(self.action_history[-6:])) == 1 and "turn" in self.action_history[-1]:
                self.server.step(None, None, reward, None, None, "task limit reached")
                return False, response, action
        
        if action == "done()":
            self.server.step(None, None, reward, None, None, "task failed")
        
        return True, response, action
