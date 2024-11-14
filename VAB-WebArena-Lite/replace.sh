#!/bin/bash

# 1. reset the original environment
cd visualwebarena
rm -rf .git
cd ..

# 2. replace files
# webarena-lite
cp -f new/test_webarena_lite.raw.json visualwebarena/config_files/wa/test_webarena_lite.raw.json
cp -f new/generate_test_data.py visualwebarena/scripts/generate_test_data.py

# agent
cp -f new/run.py visualwebarena/run.py
cp -f new/agent.py visualwebarena/agent/agent.py
cp -f new/prompt_constructor.py visualwebarena/agent/prompts/prompt_constructor.py
cp -f new/p_webrl.json visualwebarena/agent/prompts/jsons/p_webrl.json
cp -f new/p_webrl_chat.json visualwebarena/agent/prompts/jsons/p_webrl_chat.json

# browser_env
cp -f new/actions.py visualwebarena/browser_env/actions.py
cp -f new/envs.py visualwebarena/browser_env/envs.py
cp -f new/helper_functions_browser.py visualwebarena/browser_env/helper_functions.py
cp -f new/processors.py visualwebarena/browser_env/processors.py
cp -rf new/html_tools visualwebarena/browser_env/

# llms
cp -f new/utils.py visualwebarena/llms/utils.py
cp -f new/llms_init.py visualwebarena/llms/__init__.py
cp -f new/lm_config.py visualwebarena/llms/lm_config.py
cp -f new/tokenizers.py visualwebarena/llms/tokenizers.py
cp -f new/api_utils.py visualwebarena/llms/providers/api_utils.py
cp -f new/openai_utils.py visualwebarena/llms/providers/openai_utils.py
cp -f new/utils.py visualwebarena/llms/utils.py

# eval
cp -f new/evaluators.py visualwebarena/evaluation_harness/evaluators.py
cp -f new/helper_functions_eval.py visualwebarena/evaluation_harness/helper_functions.py

# misc
cp -f README.md visualwebarena/README.md
cp -f new/wa_parallel_run.sh visualwebarena/wa_parallel_run.sh

cp -f new/score.py visualwebarena/score.py
cp -f new/wa_parallel_run_webrl.sh visualwebarena/wa_parallel_run_webrl.sh
cp -f new/wa_parallel_run_webrl_chat.sh visualwebarena/wa_parallel_run_webrl_chat.sh

# 3. remove temporary files
mv visualwebarena/* .
rm -rf new
rm -rf visualwebarena
