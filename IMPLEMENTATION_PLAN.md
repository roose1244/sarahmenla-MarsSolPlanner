# Sol-Window Planner — Full Product + Implementation Plan

## 1. Product definition

**Sol-Window Planner** is a mission-control style interactive Mars planning app.

It answers one question:

> From a given starting point on Mars, what is the fastest safe route to a reachable water deposit, and how many sols will it take under terrain, daylight, and dust constraints?

### Core user journey
1. User enters a natural-language request.
2. App converts the request into structured planner inputs.
3. Route planner ranks candidate deposits.
4. App renders the winning route in 3D.
5. User watches the rover traverse the route in sync with a per-sol timeline.
6. Sidebar explains why the route was chosen.

## 2. Product scope for the hackathon

### What ships in v1
- Interactive regional 3D Mars scene in the browser.
- Animated rover following the route.
- Live sidebar that reads real planner output from `demo/plan.json`.
- Per-sol timeline with dust holds.
- Ranked water-deposit candidates.
- Static/preprocessed local data for the demo.
- LLM only for query parsing and explanation.

### What is intentionally deferred
- Full global Mars globe in CesiumJS.
- True planetary day/night terminator.
- Live NASA/MARCI fetches during runtime.
- WebXR/VR.
- Compare/swipe tool.
- Measurement tool.
- Orbiter relay constraint modeling.

## 3. Recommended architecture

### Frontend
- **Three.js** for the main 3D app.
- One unified page: `demo/plan_three.html`.
- Layout:
  - left/main = 3D scene
  - right = `Sol-Window Planner · Live` sidebar
  - top-left = compact HUD
  - bottom = playback and layer controls

### Planner/data backend
- **Python** for deterministic routing and preprocessing.
- Outputs written to `demo/plan.json`.
- Browser reads only generated files, not notebooks or raw scripts.

### LLM boundary
- Allowed:
  - natural-language request → structured planner parameters
  - route rationale summary
- Not allowed:
  - ETA calculation
  - graph search
  - route geometry
  - dust/daylight math

## 4. Current repo structure

```text
sol-window-planner/
├── README.md
├── CURSOR_BOOTSTRAP.md
├── IMPLEMENTATION_PLAN.md
├── requirements.txt
├── pyproject.toml
├── serve.py
├── demo/
│   ├── plan.png
│   ├── plan_3d.html
│   ├── plan_three.html
│   ├── plan.json
│   └── dashboard.html
├── src/sol_window/
│   ├── __init__.py
│   ├── data_io.py
│   ├── cost_map.py
│   ├── power_model.py
│   ├── planner.py
│   ├── results.py
│   ├── llm_agent.py
│   ├── viz.py
│   ├── viz3d.py
│   ├── viz_three.py
│   ├── viz_dashboard.py
│   └── demo.py
└── tests/
    └── test_smoke.py
```

## 5. File-by-file responsibility

### `src/sol_window/data_io.py`
Owns all source layers.

Responsibilities:
- load DEM / synthetic fallback
- load terrain classes / synthetic fallback
- load dust tau timeline
- load water deposits

Near-term improvements:
- add explicit `load_mola_tile(path)`
- add `load_ai4mars_tile(path)`
- add `load_deposit_catalog(path)`
- separate synthetic and real loaders

### `src/sol_window/cost_map.py`
Builds terrain traversal cost.

Responsibilities:
- slope calculation
- per-class terrain multiplier
- impassable cell masking

Near-term improvements:
- separate slope, roughness, and hazard channels
- add named cost weights so judges can see explainability

### `src/sol_window/power_model.py`
Converts tau to daily drive budget.

Responsibilities:
- solar attenuation
- drive metres per sol
- storm safety hold rule when tau exceeds threshold

Near-term improvements:
- daylight window model by LMST
- explicit communications margin
- separate dust-visibility hold vs. solar-budget degradation

### `src/sol_window/planner.py`
Core pathfinding engine.

Responsibilities:
- A* in spacetime `(row, col, sol)`
- ranked candidate deposits
- route reconstruction

Near-term improvements:
- expose per-sol consumed budget
- return a list of planner reasons for detours
- support optional target constraints

### `src/sol_window/results.py`
Single source of truth serializer.

Responsibilities:
- convert planner output into UI-ready `plan.json`
- timeline rows
- winner deposit summary
- ranked deposit list

This file is the integrity layer. If a number is on screen, it should come from here.

### `src/sol_window/llm_agent.py`
LLM wrapper only.

Responsibilities:
- templated narration fallback
- optional tool-calling loop

Near-term improvements:
- structured parser for requests like:
  - `start at Jezero`
  - `prefer shallow ice`
  - `avoid storms`
  - `within 20 sols`

### `src/sol_window/viz.py`
Static 2D figure for README/demo backup.

Responsibilities:
- route map
- dust/timeline summary
- pitch backup image

### `src/sol_window/viz3d.py`
Plotly 3D fallback.

Use case:
- lightweight interactive backup if WebGL scene breaks.

### `src/sol_window/viz_dashboard.py`
Standalone live dashboard.

Use case:
- secondary tab / backup view.

### `src/sol_window/viz_three.py`
Hero app view.

Responsibilities:
- full-screen 3D terrain scene
- animated rover
- deposit markers
- dust/storm visuals
- integrated live sidebar

### `src/sol_window/demo.py`
The single command used on stage.

Responsibilities:
- load inputs
- plan route
- write `plan.json`
- print explanation
- render all outputs

### `serve.py`
Tiny local web server.

Use it because browser `fetch()` of `plan.json` does not work reliably from `file://`.

## 6. Final target UX

### A. Planning View
- elevated regional 3D terrain camera
- visible deposits with pulsing beams
- planned route and driven route layers
- orbital-style overview feel

### B. Drive View
- chase camera
- first-person camera
- animated rover
- dust-heavy reduced-visibility mood during storm sols

### C. Live sidebar
- mission stats
- winner summary
- current route status
- per-sol timeline
- ranked deposits
- route rationale

### D. Bottom control bar
- play / pause
- scrubber
- speed
- layer toggles
- planning vs drive mode

## 7. Data model for `demo/plan.json`

```json
{
  "query": "Find shallow water within 20 sols, avoid storms.",
  "start": {"row": 10, "col": 10},
  "horizon_sols": 20,
  "tau_per_sol": [0.51, 0.48, 1.20],
  "tau_hold_threshold": 1.0,
  "winner": {
    "name": "Deposit-C RSL-associated",
    "eta_sols": 8.0,
    "distance_km": 5.8,
    "waypoints": 144,
    "idle_sols": 4,
    "peak_tau": 2.02,
    "yield_kg_m2": 200,
    "goal": {"row": 150, "col": 60}
  },
  "ranked_deposits": [],
  "timeline": []
}
```

## 8. Full implementation sequence

### Phase 1 — Stabilize current product
1. Ensure `python -m sol_window.demo` regenerates:
   - `demo/plan.png`
   - `demo/plan_3d.html`
   - `demo/plan_three.html`
   - `demo/plan.json`
   - `demo/dashboard.html`
2. Ensure `python serve.py` serves both HTML experiences.
3. Ensure sidebar and scene are both reading the same `plan.json` values.

### Phase 2 — Unify the app
1. Make `plan_three.html` the main experience.
2. Merge the live dashboard into the right side of `plan_three.html`.
3. Keep `dashboard.html` only as a fallback/debug page.
4. Add a mode toggle:
   - `Planning`
   - `Drive`

### Phase 3 — Improve route truthfulness
1. Add current route segment / distance remaining to `results.py`.
2. Add planner reasons for hold/detour.
3. Add explicit storm-day rows into the timeline.
4. Add deposit confidence and depth to ranking cards.

### Phase 4 — Improve 3D quality
1. Detailed rover mesh from primitives.
2. Wheel rotation.
3. Mast/head camera.
4. Deposit beams and pulsing rings.
5. Route waypoint glow dots.
6. Dust particle field.
7. Terrain hazard tinting.
8. Mountain silhouettes.
9. Haze/fog + stars.

### Phase 5 — Add a better control system
1. Planning / Drive toggle.
2. Chase / First-person camera toggle.
3. Layer toggles.
4. Speed selector.
5. `Now` / reset button.

### Phase 6 — Prompt-driven product layer
1. Add request box.
2. Parse user text into structured planner args.
3. Re-run route build.
4. Render returned summary in sidebar.

## 9. Exact commands for the team

### Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
pip install pytest plotly
```

### Verify
```bash
python -m pytest -q
python -m sol_window.demo
python serve.py
```

### Open in browser
```text
http://localhost:8000/demo/plan_three.html
http://localhost:8000/demo/dashboard.html
```

### Regenerate after a tweak
```bash
python -m sol_window.demo --start 5,5
```

### Git workflow
```bash
git pull
git add -A
git commit -m "describe your change"
git push
```

## 10. Proposed implementation tasks by teammate

### Person A — planner + results
- `planner.py`
- `results.py`
- `power_model.py`

### Person B — 3D app
- `viz_three.py`
- `viz3d.py`
- `viz.py`

### Person C — product shell + prompt flow
- `demo.py`
- `llm_agent.py`
- README/demo narration

## 11. Exact next code changes

### Change 1 — add camera modes to `viz_three.py`
Add:
- `planning`
- `chase`
- `first_person`

### Change 2 — add richer timeline fields to `results.py`
Each timeline row should expose:
- status
- tau
- distance advanced this sol
- remaining distance
- daylight budget used
- note

### Change 3 — add route rationale to `plan.json`
Add:
- top-level `summary`
- top-level `constraints`
- per-deposit `reason`

### Change 4 — add sidebar sections in `viz_three.py`
Sidebar sections:
- mission stats
- current event
- route rationale
- timeline
- ranked deposits

### Change 5 — add input controls in `demo.py`
Support:
- `--target deposit-c`
- `--prefer-shallow`
- `--avoid-storms`
- `--tau-threshold 1.0`

## 12. Slide deck outline

### Slide 1 — title
Sol-Window Planner

### Slide 2 — problem
Mars routing is not just geometry; it is geometry + terrain + dust + daylight.

### Slide 3 — solution
Mission-control style planner that predicts route-to-water in sols.

### Slide 4 — architecture
Python planner + `plan.json` + Three.js app + LLM summary layer.

### Slide 5 — data layers
MOLA, AI4Mars, MARCI-style tau, deposit catalog.

### Slide 6 — planner logic
A* in spacetime with storm/daylight constraints.

### Slide 7 — product demo
Planning view + drive view + live sidebar.

### Slide 8 — why it wins
Clear impact, visual wow, honest numbers, strong demo story.

## 13. README/demo copy to use in the pitch

> Sol-Window Planner computes the fastest safe route to a water deposit on Mars by combining terrain cost, dust risk, and per-sol operational windows. Instead of asking only where a rover should go, it asks when it can safely move.

## 14. Demo script

1. Open `plan_three.html`.
2. Show the route and deposit ranking.
3. Hit play.
4. Point out storm hold rows in the live sidebar.
5. Switch to chase or first-person camera.
6. End on arrival and water-yield number.

Suggested spoken line:

> Water is the first thing a Martian settlement needs. Sol-Window Planner predicts not just where to go, but when a rover can safely reach it under terrain, daylight, and dust constraints.

## 15. Final deliverables checklist

- [ ] `demo/plan.png`
- [ ] `demo/plan_3d.html`
- [ ] `demo/plan_three.html`
- [ ] `demo/plan.json`
- [ ] `demo/dashboard.html`
- [ ] repo pushed to GitHub
- [ ] one README section explaining how to run the demo
- [ ] slide deck ready
