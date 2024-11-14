import os, json, sys, copy

USE_TASKS = [i for i in range(165)]

def get_result(res_dict, src="all"):
    if len(res_dict) == 0:
        return ''
    
    success_id = [k for k, v in res_dict.items() if v >= 1.0]
    score = len(success_id)
    finish_count = len(res_dict)
    pacc, acc = score / finish_count * 100, score / TASKS * 100

    print(sorted(success_id))

    meta = """
--------
src file:  {}
successed: {:3} / {:4} (812)
partial accuracy: {:7}
overall accuracy: {:7}
--------
""".format(src, int(score), finish_count, round(pacc, 2), round(acc, 2))

    print(meta)

def export_result(res_dict, src=".", note=["1.0", "0.0"], show_all=False):
    out_string = ""
    for id in USE_TASKS:
        # with open(f"Pipeline/config_files/{id}.json", "r") as f:
        #     jd = json.load(f)
        
        # if "map" in  jd["sites"]:
        #     continue
        if id in res_dict:
            if res_dict[id] >= 1.0:
                out_string += note[0]
            else:
                out_string += note[1]
        elif show_all:
            out_string += note[1]
        out_string += "\n"
    
    with open(os.path.join(src, 'export.txt'), 'w') as f:
        f.write(out_string)
        
TASKS = 165

files = sys.argv[1]
file_list = files.split(',')

all_result = {}

for src in file_list:
    path = os.path.join(src, 'actions')

    result = {}
    finished = os.listdir(path)

    for file in finished:
        if not file.endswith('.json'):
            continue
        with open(os.path.join(path, file), 'r') as f:
            data = json.load(f)
        
        if not isinstance(data, dict):
            continue
        
        task_id = data.get('task_id', 1000)
        # if task_id >= TASKS:
        #     continue
        
        task_score = data.get('score', 0)
        if task_score < 0:
            continue
        
        result[task_id] = task_score
        if task_id not in all_result or task_score > all_result[task_id]:
            all_result[task_id] = task_score
        
    get_result(result, src)
    export_result(result, src=src)

if len(file_list) > 1:
    get_result(all_result)
export_result(all_result, show_all=True)

with open('./config_files/wa/test_webarena_lite.raw.json') as fp:
    configs = json.load(fp)
sub_results = {}
sub_ids = {}
for item in configs:
    web = tuple(item['sites'])
    task_id = int(item['task_id'])
    old_task_id = int(item['old_task_id'])
    if web not in sub_results:
        sub_results[web] = []
    if web not in sub_ids:
        sub_ids[web] = []
    if task_id in all_result:
        sub_results[web].append(all_result[task_id])
        if all_result[task_id] == 1:
            sub_ids[web].append(old_task_id)
    else:
        sub_results[web].append(0)
for web in sub_results:
    print(web, round(sum(sub_results[web]) / len(sub_results[web]) * 100, 1))

print('\n\n')
for web in sub_ids:
    print(web, sorted(sub_ids[web]), len(sub_ids[web]))