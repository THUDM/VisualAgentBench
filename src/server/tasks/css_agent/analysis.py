import json
import os

count = 0
# for dir in os.listdir('./'):
for dir in os.listdir('../css_dataset/'):
    if dir == "analysis.py":
        continue
    # with open(os.path.join(dir, "corruption", 'record.txt')) as f:
    with open(os.path.join('../css_dataset/', dir, "corruption", 'record.txt')) as f:
        record = f.read()
        record = record.replace('"', '\\"')
        record = record.replace("'", "\"")
        record = json.loads(record)
    print(record["operation"])
    if record["operation"] == "delete":
        count += 1

print(count)