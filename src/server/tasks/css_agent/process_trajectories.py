import os
import re
import shlex
import random
import json
from actions import CSSInteractor
from tqdm import tqdm

with open("em_dirs.json", "r") as f:
    em_dirs = json.load(f)

with open("em_dirs_gold.json", "r") as f:
    em_dirs_gold = json.load(f)

with open("em_dirs_hint.json", "r") as f:
    em_dirs_hint = json.load(f)

# print(len(em_dirs))
# print(len(em_dirs_gold))
# exit(0)


# open the trajectories file, and only keep these with input in em_dirs
# trajectories = []
failed_trajectories = []
with open("/local/scratch/gu.826/projects/updated_agentbench/AgentBench/css_trajectories/4o/generation.jsonl") as f:
    for line in f:
        line_obj = json.loads(line)
        if line_obj['input'] in em_dirs:
            # trajectories.append(line_obj)
            pass
        else:
            failed_trajectories.append(line_obj)


trajectories = {}
with open("/local/scratch/gu.826/projects/updated_agentbench/AgentBench/css_trajectories/4o_gold_selector_2/generation.jsonl") as f:
    for line in f:
        line_obj = json.loads(line)
        if line_obj['input'] in em_dirs_gold:
            # trajectories.append(line_obj)
            trajectories[line_obj['input']] = line_obj
with open("/local/scratch/gu.826/projects/updated_agentbench/AgentBench/css_trajectories/4o_gold_selector/generation.jsonl") as f:
    for line in f:
        line_obj = json.loads(line)
        if line_obj['input'] in em_dirs_gold:
            if line_obj['input'] not in trajectories:   # for em_dirs_gold, prioritize 4o_gold_selector_2
                trajectories[line_obj['input']] = line_obj

print(len(trajectories))

with open("/local/scratch/gu.826/projects/updated_agentbench/AgentBench/css_trajectories/4o_hint/generation.jsonl") as f:
    for line in f:
        line_obj = json.loads(line)
        if line_obj['input'] in em_dirs_hint:
            trajectories[line_obj['input']] = line_obj

print(len(trajectories))


# discard repeated actions in failed trajectory; only keep the first occurance
def clean_history(history):
    new_history = []
    actions = set()
    delete_user = False
    for message in history:
        if message["role"] != "agent":
            if delete_user:
                delete_user = False
                continue
            new_history.append(message)
            continue
        # retrieve action using regex
        lines = message["content"].split("\n")
        for line in lines:
            line = line.strip()
            if re.match(r"Action.*?:", line):
                if "revert_last_edit" not in line:
                    break
        if line in actions:
            delete_user = True
            continue
        else:
            actions.add(line)
            new_history.append(message)

    return new_history


# reconstruct the failed trajectory
def reconstruct_failed_trajectory(history, count_edits=2):
    history = clean_history(history)

    keep_flag = False

    # create a list of random messages saying "I need to revert the previous action."
    revert_thoughts = [
        "I need to revert the previous action.",
        "The previous action did not fix the issue. I need to revert it.",
        "The previous action did not work. I need to revert it.",
        "The previous action did not solve the problem. I need to revert it.",
        "I need to revert the previous action. It did not work.",
        "I need to revert the previous action. It did not solve the problem.",
        "I need to revert the previous action. The previous action did not work."
    ]

    # get the selectors in the first count_edits edit_rule actions
    selectors = []
    for message in history:
        if len(selectors) == count_edits + 1:
            break
        if message["role"] == "agent":
            if "edit_rule" in message["content"]:
                # the selector should be the first argument of the edit_rule function
                lines = message["content"].split("\n")
                for line in lines:
                    line = line.strip()
                    if re.match(r"Action.*?:", line):
                        pattern = r'edit_rule\((.*?)\)'
                        matches = re.findall(pattern, line)
                        # Use shlex.split to correctly handle the quoted strings
                        try:
                            arguments = shlex.split(matches[0])
                            # Remove trailing comma from each argument
                            arguments = [arg.rstrip(',') for arg in arguments]
                            selectors.append(arguments[0])
                        except Exception as e:
                            pass
    
    # print("selectors:", selectors)
    other_actions_max = 1   # this actually allows no irrelevant action; only allows the input message
    i = 0
    new_history = []
    while i < len(history):
        try:
            if history[i]["role"] == "agent":
                if count_edits > 0:
                    if "edit_rule" in history[i]["content"]:
                        # print("hahaha:", history[i]["content"])
                        if isinstance(history[i+1]["content"], list):
                            # if "You have successfully edited the rule." in history1[i+1]["content"]:
                            count_edits -= 1
                            new_history.append(history[i])
                            # print("123:", history[i]["content"])
                            new_history.append(history[i+1])
                            # print("456:", history[i+1]["content"])

                            i += 2
                            if i < len(history) and "revert_last_edit" in history[i]["content"]:
                                new_history.append(history[i])
                                # print(history[i]["content"])
                                if "You have successfully reverted the last edit." not in history[i+1]["content"]:
                                    raise Exception("no user message to revert_last_edit")
                                new_history.append(history[i+1])
                                # print(history[i+1]["content"])
                                i += 2
                            else:  # manually add the revert_last_edit action
                                # pick a random thought from revert_thoughts
                                thought = random.choice(revert_thoughts)
                                new_history.append({"role": "agent", "content": f"Thought: {thought}\nAction: revert_last_edit()"})
                                # print(f"Thought: {thought}\nAction: revert_last_edit()")
                                new_history.append({"role": "user", "content": "You have successfully reverted the last edit."})
                                # print("You have successfully reverted the last edit.")
                            continue
                        else:
                            new_history.append(history[i])
                            # print(history[i]["content"])
                            new_history.append(history[i+1])
                            # print(history[i+1]["content"])
                            i += 2
                            continue
                    else:
                        if "get_selectors_by_html_elements" in history[i]["content"]:
                            # if any selector in history[i+1]["content"]
                            if any(selector in history[i+1]["content"] for selector in selectors):
                                new_history.append(history[i])
                                # print(history[i]["content"])
                                new_history.append(history[i+1])
                                # print(history[i+1]["content"])
                                i += 2
                            else:
                                i += 2
                        # elif any selector in history[i]["content"]
                        elif any(selector in history[i]["content"] for selector in selectors):
                            if i + 1 >= len(history):
                                keep_flag = True
                                break
                            new_history.append(history[i])
                            # print("aaa", history[i]["content"])
                            new_history.append(history[i+1])
                            # print("bbb", history[i+1]["content"])
                            i += 2
                        elif (i + 1) < len(history):  # make sure the last message is a user message
                            if other_actions_max > 0:   # it turns out that we can't just skip other actions, which could mess up the conversation
                                new_history.append(history[i])
                                # print("aaaa", history[i]["content"])
                                new_history.append(history[i+1])
                                # print("bbbb", history[i+1]["content"])
                                other_actions_max -= 1
                            i += 2
                            continue
                        else:   # agent provides the last message, then just skip
                            break
                else:
                    break
            else:
                new_history.append(history[i])
                # print(history[i]["content"])
                i += 1
        except Exception as e:
            print(e)
            break
    # print("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
    return new_history, keep_flag



def concactenate_conversation(trajectory1, trajectory2):
    # 1. discard repeated actions in failed trajectory; only keep the first occurance
    # 2. Randomly keep some edit_rule actions, if the subsequent action is a revert action, also keeps that. Or, we should add a revert action with Thought: I need to revert the previous action. after the edit_rule action
    # 3. concatenate the cleaned failed trajectory with the last three messages in the successful trajectory (or more generally, not the last three messages, but the last edit_rule action in the successful trajectory not being reverted)

    history1 = trajectory1['history']
    history2 = trajectory2['history']

    history1 = clean_history(history1)
    history2 = clean_history(history2)


    # if # history2 has more than two edit_rule actions
    count_edits = 0
    for i, message in enumerate(history2):
        if message["role"] == "agent":
            if "edit_rule" in message["content"]:
                if isinstance(history2[i+1]["content"], list) and "You have successfully edited the rule." in history2[i+1]["content"][0]["text"]:
                    count_edits += 1
    # print(count_edits)
    if count_edits > 1:
        new_history = history1[:3] + history2[3:]
    else: 
        new_history, keep_flag = reconstruct_failed_trajectory(history1)

        if not keep_flag:
            return None
    
        # print(len(new_history))

        # remove the last edit_rule action in history2 from new_history
        line = None
        for i in range(len(history2)):
            if history2[i]["role"] == "agent" and "edit_rule" in history2[i]["content"]:
                if (i+2) < len(history2) and "I have fixed the css style" in history2[i+2]["content"]:
                    # use regex to retrieve the edit_rule action
                    lines = history2[i]["content"].split("\n")
                    for line in lines:
                        line = line.strip()
                        if re.match(r"Action.*?:", line):
                            break
        # print("line:", line)
        if line is not None:
            new_new_history = []
            # add all messages to new_new_history except for the message with line and the next message
            skip_flag = False
            for message in new_history:
                if skip_flag:
                    skip_flag = False
                    continue
                if message["role"] == "agent" and line in message["content"]:
                    skip_flag = True
                else:
                    new_new_history.append(message)

        new_history = new_history + history2[3:]

    # print(len(new_history))

    trajectory1['history'] = new_history

    return trajectory1
            


# this is used to get the screenshots during the process
def process_one_trajectory(trajectory):
    dir = trajectory['input']
    history = trajectory['history']
    data_item = dir

    # print("directory:", data_item)

    # if .cache directory does not exist, create it
    if not os.path.exists(f"./temp_dir3"):
        os.makedirs(f"./temp_dir3")

    if not os.path.exists(f"./trajectories3"):
        os.makedirs(f"./trajectories3")

    # cp the directory to the temporay working directory
    os.system(f"cp -r {dir} ./temp_dir3")
    # change data_item to the new path
    data_item = f"./temp_dir3/" + os.path.basename(dir)

    trajectories_dir = f"./trajectories3/" + os.path.basename(dir)
    if not os.path.exists(trajectories_dir):
        os.makedirs(trajectories_dir)


  
    interface = CSSInteractor(os.path.join(data_item, "index.html"))

    png_id = 0

    for message in history[3:]:
        if message["role"] == "user":
            continue
        
        message = message["content"]

        # print("received message:", message)

        if "I have fixed the css style" in message:
            # update the css file and take a new screenshot
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
                # print(function_names)
                for function_name in function_names:
                    find_action = True
                    if function_name == "revert_last_edit":  # no arguments to parse
                        func = getattr(interface, function_name)
                        execution = func()
                        break

                    try:
                        func = getattr(interface, function_name)
                        if function_name != "get_selectors_by_html_elements":
                            pattern = r'{}\((.*?)\)'.format(re.escape(function_name))
                            matches = re.findall(pattern, line)
                            # Use shlex.split to correctly handle the quoted strings
                            arguments = shlex.split(matches[0])

                            # Remove trailing comma from each argument
                            arguments = [arg.rstrip(',') for arg in arguments]
                            # print("arguments:", arguments)
                            ori_arguments = [argument for argument in arguments]
                        else:
                            arguments = re.findall(r"get_selectors_by_html_elements\((.+?)\)", line)[0]
                            if arguments.startswith("'") and arguments.endswith("'"):
                                arguments = arguments[1:-1]
                            if arguments.startswith('"') and arguments.endswith('"'):
                                arguments = arguments[1:-1]
                            arguments = [arguments]
                            # print("arguments:", arguments)
                        execution = func(*arguments)

                        if function_name == "edit_rule" and execution:
                            # mv new_screenshot.png to {png_id}.png
                            os.system(f"mv {os.path.join(data_item, 'new_screenshot.png')} {os.path.join(trajectories_dir, f'{png_id}.png')}")
                            png_id += 1

                    except Exception as e:
                        break

    # interface.finalize()


# this is used to format the conversation
def prepare_conversation(trajectory):
    dir = trajectory['input']
    history = trajectory['history']
    trajectories_dir = f"./trajectories3/" + os.path.basename(dir)
    # print(trajectories_dir)
    # print("final # of rounds:", len(history))

    # cp index.png to trajectories_dir
    os.system(f"cp {os.path.join(dir, 'index.png')} {trajectories_dir}")
    os.system(f"cp {os.path.join(dir, 'corruption', 'index_corrupted.png')} {trajectories_dir}")

    if os.path.exists(f"{trajectories_dir}/dialog.jsonl"):
        os.remove(f"{trajectories_dir}/dialog.jsonl")

    with open(f"{trajectories_dir}/dialog.jsonl", "a") as f:
        png_id = 0
        for i, message in enumerate(history):
            if i < 2:
                f.write(json.dumps(message) + "\n")
            elif i == 2:
                message['content'][1]["image_url"] = "index.png"
                message['content'][5]["image_url"] = "index_corrupted.png"
                f.write(json.dumps(message) + "\n")
            else:
                if message["role"] == "agent":
                    f.write(json.dumps(message) + "\n")
                else:
                    if isinstance(message["content"], list):
                        # print(png_id, message["content"][1])
                        if not os.path.exists(f"{trajectories_dir}/{png_id}.png"):
                            raise Exception("missing image")
                            break
                        message["content"][1]["image_url"] = f"{png_id}.png"
                        png_id += 1
                    f.write(json.dumps(message) + "\n")

                




if __name__ == "__main__":
    # for trajectory in tqdm(trajectories):
    #     process_one_trajectory(trajectory)
    #     prepare_conversation(trajectory)
    #     break


    count = 0
    flag = False
    for trajectory in failed_trajectories:
        # if os.path.exists(f"./trajectories3/" + os.path.basename(trajectory['input'])):
        #     print("already processed:", trajectory['input'])
        #     continue
        # if "/local/scratch/gu.826/projects/updated_agentbench/AgentBench/css_training/jumpstart" != trajectory['input']:
        #     continue
        if trajectory['input'] in trajectories:
            # print("processing:", trajectory['input'])
            # print("begin to concatenate the conversation")
            concat_trajectory = concactenate_conversation(trajectory, trajectories[trajectory['input']])
            if concat_trajectory is None:
                print("this one is fine")
                continue
            print("reprocess the trajectory", trajectory['input'])
            # print("begin to process the trajectory")
            process_one_trajectory(concat_trajectory)
            # print("begin to prepare the conversation")
            try:
                prepare_conversation(concat_trajectory)
            except Exception as e:
                print(e)
                # save the failed input to a file
                with open("failed_input.txt", "a") as f:
                    f.write(trajectory['input'] + "\n")
                count += 1
        else:
            count += 1

    print("failed cases:", count)


    # # count number of png images in each directory
    # for trajectory in tqdm(trajectories):
    #     dir = trajectory['input']
    #     trajectories_dir = f"./trajectories3/" + os.path.basename(dir)
    #     print(trajectories_dir)
    #     print(len([name for name in os.listdir(trajectories_dir) if name.endswith(".png")]))

    # exit(0)
    