#!/bin/bash
DATASET='webarena' # TODO: select from ['webarena', 'visualwebarena']
result_dir='' # TODO: set your result_dir
provider='openai' # TODO: select from ['openai', 'finetune', ...]
model='' # TODO: assign model name, which is used for action generation
planner_ip='' # TODO: ip address of the model you are deploying (only if you are deploying your own model using e.g. vllm)
instruction_path='agent/prompts/jsons/p_webrl_chat.json' # e.g., agent/prompts/jsons/p_cot_id_actree_2s.json
test_config_base_dir='config_files/wa/test_webarena_lite' # e.g., config_files/wa/test_webarena_lite
temperature=0.0

SERVER='' # TODO: your server address
MAP_SERVER='' # TODO: the server address for MAP tasks
OPENAI_API_KEY='' # TODO: if you test OpenAI APIs
OPENAI_ORGANIZATION=''
CONDA_ENV_NAME='' # TODO: the name of your conda environment for testing WebArena

ENV_VARIABLES="export DATASET=${DATASET}; export SHOPPING='http://${SERVER}:7770';export SHOPPING_ADMIN='http://${SERVER}:7780/admin';export REDDIT='http://${SERVER}:9999';export GITLAB='http://${SERVER}:8023';export MAP='http://${MAP_SERVER}:3000';export WIKIPEDIA='http://${SERVER}:8888/wikipedia_en_all_maxi_2022-05/A/User:The_other_Kiwix_guy/Landing';export HOMEPAGE='http://${SERVER}:4399';export OPENAI_API_KEY=${OPENAI_API_KEY};export OPENAI_ORGANIZATION=${OPENAI_ORGANIZATION}"

# get the number of tmux panes
num_panes=$(tmux list-panes | wc -l)

# calculate how many panes need to be created
let "panes_to_create = 7 - num_panes"

# array of tmux commands to create each pane
tmux_commands=(
    'tmux split-window -h'
    'tmux split-window -v'
    'tmux select-pane -t 0; tmux split-window -v'
    'tmux split-window -v'
    'tmux select-pane -t 3; tmux split-window -v'
    'tmux select-pane -t 5; tmux split-window -v'
)

# create panes up to 7
for ((i=0; i<$panes_to_create; i++)); do
    eval ${tmux_commands[$i]}
done

#!/bin/bash

# Function to run a job
run_job() {
    tmux select-pane -t $1
    COMMAND="python run.py \
        --instruction_path ${instruction_path} \
        --test_start_idx $2 \
        --test_end_idx $3 \
        --result_dir ${result_dir} \
        --test_config_base_dir ${test_config_base_dir} \
        --provider ${provider} \
        --model ${model} \
        --mode chat \
        --planner_ip ${planner_ip} \
        --stop_token \"<|eot_id|>\" \
        --temperature ${temperature} \
        --max_obs_length 0 \
        --max_tokens 2048 \
        --viewport_width 1280 \
        --viewport_height 720 \
        --parsing_failure_th 5 \
        --repeating_action_failure_th 5 \
        --action_set_tag webrl_id  --observation_type webrl"
    tmux send-keys "tmux set mouse on; conda activate ${CONDA_ENV_NAME}; ${ENV_VARIABLES}; until ${COMMAND}; do echo 'crashed' >&2; sleep 1; done" C-m
    sleep 3
}

TOLERANCE=2
run_batch() {
    args=("$@") # save all arguments in an array
    num_jobs=${#args[@]} # get number of arguments

    for ((i=1; i<$num_jobs; i++)); do
        run_job $i ${args[i-1]} ${args[i]}
    done

    # Wait for all jobs to finish
    while tmux list-panes -F "#{pane_pid} #{pane_current_command}" | grep -q python; do
        sleep 100  # wait for 10 seconds before checking again
    done

    # Run checker
    while ! python scripts/check_error_runs.py ${result_dir} --delete_errors --tolerance ${TOLERANCE}; do
        echo "Check failed, rerunning jobs..."
        for ((i=1; i<$num_jobs; i++)); do
            run_job $i ${args[i-1]} ${args[i]}
        done

        # Wait for all jobs to finish
        while tmux list-panes -F "#{pane_pid} #{pane_current_command}" | grep -q python; do
            sleep 100  # wait for 10 seconds before checking again
        done
    done

}
run_batch 0 28 56 84 112 140 165

