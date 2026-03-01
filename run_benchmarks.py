"""Run Haiku 4.5 evaluation against HuggingFace benchmark datasets.

Usage:
    python run_benchmarks.py                                    # Run both datasets
    python run_benchmarks.py --dataset blind                    # Just VLMs-are-Blind
    python run_benchmarks.py --dataset biased                   # Just VLMs-are-Biased
    python run_benchmarks.py --dataset blind --tasks counting_circles nested_squares
    python run_benchmarks.py --dataset biased --topics "Game Board" "Optical Illusion"
    python run_benchmarks.py --max-per-group 10                 # Quick sweep (10 per task/topic)
    python run_benchmarks.py --dataset biased --split original  # Use a specific split
"""

import argparse
import os
import sys

import config
from data.blind import load_blind, list_tasks as list_blind_tasks
from data.biased import load_biased, list_topics as list_biased_topics, AVAILABLE_SPLITS
from evaluate.run_eval import run_evaluation, print_summary


def main():
    parser = argparse.ArgumentParser(description="Run evals on HF benchmark datasets")
    parser.add_argument("--dataset", choices=["blind", "biased", "both"], default="both",
                        help="Which dataset to evaluate (default: both)")
    parser.add_argument("--tasks", nargs="+", default=None,
                        help="VLMs-are-Blind: filter to these task types")
    parser.add_argument("--topics", nargs="+", default=None,
                        help="VLMs-are-Biased: filter to these topics")
    parser.add_argument("--split", default="main",
                        choices=AVAILABLE_SPLITS,
                        help="VLMs-are-Biased: which split (default: main)")
    parser.add_argument("--max-per-group", type=int, default=None,
                        help="Cap instances per task/topic (for quick sweeps)")
    parser.add_argument("--workers", type=int, default=10,
                        help="Number of concurrent API calls (default: 10)")
    parser.add_argument("--thinking", action="store_true",
                        help="Enable extended thinking (step-by-step reasoning)")
    parser.add_argument("--thinking-budget", type=int, default=4096,
                        help="Max tokens for thinking phase (default: 4096)")
    parser.add_argument("--list", action="store_true",
                        help="List available tasks/topics and exit")
    args = parser.parse_args()

    if args.list:
        _list_available(args.dataset)
        return

    all_results = []

    # --- VLMs-are-Blind ---
    if args.dataset in ("blind", "both"):
        print("=" * 60)
        print("VLMs-are-Blind benchmark")
        print("=" * 60)
        instances = load_blind(
            tasks=args.tasks,
            max_per_task=args.max_per_group,
        )
        if instances:
            suffix = "_thinking" if args.thinking else ""
            results_path = os.path.join(config.RESULTS_DIR, f"blind_benchmark_results{suffix}.jsonl")
            results = run_evaluation(
                instances, results_path, max_workers=args.workers,
                thinking=args.thinking, thinking_budget=args.thinking_budget,
            )
            all_results.extend(results)

    # --- VLMs-are-Biased ---
    if args.dataset in ("biased", "both"):
        print("=" * 60)
        print(f"VLMs-are-Biased benchmark (split: {args.split})")
        print("=" * 60)
        instances = load_biased(
            split=args.split,
            topics=args.topics,
            max_per_topic=args.max_per_group,
        )
        if instances:
            suffix = "_thinking" if args.thinking else ""
            results_path = os.path.join(config.RESULTS_DIR, f"biased_benchmark_results{suffix}.jsonl")
            results = run_evaluation(
                instances, results_path, max_workers=args.workers,
                thinking=args.thinking, thinking_budget=args.thinking_budget,
            )
            all_results.extend(results)

    if all_results:
        print("\n" + "=" * 60)
        print("COMBINED RESULTS")
        print("=" * 60)
        print_summary(all_results)


def _list_available(dataset: str):
    """Print available tasks/topics without downloading images."""
    if dataset in ("blind", "both"):
        print("VLMs-are-Blind tasks:")
        for t in list_blind_tasks():
            print(f"  {t}")
    if dataset in ("biased", "both"):
        print("VLMs-are-Biased topics:")
        for t in list_biased_topics():
            print(f"  {t}")


if __name__ == "__main__":
    main()
