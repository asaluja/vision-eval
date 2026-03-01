"""Reproduce and verify circled-letter off-by-one error statistics."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / "results"


def load_jsonl(path: Path) -> list[dict]:
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


def analyze_off_by_one(rows: list[dict], index_key: str, label: str) -> None:
    """Analyze off-by-one errors for a set of circled-letter results.

    index_key: metadata field for circle position ('circle_index' for HF,
               'target_index' for phase 1).
    """
    total = len(rows)
    correct = sum(1 for r in rows if r.get("correct", False))
    errors = [r for r in rows if not r.get("correct", False)]
    print(f"\n{'='*60}")
    print(f"[{label}] {correct}/{total} = {correct/total*100:.1f}% accuracy")
    print(f"  {len(errors)} total errors")

    valid_errors = []
    invalid_errors = []
    for r in errors:
        extracted = r.get("extracted")
        if extracted and len(extracted) == 1 and extracted.isalpha():
            valid_errors.append(r)
        else:
            invalid_errors.append(r)

    print(f"  {len(valid_errors)} errors with valid letter extraction")
    if invalid_errors:
        invalid_vals = [r.get("extracted", "None") for r in invalid_errors]
        print(f"  {len(invalid_errors)} invalid extractions: {invalid_vals}")

    off_by_one = 0
    left_neighbor = 0
    right_neighbor = 0
    off_by_one_details = []
    non_local_details = []

    for r in valid_errors:
        meta = r.get("metadata", {})
        word = meta.get("word", "")
        pos = meta.get(index_key)
        extracted = r.get("extracted", "").upper()

        if not word or pos is None:
            continue

        # Check left neighbor
        is_left = pos > 0 and word[pos - 1].upper() == extracted
        # Check right neighbor
        is_right = pos < len(word) - 1 and word[pos + 1].upper() == extracted

        if is_left or is_right:
            off_by_one += 1
            direction = "left" if is_left else "right"
            if is_left and is_right:
                direction = "both"
            if is_left:
                left_neighbor += 1
            if is_right:
                right_neighbor += 1
            off_by_one_details.append(
                f"    word={word}, pos={pos}, gt={word[pos]}, "
                f"extracted={r.get('extracted')}, neighbor={direction}"
            )
        else:
            # Show what the neighbors actually were for non-local errors
            left_char = word[pos - 1] if pos > 0 else "-"
            right_char = word[pos + 1] if pos < len(word) - 1 else "-"
            non_local_details.append(
                f"    word={word}, pos={pos}, gt={word[pos]}, "
                f"extracted={r.get('extracted')}, "
                f"neighbors=[{left_char},{right_char}]"
            )

    denom = len(valid_errors)
    if denom > 0:
        pct = off_by_one / denom * 100
        print(f"\n  Off-by-one: {off_by_one}/{denom} = {pct:.1f}%")
        print(f"    Left neighbor: {left_neighbor}, Right neighbor: {right_neighbor}")
    else:
        print("\n  No valid errors to analyze")
        return

    print(f"\n  Off-by-one errors ({off_by_one}):")
    for d in off_by_one_details:
        print(d)

    print(f"\n  Non-local errors ({denom - off_by_one}):")
    for d in non_local_details:
        print(d)


def analyze_target_letter_accuracy(rows: list[dict], label: str) -> None:
    """Break down accuracy by target letter."""
    by_letter = defaultdict(lambda: [0, 0])
    for r in rows:
        gt = r.get("ground_truth", "").upper()
        by_letter[gt][1] += 1
        if r.get("correct", False):
            by_letter[gt][0] += 1

    print(f"\n  [{label}] Accuracy by target letter:")
    for letter in sorted(by_letter.keys()):
        c, t = by_letter[letter]
        pct = c / t * 100
        flag = " <-- LOW" if pct < 50 else ""
        print(f"    '{letter}': {c}/{t} = {pct:.1f}%{flag}")


def analyze_acknowledgement_pos14(rows: list[dict], index_key: str) -> None:
    """Check the specific claim about position 14 of Acknowledgement."""
    ack_14 = [
        r for r in rows
        if r.get("metadata", {}).get("word") == "Acknowledgement"
        and r.get("metadata", {}).get(index_key) == 14
    ]
    if not ack_14:
        print("\n  No Acknowledgement position 14 instances found")
        return

    word = "Acknowledgement"
    print(f"\n  Acknowledgement position 14 = '{word[14]}'")
    print(f"  {len(ack_14)} instances:")
    errors = [r for r in ack_14 if not r.get("correct", False)]
    correct = len(ack_14) - len(errors)
    print(f"    Correct: {correct}/{len(ack_14)}")
    if errors:
        extracted_vals = [r.get("extracted", "?") for r in errors]
        from collections import Counter
        counts = Counter(extracted_vals)
        print(f"    Error extractions: {dict(counts)}")
        print(f"    Note: 's' appears in 'Acknowledgement'? "
              f"{'Yes' if 's' in word or 'S' in word else 'No'}")


if __name__ == "__main__":
    # HF blind benchmark
    blind = load_jsonl(BASE / "blind_circled_letter_results.jsonl")
    if blind:
        analyze_off_by_one(blind, "circle_index", "HF Blind")
        analyze_target_letter_accuracy(blind, "HF Blind")
        analyze_acknowledgement_pos14(blind, "circle_index")

    # Phase 1 (generated)
    phase1 = load_jsonl(BASE / "circled_letter_results.jsonl")
    if phase1:
        analyze_off_by_one(phase1, "target_index", "Phase 1 (generated)")
        analyze_target_letter_accuracy(phase1, "Phase 1 (generated)")
        analyze_acknowledgement_pos14(phase1, "target_index")

    # Combined
    if blind and phase1:
        # Normalize index key for combined analysis
        combined = []
        for r in blind:
            r2 = dict(r)
            r2.setdefault("metadata", {})["_norm_index"] = r2["metadata"].get("circle_index")
            combined.append(r2)
        for r in phase1:
            r2 = dict(r)
            r2.setdefault("metadata", {})["_norm_index"] = r2["metadata"].get("target_index")
            combined.append(r2)
        analyze_off_by_one(combined, "_norm_index", "Combined")
