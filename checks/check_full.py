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

# === FULL AUDIT SUMMARY ===

# 1. TABLE CELL LOOKUP
rows_v1 = load_jsonl(f"{base}/table_cell_lookup_results.jsonl")
rows_v2 = load_jsonl(f"{base}/table_cell_lookup_v2_results.jsonl")
all_table = rows_v1 + rows_v2
t_total = len(all_table)
t_correct = sum(1 for r in all_table if r.get("correct",False))
print(f"[TABLE] {t_correct}/{t_total} = {t_correct/t_total*100:.1f}%")

# 2. DIAGRAM
rows_diag_v2 = load_jsonl(f"{base}/diagram_spatial_v2_results.jsonl")
d_total = len(rows_diag_v2)
d_correct = sum(1 for r in rows_diag_v2 if r.get("correct",False))
print(f"[DIAGRAM] {d_correct}/{d_total} = {d_correct/d_total*100:.1f}%")

by_type = defaultdict(lambda: [0,0])
by_tmpl = defaultdict(lambda: [0,0])
for r in rows_diag_v2:
    tt = r.get("task_type","?")
    meta = r.get("metadata",{})
    tmpl = meta.get("template","?")
    by_type[tt][1] += 1
    if r.get("correct",False): by_type[tt][0] += 1
    key = (tt, tmpl)
    by_tmpl[key][1] += 1
    if r.get("correct",False): by_tmpl[key][0] += 1

for tt in sorted(by_type.keys()):
    c,t = by_type[tt]
    print(f"  [DIAGRAM-{tt}] {c}/{t} = {c/t*100:.1f}%")
for key in sorted(by_tmpl.keys()):
    c,t = by_tmpl[key]
    print(f"  [DIAGRAM-{key[0]}/{key[1]}] {c}/{t} = {c/t*100:.1f}%")

# 3. CHARTS
rows_spatial = load_jsonl(f"{base}/chart_spatial_results.jsonl")
rows_line = load_jsonl(f"{base}/chart_line_value_results.jsonl")

for tt_filter in ["chart_bar_value","chart_grouped_value"]:
    subset = [r for r in rows_spatial if r.get("task_type")==tt_filter]
    c = sum(1 for r in subset if r.get("correct",False))
    t = len(subset)
    print(f"  [CHART-{tt_filter}] {c}/{t} = {c/t*100:.1f}%")

c_line = sum(1 for r in rows_line if r.get("correct",False))
t_line = len(rows_line)
print(f"  [CHART-line_value] {c_line}/{t_line} = {c_line/t_line*100:.1f}%")

# Grouped bar by n_series
print("  Grouped bar by n_series:")
grouped = [r for r in rows_spatial if r.get("task_type")=="chart_grouped_value"]
by_ns = defaultdict(lambda: [0,0])
for r in grouped:
    ns = r.get("metadata",{}).get("n_series","?")
    by_ns[ns][1] += 1
    if r.get("correct",False): by_ns[ns][0] += 1
for ns in sorted(by_ns.keys(), key=lambda x: (str(type(x)),x)):
    c,t = by_ns[ns]
    print(f"    n_series={ns}: {c}/{t} = {c/t*100:.0f}%")

# Line by n_series
print("  Line by n_series:")
by_ns2 = defaultdict(lambda: [0,0])
for r in rows_line:
    ns = r.get("metadata",{}).get("n_series","?")
    by_ns2[ns][1] += 1
    if r.get("correct",False): by_ns2[ns][0] += 1
for ns in sorted(by_ns2.keys(), key=lambda x: (str(type(x)),x)):
    c,t = by_ns2[ns]
    print(f"    n_series={ns}: {c}/{t} = {c/t*100:.0f}%")

# Line show_values
print("  Line by show_values:")
by_sv = defaultdict(lambda: [0,0])
for r in rows_line:
    sv = r.get("metadata",{}).get("show_values","?")
    by_sv[sv][1] += 1
    if r.get("correct",False): by_sv[sv][0] += 1
for sv in sorted(by_sv.keys(), key=str):
    c,t = by_sv[sv]
    print(f"    show_values={sv}: {c}/{t} = {c/t*100:.0f}%")

# 4. CIRCLED LETTER (blind HF)
rows_blind = load_jsonl(f"{base}/blind_circled_letter_results.jsonl")
cl_total = len(rows_blind)
cl_correct = sum(1 for r in rows_blind if r.get("correct",False))
print(f"[CIRCLED LETTER HF] {cl_correct}/{cl_total} = {cl_correct/cl_total*100:.1f}%")

# By word
by_word = defaultdict(lambda: [0,0])
for r in rows_blind:
    word = r.get("metadata",{}).get("word","?")
    by_word[word][1] += 1
    if r.get("correct",False): by_word[word][0] += 1
for w in sorted(by_word.keys()):
    c,t = by_word[w]
    print(f"  [{w}] {c}/{t} = {c/t*100:.1f}%")

# By position for each word
print("  By (word, position):")
by_wp = defaultdict(lambda: [0,0])
for r in rows_blind:
    meta = r.get("metadata",{})
    word = meta.get("word","?")
    pos = meta.get("circle_index","?")
    key = (word, pos)
    by_wp[key][1] += 1
    if r.get("correct",False): by_wp[key][0] += 1
for word in ["Acknowledgement","Subdermatoglyphic","tHyUiKaRbNqWeOpXcZvM"]:
    positions = sorted(set(k[1] for k in by_wp if k[0]==word))
    for pos in positions:
        c,t = by_wp[(word,pos)]
        pct = c/t*100
        flag = " <-- ZERO" if pct == 0 else (" <-- LOW" if pct < 50 else "")
        print(f"    {word[:15]}... pos={pos}: {c}/{t} = {pct:.0f}%{flag}")

# 5. PIE VALUE ESTIMATE
rows_pie = load_jsonl(f"{base}/pie_charts_results.jsonl")
pie_rows = [r for r in rows_pie if r.get("task_type")=="pie_value_estimate"]
pie_c = sum(1 for r in pie_rows if r.get("correct",False))
pie_t = len(pie_rows)
print(f"[PIE VALUE ESTIMATE] {pie_c}/{pie_t} = {pie_c/pie_t*100:.1f}%")

# 6. Check error counts for diagram - "6 of 7 errors"
errors_diag = [r for r in rows_diag_v2 if r.get("task_type")=="diagram_next_step" and not r.get("correct",False)]
print(f"\n[DIAGRAM ERRORS] {len(errors_diag)} total errors")
for r in errors_diag:
    meta = r.get("metadata",{})
    img = r.get("image_path","?").split("/")[-1]
    print(f"  template={meta.get('template')}, img={img}, gt={r.get('ground_truth')}, extracted={r.get('extracted')}")
