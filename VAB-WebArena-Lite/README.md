# Setup for VAB-WebArena-Lite

## Brief Introduction

VAB-WebArena-Lite is a 165-task refined subset from <a href="https://webarena.dev/" target="_blank">WebArena</a>.
The purpose of building this subset is to manually ensure task correctness & feasibility, and speed up testing (original 812-task WebArena usually takes more than 6h to run through, while VAB-WebArena-Lite takes around 40m in practice). 
The modified version of the test cases can be found in `config_files/wa/test_webarena_lite.raw.json`.


## Install

First, you should clone the official repository of <a href="https://github.com/web-arena-x/visualwebarena">VisualWebArena</a> to this directory

```bash
# Assume you have cloned VAB and is now in the `VAB-WebArena-Lite` directory
git clone https://github.com/web-arena-x/visualwebarena.git visualwebarena
cd visualwebarena
git reset --hard ad57aae4dad71531504726900b80db02e0526158
cd ..
```

Then, you should substitute the file with the commands below:

```bash
bash replace.sh
```

After that, you should install the dependencies for VAB-WebArena-Lite (recommend using a independent conda environment to VAB):

```bash
# Python 3.10 (or 3.11, but not 3.12 cause 3.12 deprecated distutils needed here)
python -m wal wal
source venv/bin/activate
pip install -r requirements.txt
playwright install
pip install -e .
```

You can also run the unit tests to ensure that WebArena-Lite is installed correctly:

```bash
pytest -x
```

## Setup WebArena-Lite Environments

1. Setup the standalone environments.
Please check out [this page](https://github.com/web-arena-x/webarena/tree/main/environment_docker) for details.

2. Configurate the urls for each website.
First, export the `DATASET` to be `webarena`:

```bash
export DATASET=webarena
```

Then, set the URL for the websites
(🚨 Notice: check if default ports of websites below correspond to those you setup in the first step)

```bash
# Actually, the CLASSIFIEDS environment is not included in the WebArena-Lite evaluation, we keep the environment variables here just for consistency.
export CLASSIFIEDS="<your_classifieds_domain>:9980"
export CLASSIFIEDS_RESET_TOKEN="4b61655535e7ed388f0d40a93600254c"

# Below are the variables you should set for the evaluation.
export SHOPPING="<your_shopping_site_domain>:7770"
export REDDIT="<your_reddit_domain>:9999"
export SHOPPING_ADMIN="<your_e_commerce_cms_domain>:7780/admin"
export GITLAB="<your_gitlab_domain>:8023"
export MAP="<your_map_domain>:3000"
export WIKIPEDIA="<your_wikipedia_domain>:8888"
export HOMEPAGE="<your_homepage_domain>:4399"
```

3. Generate config files for each test example:

```bash
python scripts/generate_test_data.py
```

You will see `*.json` files generated in the [config_files](./config_files) folder. Each file contains the configuration for one test example.

4. Obtain and save the auto-login cookies for all websites:

```bash
bash prepare.sh
```

5. Set up API keys.

```bash
export OPENAI_API_KEY=your_key

# Optional: if you use a different OpenAI model source
export OPENAI_API_URL=your_url 

# Optional: you can set the following variables to evaluate the preset model in llms/providers/api_utils.py
export GEMENI_API_KEY=your_key
export QWEN_API_KEY=your_key
export CLAUDE_API_KEY=your_key

# Optional: if you have trained your model, we recommend deploying it as an API service, where you can set a FINETUNED_URL to evaluate it.
export FINETUNED_URL=your_url

```

If using Gemini, first install the [gcloud CLI](https://cloud.google.com/sdk/docs/install). Configure the API key by authenticating with Google Cloud:

```bash
gcloud auth login
gcloud config set project <your_project_name>
```

## 🖼️ Evaluating in VAB Standard Setting with SoM (Set-of-Marks) Visual Agents

### 👎 Run Single Agent For Evalution (Slow, but please read to understand meaning of arguments)

To run your own model with SoM visual agent,  you can run evaluation with the following flags:

```bash
python run.py \
  --instruction_path agent/prompts/jsons/p_som_cot_id_actree_3s.json \
  --test_start_idx 0 \
  --test_end_idx 1 \
  --result_dir <your_result_dir> \
  --test_config_base_dir config_files/wa/test_webarena_lite \
  --provider api \
  --model openai_gpt-4-vision-preview \
  --action_set_tag som  --observation_type image_som
```

Besides the original model providers (OpenAI, Google), you can also add your models in `llms/providers/api_utils.py`. Remember to set `--provider` to:

- `api`: Keep the same input style as WebArena, suitable for regular API calls
- `finetune`: This is required for models trained with the data we provide.

For the `--model` variable, we use the format `<source>_<model-name>` .

- If there is no more optional models under source, you can set it to just `source`.
- Remember that the source name here should be added in the init function of `APIModel` in `llms/providers/api_utils.py`.
- For example, if you want to use the openai model "gpt-4o", you can set the flag like this: `--model openai_gpt-4o`.

Finally, run `score.py` to get the pass rate
```bash 
python score.py <your_result_dir>
```

### 👍 Run Parallel Agent For Evaluation (Recommended)

To run the tests in parallel, you can first configure `wa_parallel_run.sh`, then run it. We default split the test set to 8 parallel-group for evaluation in VAB.

```bash
# Remember to first launch a tmux session
tmux
bash wa_parallel_run.sh
```

The script is enabled with auto-resuming if it is interrupted or met unexpected error. Please feel free to rerun the above command until all tasks finish.

After all parallel groupes finish, run `score.py` to get the pass rate
```bash 
python score.py <your_result_dir>
```

## 🚀 Evaluating in WebRL Setting (Text Modal)

[WebRL](https://github.com/THUDM/WebRL) is one of the top-performing models on WebArena-Lite. It uses a plain text modality as input. Additionally, we provide evaluation scripts that support this plain text modality.

### Evaluation of Finetuned Models

To run the finetuned model in WebRL setting,  you can run evaluation with the following flags:

```bash
python run.py \
  --instruction_path agent/prompts/jsons/p_webrl.json \
  --test_start_idx 0 \
  --test_end_idx 1 \
  --result_dir <your_result_dir> \
  --test_config_base_dir config_files/wa/test_webarena_lite \
  --provider openai \
  --mode completion \
  --model <your_deployed_model_name> \
  --planner_ip <your_deployed_model_ip> \
  --stop_token "<|eot_id|>" \
  --max_obs_length 0 \
  --max_tokens 2048 \
  --viewport_width 1280 \
  --viewport_height 720 \
  --action_set_tag webrl_id  --observation_type webrl
```

You need to first use tools like vllm to deploy the finetuned model locally. Once deployed, the model can be accessed through the OpenAI API call method. 

Ensure that the `--model` and `--planner_ip` fields are completed with the appropriate model name and the IP address of the deployed model instance.

We also provide the parallel script.

```bash
# Remember to first launch a tmux session
tmux
bash wa_parallel_run_webrl.sh
```

### Evaluation of Proprietary Models

To run the proprietary model in WebRL setting,  you can run evaluation with the following flags:

```bash
python run.py \
  --instruction_path agent/prompts/jsons/p_webrl_chat.json \
  --test_start_idx 0 \
  --test_end_idx 1 \
  --result_dir <your_result_dir> \
  --test_config_base_dir config_files/wa/test_webarena_lite \
  --provider openai \
  --model GPT-4o \
  --mode chat \
  --planner_ip '' \
  --max_obs_length 0 \
  --max_tokens 2048 \
  --viewport_width 1280 \
  --viewport_height 720 \
  --action_set_tag webrl_id  --observation_type webrl
```

You can switch the evaluation model by modifying `--model`. We also provide the parallel script.

```bash
# Remember to first launch a tmux session
tmux
bash wa_parallel_run_webrl_chat.sh
```

## 🚨 Important: Refresh all websites before re-run another round of testing!
Since tasks in WebArena may involve changing status and database of websites (e.g., posting comments on Reddit), if websites are not all refreshed before another round of evaluation, the results would be problematic.

Please remember to run following command (assume you are hosting WebArena websites on your own) to restart and refresh all website dockers to avoid potential contamination.
The process usually takes 3-5 minites.

```bash
# Make sure the script is executed on the machine that you run those website dockers
bash refresh_website_docker.sh
```

You may need to change some contents in the script (e.g. configured ports of websites, names of dockers, etc.).

## Run Visualized Demostration
Original WebArena have also prepared a demo for you to run the agents on your own task on an arbitrary webpage. An example is shown above where the agent is tasked to find the best Thai restaurant in Pittsburgh.

After following the setup instructions above and setting the OpenAI API key (the other environment variables for website URLs aren't really used, so you should be able to set them to some dummy variable), you can run the GPT-4V + SoM agent with the following command:

```bash
python run_demo.py \
  --instruction_path agent/prompts/jsons/p_som_cot_id_actree_3s.json \
  --start_url "https://www.amazon.com" \
  --image "https://media.npr.org/assets/img/2023/01/14/this-is-fine_wide-0077dc0607062e15b476fb7f3bd99c5f340af356-s1400-c100.jpg" \
  --intent "Help me navigate to a shirt that has this on it." \
  --result_dir demo_test_amazon \
  --model gpt-4-vision-preview \
  --action_set_tag som  --observation_type image_som \
  --render
```

This tasks the agent to find a shirt that looks like the provided image (the "This is fine" dog) from Amazon. Have fun!

## Acknowledgements

Our code is heavily based off the <a href="https://github.com/web-arena-x/webarena">WebArena codebase</a> and <a href="https://github.com/web-arena-x/visualwebarena">VisualWebArena codebase</a>.

If you find this environment useful, please consider citing <a href="https://jykoh.com/vwa" target="_blank">VisualWebArena</a> as well as <a href="https://webarena.dev/" target="_blank">WebArena</a>:

```bibtex
@article{koh2024visualwebarena,
  title={VisualWebArena: Evaluating Multimodal Agents on Realistic Visual Web Tasks},
  author={Koh, Jing Yu and Lo, Robert and Jang, Lawrence and Duvvur, Vikram and Lim, Ming Chong and Huang, Po-Yu and Neubig, Graham and Zhou, Shuyan and Salakhutdinov, Ruslan and Fried, Daniel},
  journal={arXiv preprint arXiv:2401.13649},
  year={2024}
}

@article{zhou2024webarena,
  title={WebArena: A Realistic Web Environment for Building Autonomous Agents},
  author={Zhou, Shuyan and Xu, Frank F and Zhu, Hao and Zhou, Xuhui and Lo, Robert and Sridhar, Abishek and Cheng, Xianyi and Bisk, Yonatan and Fried, Daniel and Alon, Uri and others},
  journal={ICLR},
  year={2024}
}
```

