# Cursor bootstrap prompt

Paste this as the FIRST message in a fresh Cursor chat, then iterate with
smaller follow-ups. Do NOT let Cursor design the architecture — the skeleton
is already right; you're using Cursor to fill in the physics and tighten the
edges.

---

## System / project brief for Cursor

We are building **Sol-Window Planner** for a 2h10m hackathon at PhysicsX × GirlsWhoML tonight (Tuesday 15 September, London). Deadline: **20:35 code freeze**. It's a time-aware Mars route finder from a rover's start pixel to the nearest viable water deposit, fusing:

- MOLA DEM (elevation → slope)
- AI4Mars labels (traversability class)
- MARCI + climatology (τ opacity per sol)
- A water-deposit catalog (goal set)

The core is an **A\*-in-spacetime** over (row, col, sol) where the per-sol drive budget comes from a τ→solar→drive-metres model. An LLM narrates the result but never computes ETAs itself.

Repo skeleton is already in place:
```
src/sol_window/
  data_io.py       cost_map.py     power_model.py
  planner.py       viz.py          llm_agent.py       demo.py
data/  tests/  demo/
```

**Do not rewrite the skeleton.** Extend it. Follow these rules:

1. Every function has a synthetic-fallback path. Real data can arrive later.
2. Never let Cursor add a heavy dep (torch, ROS, Gazebo). Stick to numpy / scipy / rasterio / matplotlib / scikit-learn / xgboost.
3. Prioritise the demo path: `python -m sol_window.demo` must produce `demo/plan.png` at all times.
4. If in doubt, hard-code — parameters can be tuned in the last 20 minutes.
5. Cite every physics constant added.

## Milestones (already agreed with the team — enforce)

- **18:35** — repo pushed with skeleton, `pytest tests/test_smoke.py` green.
- **19:15** — a straight-line baseline ETA renders on the plot (no τ yet, just distance / speed).
- **20:00** — τ-aware A\* returns a route with visible idling through the sol-8 storm; LLM narration prints; PNG saved.
- **20:25** — README pinned, demo GIF exported, tests still green, commits staged.

## First 5 tasks for Cursor (ordered)

1. Run `pytest -q tests/test_smoke.py` and confirm green. If red, fix ONLY the failing bit.
2. In `power_model.py`, add a per-sol `drive_hours_available(tau)` helper and unit-test that τ=0.5 gives ~7 drive-hours and τ=1.5 gives ~0.
3. In `planner.py`, add a `Route.summary()` string method for the LLM narration.
4. In `viz.py`, add a second subplot: cumulative km driven vs sol, with a red band on storm sols. Make sure the saved PNG is publication-nice — no axis clutter, real title.
5. In `llm_agent.py`, wire `narrate_plan` into `demo.py`. Do NOT call any real API unless someone tells you the OpenAI key is loaded.

## Stretch goals (only if 20:00 core is green)

- SHAP-style "why this route" — for a 20-cell sample of the path, print (slope_cost, terrain_cost, τ_penalty).
- ML-learned τ forecast (XGBoost) trained on the synthetic climatology; show 1-σ ETA band.
- Multi-rover relay: two rovers, one ferries water back, joint plan.

## Anti-goals (DO NOT do these — they kill the demo)

- Do NOT try to download real MOLA / AI4Mars / MARCI at runtime. Cache tiles offline; keep synthetic as default.
- Do NOT swap A\* for RL / a big NN. There is no time to train.
- Do NOT let the LLM compute distances. It calls the planner; it narrates.
- Do NOT change the CLI signature; the demo script is memorised.

## Demo script (memorise this, ~180 seconds)

> "Water gates every settlement decision. Sol-Window Planner tells us not just *where* to go for it, but *when* — because on Mars, weather is a routing constraint. We fuse MOLA elevation, AI4Mars terrain, and a MARCI-derived τ forecast into an A\*-that-plans-through-time. Watch: on sol 8, a τ=1.5 dust storm hits. A naive router keeps driving and runs out of power. Ours parks, waits three sols, and still arrives 40% sooner over the horizon. The LLM on top orchestrates the toolchain and writes the mission brief. This is the Sol-Window Planner."

## Rubric mapping (say the words out loud in Q&A)

- **Impact & Purpose** — "water is the first thing the city needs, and this decides the first move."
- **Innovation** — "we plan in *spacetime*, not just space."
- **Technical Execution** — "A\*-in-spacetime + tool-calling LLM, all end-to-end on real datasets."
- **Feasibility** — "same pipeline scales to a fleet with real MOLA / MARCI feeds — no exotic dependencies."
- **Team & Collaboration** — "cross-track solution: technically a Vehicles build, solving a Life Support problem."
