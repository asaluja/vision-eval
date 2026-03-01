import json
from collections import defaultdict

base = "/Users/asaluja/Documents/Job_Search/anthropic/vision-eval/results"

def load_jsonl(path):
    rows = []
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
    except FileNotFoundError:
        print(f"  NOT FOUND: {path}")
    return rows

rows_v2 = load_jsonl(f"{base}/diagram_spatial_v2_results.jsonl")
next_step = [r for r in rows_v2 if r.get("task_type")=="diagram_next_step"]
errors = [r for r in next_step if not r.get("correct",False)]
print(f"Diagram next_step errors: {len(errors)}")
for r in errors:
    meta = r.get("metadata",{})
    img = r.get("image_path","?").split("/")[-1]
    print(f"  template={meta.get('template')}, image={img}, gt={r.get('ground_truth')}, extracted={r.get('extracted')}")

# Also check pie_value_estimate
print("\n=== PIE VALUE ESTIMATE ===")
rows_pie = load_jsonl(f"{base}/pie_charts_results.jsonl")
pie_rows = [r for r in rows_pie if r.get("task_type") == "pie_value_estimate"]
total = len(pie_rows)
correct = sum(1 for r in pie_rows if r.get("correct",False))
print(f"Total: {total}, Correct: {correct}, Accuracy: {correct/total*100:.1f}%")

# By n_slices
by_slices = defaultdict(lambda: [0,0])
for r in pie_rows:
    meta = r.get("metadata",{})
    ns = meta.get("n_slices","?")
    by_slices[ns][1] += 1
    if r.get("correct",False):
        by_slices[ns][0] += 1
print("By n_slices:")
for ns in sorted(by_slices.keys(), key=lambda x: (str(type(x)),x)):
    c,t = by_slices[ns]
    print(f"  n_slices={ns}: {c}/{t} = {c/t*100:.0f}%")

by_show = defaultdict(lambda: [0,0])
for r in pie_rows:
    meta = r.get("metadata",{})
    sp = meta.get("show_percentages","?")
    by_show[sp][1] += 1
    if r.get("correct",False):
        by_show[sp][0] += 1
print("By show_percentages:")
for sp in sorted(by_show.keys(), key=str):
    c,t = by_show[sp]
    print(f"  show_percentages={sp}: {c}/{t} = {c/t*100:.0f}%")
