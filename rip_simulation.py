"""
RIP Protocol Simulation
========================
Simulates the Routing Information Protocol (RIP) using the Bellman-Ford algorithm
on a square topology (A-B-C-D), including:
  - Normal convergence
  - Link failure without poison reverse (count-to-infinity)
  - Link failure with poison reverse

Based on assignment by Miguel Veloso.
"""

INFINITY = 16  # RIP's maximum hop count (unreachable)


# ---------------------------------------------------------------------------
# Core data structures
# ---------------------------------------------------------------------------

def make_table(routers):
    """Create a routing table: table[router][destination] = (hop_count, next_hop, learned_from)."""
    table = {}
    for r in routers:
        table[r] = {}
        for d in routers:
            if r == d:
                table[r][d] = (0, "-", "Self")
            else:
                table[r][d] = (INFINITY, "-", "Unknown")
    return table


def set_direct_links(table, links):
    """Populate direct (1-hop) neighbours."""
    for a, b in links:
        table[a][b] = (1, b, "Direct")
        table[b][a] = (1, a, "Direct")


def copy_table(table):
    return {r: dict(entries) for r, entries in table.items()}


# ---------------------------------------------------------------------------
# Bellman-Ford update
# ---------------------------------------------------------------------------

def bellman_ford_round(table, routers, links, poison_reverse=False, verbose=True):
    """
    Run one round of RIP updates across all routers simultaneously.
    Returns (new_table, changed) where changed is True if any entry was updated.
    """
    new_table = copy_table(table)
    changed = False
    changes = []

    # Build adjacency map
    neighbours = {r: [] for r in routers}
    for a, b in links:
        neighbours[a].append(b)
        neighbours[b].append(a)

    for router in routers:
        for neighbour in neighbours[router]:
            # What does this neighbour advertise?
            for dest in routers:
                advertised_cost, _, _ = table[neighbour][dest]

                # Poison reverse: neighbour won't advertise routes it learned via us
                if poison_reverse:
                    _, dest_next_hop, _ = table[neighbour][dest]
                    if dest_next_hop == router:
                        advertised_cost = INFINITY  # poisoned

                if advertised_cost >= INFINITY:
                    continue  # unreachable, skip

                new_cost = advertised_cost + 1
                current_cost, _, _ = new_table[router][dest]

                if new_cost < current_cost:
                    old = new_table[router][dest]
                    new_table[router][dest] = (new_cost, neighbour, neighbour)
                    changes.append((router, dest, old[0], new_cost, neighbour))
                    changed = True

    if verbose and changes:
        for router, dest, old_cost, new_cost, via in changes:
            print(f"  [UPDATE] Router {router} -> {dest}: {old_cost} hops → {new_cost} hops via {via}")
    elif verbose:
        print("  No changes.")

    return new_table, changed


# ---------------------------------------------------------------------------
# Simulation scenarios
# ---------------------------------------------------------------------------

def simulate_normal(verbose=True):
    """Simulate normal convergence on a square topology A-B-C-D."""
    routers = ["A", "B", "C", "D"]
    # Square: A-B, B-C, C-D, D-A
    links = [("A", "B"), ("B", "C"), ("C", "D"), ("D", "A")]

    table = make_table(routers)
    set_direct_links(table, links)

    history = [copy_table(table)]

    if verbose:
        print("=" * 60)
        print("SCENARIO 1: Normal Convergence")
        print("Topology: A — B — C — D — A  (square)")
        print("=" * 60)
        print_table(table, "Round 0 (initial)")

    for round_num in range(1, 10):
        if verbose:
            print(f"\nRound {round_num}:")
        table, changed = bellman_ford_round(table, routers, links, verbose=verbose)
        history.append(copy_table(table))
        if verbose:
            print_table(table, f"Round {round_num}")
        if not changed:
            if verbose:
                print(f"\n✔ Network converged after {round_num - 1} round(s) of updates.")
            break

    return history, routers, links


def simulate_failure(poison_reverse=False, verbose=True):
    """Simulate convergence after A-B link failure, with or without poison reverse."""
    routers = ["A", "B", "C", "D"]
    # After failure: A-B removed, remaining: B-C, C-D, D-A
    links_after_failure = [("B", "C"), ("C", "D"), ("D", "A")]

    table = make_table(routers)
    set_direct_links(table, links_after_failure)

    history = [copy_table(table)]
    label = "With Poison Reverse" if poison_reverse else "Without Poison Reverse"

    if verbose:
        print("=" * 60)
        print(f"SCENARIO 2: Link Failure A–B ({label})")
        print("Remaining links: B-C, C-D, D-A")
        print("=" * 60)
        print_table(table, "Round 0 (post-failure)")

    for round_num in range(1, 20):
        if verbose:
            print(f"\nRound {round_num}:")
        table, changed = bellman_ford_round(
            table, routers, links_after_failure,
            poison_reverse=poison_reverse, verbose=verbose
        )
        history.append(copy_table(table))
        if verbose:
            print_table(table, f"Round {round_num}")
        if not changed:
            if verbose:
                print(f"\n✔ Network converged after {round_num - 1} round(s).")
            break

    return history


# ---------------------------------------------------------------------------
# Pretty printer
# ---------------------------------------------------------------------------

def print_table(table, title="Routing Table"):
    routers = sorted(table.keys())
    print(f"\n  {title}")
    print(f"  {'Router':<8} {'Dest':<8} {'Next Hop':<12} {'Hops':<6} {'Learned From'}")
    print(f"  {'-'*50}")
    for r in routers:
        for d in routers:
            cost, nh, src = table[r][d]
            hops = str(cost) if cost < INFINITY else "∞"
            print(f"  {r:<8} {d:<8} {nh:<12} {hops:<6} {src}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    simulate_normal(verbose=True)
    print("\n")
    simulate_failure(poison_reverse=False, verbose=True)
    print("\n")
    simulate_failure(poison_reverse=True, verbose=True)
