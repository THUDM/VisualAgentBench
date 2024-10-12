mkdir -p data/minecraft/mineclip
mkdir -p data/minecraft/steve1
mkdir -p data/minecraft/vpt

wget https://openaipublic.blob.core.windows.net/minecraft-rl/models/2x.model -P data/minecraft/vpt

gdown https://drive.google.com/uc?id=1uaZM1ZLBz2dZWcn85rZmjP7LV6Sg5PZW -O data/minecraft/mineclip/attn.pth

gdown https://drive.google.com/uc?id=1E3fd_-H1rRZqMkUKHfiMhx-ppLLehQPI -O data/minecraft/steve1/steve1.weights

gdown https://drive.google.com/uc?id=1OdX5wiybK8jALVfP5_dEo0CWm9BQbDES -O data/minecraft/steve1/steve1_prior.pt
