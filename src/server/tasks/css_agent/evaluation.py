import os
import io
import json
import numpy as np

from skimage import io
from skimage.metrics import structural_similarity as ssim
from skimage.transform import resize

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


def main_metric(outputs, targets):
    # outputs: path to the final screenshot; actions
    # targets: path to the target screenshot; original distance
    distance_sum = 0
    em_sum = 0
    improve_sum = 0
    count = 0
    print(len(outputs))
    em_dirs = []
    improve_dirs = []
    # with open("em_dirs_gold.json") as f:
    #     em_dirs = json.load(f)
    # with open("improve_dirs_gold.json") as f:
    #     improve_dirs = json.load(f)
    # with open("em_dirs.json") as f:
    #     em_dirs = json.load(f)
    # with open("improve_dirs.json") as f:
    #     improve_dirs = json.load(f)
    for i in range(len(outputs)):
        print(outputs[i]['screenshot'])
        count += 1
        new_distance = 1 - compare_images_ssim_gray(targets[i]['screenshot'], outputs[i]['screenshot'])
        # new_distance = 1 - compare_images_ssim_gray(outputs[i]['screenshot'], targets[i]['screenshot'])
        # with open(os.path.join(os.path.dirname(targets[i]['screenshot']), "distance.txt"), "w") as f:
        #     f.write(str(new_distance))
        print(i, new_distance, targets[i]['distance'])
        distance_sum += new_distance
        if new_distance < targets[i]['distance'] - 0.05:
            improve_sum += 1
            improve_dirs.append(os.path.dirname(targets[i]['screenshot']))
        # if new_distance < 0.2:
        if new_distance < 0.1:
            em_sum += 1
            em_dirs.append(os.path.dirname(targets[i]['screenshot']))

    print("em_sum", em_sum, count)
    print("improve_sum", improve_sum, count)
    print("distance_sum", distance_sum, count)

    # json.dump(em_dirs, open("em_dirs_hint.json", "w"))
    # json.dump(improve_dirs, open("improve_dirs_hint.json", "w"))

    # return distance_sum / count, improve_sum / count, em_sum / count
    return distance_sum / 165, improve_sum / 165, em_sum / 165

# training/adister, test/minimalista/css/lightcase.css css file not exist bug
# 4o: (0.4242, 0.3333) second run: (0.4485, 0.3455)
# 4turbo: (0.3576, 0.2788)
# 4v: (0.3576, 0.2909)
# gemini-1.5: (31/0.18787879, 18/0.10909091)
# claude-3: (58/0.35151515, 33/0.2)
# cogvlm2: (32/0.19393939， 24/0.145454545)
# cogagent:
# em_sum 14 154
# improve_sum 22 154
# distance_sum 48.73055523931893 154
# (0.29533669842011473, 0.13333333333333333, 0.08484848484848485)
# qwen-7b:
# em_sum 16 154
# improve_sum 26 154
# distance_sum 47.81760582138789 154
# (0.2898036716447751, 0.15757575757575756, 0.09696969696969697)

# 4o w/o thought:
# em_sum 63 163
# improve_sum 79 163
# distance_sum 32.96666765403506 163
# (0.19979798578203065, 0.47878787878787876, 0.38181818181818183)
# 4o w/o thought2:
# em_sum 66 162
# improve_sum 78 162
# distance_sum 32.1616451210288 162
# (0.19491906133956846, 0.4727272727272727, 0.4)


if __name__ == "__main__":


    outputs = []
    targets = []
    # with open("/local/scratch/gu.826/projects/updated_agentbench/AgentBench/css_output/wtf3/generation.jsonl") as f:
    # with open("/local/scratch/gu.826/projects/updated_agentbench/AgentBench/css_output/claude3/generation.jsonl") as f:
    # with open("/local/scratch/gu.826/projects/updated_agentbench/AgentBench/css_output/gpt4o/generation.jsonl") as f:
    # with open("/local/scratch/gu.826/projects/updated_agentbench/AgentBench/css_output/gemini/generation.jsonl") as f:
    # with open("/local/scratch/gu.826/projects/updated_agentbench/AgentBench/css_output/gemini-1.0/generation.jsonl") as f:
    # with open("/local/scratch/gu.826/projects/updated_agentbench/AgentBench/css_output/wtfff/generation.jsonl") as f:
    # with open("/local/scratch/gu.826/projects/updated_agentbench/AgentBench/css_output/wtfff2/generation.jsonl") as f:
    # with open("/local/scratch/gu.826/projects/updated_agentbench/AgentBench/css_output/wtffff/generation.jsonl") as f:
    # with open("/local/scratch/gu.826/projects/updated_agentbench/AgentBench/css_output/wtffff2/generation.jsonl") as f:
    # with open("/local/scratch/gu.826/projects/updated_agentbench/AgentBench/css_output/4o_gold_selector/generation.jsonl") as f:
    # with open("/local/scratch/gu.826/projects/updated_agentbench/AgentBench/css_output/4turbo_no_nl/generation.jsonl") as f:
    # with open("/local/scratch/gu.826/projects/updated_agentbench/AgentBench/css_output/qwen/generation.jsonl") as f:
    # with open("/local/scratch/gu.826/projects/updated_agentbench/AgentBench/css_trajectories/4o_hint/generation.jsonl") as f:
    # with open("/home/gy/AgentBench/css_output_final/cogvlm_full/generation.jsonl") as f:
    with open("/home/gy/AgentBench/css_output_final/qwen-7b_full/generation.jsonl") as f:
        for line in f:
            line_obj = json.loads(line)
            target_dir = line_obj['input']
            target_obj = {"screenshot": os.path.join(target_dir, "index.png")}
            with open(os.path.join(target_dir, "distance.txt")) as f:
                target_obj['distance'] = float(f.read().strip())
            targets.append(target_obj)
            outputs.append(line_obj['output'])



    print(main_metric(outputs, targets))



