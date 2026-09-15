"""Serialise the planner's ACTUAL output to demo/plan.json.

Both the mission-timeline card and the Three.js HUD read this file. Anything
that appears on screen — ETA, distance, idled sols, per-sol τ, deposits,
timeline events — comes from here. No hand-typed numbers, ever.
"""
from __future__ import annotations
import json
import numpy as np
from pathlib import Path

TAU_HOLD = 1.0  # matches power_model.py — safety-hold threshold


def _timeline(route, tau):
    """Build one event per sol along the route with a drive|hold|arrive tag."""
    sols = np.array(route.sols)
    events = []
    seen = set()
    for i, s in enumerate(sols):
        if s in seen:
            continue
        seen.add(s)
        # first waypoint at that sol → drive step
        events.append({
            "sol": int(s),
            "tau": float(tau[min(s, len(tau) - 1)]),
            "status": "drive",
            "row": int(route.path[i][0]),
            "col": int(route.path[i][1]),
        })
    # Insert HOLD events for any storm sol that the rover skipped over
    # (i.e. path jumped sol S+1 → sol S+K because storm parked it).
    all_sols_covered = sorted(seen)
    filled = []
    for i, s in enumerate(all_sols_covered):
        filled.append(next(e for e in events if e["sol"] == s))
        if i + 1 < len(all_sols_covered):
            gap = all_sols_covered[i + 1] - s
            for k in range(1, gap):
                idle_sol = s + k
                filled.append({
                    "sol": int(idle_sol),
                    "tau": float(tau[min(idle_sol, len(tau) - 1)]),
                    "status": "hold",
                    "row": int(route.path[[j for j, x in enumerate(sols) if x == s][-1]][0]),
                    "col": int(route.path[[j for j, x in enumerate(sols) if x == s][-1]][1]),
                })
    # Mark last event as arrive
    if filled:
        filled[-1]["status"] = "arrive"
    return filled


def build_payload(*, elev, tclass, tau, ranked, start, query):
    top = ranked[0]
    route = top["route"]
    payload = {
        "query": query,
        "start": {"row": int(start[0]), "col": int(start[1])},
        "horizon_sols": int(len(tau)),
        "tau_per_sol": [float(x) for x in tau],
        "tau_hold_threshold": TAU_HOLD,
        "winner": {
            "name": top["name"],
            "eta_sols": float(route.eta_sols),
            "distance_km": float(route.total_m) / 1000.0,
            "waypoints": int(len(route.path)),
            "idle_sols": int(route.idle_sols),
            "peak_tau": float(max(tau)),
            "yield_kg_m2": float(top["yield_kg_m2"]),
            "goal": {"row": int(top["goal"][0]), "col": int(top["goal"][1])},
        },
        "ranked_deposits": [
            {
                "name": r["name"],
                "eta_sols": float(r["route"].eta_sols),
                "distance_km": float(r["route"].total_m) / 1000.0,
                "yield_kg_m2": float(r["yield_kg_m2"]),
                "row": int(r["goal"][0]),
                "col": int(r["goal"][1]),
            } for r in ranked
        ],
        "timeline": _timeline(route, tau),
        "shape": {"h": int(elev.shape[0]), "w": int(elev.shape[1])},
    }
    return payload


def write_json(payload, path="demo/plan.json"):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, indent=2))
    return path
