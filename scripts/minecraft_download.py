import os
import subprocess

directories_to_create = [
    "data/minecraft/mineclip",
    "data/minecraft/steve1",
    "data/minecraft/vpt"
]

files_to_download = [
    {
        "url": "https://openaipublic.blob.core.windows.net/minecraft-rl/models/2x.model",
        "output_dir": "data/minecraft/vpt",
        "output_file": "2x.model"
    },
    {
        "url": "https://drive.google.com/uc?id=1uaZM1ZLBz2dZWcn85rZmjP7LV6Sg5PZW",
        "output_dir": "data/minecraft/mineclip",
        "output_file": "attn.pth"
    },
    {
        "url": "https://drive.google.com/uc?id=1E3fd_-H1rRZqMkUKHfiMhx-ppLLehQPI",
        "output_dir": "data/minecraft/steve1",
        "output_file": "steve1.weights"
    },
    {
        "url": "https://drive.google.com/uc?id=1OdX5wiybK8jALVfP5_dEo0CWm9BQbDES",
        "output_dir": "data/minecraft/steve1",
        "output_file": "steve1_prior.pt"
    }
]

for directory in directories_to_create:
    if not os.path.exists(directory):
        os.makedirs(directory)

for file_info in files_to_download:
    url = file_info["url"]
    output_dir = file_info["output_dir"]
    output_file = file_info["output_file"]
    output_path = os.path.join(output_dir, output_file)

    if not os.path.exists(output_path):
        if url.startswith("https://drive.google.com"):
            subprocess.run(["gdown", url, "-O", output_path])
        elif url.startswith("http"):
            subprocess.run(["wget", url, "-P", output_dir])