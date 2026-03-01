"""Interactive error analysis UI for vision eval results.

Run with: streamlit run analyze/app.py
"""

import json
import os
import glob

import pandas as pd
import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results")


@st.cache_data
def load_results() -> pd.DataFrame:
    """Load all *_results.jsonl files into a single DataFrame."""
    rows = []
    for path in sorted(glob.glob(os.path.join(RESULTS_DIR, "*_results.jsonl"))):
        with open(path) as f:
            for line in f:
                try:
                    rows.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    # Flatten useful metadata fields
    if "metadata" in df.columns:
        meta_df = pd.json_normalize(df["metadata"])
        meta_df.columns = [f"meta_{c}" for c in meta_df.columns]
        df = pd.concat([df, meta_df], axis=1)
    return df


def accuracy_chart(df: pd.DataFrame):
    """Horizontal bar chart of accuracy by task type."""
    acc = df.groupby("task_type")["correct"].mean().sort_values()
    fig, ax = plt.subplots(figsize=(8, max(3, len(acc) * 0.4)))
    colors = ["#d62728" if v < 0.5 else "#ff7f0e" if v < 0.8 else "#2ca02c" for v in acc.values]
    acc.plot.barh(ax=ax, color=colors)
    ax.set_xlim(0, 1)
    ax.set_xlabel("Accuracy")
    ax.set_title("Accuracy by Task Type")
    for i, v in enumerate(acc.values):
        ax.text(v + 0.01, i, f"{v:.0%}", va="center", fontsize=10)
    plt.tight_layout()
    return fig


def render_instance(row, idx):
    """Render a single result instance as a card."""
    is_correct = row.get("correct", False)
    badge = "🟢 Correct" if is_correct else "🔴 Wrong"

    with st.container(border=True):
        col_img, col_info = st.columns([1, 1])

        with col_img:
            img_path = row.get("image_path", "")
            if os.path.exists(img_path):
                st.image(img_path, use_container_width=True)
            else:
                st.warning(f"Image not found: {img_path}")

        with col_info:
            st.markdown(f"**{badge}**  &nbsp; `{row.get('task_type', '')}` / `{row.get('subtask', '')}`")
            st.markdown(f"**Prompt:** {row.get('prompt', '')}")
            st.markdown(f"**Ground truth:** `{row.get('ground_truth', '')}`")
            st.markdown(f"**Extracted:** `{row.get('extracted', 'None')}`")

            # Show bias info if present
            meta = row.get("metadata", {})
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except Exception:
                    meta = {}
            if "expected_bias" in meta:
                st.markdown(f"**Expected bias:** `{meta['expected_bias']}`")

            with st.expander("Full model response"):
                st.text(row.get("response", ""))
            with st.expander("Metadata"):
                st.json(meta)


def main():
    st.set_page_config(page_title="Vision Eval Explorer", layout="wide")
    st.title("Vision Eval — Error Analysis")

    df = load_results()
    if df.empty:
        st.error("No results found. Run the evaluation first.")
        return

    # ── Sidebar filters ──
    st.sidebar.header("Filters")

    # Data source filter (synthetic vs benchmark)
    if "meta_source" in df.columns:
        df["meta_source"] = df["meta_source"].fillna("synthetic")
    else:
        df["meta_source"] = "synthetic"
    sources = ["All"] + sorted(df["meta_source"].unique().tolist())
    selected_source = st.sidebar.selectbox("Data source", sources)
    filtered = df if selected_source == "All" else df[df["meta_source"] == selected_source]

    task_types = ["All"] + sorted(filtered["task_type"].unique().tolist())
    selected_task = st.sidebar.selectbox("Task type", task_types)

    filtered = filtered if selected_task == "All" else filtered[filtered["task_type"] == selected_task]

    subtasks = ["All"] + sorted(filtered["subtask"].dropna().unique().tolist())
    selected_subtask = st.sidebar.selectbox("Subtask", subtasks)
    if selected_subtask != "All":
        filtered = filtered[filtered["subtask"] == selected_subtask]

    result_filter = st.sidebar.radio("Show", ["All", "Errors only", "Correct only"])
    if result_filter == "Errors only":
        filtered = filtered[filtered["correct"] == False]
    elif result_filter == "Correct only":
        filtered = filtered[filtered["correct"] == True]

    # Dynamic metadata filters based on selected task
    if selected_task != "All":
        meta_cols = [c for c in filtered.columns if c.startswith("meta_")]
        for col in meta_cols:
            # Skip columns with unhashable types (lists, dicts)
            sample = filtered[col].dropna().iloc[0] if len(filtered[col].dropna()) > 0 else None
            if isinstance(sample, (list, dict)):
                continue
            try:
                unique_vals = filtered[col].dropna().unique()
            except TypeError:
                continue
            if len(unique_vals) > 1 and len(unique_vals) <= 20:
                nice_name = col.replace("meta_", "")
                if filtered[col].dtype in ["float64", "int64"] and len(unique_vals) > 5:
                    vmin, vmax = float(filtered[col].min()), float(filtered[col].max())
                    lo, hi = st.sidebar.slider(nice_name, vmin, vmax, (vmin, vmax))
                    filtered = filtered[(filtered[col] >= lo) & (filtered[col] <= hi)]
                else:
                    options = ["All"] + sorted([str(v) for v in unique_vals])
                    sel = st.sidebar.selectbox(nice_name, options, key=f"filter_{col}")
                    if sel != "All":
                        filtered = filtered[filtered[col].astype(str) == sel]

    st.sidebar.markdown(f"**Showing {len(filtered)} / {len(df)} instances**")

    # ── Summary stats ──
    col1, col2, col3, col4 = st.columns(4)
    total = len(filtered)
    correct = int(filtered["correct"].sum()) if total else 0
    errors = total - correct
    acc = correct / total if total else 0
    col1.metric("Total", total)
    col2.metric("Correct", correct)
    col3.metric("Errors", errors)
    col4.metric("Accuracy", f"{acc:.1%}")

    # ── Accuracy chart ──
    if selected_task == "All" and total > 0:
        st.pyplot(accuracy_chart(filtered))
    elif total > 0:
        # Show subtask breakdown for selected task
        sub_acc = filtered.groupby("subtask")["correct"].agg(["mean", "count"])
        sub_acc.columns = ["accuracy", "n"]
        sub_acc = sub_acc.sort_values("accuracy")
        if len(sub_acc) > 1:
            fig, ax = plt.subplots(figsize=(8, max(3, len(sub_acc) * 0.35)))
            colors = ["#d62728" if v < 0.5 else "#ff7f0e" if v < 0.8 else "#2ca02c"
                       for v in sub_acc["accuracy"].values]
            sub_acc["accuracy"].plot.barh(ax=ax, color=colors)
            ax.set_xlim(0, 1)
            ax.set_xlabel("Accuracy")
            ax.set_title(f"Accuracy by Subtask — {selected_task}")
            for i, (v, n) in enumerate(zip(sub_acc["accuracy"].values, sub_acc["n"].values)):
                ax.text(v + 0.01, i, f"{v:.0%} (n={n})", va="center", fontsize=9)
            plt.tight_layout()
            st.pyplot(fig)

    # ── Instance browser ──
    st.markdown("---")
    st.subheader("Instance Browser")

    page_size = 20
    n_pages = max(1, (len(filtered) + page_size - 1) // page_size)
    page = st.number_input("Page", min_value=1, max_value=n_pages, value=1) - 1
    start = page * page_size
    end = min(start + page_size, len(filtered))

    for idx in range(start, end):
        row = filtered.iloc[idx]
        render_instance(row.to_dict(), idx)


if __name__ == "__main__":
    main()
