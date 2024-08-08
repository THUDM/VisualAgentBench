# Create the directory structure if it doesn't exist
mkdir -p data/weights/vpt
mkdir -p data/weights/mineclip
mkdir -p data/weights/steve1
mkdir -p data/visual_prompt_embeds
mkdir -p data/prior_dataset

# Base models for VPT
# wget https://openaipublic.blob.core.windows.net/minecraft-rl/models/rl-from-foundation-2x.weights -P data/weights/vpt
# wget https://openaipublic.blob.core.windows.net/minecraft-rl/models/2x.model -P data/weights/vpt

# MineCLIP weights
gdown https://drive.google.com/uc?id=1uaZM1ZLBz2dZWcn85rZmjP7LV6Sg5PZW -O data/weights/mineclip/attn.pth

# STEVE-1 weights
gdown https://drive.google.com/uc?id=1E3fd_-H1rRZqMkUKHfiMhx-ppLLehQPI -O data/weights/steve1/steve1.weights

# Prior weights
gdown https://drive.google.com/uc?id=1OdX5wiybK8jALVfP5_dEo0CWm9BQbDES -O data/weights/steve1/steve1_prior.pt

# Prior dataset
gdown https://drive.google.com/uc?id=18JKzIwHmFBrAjfiRNobtwkN7zhwQc7IO -O data/prior_dataset/data.pkl

# Download visual prompt embeds
gdown https://drive.google.com/uc?id=1K--DOHMDKjtklTK6SbpH11wrI2j_61mu -O data/visual_prompt_embeds.zip
unzip data/visual_prompt_embeds.zip -d data