"""CLIP-DINOv2 divergent pair selection for chart images.

Loads ChartQA and PlotQA images, computes CLIP and DINOv2 embeddings,
and selects pairs with high CLIP similarity but low DINOv2 similarity.
These pairs are semantically similar but perceptually different --
good for testing whether VLMs actually look at visual details.

Usage:
    python -m data.clip_dino_pairs                          # both datasets
    python -m data.clip_dino_pairs --dataset chartqa        # ChartQA only
    python -m data.clip_dino_pairs --clip-pct 80 --dino-pct 20 --top-k 200
    python -m data.clip_dino_pairs --use-cached             # reuse embeddings
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
from collections import defaultdict

import numpy as np
from PIL import Image
from tqdm import tqdm

# --------------- Constants ---------------

CHARTQA_DATASET_ID = "HuggingFaceM4/ChartQA"
PLOTQA_DATASET_ID = "achang/plot_qa"

CLIP_MODEL_ID = "openai/clip-vit-base-patch32"
DINO_MODEL_ID = "facebook/dinov2-base"

# Zero-shot chart type labels for CLIP classification
CHART_TYPE_LABELS = [
    "a vertical bar chart",
    "a horizontal bar chart",
    "a line chart",
    "a pie chart",
]

# Map raw labels → unified taxonomy
CHART_TYPE_MAP = {
    # CLIP zero-shot labels
    "a vertical bar chart": "bar_vertical",
    "a horizontal bar chart": "bar_horizontal",
    "a line chart": "line",
    "a pie chart": "pie",
    # PlotQA annotation types
    "vbar_categorical": "bar_vertical",
    "hbar_categorical": "bar_horizontal",
    "dot_line": "line",
    "line": "line",
}

# Directories
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
IMAGE_DIR = os.path.join(BASE_DIR, "data", "images", "chart_pairs")
CACHE_DIR = os.path.join(BASE_DIR, "data", "cache", "chart_pairs")
EMBED_DIR = os.path.join(CACHE_DIR, "embeddings")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
FIGURES_DIR = os.path.join(BASE_DIR, "figures")


# --------------- Device Selection ---------------

def get_device() -> str:
    """Select best available device: mps > cuda > cpu."""
    import torch

    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


# --------------- Data Loading: ChartQA ---------------

def load_chartqa_images(
    split: str = "test",
    cache_dir: str | None = None,
    image_dir: str | None = None,
) -> list[dict]:
    """Load ChartQA images, deduplicate, and save to disk.

    Returns list of dicts: {image_path, dataset, index, chart_type}.
    chart_type is None here — filled later by CLIP zero-shot.
    """
    from datasets import load_dataset

    cache_dir = cache_dir or CACHE_DIR
    image_dir = image_dir or os.path.join(IMAGE_DIR, "chartqa")
    os.makedirs(image_dir, exist_ok=True)

    # Check for cached records
    records_path = os.path.join(cache_dir, "chartqa_records.json")
    if os.path.exists(records_path):
        with open(records_path) as f:
            records = json.load(f)
        print(f"Loaded {len(records)} cached ChartQA records")
        # Verify images still exist
        if all(os.path.exists(r["image_path"]) for r in records[:5]):
            return records

    ds = load_dataset(CHARTQA_DATASET_ID, split=split, cache_dir=cache_dir)

    seen_hashes: set[str] = set()
    records: list[dict] = []

    for idx, row in enumerate(tqdm(ds, desc="Loading ChartQA")):
        img = row["image"].convert("RGB")
        # Deduplicate by image content hash
        img_hash = hashlib.md5(img.tobytes()).hexdigest()
        if img_hash in seen_hashes:
            continue
        seen_hashes.add(img_hash)

        image_path = os.path.join(image_dir, f"chartqa_{idx:05d}.png")
        if not os.path.exists(image_path):
            img.save(image_path)

        records.append({
            "image_path": os.path.abspath(image_path),
            "dataset": "chartqa",
            "index": idx,
            "chart_type": None,
        })

    # Cache records
    os.makedirs(cache_dir, exist_ok=True)
    with open(records_path, "w") as f:
        json.dump(records, f)

    print(f"ChartQA: {len(records)} unique images from {len(ds)} rows")
    return records


# --------------- Data Loading: PlotQA ---------------

def extract_plotqa_chart_type(text: str) -> str | None:
    """Parse chart type from PlotQA text field.

    Tries Donut-style tokens first, then keyword matching.
    """
    # Donut-style: <s_type>vbar_categorical</s_type>
    m = re.search(r"<s_type>(.*?)</s_type>", text)
    if m:
        return m.group(1).strip()
    # Keyword fallback
    for kw in ["vbar_categorical", "hbar_categorical", "dot_line"]:
        if kw in text:
            return kw
    if "line" in text.lower():
        return "line"
    return None


def load_plotqa_images(
    split: str = "test",
    max_images: int = 3000,
    cache_dir: str | None = None,
    image_dir: str | None = None,
) -> list[dict]:
    """Load PlotQA images with stratified sampling by chart type.

    Returns list of dicts: {image_path, dataset, index, chart_type}.
    """
    from datasets import load_dataset

    cache_dir = cache_dir or CACHE_DIR
    image_dir = image_dir or os.path.join(IMAGE_DIR, "plotqa")
    os.makedirs(image_dir, exist_ok=True)

    # Check for cached records
    records_path = os.path.join(cache_dir, "plotqa_records.json")
    if os.path.exists(records_path):
        with open(records_path) as f:
            records = json.load(f)
        print(f"Loaded {len(records)} cached PlotQA records")
        if all(os.path.exists(r["image_path"]) for r in records[:5]):
            return records

    print("Loading PlotQA dataset (this may take a while on first run)...")
    ds = load_dataset(PLOTQA_DATASET_ID, split=split, cache_dir=cache_dir)

    # First pass: collect indices by chart type
    by_type: dict[str, list[int]] = defaultdict(list)
    print("Extracting chart types...")
    for idx, row in enumerate(tqdm(ds, desc="Scanning PlotQA")):
        text = row.get("text", "")
        ct = extract_plotqa_chart_type(text)
        mapped = CHART_TYPE_MAP.get(ct, ct) if ct else None
        by_type[mapped or "unknown"].append(idx)

    # Report type distribution
    print("PlotQA chart type distribution:")
    for ct, indices in sorted(by_type.items()):
        print(f"  {ct}: {len(indices)}")

    # If most types are unknown, we'll classify with CLIP later
    unknown_frac = len(by_type.get("unknown", [])) / len(ds) if len(ds) > 0 else 0
    if unknown_frac > 0.5:
        print(f"  Warning: {unknown_frac:.0%} unknown types — will use CLIP classification")
        # Sample uniformly from all images
        all_indices = list(range(len(ds)))
        random.shuffle(all_indices)
        sample_indices = all_indices[:max_images]
    else:
        # Stratified sample
        known_types = {k: v for k, v in by_type.items() if k != "unknown"}
        per_type = max_images // max(len(known_types), 1)
        sample_indices = []
        for ct, indices in known_types.items():
            random.shuffle(indices)
            sample_indices.extend(indices[:per_type])
        # Fill remaining with unknown if needed
        remaining = max_images - len(sample_indices)
        if remaining > 0 and "unknown" in by_type:
            unknown = by_type["unknown"]
            random.shuffle(unknown)
            sample_indices.extend(unknown[:remaining])

    sample_indices_set = set(sample_indices)

    # Second pass: save sampled images
    records: list[dict] = []
    for idx, row in enumerate(tqdm(ds, desc="Saving PlotQA images")):
        if idx not in sample_indices_set:
            continue
        img = row["image"].convert("RGB")
        image_path = os.path.join(image_dir, f"plotqa_{idx:06d}.png")
        if not os.path.exists(image_path):
            img.save(image_path)

        text = row.get("text", "")
        ct = extract_plotqa_chart_type(text)
        mapped = CHART_TYPE_MAP.get(ct, ct) if ct else None

        records.append({
            "image_path": os.path.abspath(image_path),
            "dataset": "plotqa",
            "index": idx,
            "chart_type": mapped,  # may be None
        })

    # Cache records
    os.makedirs(cache_dir, exist_ok=True)
    with open(records_path, "w") as f:
        json.dump(records, f)

    print(f"PlotQA: sampled {len(records)} images from {len(ds)} rows")
    return records


# --------------- Chart Type Classification ---------------

def classify_chart_types_clip(
    image_paths: list[str],
    model,
    processor,
    device: str,
    labels: list[str] | None = None,
    batch_size: int = 32,
) -> list[str]:
    """Zero-shot chart type classification using CLIP.

    Returns predicted label string per image.
    """
    import torch

    labels = labels or CHART_TYPE_LABELS

    # Encode text labels
    text_inputs = processor(
        text=labels, return_tensors="pt", padding=True
    ).to(device)
    with torch.no_grad():
        text_features = model.get_text_features(**text_inputs)
        text_features = text_features / text_features.norm(dim=-1, keepdim=True)

    all_types: list[str] = []
    for i in tqdm(range(0, len(image_paths), batch_size), desc="Classifying chart types"):
        batch_paths = image_paths[i : i + batch_size]
        images = [Image.open(p).convert("RGB") for p in batch_paths]
        inputs = processor(images=images, return_tensors="pt", padding=True).to(device)

        with torch.no_grad():
            image_features = model.get_image_features(**inputs)
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)

        sims = image_features @ text_features.T
        predicted_idx = sims.argmax(dim=-1).cpu().tolist()
        all_types.extend([labels[j] for j in predicted_idx])

    return all_types


# --------------- Embedding Computation ---------------

def load_clip_model(device: str):
    """Load CLIP model + processor. Returns (model, processor)."""
    from transformers import CLIPModel, CLIPProcessor

    print(f"Loading CLIP model ({CLIP_MODEL_ID}) on {device}...")
    processor = CLIPProcessor.from_pretrained(CLIP_MODEL_ID)
    model = CLIPModel.from_pretrained(CLIP_MODEL_ID).to(device).eval()
    return model, processor


def load_dino_model(device: str):
    """Load DINOv2 model + processor. Returns (model, processor)."""
    from transformers import AutoImageProcessor, AutoModel

    print(f"Loading DINOv2 model ({DINO_MODEL_ID}) on {device}...")
    processor = AutoImageProcessor.from_pretrained(DINO_MODEL_ID)
    model = AutoModel.from_pretrained(DINO_MODEL_ID).to(device).eval()
    return model, processor


def compute_clip_embeddings(
    image_paths: list[str],
    model,
    processor,
    device: str,
    batch_size: int = 32,
) -> np.ndarray:
    """Compute L2-normalized CLIP vision embeddings. Returns (N, 512)."""
    import torch

    all_embeddings: list[np.ndarray] = []
    for i in tqdm(range(0, len(image_paths), batch_size), desc="CLIP embeddings"):
        batch_paths = image_paths[i : i + batch_size]
        images = [Image.open(p).convert("RGB") for p in batch_paths]
        inputs = processor(images=images, return_tensors="pt", padding=True).to(device)

        with torch.no_grad():
            features = model.get_image_features(**inputs)
            features = features / features.norm(dim=-1, keepdim=True)

        all_embeddings.append(features.cpu().numpy())

    return np.concatenate(all_embeddings, axis=0)


def compute_dino_embeddings(
    image_paths: list[str],
    model,
    processor,
    device: str,
    batch_size: int = 32,
) -> np.ndarray:
    """Compute L2-normalized DINOv2 CLS token embeddings. Returns (N, 768)."""
    import torch

    all_embeddings: list[np.ndarray] = []
    for i in tqdm(range(0, len(image_paths), batch_size), desc="DINOv2 embeddings"):
        batch_paths = image_paths[i : i + batch_size]
        images = [Image.open(p).convert("RGB") for p in batch_paths]
        inputs = processor(images=images, return_tensors="pt").to(device)

        with torch.no_grad():
            outputs = model(**inputs)
            cls_features = outputs.last_hidden_state[:, 0, :]
            cls_features = cls_features / cls_features.norm(dim=-1, keepdim=True)

        all_embeddings.append(cls_features.cpu().numpy())

    return np.concatenate(all_embeddings, axis=0)


def save_embeddings(embeddings: np.ndarray, path: str) -> None:
    """Cache embeddings as .npy file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    np.save(path, embeddings)
    print(f"Saved embeddings {embeddings.shape} to {path}")


def load_embeddings(path: str) -> np.ndarray | None:
    """Load cached embeddings. Returns None if not found."""
    if os.path.exists(path):
        emb = np.load(path)
        print(f"Loaded cached embeddings {emb.shape} from {path}")
        return emb
    return None


# --------------- Pair Selection ---------------

def select_divergent_pairs(
    image_records: list[dict],
    clip_embeddings: np.ndarray,
    dino_embeddings: np.ndarray,
    clip_percentile: float = 75.0,
    dino_percentile: float = 25.0,
    top_k: int = 100,
    within_chart_type: bool = True,
    min_group_size: int = 20,
) -> list[dict]:
    """Select image pairs with high CLIP but low DINOv2 similarity.

    Groups by chart_type if within_chart_type=True.
    Returns list of pair dicts ranked by gap = clip_sim - dino_sim.
    """
    all_pairs: list[dict] = []

    if within_chart_type:
        groups: dict[str, list[int]] = defaultdict(list)
        for i, rec in enumerate(image_records):
            ct = rec.get("chart_type") or "unknown"
            groups[ct].append(i)
    else:
        groups = {"all": list(range(len(image_records)))}

    for chart_type, indices in groups.items():
        if len(indices) < min_group_size:
            print(f"  Skipping {chart_type} ({len(indices)} images < {min_group_size})")
            continue

        idx_arr = np.array(indices)
        clip_sub = clip_embeddings[idx_arr]
        dino_sub = dino_embeddings[idx_arr]

        # Cosine similarity (embeddings are L2-normalized)
        clip_sim = clip_sub @ clip_sub.T
        dino_sim = dino_sub @ dino_sub.T

        # Upper triangle mask (exclude diagonal and lower triangle)
        n = len(indices)
        triu_rows, triu_cols = np.triu_indices(n, k=1)

        clip_vals = clip_sim[triu_rows, triu_cols]
        dino_vals = dino_sim[triu_rows, triu_cols]

        clip_thresh = np.percentile(clip_vals, clip_percentile)
        dino_thresh = np.percentile(dino_vals, dino_percentile)

        print(f"  {chart_type}: {n} images, "
              f"CLIP thresh={clip_thresh:.3f} (p{clip_percentile:.0f}), "
              f"DINOv2 thresh={dino_thresh:.3f} (p{dino_percentile:.0f})")

        # Select pairs meeting both criteria
        mask = (clip_vals >= clip_thresh) & (dino_vals <= dino_thresh)
        selected_positions = np.where(mask)[0]

        for pos in selected_positions:
            local_i, local_j = triu_rows[pos], triu_cols[pos]
            global_i, global_j = idx_arr[local_i], idx_arr[local_j]
            c_sim = float(clip_vals[pos])
            d_sim = float(dino_vals[pos])
            all_pairs.append({
                "image_a_path": image_records[global_i]["image_path"],
                "image_b_path": image_records[global_j]["image_path"],
                "clip_sim": c_sim,
                "dino_sim": d_sim,
                "gap": c_sim - d_sim,
                "chart_type": chart_type,
                "dataset_a": image_records[global_i]["dataset"],
                "dataset_b": image_records[global_j]["dataset"],
            })

    # Rank by gap descending
    all_pairs.sort(key=lambda p: p["gap"], reverse=True)
    print(f"\nTotal candidate pairs: {len(all_pairs)}, returning top {top_k}")
    return all_pairs[:top_k]


# --------------- Output ---------------

def save_pairs_jsonl(pairs: list[dict], output_path: str) -> None:
    """Write selected pairs as JSONL."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        for p in pairs:
            f.write(json.dumps(p) + "\n")
    print(f"Saved {len(pairs)} pairs to {output_path}")


def generate_pair_grid(
    pairs: list[dict],
    output_path: str,
    n_pairs: int = 12,
) -> None:
    """Create a visual grid of top divergent pairs."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    n_pairs = min(n_pairs, len(pairs))
    if n_pairs == 0:
        print("No pairs to visualize")
        return

    fig, axes = plt.subplots(n_pairs, 2, figsize=(14, 3 * n_pairs))
    if n_pairs == 1:
        axes = axes.reshape(1, 2)

    for row_idx in range(n_pairs):
        pair = pairs[row_idx]
        for col_idx, key in enumerate(["image_a_path", "image_b_path"]):
            ax = axes[row_idx, col_idx]
            img = Image.open(pair[key])
            ax.imshow(img)
            ax.set_xticks([])
            ax.set_yticks([])

        # Annotate
        label = (f"CLIP={pair['clip_sim']:.3f}  "
                 f"DINOv2={pair['dino_sim']:.3f}  "
                 f"gap={pair['gap']:.3f}  "
                 f"[{pair['chart_type']}]")
        axes[row_idx, 0].set_ylabel(
            f"#{row_idx + 1}", fontsize=10, rotation=0, labelpad=25, va="center"
        )
        axes[row_idx, 0].set_title(label, fontsize=8, loc="left")

    fig.suptitle(
        "Top Divergent Pairs: High CLIP (semantic) / Low DINOv2 (perceptual)",
        fontsize=13, fontweight="bold",
    )
    fig.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved pair grid to {output_path}")


def print_summary(pairs: list[dict]) -> None:
    """Print summary statistics of selected pairs."""
    if not pairs:
        print("No pairs selected.")
        return

    clip_sims = [p["clip_sim"] for p in pairs]
    dino_sims = [p["dino_sim"] for p in pairs]
    gaps = [p["gap"] for p in pairs]

    print(f"\n{'='*60}")
    print(f"Selected {len(pairs)} divergent pairs")
    print(f"{'='*60}")
    print(f"  CLIP sim:  mean={np.mean(clip_sims):.3f}  "
          f"min={np.min(clip_sims):.3f}  max={np.max(clip_sims):.3f}")
    print(f"  DINOv2 sim: mean={np.mean(dino_sims):.3f}  "
          f"min={np.min(dino_sims):.3f}  max={np.max(dino_sims):.3f}")
    print(f"  Gap:       mean={np.mean(gaps):.3f}  "
          f"min={np.min(gaps):.3f}  max={np.max(gaps):.3f}")

    # By chart type
    by_type: dict[str, int] = defaultdict(int)
    for p in pairs:
        by_type[p["chart_type"]] += 1
    print(f"\n  By chart type:")
    for ct, count in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f"    {ct}: {count}")

    # Cross-dataset pairs
    cross = sum(1 for p in pairs if p["dataset_a"] != p["dataset_b"])
    print(f"\n  Cross-dataset pairs: {cross}/{len(pairs)}")


# --------------- Main ---------------

def main():
    import torch

    parser = argparse.ArgumentParser(
        description="Select chart image pairs with high CLIP but low DINOv2 similarity"
    )
    parser.add_argument(
        "--dataset", choices=["chartqa", "plotqa", "both"], default="both",
        help="Which dataset(s) to use (default: both)",
    )
    parser.add_argument(
        "--max-plotqa", type=int, default=3000,
        help="Max PlotQA images to sample (default: 3000)",
    )
    parser.add_argument(
        "--clip-pct", type=float, default=75.0,
        help="CLIP similarity percentile threshold (default: 75)",
    )
    parser.add_argument(
        "--dino-pct", type=float, default=25.0,
        help="DINOv2 similarity percentile threshold (default: 25)",
    )
    parser.add_argument(
        "--top-k", type=int, default=100,
        help="Number of top pairs to output (default: 100)",
    )
    parser.add_argument(
        "--batch-size", type=int, default=32,
        help="Batch size for embedding computation (default: 32)",
    )
    parser.add_argument(
        "--use-cached", action="store_true",
        help="Use cached embeddings if available",
    )
    parser.add_argument(
        "--no-grid", action="store_true",
        help="Skip generating the visual pair grid",
    )
    parser.add_argument(
        "--n-grid-pairs", type=int, default=12,
        help="Number of pairs in the visual grid (default: 12)",
    )
    args = parser.parse_args()

    device = get_device()
    print(f"Using device: {device}")

    # ---- Step 1: Load images ----
    all_records: list[dict] = []

    if args.dataset in ("chartqa", "both"):
        chartqa_records = load_chartqa_images()
        all_records.extend(chartqa_records)

    if args.dataset in ("plotqa", "both"):
        plotqa_records = load_plotqa_images(max_images=args.max_plotqa)
        all_records.extend(plotqa_records)

    print(f"\nTotal images: {len(all_records)}")

    # ---- Step 2: Load CLIP model, classify chart types, compute embeddings ----
    image_paths = [r["image_path"] for r in all_records]

    clip_model, clip_processor = load_clip_model(device)

    # Classify chart types for images that don't have one
    needs_classification = [i for i, r in enumerate(all_records) if r["chart_type"] is None]
    if needs_classification:
        print(f"\nClassifying {len(needs_classification)} images by chart type (CLIP zero-shot)...")
        paths_to_classify = [all_records[i]["image_path"] for i in needs_classification]
        predicted = classify_chart_types_clip(
            paths_to_classify, clip_model, clip_processor, device, batch_size=args.batch_size
        )
        for idx, label in zip(needs_classification, predicted):
            all_records[idx]["chart_type"] = CHART_TYPE_MAP.get(label, label)

        # Report classification results
        type_counts: dict[str, int] = defaultdict(int)
        for i in needs_classification:
            type_counts[all_records[i]["chart_type"]] += 1
        print("  CLIP classification results:")
        for ct, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            print(f"    {ct}: {count}")

    # Compute CLIP embeddings
    clip_cache_path = os.path.join(EMBED_DIR, f"clip_{args.dataset}.npy")
    clip_embeddings = load_embeddings(clip_cache_path) if args.use_cached else None

    if clip_embeddings is None or len(clip_embeddings) != len(all_records):
        clip_embeddings = compute_clip_embeddings(
            image_paths, clip_model, clip_processor, device, batch_size=args.batch_size
        )
        save_embeddings(clip_embeddings, clip_cache_path)

    # Free CLIP model memory
    del clip_model, clip_processor
    if device == "mps":
        torch.mps.empty_cache()
    elif device == "cuda":
        torch.cuda.empty_cache()

    # ---- Step 3: Compute DINOv2 embeddings ----
    dino_cache_path = os.path.join(EMBED_DIR, f"dino_{args.dataset}.npy")
    dino_embeddings = load_embeddings(dino_cache_path) if args.use_cached else None

    if dino_embeddings is None or len(dino_embeddings) != len(all_records):
        dino_model, dino_processor = load_dino_model(device)
        dino_embeddings = compute_dino_embeddings(
            image_paths, dino_model, dino_processor, device, batch_size=args.batch_size
        )
        save_embeddings(dino_embeddings, dino_cache_path)
        del dino_model, dino_processor
        if device == "mps":
            torch.mps.empty_cache()
        elif device == "cuda":
            torch.cuda.empty_cache()

    # ---- Step 4: Select divergent pairs ----
    print(f"\nSelecting divergent pairs (CLIP p{args.clip_pct} / DINOv2 p{args.dino_pct})...")
    pairs = select_divergent_pairs(
        all_records, clip_embeddings, dino_embeddings,
        clip_percentile=args.clip_pct,
        dino_percentile=args.dino_pct,
        top_k=args.top_k,
    )

    # ---- Step 5: Output ----
    output_path = os.path.join(RESULTS_DIR, "chart_divergent_pairs.jsonl")
    save_pairs_jsonl(pairs, output_path)
    print_summary(pairs)

    if not args.no_grid and pairs:
        grid_path = os.path.join(FIGURES_DIR, "chart_divergent_pairs.png")
        generate_pair_grid(pairs, grid_path, n_pairs=args.n_grid_pairs)

    # Save updated records with chart types
    records_path = os.path.join(CACHE_DIR, "all_records.json")
    with open(records_path, "w") as f:
        json.dump(all_records, f)
    print(f"\nSaved {len(all_records)} records with chart types to {records_path}")


if __name__ == "__main__":
    main()
