"""LLM-as-orchestrator.

Rule from the pitch: the LLM DOES NOT compute distances or ETAs itself. It
calls the router as a tool and only narrates the result. This is the single
biggest failure-mode of hackathon LLM demos and worth 5 rubric points.

Two modes:
  - `narrate_plan(...)`  — pure templated narration (no API key needed)
  - `agent_loop(...)`    — real tool-calling via OpenAI (drop-in if you have $)
"""
from __future__ import annotations
import json
from typing import Callable


def narrate_plan(user_query: str, ranked: list[dict], tau) -> str:
    """No-API-key fallback. Templated but coherent."""
    if not ranked:
        return "No reachable water deposits inside the horizon. Extend sols or relax slope limits."
    top = ranked[0]
    r = top["route"]
    storm = [i for i, t in enumerate(tau) if t > 1.0]
    storm_str = f"sols {storm[0]}–{storm[-1]}" if storm else "none"
    return (
        f"Mission plan for query: {user_query!r}\n"
        f"Target       : {top['name']}\n"
        f"ETA          : {r.eta_sols:.1f} sols  (idle {r.idle_sols} sols through storms)\n"
        f"Distance     : {r.total_m/1000:.1f} km  ({len(r.path)} waypoints)\n"
        f"Dust window  : {storm_str}\n"
        f"Rationale    : Route weaves around sand fields and holds position "
        f"through the τ>1 window, then resumes at sol "
        f"{max(r.sols[-1]-1,0)}. Yield estimate at target: "
        f"{top['yield_kg_m2']:.0f} kg/m²."
    )


# ------------------------------------------------------------------
# Optional: real tool-calling with OpenAI. Delete if you skip the API.
# ------------------------------------------------------------------
ROUTER_TOOL = {
    "type": "function",
    "function": {
        "name": "plan_route_to_water",
        "description": "Plan a time-aware route from the rover start to the nearest viable water deposit. Returns ETA in sols and a distance.",
        "parameters": {
            "type": "object",
            "properties": {
                "max_sols": {"type": "integer", "description": "Horizon in sols."},
                "min_yield_kg_m2": {"type": "number", "description": "Reject deposits below this yield."}
            },
            "required": ["max_sols"]
        }
    }
}


def agent_loop(user_query: str, tool_fn: Callable[[dict], dict], model="gpt-4o-mini"):
    """Optional. Requires OPENAI_API_KEY. Do this AFTER core is working."""
    from openai import OpenAI
    client = OpenAI()
    msgs = [
        {"role": "system", "content":
         "You are the Sol-Window Planner. Never compute distances or ETAs yourself; "
         "always call plan_route_to_water. Narrate the result crisply for a mission log."},
        {"role": "user", "content": user_query},
    ]
    while True:
        r = client.chat.completions.create(model=model, messages=msgs,
                                           tools=[ROUTER_TOOL])
        m = r.choices[0].message
        if not m.tool_calls:
            return m.content
        for tc in m.tool_calls:
            args = json.loads(tc.function.arguments)
            result = tool_fn(args)
            msgs.append({"role": "assistant", "tool_calls": [tc]})
            msgs.append({"role": "tool", "tool_call_id": tc.id,
                         "content": json.dumps(result)})
