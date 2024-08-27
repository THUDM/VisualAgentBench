mkdir -p data/minecraft/mineclip
mkdir -p data/minecraft/steve1
mkdir -p data/minecraft/vpt

wget https://openaipublic.blob.core.windows.net/minecraft-rl/models/2x.model -P data/minecraft/vpt

curl -L -o data/minecraft/mineclip/attn.pth "https://drive.google.com/uc?export=download&id=1uaZM1ZLBz2dZWcn85rZmjP7LV6Sg5PZW"

curl -L -o data/minecraft/steve1/steve1.weights "https://drive.google.com/uc?id=1E3fd_-H1rRZqMkUKHfiMhx-ppLLehQPI"

curl -L -o data/weights/steve1/steve1_prior.pt "https://drive.google.com/uc?id=1OdX5wiybK8jALVfP5_dEo0CWm9BQbDES"
