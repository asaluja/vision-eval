import json
from collections import defaultdict

base = "/Users/asaluja/Documents/Job_Search/anthropic/vision-eval/results"

def load_jsonl(path):
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows

# Check summaries/ version (v1+v2 combined)
rows_v1 = load_jsonl(f"{base}/diagram_spatial_results.jsonl")
rows_v2 = load_jsonl(f"{base}/diagram_spatial_v2_results.jsonl")
all_diag = rows_v1 + rows_v2

total = len(all_diag)
correct = sum(1 for r in all_diag if r.get("correct",False))
print(f"v1+v2 combined: {correct}/{total} = {correct/total*100:.1f}%")

by_type = defaultdict(lambda: [0,0])
by_tmpl = defaultdict(lambda: [0,0])
for r in all_diag:
    tt = r.get("task_type","?")
    by_type[tt][1] += 1
    if r.get("correct",False): by_type[tt][0] += 1
    meta = r.get("metadata",{})
    tmpl = meta.get("template","?")
    key = (tt, tmpl)
    by_tmpl[key][1] += 1
    if r.get("correct",False): by_tmpl[key][0] += 1

print("By type (v1+v2):")
for tt in sorted(by_type.keys()):
    c,t = by_type[tt]
    print(f"  {tt}: {c}/{t} = {c/t*100:.1f}%")
print("By (type, template) (v1+v2):")
for key in sorted(by_tmpl.keys()):
    c,t = by_tmpl[key]
    print(f"  {key[0]}/{key[1]}: {c}/{t} = {c/t*100:.1f}%")

print("\nSummaries/ version says:")
print("  Diagram decision: 100%, n=300")
print("  Diagram next step: 96.1%, n=180")
print("  Template table: linear 100%(60/60), single_branch 100%(120/120), asymmetric 100%(60/60), multi_decision 76.7%(23/30)")

# Check: the summaries/ version also says "Only 25% non-local" for circled letter
print("\nSummaries/ version circled letter claim: 'Only 25% non-local'")
print("Actual: 32/106 = 30.2%")
