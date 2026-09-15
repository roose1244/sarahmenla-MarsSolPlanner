# Sol-Window Planner — High-Tech Mars Terrain Viewer

## Original problem statement
Existing GitHub project MarsSolPlanner (Mars route finder using MOLA elevation, AI4Mars terrain classes, MARCI dust opacity, water-deposit catalog + A*-in-spacetime planner). User asked: **"improve on the 3D model of the mars terrain, make it high tech looking"** then followed up with **"make it similar to if someone was playing a game based on mars terrain"** because the first iteration was washed out.

## Architecture
- **Backend (FastAPI, port 8001):** `/app/backend/server.py`
  - `GET /api/health` — liveness
  - `GET /api/plan` — returns `demo/plan.json`
  - `POST /api/regenerate` — reruns the `sol_window.demo` pipeline (~15 s)
  - `GET /api/mars/{name}` — serves any file under `/app/demo/` (plan_three.html, plan.json, plan.png)
- **Frontend (React CRA, port 3000):** `/app/frontend/src/App.js`
  - Header with mission brand + ONLINE pill + RE-PLAN + OPEN TAB buttons
  - Full-viewport iframe embedding the 3D scene
- **Core pipeline (`/app/src/sol_window/`):** unchanged planner + rewritten viz_three.py

## What was implemented (Jan 2026)
- **Rebuilt viz_three.py** with:
  - MeshStandardMaterial terrain with rich per-vertex Mars albedo (basalt → rust → dust height blend, slope-exposed rock, aeolian wind streaks, fake ambient occlusion, terrain-class overrides for sand / bedrock / rock)
  - Mars sky-gradient dome shader (dark red top → warm horizon)
  - Topographic contour line overlay (marching-squares lite)
  - Distant hill-ring backdrop for horizon depth
  - Curiosity-style rover: chassis, orange accent stripe, RTG with heat fins, solar deck, six wheels with hubs, mast + camera head + emissive lens, ChemCam laser beam, folded robotic arm, glowing beacon + PointLight
  - Holographic water deposits: emissive cone + rotating data ring with 12 markers + pulsing torus + vertical shader-gradient beam
  - Animated flowing route tube (shader with sliding pulse) + dashed baseline + growing driven trail
  - Sci-fi HUD (JetBrains Mono + Space Grotesk): telemetry panel, solar/battery/dust gauges, terminal telemetry feed, SVG targeting brackets on rover & target, SECTOR SCAN radar minimap with sweep + rover blip + deposit blips, LAYERS legend, PLAY/RESET/FLY controls, live sidebar reading plan.json
  - Post-processing: bloom (subtle threshold 1.05), chromatic aberration, film grain — tuned so terrain stays visible
- Added FastAPI backend and minimal React frontend to serve/preview the scene through the preview URL
- Elevation smoothing (2× 3-px box blur) in `render_three` to remove per-pixel voxel spikes

## Testing status
- iteration_1.json: **backend 100% / frontend 100%**, all endpoints work, scene renders correctly, no `__PAYLOAD__` placeholder leak. One non-blocking console warning (NaN in a geometry).

## Backlog / future
- Track down NaN bounding-sphere warning (likely in tube geometry or contour overlay when a route point falls outside terrain bounds)
- Wire the RE-PLAN button to accept custom start `row,col` and horizon sols
- Real MOLA DEM tile loader (currently synthetic)
- Add live camera thumbnails from the rover mast (procedural render-to-texture)
