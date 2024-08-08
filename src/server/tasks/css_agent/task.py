import os
import re
import shlex
import json
import base64
from typing import Dict, List, Any, Tuple
import numpy as np

import uuid
import time

# import openai
# from openai import OpenAI

from skimage import io
from skimage.metrics import structural_similarity as ssim
from skimage.transform import resize

# from src.task import Task, Dataset, DataPiece
from src.server.task import Task, Session
from src.typings import TaskSampleExecutionResult, TaskOutput, SampleIndex, AgentOutputStatus, SampleStatus
from .actions import CSSInteractor

# Thought and Action
INSTRUCTIONS = """
You are a CSS agent. You will be given a target screenshot and an html file. Fix the css rules used in the html file to match the target screenshot.
To facilitate the process, you can use the following tools provided by the system:
1. get_selectors_by_html_elements
Sometimes, the exact selector of the rule you want to edit is not clear. This tool takes the html element specification that could be directly passed to soup.find_all as input and returns the matched selectors. For example, get_selectors_by_html_elements("'a', {'data-custom': 'custom-value'}, string='haha', class_='xxx'"). The argument should be the string representation of valid arguments of the find_all method in BeautifulSoup, which means we can directly do eval(f"soup.find_all({argument})"). Please strictly stick to the usage of BeautifulSoup. Make sure the arguments are valid (e.g., the tag name must be wrapped with quotes, attributes should be a dictionary). You can use this tool to first find the selector of the rule of a specific html element whose style you want to fix.
2. select_rule
This takes the css rule's selectorText as input and returns the rule. You can use this tool to view the properties of a rule, which may help you to decide which rule to edit. Usually, it's recommended to first use this tool to view the rule before deciding which rule to edit.
3. edit_rule
This takes the css rule's selectorText, the property name, and the value of the property as input. You can use this tool to change the value of a property of a rule or insert a new property to the rule, if you believe this change would make the rule closer to the target screenshot. Note that, most of the layout issues are related to the categorical properties, such as border, float, display, overflow, position, etc.
4. revert_last_edit
This tool reverts the last single edit you made. You can use this tool to undo the last edit, if you believe it was a mistake. This action takes no arguments.

Make sure the selectorText is valid based on the html file, i.e., it's from the class or id of the html elements. In addition, please focus on the major layout issue! Ignore the font size, font family, and color of the text, even if you believe they are not perfect.

You can only take ONE action at a time!! For each step, you may first state your thought, then take an action following the format of Thought: ...\n Action: ... (do not add any linebreak after the colon).
For example, you may output 
"Thought: I think I should adjust the alignment property of the rule, because the target screenshot shows the text should be centered.\n Action: edit_rule('.templatemo_menu li', 'text-align', 'center')".

After editing a rule or inserting a rule, you will see the updated screenshot of the html file. You should decide your next action (e.g., to revert the last edit or keep adjusting the css) based on the updated screenshot. If you think you have already fixed the css style, please say exactly "I have fixed the css style".

Please strictly follow the format specified above, and please don't repeat the same action in multiple rounds. Also note that, you don't need to worry about how these tools are executed, your job is just to correctly predict the tool invocation.
"""

# Action only
# INSTRUCTIONS = """
# You are a CSS agent. You will be given a target screenshot and an html file. Fix the css rules used in the html file to match the target screenshot.
# To facilitate the process, you can use the following tools provided by the system:
# 1. get_selectors_by_html_elements
# Sometimes, the exact selector of the rule you want to edit is not clear. This tool takes the html element specification that could be directly passed to soup.find_all as input and returns the matched selectors. For example, get_selectors_by_html_elements("'a', {'data-custom': 'custom-value'}, string='haha', class_='xxx'"). The argument should be the string representation of valid arguments of the find_all method in BeautifulSoup, which means we can directly do eval(f"soup.find_all({argument})"). Please strictly stick to the usage of BeautifulSoup. Make sure the arguments are valid (e.g., the tag name must be wrapped with quotes, attributes should be a dictionary). You can use this tool to first find the selector of the rule of a specific html element whose style you want to fix.
# 2. select_rule
# This takes the css rule's selectorText as input and returns the rule. You can use this tool to view the properties of a rule, which may help you to decide which rule to edit. Usually, it's recommended to first use this tool to view the rule before deciding which rule to edit.
# 3. edit_rule
# This takes the css rule's selectorText, the property name, and the value of the property as input. You can use this tool to change the value of a property of a rule or insert a new property to the rule, if you believe this change would make the rule closer to the target screenshot. Note that, most of the layout issues are related to the categorical properties, such as border, float, display, overflow, position, etc.
# 4. revert_last_edit
# This tool reverts the last single edit you made. You can use this tool to undo the last edit, if you believe it was a mistake. This action takes no arguments.

# Make sure the selectorText is valid based on the html file, i.e., it's from the class or id of the html elements. In addition, please focus on the major layout issue! Ignore the font size, font family, and color of the text, even if you believe they are not perfect.

# You can only take ONE action at a time!! For each step, directly output an action following the format of Action: ... (do not add any linebreak after the colon). Don't output anything else.
# For example, you may output 
# "Action: edit_rule('.templatemo_menu li', 'text-align', 'center')".

# After editing a rule or inserting a rule, you will see the updated screenshot of the html file. You should decide your next action (e.g., to revert the last edit or keep adjusting the css) based on the updated screenshot. If you think you have already fixed the css style, please say exactly "I have fixed the css style".

# Please strictly follow the format specified above, and please don't repeat the same action in multiple rounds. Also note that, you don't need to worry about how these tools are executed, your job is just to correctly predict the tool invocation.
# """


def compare_images_ssim_gray(img1_path, img2_path):   # for now we also use this as the metric
    # Read the images as color
    img1 = io.imread(img1_path, as_gray=True)
    img2 = io.imread(img2_path, as_gray=True)

    # print(img1.shape, img2.shape)
    # Resize img2 to match the dimensions of img1
    fake_size_change = False
    if img1.shape != img2.shape:
        resize_percentage = abs(np.array(img2.shape) - np.array(img1.shape)) / np.array(img2.shape)
        if all(resize_percentage < 0.1):
            fake_size_change = True
        img2 = resize(img2, img1.shape)
    #     return 0


    # Cast the images to integer type
    img1 = (img1 * 255).astype(np.uint8)
    img2 = (img2 * 255).astype(np.uint8)

    # Compute SSIM for each color channel
    ssim_val = ssim(img1, img2)
    # print(ssim_val)
    if fake_size_change:
        ssim_val = 0.5 + ssim_val / 2

    return ssim_val




class CSSAgent(Task):
    def __init__(self, data_dir, round=10, **configs):
        super().__init__(**configs)
        self.round = round
        self.data_dir = data_dir
        self.output_dir = configs.pop("output_dir", None)
        self.instruction = configs.pop("instruction", True)
        self.gold_selector = configs.pop("gold_selector", False)
        self.hint = configs.pop("hint", False)
        print("output_dir:", self.output_dir)
        self.working_dir = uuid.uuid4().hex + '_' + os.path.basename(self.output_dir)


        # load the dataset
        self.data: List[Tuple[str, dict]] = []
        self.input_dirs: List[str] = []
        self.targets: List[dict] = []
        directories = os.listdir(self.data_dir)
        # for dir in directories[::-1]:
        for dir in directories:
            dir = os.path.join(self.data_dir, dir)
            target_screenshot = os.path.join(dir, "index.png")
            with open(os.path.join(dir, "corruption", "distance.txt"), "r") as f:  # this is for sim(target, output)
            # with open(os.path.join(dir, "distance.txt"), "r") as f:   # this is for sim(output, target)
                distance = float(f.read().strip())
            if distance < 0.2:
                continue

            with open(os.path.join(dir, "corruption", "instruction.txt"), "r") as f:
                instruction = f.read()
            if "This is an invalid example" in instruction:
                continue

            self.input_dirs.append(dir)
            self.targets.append({"screenshot": target_screenshot, "distance": distance})
            self.data.append((dir, {"screenshot": target_screenshot, "distance": distance}))

    
    def calculate_overall(self, results: List[TaskOutput]) -> Dict[str, Any]:
        outputs = [None for _ in range(len(self.data))]
        for result in results:
            outputs[result.index] = result.result
        targets = self.targets
        
        def main_metric():
            distance_sum = 0
            em_sum = 0
            improve_sum = 0
            count = 0
            print(len(outputs))
            for i in range(len(outputs)):
                count += 1
                # new_distance = 1 - compare_images_ssim_gray(outputs[i]['screenshot'], targets[i]['screenshot'])
                new_distance = 1 - compare_images_ssim_gray(targets[i]['screenshot'], outputs[i]['screenshot'])
                # with open(os.path.join(os.path.dirname(targets[i]['screenshot']), "distance.txt"), "w") as f:
                #     f.write(str(new_distance))
                print(i, new_distance, targets[i]['distance'])
                distance_sum += new_distance
                if new_distance < targets[i]['distance'] - 0.05:
                    improve_sum += 1
                if new_distance < 0.1:
                    em_sum += 1

            return distance_sum / count, improve_sum / count, em_sum / count
        
        rewards, improve, em = main_metric()
        return {
            "main": em,
            "improve": improve,
            "em": em,
            "distance": rewards
        }

    
    def get_indices(self) -> List[SampleIndex]:
        return list(range(len(self.data)))[:5]


    # def predict_single(self, session: Session, data_item): # return OUTPUT object, need to be json serializable
    async def start_sample(self, index: SampleIndex, session: Session) -> TaskSampleExecutionResult:
        data_item = self.input_dirs[index]

        # if .cache directory does not exist, create it
        if not os.path.exists(f"./cache/{self.working_dir}"):
            os.makedirs(f"./cache/{self.working_dir}")

        # cp the directory to the temporay working directory
        os.system(f"cp -r {data_item} ./cache/{self.working_dir}/")
        # change data_item to the new path
        data_item = f"./cache/{self.working_dir}/" + os.path.basename(data_item)

        target_screenshot = os.path.join(data_item, "index.png")

        current_screenshot = os.path.join(data_item, "corruption", "index_corrupted.png")

        # concat_two_images(target_screenshot, current_screenshot, os.path.join(data_item, "concatenated_image.png"))

        if os.path.exists(os.path.join(data_item, "corruption", "instruction.txt")) and self.instruction:
            with open(os.path.join(data_item, "corruption", "instruction.txt")) as f:
                instruction = f.read()
        else:
            instruction = "Before taking any actions, please carefully compare the two screenshots to find the difference in layout."
        
        if self.gold_selector:
            with open(os.path.join(data_item, "corruption", "record.txt")) as f:
                record = f.read()
                # replace " with \"
                record = record.replace('"', '\\"')
                record = record.replace("'", "\"")
                record = json.loads(record)
                gold_selector = f"\"{record['selector']}\""
            instruction += f" The gold selector is {gold_selector}. Please only fix the rule with this selector and focus on adjusting its categorical properties, such as border, float, display, overflow, position, etc. All other CSS rules should be kept unchanged!"

        if self.hint:
            with open(os.path.join(data_item, "corruption", "record.txt")) as f:
                record = f.read()
                # replace " with \"
                record = record.replace('"', '\\"')
                record = record.replace("'", "\"")
                record = json.loads(record)
            instruction += f"(hint: the error is due to this corruption: {record}. Just fix this and the task will be done. However, don't mention the hint in the conversation. This is a secret between you and the system.)"

        print("instruction:", instruction)
        with open(os.path.join(data_item, "index.html"), "r") as f:
            html_content = f.read()

        # initial inputs
        session.inject({"role": "user", "content": INSTRUCTIONS})
        session.inject({"role": "agent", "content": "I've understood your instruction, start please."})

        content = [
            {
                "type": "text", 
                "text": f"Here is the target screenshot."
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{target_screenshot}",
                   "detail": "high"
                },
            },
            {
                "type": "text", 
                "text": f"Here is the html content."
            },
            {
                "type": "text",
                "text": html_content
            },
            {
                "type": "text", 
                "text": f"Here is the current screenshot."
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{current_screenshot}",
                   "detail": "high"
                },
            },
            {
                "type": "text",
                "text": instruction
            }
        ]
        session.inject({"role": "user", "content": content})      
        
        # agent loop
        actions = []
        interface = CSSInteractor(os.path.join(data_item, "index.html"))

        finalized = False
        usage = None
        finish_reason = SampleStatus.COMPLETED
        for i in range(self.round):
            print("round:", i)
            if finalized:
                break
            message = await session.action()
            if message.status == AgentOutputStatus.AGENT_CONTEXT_LIMIT:
                return TaskSampleExecutionResult(status=SampleStatus.AGENT_CONTEXT_LIMIT)
            elif message.status != AgentOutputStatus.NORMAL:
                return TaskSampleExecutionResult(status=SampleStatus.UNKNOWN)
            message = message.content
            # if message is a tuple with two elements, the first is the response, and the second is the usage
            if isinstance(message, tuple):
                if usage is None:
                    usage = message[1]
                else:
                    for key in message[1].keys():
                        usage[key] += message[1][key]
                message = message[0]
            message = message.split("Observation:")[0]
            message = message.strip()
            message = message.replace("Action:\n", "Action:")
            # session.history[-1]["content"] = message
            session.history[-1].content = message

            print("received message:", message)

            if "I have fixed the css style" in message:
                # update the css file and take a new screenshot

                finalized = True
                break
            # retrieve action using regex
            lines = message.split("\n")
            find_action = False
            for line in lines:
                if find_action:
                    break
                line = line.strip()
                if re.match(r"Action.*?:", line):
                    function_names = re.findall(r'(\w+)\(', line)
                    if "revert_last_edit" not in function_names and "revert_last_edit" in line:
                        function_names.append("revert_last_edit")
                    print(function_names)
                    for function_name in function_names:
                        find_action = True
                        if function_name == "revert_last_edit":  # no arguments to parse
                            func = getattr(interface, function_name)
                            execution = func()
                            if execution:
                                execution_message = "You have successfully reverted the last edit."
                            else:
                                execution_message = "No edit to revert."
                            actions.append(f"{function_name}({', '.join(ori_arguments)})")
                            session.inject({"role": "user", "content": execution_message})
                            break

                        try:
                            ori_arguments = []
                            func = getattr(interface, function_name)
                            if function_name != "get_selectors_by_html_elements":
                                pattern = r'{}\((.*?)\)'.format(re.escape(function_name))
                                matches = re.findall(pattern, line)
                                # Use shlex.split to correctly handle the quoted strings
                                arguments = shlex.split(matches[0])

                                # Remove trailing comma from each argument
                                arguments = [arg.rstrip(',') for arg in arguments]
                                print("arguments:", arguments)
                                ori_arguments = [argument for argument in arguments]
                            else:
                                arguments = re.findall(r"get_selectors_by_html_elements\((.+?)\)", line)[0]
                                if arguments.startswith("'") and arguments.endswith("'"):
                                    arguments = arguments[1:-1]
                                if arguments.startswith('"') and arguments.endswith('"'):
                                    arguments = arguments[1:-1]
                                arguments = [arguments]
                                print("arguments:", arguments)
                                ori_arguments = [arguments[0]]
                            if function_name == "edit_rule":
                                execution = await func(*arguments)  # because it inovles taking screenshot, which is async
                            else:
                                execution = func(*arguments)
                            actions.append(f"{function_name}({', '.join(ori_arguments)})")
                            if function_name == "get_selectors_by_html_elements":
                                elements = execution[0]
                                if len(elements) == 0:
                                    execution_message = f"No html elements found based on the input. Please specify a different html elements specification."
                                else:
                                    matched_selectors = execution[1]
                                    if not matched_selectors:
                                        execution_message = f"No matched selectors found based on the html elements. Please specify a different html elements."
                                    else:
                                        execution_message = f"The following {len(matched_selectors)} selectors are matched based on the returned html elements:\n"
                                        for sid, selector in enumerate(matched_selectors):
                                            execution_message += f"{sid+1}. '{selector}'\n"
            
                            elif function_name == "select_rule":
                                if execution[0] is None:
                                    execution_message = f"No rule found based on selector {arguments[0]}. Please specify a different selector."
                                else:
                                    execution_message = f"Here is the rule founded based on selector {arguments[0]}: {str({property: execution[0].style[property] for property in execution[0].style.keys()})}. Is this the rule you want to edit?"
                            elif function_name == "edit_rule":
                                if execution:
                                    new_screenshot_path = os.path.join(data_item, "new_screenshot.png")
                                    execution_message = [
                                        {
                                            "type": "text",
                                            "text": "You have successfully edited the rule. Here is the updated screenshot. If you think this edit is not useful, you can revert the last edit by calling revert_last_edit()."
                                        },
                                        {
                                            "type": "image_url",
                                            "image_url": {
                                                "url": f"data:image/png;base64,{new_screenshot_path}",
                                               "detail": "high"
                                            },
                                        }
                                    ]
                                else:
                                    execution_message = f"No rule found based on selector {arguments[0]}. Please specify a different selector or consider inserting a new rule."
                            elif function_name == "insert_rule":
                                # execution_message = "You have successfully inserted the rule."
                                new_screenshot_path = os.path.join(data_item, "new_screenshot.png")
                                execution_message = [
                                    {
                                        "type": "text",
                                        "text": "You have successfully inserted the rule. Here is the updated screenshot. If you think this edit is not useful, you can revert the last edit by calling revert_last_edit()."
                                    },
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/png;base64,{new_screenshot_path}",
                                           "detail": "high"
                                        },
                                    }
                                ]
                            else:
                                execution_message = f"{function_name} is not a valid function. Please check the function name and try again."
                            
                            session.inject({"role": "user", "content": execution_message})
                            if isinstance(execution_message, str):
                                print("execution message:", execution_message)
                            else:
                                print("execution message:", execution_message[0]["text"])
                        except Exception as e:
                            execution_message = f"{function_name}({', '.join(ori_arguments)}) is not valid due to exception {e}. You may make a mistake and need to fix it."
                            session.inject({"role": "user", "content": execution_message})
                            print("execution message:", execution_message)
                            break
            if not find_action:
                session.inject({"role": "user", "content": "No executable function found! Need to recheck the action. Please stick to the format of Action: ..."})
                print("No executable function found! Need to recheck the action. Please stick to the format of Action: ...")
        
        else:
            finish_reason = SampleStatus.TASK_LIMIT_REACHED
        
        await interface.finalize()

        os.makedirs(os.path.join(self.output_dir, os.path.basename(data_item)), exist_ok=False)
        # move the screenshot to the original directory
        os.system(f"mv {os.path.join(data_item, 'new_screenshot.png')} {os.path.join(self.output_dir, os.path.basename(data_item), 'index_corrupted.png')}")
        print("hhahfkdashfjsadhfkjhsdajkfhksajdhfkjdsahfkjshj")
        # # remove the temporary working directory
        # os.system(f"rm -r {data_item}")
        
        # return {"screenshot": os.path.join(self.output_dir, os.path.basename(data_item), "index_corrupted.png"), "actions": actions, "usage": usage}
        return TaskSampleExecutionResult(status=finish_reason, result={"screenshot": os.path.join(self.output_dir, os.path.basename(data_item), "index_corrupted.png"), "actions": actions, "usage": usage})