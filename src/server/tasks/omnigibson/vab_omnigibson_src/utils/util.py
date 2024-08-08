from os import path
import os
import sys
import argparse
from datetime import datetime
from colorama import Fore, Style
import random
import numpy as np

def parse_args_og():
    parser = argparse.ArgumentParser(description="og")
    parser.add_argument("--log_dir", type=str, default="/og_logs")
    parser.add_argument("--task", type=str, default="assembling_gift_baskets")
    parser.add_argument("--scene", type=str, default="Ihlen_0_int")
    parser.add_argument("--port", type=int, default=12008)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max_round", type=int, default=100)
    args = parser.parse_args()
    date = datetime.now().strftime("%Y%m%d")
    current_time = datetime.now().strftime("%H%M%S")
    args.log_dir = path.join(args.log_dir, f"{date}_logs", f"{current_time}__{args.task}__{args.scene}")
    os.makedirs(args.log_dir, exist_ok=True)
    return args

def fix_seed(seed):
    random.seed(seed)
    np.random.seed(seed)

def print_with_color(text: str, color=""):
    if color == "red":
        print(Fore.RED + text)
    elif color == "green":
        print(Fore.GREEN + text)
    elif color == "yellow":
        print(Fore.YELLOW + text)
    elif color == "blue":
        print(Fore.BLUE + text)
    elif color == "magenta":
        print(Fore.MAGENTA + text)
    elif color == "cyan":
        print(Fore.CYAN + text)
    elif color == "white":
        print(Fore.WHITE + text)
    elif color == "black":
        print(Fore.BLACK + text)
    else:
        print(text)
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
    print_with_color(text, color)
