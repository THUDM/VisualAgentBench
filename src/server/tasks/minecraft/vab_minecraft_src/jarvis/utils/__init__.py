import numpy as np
from typing import List, Union
import argparse
from colorama import Fore, Style
import os
from datetime import datetime
from os import path
import sys
import base64

def write_video(
    file_name: str, 
    frames: Union[List[np.ndarray], bytes], 
    width: int = 640, 
    height: int = 360, 
    fps: int = 20
) -> None:
    import av
    """Write video frames to video files. """
    with av.open(file_name, mode="w", format='mp4') as container:
        stream = container.add_stream("h264", rate=fps)
        stream.width = width
        stream.height = height
        for frame in frames:
            frame = av.VideoFrame.from_ndarray(frame, format="rgb24")
            for packet in stream.encode(frame):
                    container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)

def parse_args_minecraft():
    parser = argparse.ArgumentParser(description="Minecraft Evaluation")
    parser.add_argument("-task", "--task_name", "--task", type=str, default="iron_pickaxe", help="evaluation task name")
    parser.add_argument("-max_round", "--max_round", type=int, default=100, help="maximum vlm turns")
    parser.add_argument("-log_dir", "--log_dir", type=str, default="/minecraft_logs")
    parser.add_argument("-write_video", "--write_video", type=bool, default=False, help="whether to write video or not")
    parser.add_argument("-seed", "--seed", type=int, default=42, help="seed for random, numpy, torch, APIs")
    parser.add_argument("-steve_step", "--steve_step", type=int, default=800, help="steve step size")
    parser.add_argument("--port", type=int, default=12008)
    args = parser.parse_args()
    date = datetime.now().strftime("%Y%m%d")
    current_time = datetime.now().strftime("%H%M%S")
    args.log_dir = path.join(args.log_dir, f"{date}_logs", f"{current_time}__{args.task_name}")
    os.makedirs(args.log_dir, exist_ok=True)
    return args

def print_with_color(text: str, color="", task_name=""):
    task_name = f"[{task_name}] "
    if color == "red":
        print(Fore.RED + task_name + text)
    elif color == "green":
        print(Fore.GREEN + task_name + text)
    elif color == "yellow":
        print(Fore.YELLOW + task_name + text)
    elif color == "blue":
        print(Fore.BLUE + task_name + text)
    elif color == "magenta":
        print(Fore.MAGENTA + task_name + text)
    elif color == "cyan":
        print(Fore.CYAN + task_name + text)
    elif color == "white":
        print(Fore.WHITE + task_name + text)
    elif color == "black":
        print(Fore.BLACK + task_name + text)
    else:
        print(task_name + text)
    print(Style.RESET_ALL)


def log(args, text, color=""):
    text = str(text)
    log_dir = args.log_dir
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    if not os.path.exists(os.path.join(log_dir, "main.txt")):
        with open(os.path.join(log_dir, "main.txt"), 'w') as f:
            f.write(text)
    else:
        with open(os.path.join(log_dir, "main.txt"), 'a') as f:
            f.write(text)
    print_with_color(text, color, args.task_name)


def image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as f:
        image = f.read()
    return base64.b64encode(image).decode()


def fix_seed(seed):
    import random
    import numpy as np
    import torch
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    return seed
