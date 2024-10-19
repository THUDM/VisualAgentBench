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

# llms
cp -f new/utils.py visualwebarena/llms/utils.py
cp -f new/llms_init.py visualwebarena/llms/__init__.py
cp -f new/lm_config.py visualwebarena/llms/lm_config.py
cp -f new/tokenizers.py visualwebarena/llms/tokenizers.py
cp -f new/api_utils.py visualwebarena/llms/providers/api_utils.py
cp -f new/openai_utils.py visualwebarena/llms/providers/openai_utils.py

# eval
cp -f new/evaluators.py visualwebarena/evaluation_harness/evaluators.py
cp -f new/helper_functions.py visualwebarena/evaluation_harness/helper_functions.py

# misc
cp -f README.md visualwebarena/README.md
cp -f new/wa_parallel_run.sh visualwebarena/wa_parallel_run.sh

# 3. remove temporary files
mv visualwebarena/* .
rm -rf new
rm -rf visualwebarena
