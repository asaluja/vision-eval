"""Top-level runner for Phase 1: generate images and evaluate Haiku 4.5.

Usage:
    python run_phase1.py                          # Generate + evaluate all tasks
    python run_phase1.py --generate-only          # Only generate images
    python run_phase1.py --eval-only              # Only evaluate (images must exist)
    python run_phase1.py --tasks counting_circles nested_squares  # Specific tasks
    python run_phase1.py --n 5                    # N samples per config
"""

import argparse
import os
import sys

import config
from generate.base import TaskInstance, save_instances, load_instances
from evaluate.run_eval import run_evaluation, print_summary

# Registry: task_type -> (module_path, generate_function_name)
TASK_REGISTRY = {
    # VLMs Are Blind
    "counting_circles": ("generate.counting_shapes", {"shape": "circle"}),
    "counting_pentagons": ("generate.counting_shapes", {"shape": "pentagon"}),
    "line_intersection": ("generate.line_intersection", {}),
    "nested_squares": ("generate.nested_shapes", {}),
    "touching_circles": ("generate.touching_circles", {}),
    "circled_letter": ("generate.circled_letter", {}),
    "grid_counting": ("generate.grid_counting", {}),
    "path_following": ("generate.path_following", {}),
    # VLMs Are Biased
    "patterned_grid": ("generate.patterned_grids", {}),
    "board_games": ("generate.board_games", {}),
    # Business-critical
    "chart": ("generate.charts", {}),
    "table": ("generate.tables", {}),
    "diagram": ("generate.diagrams", {}),
    # Gap-filling primitives
    "relative_comparison": ("generate.relative_comparison", {}),
    "color_discrimination": ("generate.color_discrimination", {}),
    "text_reading": ("generate.text_reading", {}),
    "chart_comparison": ("generate.chart_comparison", {}),
    "text_visual_conflict": ("generate.text_visual_conflict", {}),
}


def _load_generator(module_path: str):
    """Dynamically import a generator module."""
    import importlib
    return importlib.import_module(module_path)


def generate_all(tasks: list[str], n_per_config: int) -> dict[str, list[TaskInstance]]:
    """Run generators for the specified tasks. Returns dict of task -> instances."""
    all_instances = {}

    for task_name in tasks:
        module_path, extra_kwargs = TASK_REGISTRY[task_name]
        gen_module = _load_generator(module_path)

        print(f"Generating: {task_name}...")

        # Different generators have different n parameter names
        if task_name == "line_intersection":
            instances = gen_module.generate(
                n_per_intersection=n_per_config,
                output_dir=config.GENERATED_DIR,
                **extra_kwargs,
            )
        else:
            instances = gen_module.generate(
                n_per_config=n_per_config,
                output_dir=config.GENERATED_DIR,
                **extra_kwargs,
            )

        # Save instance metadata
        meta_path = os.path.join(config.RESULTS_DIR, f"{task_name}_instances.jsonl")
        save_instances(instances, meta_path)

        all_instances[task_name] = instances
        print(f"  -> {len(instances)} instances generated")

    return all_instances


def main():
    parser = argparse.ArgumentParser(description="Phase 1: Vision eval pipeline")
    parser.add_argument("--tasks", nargs="+", default=None,
                        choices=list(TASK_REGISTRY.keys()),
                        help="Tasks to run (default: all)")
    parser.add_argument("--n", type=int, default=3,
                        help="Number of samples per configuration")
    parser.add_argument("--generate-only", action="store_true",
                        help="Only generate images, skip evaluation")
    parser.add_argument("--eval-only", action="store_true",
                        help="Only evaluate (load existing instances)")
    parser.add_argument("--workers", type=int, default=10,
                        help="Number of concurrent API calls (default: 10)")
    parser.add_argument("--thinking", action="store_true",
                        help="Enable extended thinking (step-by-step reasoning)")
    parser.add_argument("--thinking-budget", type=int, default=4096,
                        help="Max tokens for thinking phase (default: 4096)")
    args = parser.parse_args()

    tasks = args.tasks or list(TASK_REGISTRY.keys())

    if args.eval_only:
        # Load pre-generated instances
        all_instances = {}
        for task_name in tasks:
            meta_path = os.path.join(config.RESULTS_DIR, f"{task_name}_instances.jsonl")
            if not os.path.exists(meta_path):
                print(f"WARNING: No instances found for {task_name}, skipping")
                continue
            all_instances[task_name] = load_instances(meta_path)
            print(f"Loaded {len(all_instances[task_name])} instances for {task_name}")
    else:
        all_instances = generate_all(tasks, args.n)

    if args.generate_only:
        print(f"\nGeneration complete. Total: {sum(len(v) for v in all_instances.values())} instances")
        return

    # Run evaluation
    all_results = []
    for task_name, instances in all_instances.items():
        suffix = "_thinking" if args.thinking else ""
        results_path = os.path.join(config.RESULTS_DIR, f"{task_name}_results{suffix}.jsonl")
        results = run_evaluation(
            instances, results_path, max_workers=args.workers,
            thinking=args.thinking, thinking_budget=args.thinking_budget,
        )
        all_results.extend(results)

    print_summary(all_results)


if __name__ == "__main__":
    main()
