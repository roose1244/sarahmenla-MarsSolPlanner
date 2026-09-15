"""A*-in-spacetime.

State = (row, col, sol). We advance a 'metres-driven-this-sol' budget from the
τ-driven power model; when the budget for a sol is used up, we advance to the
next sol (which may have higher or lower τ). This is what makes the planner
choose to WAIT through storms.
"""
from __future__ import annotations
import heapq
import numpy as np
from dataclasses import dataclass

NEIGH = [(-1, 0, 1), (1, 0, 1), (0, -1, 1), (0, 1, 1),
         (-1, -1, np.sqrt(2)), (-1, 1, np.sqrt(2)),
         (1, -1, np.sqrt(2)), (1, 1, np.sqrt(2))]


@dataclass
class Route:
    path: list[tuple[int, int]]
    sols: list[int]
    total_m: float
    eta_sols: float
    idle_sols: int


def _heuristic(a, b, min_cost_per_cell):
    return min_cost_per_cell * np.hypot(a[0] - b[0], a[1] - b[1])


def plan(cost: np.ndarray,
         start: tuple[int, int],
         goal: tuple[int, int],
         drive_m_per_sol: np.ndarray) -> Route | None:
    """cost: [H,W] float32 (np.inf where impassable), coords in (row, col)."""
    H, W = cost.shape
    finite = cost[np.isfinite(cost)]
    min_c = float(finite.min()) if finite.size else 1.0

    open_heap: list[tuple[float, int, int, int, float]] = []
    # (f, row, col, sol, metres_used_this_sol)
    heapq.heappush(open_heap, (0.0, start[0], start[1], 0, 0.0))

    came: dict[tuple[int, int, int], tuple[int, int, int]] = {}
    g: dict[tuple[int, int, int], float] = {(start[0], start[1], 0): 0.0}

    n_sols = len(drive_m_per_sol)

    while open_heap:
        f, r, c, sol, used = heapq.heappop(open_heap)
        if (r, c) == goal:
            path, sols = [], []
            cur = (r, c, sol)
            while cur in came:
                path.append((cur[0], cur[1]))
                sols.append(cur[2])
                cur = came[cur]
            path.append(start); sols.append(0)
            path.reverse(); sols.reverse()
            total_m = g[(r, c, sol)]
            idle = sum(sols[i] - sols[i-1] - 1
                       for i in range(1, len(sols))
                       if sols[i] - sols[i-1] > 1)
            return Route(path, sols, total_m,
                         eta_sols=sol + used / max(drive_m_per_sol[sol], 1e-6),
                         idle_sols=idle)

        for dr, dc, step in NEIGH:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < H and 0 <= nc < W):
                continue
            step_cost = cost[nr, nc] * step
            if not np.isfinite(step_cost):
                continue
            n_sol, n_used = sol, used + step_cost
            # Advance to next sol if we blow the day's budget
            while n_sol < n_sols - 1 and n_used > drive_m_per_sol[n_sol]:
                n_used -= drive_m_per_sol[n_sol]
                n_sol += 1
            if n_used > drive_m_per_sol[min(n_sol, n_sols - 1)]:
                continue  # cannot reach within horizon
            tentative = g[(r, c, sol)] + step_cost
            key = (nr, nc, n_sol)
            if tentative < g.get(key, float("inf")):
                came[key] = (r, c, sol)
                g[key] = tentative
                h = _heuristic((nr, nc), goal, min_c)
                heapq.heappush(open_heap, (tentative + h, nr, nc, n_sol, n_used))
    return None


def rank_deposits(cost, start, deposits, drive_m_per_sol):
    """Plan to every deposit; return list sorted by ETA."""
    out = []
    for _, d in deposits.iterrows():
        r = plan(cost, start, (int(d.row), int(d.col)), drive_m_per_sol)
        if r is not None:
            out.append({"name": d["name"], "goal": (int(d.row), int(d.col)),
                        "route": r, "yield_kg_m2": float(d.yield_kg_m2)})
    out.sort(key=lambda x: x["route"].eta_sols)
    return out
