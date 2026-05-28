"""
RIP Protocol Visualisation
===========================
Generates plots for the GitHub portfolio:
  1. Network topology diagram
  2. Convergence animation (hop counts per round)
  3. Count-to-infinity comparison (with vs without poison reverse)

Run: python visualise.py
Output: images/ folder
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
import numpy as np

from rip_simulation import simulate_normal, simulate_failure, INFINITY

os.makedirs("images", exist_ok=True)

ROUTERS = ["A", "B", "C", "D"]
COLORS = {"A": "#4C9BE8", "B": "#E8834C", "C": "#4CE87A", "D": "#E84C8B"}
EDGE_COLOR = "#555555"
BG = "#0d1117"
TEXT = "#e6edf3"
GRID = "#21262d"


# ---------------------------------------------------------------------------
# 1. Topology diagram
# ---------------------------------------------------------------------------

def plot_topology():
    fig, ax = plt.subplots(figsize=(6, 6), facecolor=BG)
    ax.set_facecolor(BG)

    G = nx.Graph()
    G.add_nodes_from(ROUTERS)
    G.add_edges_from([("A", "B"), ("B", "C"), ("C", "D"), ("D", "A")])

    pos = {"A": (0, 1), "B": (1, 1), "C": (1, 0), "D": (0, 0)}

    nx.draw_networkx_edges(G, pos, ax=ax, edge_color=EDGE_COLOR, width=2.5)
    nx.draw_networkx_nodes(G, pos, ax=ax,
                           node_color=[COLORS[r] for r in ROUTERS],
                           node_size=1800)
    nx.draw_networkx_labels(G, pos, ax=ax,
                            font_color="white", font_size=18, font_weight="bold")

    edge_labels = {e: "1 hop" for e in G.edges()}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, ax=ax,
                                 font_color=TEXT, font_size=10,
                                 bbox=dict(boxstyle="round,pad=0.2", fc=BG, ec="none"))

    ax.set_title("Network Topology — Square (A–B–C–D)", color=TEXT, fontsize=14, pad=15)
    ax.axis("off")
    plt.tight_layout()
    plt.savefig("images/topology.png", dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close()
    print("Saved: images/topology.png")


# ---------------------------------------------------------------------------
# 2. Routing table heatmaps per round
# ---------------------------------------------------------------------------

def table_to_matrix(table):
    matrix = np.zeros((4, 4))
    for i, src in enumerate(ROUTERS):
        for j, dst in enumerate(ROUTERS):
            cost, _, _ = table[src][dst]
            matrix[i][j] = cost if cost < INFINITY else 16
    return matrix


def plot_convergence_heatmaps():
    history, routers, links = simulate_normal(verbose=False)

    n_rounds = len(history)
    fig, axes = plt.subplots(1, n_rounds, figsize=(5 * n_rounds, 4.5), facecolor=BG)
    if n_rounds == 1:
        axes = [axes]

    for idx, (table, ax) in enumerate(zip(history, axes)):
        matrix = table_to_matrix(table)
        im = ax.imshow(matrix, vmin=0, vmax=16, cmap="YlOrRd_r", aspect="equal")

        ax.set_xticks(range(4))
        ax.set_yticks(range(4))
        ax.set_xticklabels(ROUTERS, color=TEXT, fontsize=12)
        ax.set_yticklabels(ROUTERS, color=TEXT, fontsize=12)
        ax.set_xlabel("Destination", color=TEXT, fontsize=11)
        ax.set_ylabel("Router" if idx == 0 else "", color=TEXT, fontsize=11)
        ax.set_title(f"Round {idx}", color=TEXT, fontsize=13, pad=8)
        ax.tick_params(colors=TEXT)
        for spine in ax.spines.values():
            spine.set_edgecolor(GRID)
        ax.set_facecolor(BG)

        for i in range(4):
            for j in range(4):
                val = int(matrix[i][j])
                label = "∞" if val >= INFINITY else str(val)
                ax.text(j, i, label, ha="center", va="center",
                        color="white" if val > 3 else "#0d1117",
                        fontsize=14, fontweight="bold")

    fig.suptitle("RIP Convergence — Hop Count by Round", color=TEXT, fontsize=15, y=1.02)
    cbar = fig.colorbar(im, ax=axes, shrink=0.8, pad=0.02)
    cbar.set_label("Hop Count (16 = unreachable)", color=TEXT, fontsize=10)
    cbar.ax.yaxis.set_tick_params(color=TEXT)
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color=TEXT)
    cbar.outline.set_edgecolor(GRID)

    plt.savefig("images/convergence_heatmap.png", dpi=150,
                bbox_inches="tight", facecolor=BG)
    plt.close()
    print("Saved: images/convergence_heatmap.png")


# ---------------------------------------------------------------------------
# 3. Count-to-infinity comparison
# ---------------------------------------------------------------------------

def extract_hop_counts(history, src, dst):
    counts = []
    for table in history:
        cost, _, _ = table[src][dst]
        counts.append(cost)
    return counts


def plot_count_to_infinity():
    history_no_poison  = simulate_failure(poison_reverse=False, verbose=False)
    history_poison     = simulate_failure(poison_reverse=True,  verbose=False)

    # Track B's view of A across rounds (the route most affected by the A-B failure)
    no_poison_hops = extract_hop_counts(history_no_poison, "B", "A")
    poison_hops    = extract_hop_counts(history_poison,    "B", "A")

    rounds_np = list(range(len(no_poison_hops)))
    rounds_p  = list(range(len(poison_hops)))

    fig, ax = plt.subplots(figsize=(9, 5), facecolor=BG)
    ax.set_facecolor(BG)

    ax.plot(rounds_np, no_poison_hops, marker="o", linewidth=2.5,
            color="#E84C4C", label="Without Poison Reverse (count-to-infinity)")
    ax.plot(rounds_p, poison_hops, marker="s", linewidth=2.5,
            color="#4CE87A", label="With Poison Reverse")

    ax.axhline(y=INFINITY, color=TEXT, linestyle="--", linewidth=1, alpha=0.4)
    ax.text(max(len(rounds_np), len(rounds_p)) * 0.02, INFINITY + 0.3,
            "∞ (16 = unreachable)", color=TEXT, fontsize=9, alpha=0.6)

    ax.set_xlabel("Round", color=TEXT, fontsize=12)
    ax.set_ylabel("Hop Count (B → A)", color=TEXT, fontsize=12)
    ax.set_title("Link Failure A–B: Count-to-Infinity vs Poison Reverse",
                 color=TEXT, fontsize=14, pad=12)

    ax.tick_params(colors=TEXT)
    for spine in ax.spines.values():
        spine.set_edgecolor(GRID)
    ax.grid(color=GRID, linestyle="--", linewidth=0.6, alpha=0.7)
    ax.yaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator())

    legend = ax.legend(facecolor="#161b22", edgecolor=GRID, labelcolor=TEXT, fontsize=11)
    plt.tight_layout()
    plt.savefig("images/count_to_infinity.png", dpi=150,
                bbox_inches="tight", facecolor=BG)
    plt.close()
    print("Saved: images/count_to_infinity.png")


# ---------------------------------------------------------------------------
# 4. Topology with failed link highlighted
# ---------------------------------------------------------------------------

def plot_topology_failure():
    fig, ax = plt.subplots(figsize=(6, 6), facecolor=BG)
    ax.set_facecolor(BG)

    G = nx.Graph()
    G.add_nodes_from(ROUTERS)
    active_edges = [("B", "C"), ("C", "D"), ("D", "A")]
    failed_edges = [("A", "B")]
    G.add_edges_from(active_edges + failed_edges)

    pos = {"A": (0, 1), "B": (1, 1), "C": (1, 0), "D": (0, 0)}

    nx.draw_networkx_edges(G, pos, edgelist=active_edges, ax=ax,
                           edge_color=EDGE_COLOR, width=2.5)
    nx.draw_networkx_edges(G, pos, edgelist=failed_edges, ax=ax,
                           edge_color="#E84C4C", width=2.5, style="dashed")
    nx.draw_networkx_nodes(G, pos, ax=ax,
                           node_color=[COLORS[r] for r in ROUTERS],
                           node_size=1800)
    nx.draw_networkx_labels(G, pos, ax=ax,
                            font_color="white", font_size=18, font_weight="bold")

    failed_patch = mpatches.Patch(color="#E84C4C", linestyle="dashed", label="Failed link (A–B)")
    active_patch = mpatches.Patch(color=EDGE_COLOR, label="Active link")
    legend = ax.legend(handles=[active_patch, failed_patch],
                       facecolor="#161b22", edgecolor=GRID, labelcolor=TEXT,
                       fontsize=11, loc="lower right")

    ax.set_title("Link Failure Scenario — A–B Link Down", color=TEXT, fontsize=14, pad=15)
    ax.axis("off")
    plt.tight_layout()
    plt.savefig("images/topology_failure.png", dpi=150,
                bbox_inches="tight", facecolor=BG)
    plt.close()
    print("Saved: images/topology_failure.png")


# ---------------------------------------------------------------------------
# Run all
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import matplotlib.ticker
    plot_topology()
    plot_convergence_heatmaps()
    plot_count_to_infinity()
    plot_topology_failure()
    print("\nAll images saved to images/")
