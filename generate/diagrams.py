"""Generate flowchart/diagram images for path following and node counting.

Templates:
- Linear: Start → A → B → C → End
- Single branch: Start → A → Decision → (Yes: B) / (No: C) → End
- Multi-branch: Start → A → D1 → (Yes: B → D2 → ...) / (No: C) → End

Uses matplotlib with FancyBboxPatch and Polygon for rendering (no graphviz).
"""

from __future__ import annotations

import os
import random
from dataclasses import dataclass, field

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch

from generate.base import TaskInstance, ensure_dir, make_instances

# Content pools
PROCESS_LABELS = [
    "Review Data", "Submit Form", "Send Email", "Update Database",
    "Generate Report", "Validate Input", "Notify Team", "Process Payment",
    "Archive File", "Check Inventory", "Assign Task", "Run Tests",
    "Deploy Code", "Backup System", "Log Event", "Encrypt Data",
]

DECISION_LABELS = [
    "Approved?", "Valid?", "In Stock?", "Amount > $100?",
    "Passed Tests?", "User Exists?", "Retry?", "Complete?",
]


@dataclass
class FlowNode:
    id: str
    label: str
    node_type: str  # "start", "process", "decision", "end"
    x: float = 0.0
    y: float = 0.0


@dataclass
class FlowEdge:
    source: str
    target: str
    label: str = ""  # "Yes", "No", or ""


@dataclass
class FlowChart:
    nodes: list[FlowNode] = field(default_factory=list)
    edges: list[FlowEdge] = field(default_factory=list)

    def node_by_id(self, nid: str) -> FlowNode | None:
        for n in self.nodes:
            if n.id == nid:
                return n
        return None

    def successors(self, nid: str) -> list[tuple[str, str]]:
        """Return list of (target_id, edge_label) for edges from nid."""
        return [(e.target, e.label) for e in self.edges if e.source == nid]

    @property
    def process_nodes(self) -> list[FlowNode]:
        return [n for n in self.nodes if n.node_type in ("process", "decision")]


def _build_linear(n_steps: int) -> FlowChart:
    """Build a linear flowchart: Start → step1 → step2 → ... → End."""
    labels = random.sample(PROCESS_LABELS, min(n_steps, len(PROCESS_LABELS)))
    fc = FlowChart()
    fc.nodes.append(FlowNode("start", "Start", "start"))
    for i, label in enumerate(labels):
        fc.nodes.append(FlowNode(f"p{i}", label, "process"))
    fc.nodes.append(FlowNode("end", "End", "end"))

    ids = [n.id for n in fc.nodes]
    for i in range(len(ids) - 1):
        fc.edges.append(FlowEdge(ids[i], ids[i + 1]))

    return fc


def _build_single_branch(n_steps: int) -> FlowChart:
    """Build: Start → steps → Decision → (Yes: steps) / (No: steps) → End."""
    fc = FlowChart()
    labels = random.sample(PROCESS_LABELS, min(n_steps + 2, len(PROCESS_LABELS)))
    decision_label = random.choice(DECISION_LABELS)

    fc.nodes.append(FlowNode("start", "Start", "start"))

    # Pre-decision steps (1-2)
    n_pre = min(2, n_steps // 3)
    for i in range(n_pre):
        fc.nodes.append(FlowNode(f"pre{i}", labels.pop(0), "process"))

    # Decision node
    fc.nodes.append(FlowNode("d0", decision_label, "decision"))

    # Yes branch (1-2 steps)
    n_yes = max(1, (n_steps - n_pre) // 2)
    for i in range(n_yes):
        fc.nodes.append(FlowNode(f"yes{i}", labels.pop(0), "process"))

    # No branch (1-2 steps)
    n_no = max(1, n_steps - n_pre - n_yes)
    for i in range(min(n_no, len(labels))):
        fc.nodes.append(FlowNode(f"no{i}", labels.pop(0), "process"))

    fc.nodes.append(FlowNode("end", "End", "end"))

    # Edges: start → pre steps → decision
    prev = "start"
    for i in range(n_pre):
        fc.edges.append(FlowEdge(prev, f"pre{i}"))
        prev = f"pre{i}"
    fc.edges.append(FlowEdge(prev, "d0"))

    # Yes branch
    prev = "d0"
    for i in range(n_yes):
        fc.edges.append(FlowEdge(prev, f"yes{i}", "Yes" if prev == "d0" else ""))
        prev = f"yes{i}"
    fc.edges.append(FlowEdge(prev, "end"))

    # No branch
    n_no_actual = len([n for n in fc.nodes if n.id.startswith("no")])
    prev = "d0"
    for i in range(n_no_actual):
        fc.edges.append(FlowEdge(prev, f"no{i}", "No" if prev == "d0" else ""))
        prev = f"no{i}"
    fc.edges.append(FlowEdge(prev, "end"))

    return fc


def _layout(fc: FlowChart):
    """Assign (x, y) positions to nodes using simple top-down layout."""
    # Identify branch structure
    yes_nodes = {n.id for n in fc.nodes if n.id.startswith("yes")}
    no_nodes = {n.id for n in fc.nodes if n.id.startswith("no")}
    has_branches = bool(yes_nodes or no_nodes)

    y = 0.0
    row_height = 1.5
    center_x = 0.0
    branch_offset = 2.5

    for node in fc.nodes:
        if node.node_type == "start":
            node.x, node.y = center_x, y
            y -= row_height
        elif node.id.startswith("pre") or (node.node_type == "process" and not has_branches):
            node.x, node.y = center_x, y
            y -= row_height
        elif node.node_type == "decision":
            node.x, node.y = center_x, y
            y -= row_height
        elif node.id.startswith("yes"):
            idx = int(node.id[3:])
            node.x = -branch_offset
            node.y = y - idx * row_height
        elif node.id.startswith("no"):
            idx = int(node.id[2:])
            node.x = branch_offset
            node.y = y - idx * row_height
        elif node.node_type == "end":
            # Place end below the deepest branch node
            all_ys = [n.y for n in fc.nodes if n.id != "end"]
            node.x = center_x
            node.y = min(all_ys) - row_height

    # For linear charts (no branches), just stack vertically
    if not has_branches:
        y = 0.0
        for node in fc.nodes:
            node.x = center_x
            node.y = y
            y -= row_height


def _draw_flowchart(fc: FlowChart, output_path: str):
    """Render flowchart to PNG using matplotlib."""
    _layout(fc)

    fig, ax = plt.subplots(figsize=(8, max(6, len(fc.nodes) * 1.2)))
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_facecolor("white")

    node_w = 2.0
    node_h = 0.7
    diamond_size = 0.9

    # Draw edges first (behind nodes)
    for edge in fc.edges:
        src = fc.node_by_id(edge.source)
        tgt = fc.node_by_id(edge.target)
        if not src or not tgt:
            continue

        # Determine connection points
        sx, sy = src.x, src.y
        tx, ty = tgt.x, tgt.y

        # Offset from node edges
        if src.node_type == "decision":
            if edge.label == "Yes":
                sx -= diamond_size * 0.8
            elif edge.label == "No":
                sx += diamond_size * 0.8
            else:
                sy -= node_h / 2
        else:
            sy -= node_h / 2

        if tgt.node_type == "decision":
            ty += diamond_size * 0.8
        else:
            ty += node_h / 2

        ax.annotate("", xy=(tx, ty), xytext=(sx, sy),
                     arrowprops=dict(arrowstyle="-|>", lw=1.5, color="black",
                                     connectionstyle="arc3,rad=0.0"))

        # Edge label
        if edge.label:
            mx = (sx + tx) / 2
            my = (sy + ty) / 2
            ax.text(mx + 0.15, my, edge.label, fontsize=9, color="green",
                    fontweight="bold", ha="left", va="center")

    # Draw nodes
    for node in fc.nodes:
        x, y = node.x, node.y

        if node.node_type in ("start", "end"):
            box = FancyBboxPatch((x - node_w / 2, y - node_h / 2), node_w, node_h,
                                  boxstyle="round,pad=0.15",
                                  facecolor="#90EE90" if node.node_type == "start" else "#FFB6C1",
                                  edgecolor="black", linewidth=1.5)
            ax.add_patch(box)
            ax.text(x, y, node.label, ha="center", va="center", fontsize=11, fontweight="bold")

        elif node.node_type == "process":
            box = FancyBboxPatch((x - node_w / 2, y - node_h / 2), node_w, node_h,
                                  boxstyle="round,pad=0.08",
                                  facecolor="#ADD8E6", edgecolor="black", linewidth=1.5)
            ax.add_patch(box)
            ax.text(x, y, node.label, ha="center", va="center", fontsize=9,
                    wrap=True)

        elif node.node_type == "decision":
            d = diamond_size
            diamond = plt.Polygon(
                [(x, y + d), (x + d * 1.3, y), (x, y - d), (x - d * 1.3, y)],
                facecolor="#FFFACD", edgecolor="black", linewidth=1.5,
            )
            ax.add_patch(diamond)
            ax.text(x, y, node.label, ha="center", va="center", fontsize=8,
                    fontweight="bold")

    # Auto-scale
    all_x = [n.x for n in fc.nodes]
    all_y = [n.y for n in fc.nodes]
    pad = 2.0
    ax.set_xlim(min(all_x) - pad, max(all_x) + pad)
    ax.set_ylim(min(all_y) - pad, max(all_y) + pad)

    fig.savefig(output_path, dpi=100, bbox_inches="tight", pad_inches=0.2)
    plt.close(fig)


def generate(
    n_per_config: int = 1,
    output_dir: str = "generate/images",
    templates: list[str] | None = None,
    n_steps_list: list[int] | None = None,
) -> list[TaskInstance]:
    """Generate flowchart images with multiple questions per diagram."""
    if templates is None:
        templates = ["linear", "single_branch"]
    if n_steps_list is None:
        n_steps_list = [3, 5, 7]

    out = ensure_dir(os.path.join(output_dir, "diagrams"))
    instances = []

    for template in templates:
        for n_steps in n_steps_list:
            for i in range(n_per_config):
                fname = f"flow_{template}_n{n_steps}_{i}.png"
                fpath = os.path.join(out, fname)

                if template == "linear":
                    fc = _build_linear(n_steps)
                elif template == "single_branch":
                    fc = _build_single_branch(n_steps)
                else:
                    fc = _build_linear(n_steps)

                _draw_flowchart(fc, fpath)
                process_nodes = fc.process_nodes

                # Q1: node count (excluding start/end)
                instances.extend(make_instances(
                    fpath, "diagram_node_count", len(process_nodes),
                    subtask=f"{template}_n{n_steps}",
                    metadata={"template": template, "n_steps": n_steps,
                              "n_process_nodes": len(process_nodes)},
                ))

                # Q2: next step (pick a non-end process node)
                candidates = [n for n in fc.nodes
                              if n.node_type in ("process", "start")
                              and fc.successors(n.id)]
                if candidates:
                    src = random.choice(candidates)
                    succs = fc.successors(src.id)
                    tgt_id, _ = succs[0]
                    tgt_node = fc.node_by_id(tgt_id)
                    if tgt_node:
                        instances.extend(make_instances(
                            fpath, "diagram_next_step", tgt_node.label,
                            subtask=f"{template}_next",
                            metadata={"template": template, "source_node": src.label,
                                      "target_node": tgt_node.label},
                            node_label=src.label,
                        ))

                # Q3: decision following (if there are decision nodes)
                decision_nodes = [n for n in fc.nodes if n.node_type == "decision"]
                for dnode in decision_nodes:
                    succs = fc.successors(dnode.id)
                    for tgt_id, edge_label in succs:
                        if edge_label in ("Yes", "No"):
                            tgt_node = fc.node_by_id(tgt_id)
                            if tgt_node:
                                instances.extend(make_instances(
                                    fpath, "diagram_decision", tgt_node.label,
                                    subtask=f"{template}_decision_{edge_label}",
                                    metadata={"template": template,
                                              "condition": dnode.label,
                                              "branch": edge_label,
                                              "target_node": tgt_node.label},
                                    condition=dnode.label,
                                    answer=edge_label,
                                ))

    return instances


if __name__ == "__main__":
    insts = generate(n_per_config=1, templates=["linear", "single_branch"],
                     n_steps_list=[4])
    print(f"Generated {len(insts)} instances")
    for inst in insts:
        print(f"  {inst.task_type:25s} -> {inst.ground_truth}")
