"""High-tech Three.js Mars mission-control scene.

Renders one self-contained HTML file that:
  - Custom terrain ShaderMaterial: slope-glow, elevation contours, radial scan sweep,
    holographic grid overlay, fresnel rim, atmospheric attenuation
  - EffectComposer post-processing: UnrealBloom + film grain/scanlines + vignette + CA
  - Sci-fi HUD: radar/minimap, targeting brackets on rover (SVG overlay), altitude
    & power gauges, terminal command feed, scanline overlay
  - Curiosity-style rover with articulated arm, RTG, mast laser
  - Holographic water deposits with rotating data rings + sky beams
  - Route rendered as animated flowing energy pulses (custom shader)
  - Live sidebar reads plan.json (auto-refreshes)
"""
from __future__ import annotations
import json
import numpy as np
from pathlib import Path


def render_three(elev, tclass, tau, route, deposits, start,
                 save="demo/plan_three.html",
                 title="Sol-Window Planner"):
    H, W = elev.shape
    step = max(1, max(H, W) // 240)
    e = elev[::step, ::step].astype(float)
    tc = tclass[::step, ::step].astype(int)
    # Smooth elevation slightly (3x3 box blur, twice) to remove per-pixel jaggies
    from scipy.ndimage import uniform_filter
    e = uniform_filter(e, size=3, mode="nearest")
    e = uniform_filter(e, size=3, mode="nearest")
    h, w = e.shape

    payload = {
        "title": title,
        "w": w, "h": h, "step": step,
        "elev": e.flatten().tolist(),
        "eMin": float(e.min()), "eMax": float(e.max()),
        "terrainClass": tc.flatten().tolist(),
        "route": [[int(r // step), int(c // step)] for r, c in route.path],
        "routeSols": list(map(int, route.sols)),
        "eta": float(route.eta_sols),
        "totalKm": float(route.total_m) / 1000.0,
        "idleSols": int(route.idle_sols),
        "tau": [float(x) for x in tau],
        "deposits": [
            {"row": int(row // step), "col": int(col // step),
             "name": name, "depth": float(depth), "yield": float(y)}
            for row, col, depth, y, name in
            zip(deposits.row, deposits.col, deposits.depth_m,
                deposits.yield_kg_m2, deposits["name"])
        ],
        "start": [int(start[0] // step), int(start[1] // step)],
    }
    html = _HTML.replace("__PAYLOAD__", json.dumps(payload))
    Path(save).parent.mkdir(parents=True, exist_ok=True)
    Path(save).write_text(html)
    return save


_HTML = r"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<title>Sol-Window Planner · Mission Control</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#050308;--bg-2:#0a0710;--panel:rgba(10,7,16,0.78);
  --border:#8a3a1e;--border-hi:#ff7a3a;
  --text:#f4e4c8;--dim:#c9a37c;--fade:#7d6244;
  --accent:#ff8a2c;--accent-2:#ffb060;--route:#ff5040;
  --cyan:#4de5ff;--cyan-dim:#1a5a70;
  --coral-50:#3a1a10;--coral-80:#ff9b83;
  --green-50:#0f2418;--green-80:#5ff0a2;
  --blue-50:#0a1a30;--blue-80:#7ab5ff;
  --mono:'JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,monospace;
  --display:'Space Grotesk',system-ui,sans-serif;
}
*{box-sizing:border-box}
html,body{margin:0;padding:0;height:100%;background:#000;color:var(--text);
  font-family:var(--display);overflow:hidden;-webkit-font-smoothing:antialiased;}

#stage{position:absolute;top:0;left:0;right:360px;bottom:0;}
#scene{position:absolute;inset:0;}

/* global scanline overlay */
#scanlines{position:absolute;inset:0;pointer-events:none;z-index:20;opacity:0.18;
  background:repeating-linear-gradient(0deg,
    rgba(255,255,255,0.025) 0px,rgba(255,255,255,0.025) 1px,
    transparent 1px,transparent 3px);mix-blend-mode:overlay;}
#vignette{position:absolute;inset:0;pointer-events:none;z-index:19;
  background:radial-gradient(ellipse at center,transparent 55%,rgba(0,0,0,0.35) 100%);}

/* SVG overlay layer for targeting brackets etc */
#svg-overlay{position:absolute;inset:0;pointer-events:none;z-index:15;}

/* HUD panels — brutalist mono */
.panel{background:var(--panel);border:1px solid var(--border);
  backdrop-filter:blur(8px);position:relative;}
.panel::before,.panel::after{content:'';position:absolute;width:10px;height:10px;
  border:1px solid var(--border-hi);}
.panel::before{top:-1px;left:-1px;border-right:none;border-bottom:none;}
.panel::after{bottom:-1px;right:-1px;border-left:none;border-top:none;}

#hud-top{position:absolute;top:16px;left:16px;padding:14px 18px;z-index:10;
  min-width:280px;font-family:var(--mono);}
#hud-top h1{margin:0 0 2px;font-size:11px;font-weight:700;color:var(--accent);
  letter-spacing:0.24em;text-transform:uppercase;font-family:var(--mono);}
#hud-top .sub{font-size:9px;color:var(--fade);letter-spacing:0.16em;
  text-transform:uppercase;margin-bottom:12px;}
#hud-top .row{display:flex;justify-content:space-between;gap:16px;padding:3px 0;
  font-size:11px;letter-spacing:0.04em;}
#hud-top .row span:first-child{color:var(--dim);font-size:9px;letter-spacing:0.14em;
  text-transform:uppercase;align-self:center;}
#hud-top .row b{color:var(--text);font-variant-numeric:tabular-nums;font-weight:600;
  font-size:13px;}
#hud-top .status{margin-top:10px;padding:6px 10px;font-weight:700;
  text-align:center;font-size:10px;letter-spacing:0.18em;text-transform:uppercase;
  border:1px solid;font-family:var(--mono);}
.status.drive{border-color:var(--blue-80);color:var(--blue-80);background:rgba(122,181,255,0.06);}
.status.hold{border-color:var(--coral-80);color:var(--coral-80);background:rgba(255,155,131,0.08);
  animation:pulse 1.2s ease-in-out infinite}
.status.arrive{border-color:var(--green-80);color:var(--green-80);background:rgba(95,240,162,0.08);}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.5;letter-spacing:0.24em}}

/* Radar minimap bottom-right of stage */
#radar{position:absolute;bottom:20px;right:20px;width:180px;height:180px;z-index:10;
  padding:10px;font-family:var(--mono);}
#radar-canvas{width:100%;height:100%;}
#radar-label{position:absolute;top:-1px;left:12px;background:var(--bg);padding:0 6px;
  font-size:8px;color:var(--accent);letter-spacing:0.24em;font-weight:700;
  transform:translateY(-50%);}

/* Legend */
#legend{position:absolute;bottom:20px;left:20px;padding:12px 16px;z-index:10;
  font-size:10px;line-height:1.9;font-family:var(--mono);letter-spacing:0.06em;}
#legend .dot{display:inline-block;width:8px;height:8px;
  margin-right:8px;vertical-align:middle;border:1px solid rgba(255,255,255,0.3);}
#legend .lbl{font-size:8px;color:var(--accent);letter-spacing:0.24em;font-weight:700;
  text-transform:uppercase;margin-bottom:6px;display:block;}

/* Controls bar */
#controls{position:absolute;bottom:20px;left:50%;transform:translateX(-50%);z-index:10;
  padding:10px 16px;display:flex;align-items:center;gap:14px;font-family:var(--mono);}
#controls button{background:transparent;color:var(--accent);border:1px solid var(--border-hi);
  padding:6px 14px;font-size:10px;cursor:pointer;font-weight:700;letter-spacing:0.14em;
  text-transform:uppercase;font-family:var(--mono);transition:all 0.15s;}
#controls button:hover{background:var(--accent);color:var(--bg);}
#controls input[type="range"]{width:220px;-webkit-appearance:none;height:2px;
  background:linear-gradient(90deg,var(--accent) 0%,var(--accent) var(--p,0%),
    rgba(255,255,255,0.15) var(--p,0%),rgba(255,255,255,0.15) 100%);
  outline:none;}
#controls input[type="range"]::-webkit-slider-thumb{-webkit-appearance:none;
  width:12px;height:12px;background:var(--accent);cursor:pointer;
  border:1px solid var(--text);}
#controls .sol-label{font-size:10px;color:var(--text);min-width:70px;
  font-variant-numeric:tabular-nums;letter-spacing:0.08em;}

/* Terminal log feed - top right of stage */
#term{position:absolute;top:16px;right:20px;padding:10px 14px;z-index:10;
  width:280px;max-height:180px;overflow:hidden;font-family:var(--mono);
  font-size:9px;line-height:1.6;letter-spacing:0.04em;}
#term .t-lbl{color:var(--accent);font-size:8px;letter-spacing:0.24em;font-weight:700;
  text-transform:uppercase;margin-bottom:6px;display:block;}
#term-lines .line{color:var(--dim);opacity:0;transform:translateX(-4px);
  animation:slidein 0.4s forwards;white-space:nowrap;overflow:hidden;
  text-overflow:ellipsis;padding:1px 0;}
#term-lines .line.new{color:var(--cyan);}
#term-lines .line b{color:var(--text);}
@keyframes slidein{to{opacity:1;transform:translateX(0)}}

/* Gauge stack */
#gauges{position:absolute;top:220px;left:16px;display:flex;flex-direction:column;
  gap:8px;z-index:10;font-family:var(--mono);}
.gauge{width:280px;padding:8px 12px;}
.gauge .g-hd{display:flex;justify-content:space-between;font-size:8px;
  letter-spacing:0.2em;text-transform:uppercase;margin-bottom:4px;}
.gauge .g-hd b{color:var(--text);font-variant-numeric:tabular-nums;letter-spacing:0.04em;}
.gauge .g-hd span{color:var(--fade)}
.gauge .g-bar{height:6px;background:rgba(255,255,255,0.06);position:relative;
  border:1px solid rgba(255,255,255,0.08);}
.gauge .g-fill{position:absolute;top:0;bottom:0;left:0;background:var(--accent);
  transition:width 0.35s ease-out;}
.gauge.hot .g-fill{background:var(--coral-80);}
.gauge.good .g-fill{background:var(--green-80);}
.gauge.cool .g-fill{background:var(--cyan);}
.gauge .g-notch{position:absolute;top:-2px;bottom:-2px;width:1px;background:var(--fade);}

#tooltip{position:absolute;padding:7px 12px;background:var(--bg);
  border:1px solid var(--border-hi);font-size:10px;pointer-events:none;
  display:none;z-index:100;white-space:nowrap;font-family:var(--mono);
  letter-spacing:0.06em;}
#tooltip::before{content:'';position:absolute;top:-1px;left:-1px;width:6px;height:6px;
  border-top:1px solid var(--accent);border-left:1px solid var(--accent);}

/* SIDEBAR */
#sidebar{position:absolute;top:0;right:0;bottom:0;width:360px;
  background:linear-gradient(180deg,var(--bg-2) 0%,var(--bg) 100%);
  border-left:1px solid var(--border);overflow-y:auto;padding:22px 20px;font-size:12px;
  font-family:var(--display);}
#sidebar::-webkit-scrollbar{width:4px;}
#sidebar::-webkit-scrollbar-thumb{background:var(--border);}
#sidebar header{display:flex;justify-content:space-between;align-items:flex-start;
  padding-bottom:16px;border-bottom:1px solid var(--border);}
#sidebar h2{margin:0;font-size:15px;font-weight:600;color:var(--text);letter-spacing:0.01em;
  font-family:var(--display);}
#sidebar .brand{font-size:9px;color:var(--accent);letter-spacing:0.24em;font-weight:700;
  text-transform:uppercase;font-family:var(--mono);margin-bottom:3px;}
#sidebar .sub{font-size:10px;color:var(--dim);margin-top:4px;text-transform:uppercase;
  letter-spacing:0.1em;font-family:var(--mono);}
#pill{padding:4px 8px;font-size:8px;font-weight:700;letter-spacing:0.14em;
  text-transform:uppercase;background:var(--green-50);color:var(--green-80);
  border:1px solid var(--green-80);font-family:var(--mono);}
#pill.stale{background:var(--coral-50);color:var(--coral-80);border-color:var(--coral-80);
  animation:pulse 1.4s infinite;}
.stats{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin:18px 0;}
.stat{padding:12px 10px;background:rgba(255,255,255,0.02);border:1px solid var(--border);
  position:relative;}
.stat::before{content:'';position:absolute;top:0;left:0;width:2px;height:14px;
  background:var(--accent);}
.stat b{display:block;font-size:20px;font-weight:600;color:var(--text);
  font-variant-numeric:tabular-nums;font-family:var(--mono);letter-spacing:-0.01em;}
.stat small{display:block;margin-top:3px;font-size:8px;color:var(--fade);
  text-transform:uppercase;letter-spacing:0.14em;font-family:var(--mono);}
h3{font-size:9px;font-weight:700;margin:22px 0 10px;color:var(--accent);
  text-transform:uppercase;letter-spacing:0.24em;font-family:var(--mono);
  display:flex;align-items:center;gap:8px;}
h3::before{content:'';flex:0 0 3px;height:10px;background:var(--accent);}
h3::after{content:'';flex:1;height:1px;background:var(--border);}
.tl{display:grid;gap:3px;}
.tl-row{display:grid;grid-template-columns:52px 1fr 46px;align-items:center;gap:10px;
  padding:8px 10px;background:rgba(255,255,255,0.02);border:1px solid var(--border);
  font-size:11px;position:relative;}
.tl-row.hl{border-color:var(--coral-80);background:rgba(255,80,64,0.05);}
.tl-row.current{border-color:var(--accent);box-shadow:inset 3px 0 0 var(--accent);}
.tl-row .d b{display:block;font-weight:600;font-size:11px;font-family:var(--mono);}
.tl-row .d small{display:block;font-size:8px;color:var(--fade);margin-top:1px;
  font-variant-numeric:tabular-nums;font-family:var(--mono);letter-spacing:0.06em;}
.tl-row .body{font-size:10px;color:var(--dim);line-height:1.4;}
.tl-row .body b{color:var(--text);font-weight:600;font-size:11px;display:block;}
.tl-row .pill{justify-self:end;font-size:7px;font-weight:700;padding:3px 6px;
  letter-spacing:0.16em;text-transform:uppercase;font-family:var(--mono);border:1px solid;}
.pill.drive{border-color:var(--blue-80);color:var(--blue-80);}
.pill.hold{border-color:var(--coral-80);color:var(--coral-80);}
.pill.arrive{border-color:var(--green-80);color:var(--green-80);}
.dep{display:grid;grid-template-columns:26px 1fr 60px;align-items:center;gap:10px;
  padding:10px;background:rgba(255,255,255,0.02);border:1px solid var(--border);
  font-size:11px;margin-bottom:3px;}
.dep.winner{border-color:var(--green-80);background:rgba(95,240,162,0.04);}
.dep .rank{text-align:center;font-size:14px;font-weight:600;color:var(--fade);
  font-family:var(--mono);}
.dep.winner .rank{color:var(--green-80);}
.dep .body b{display:block;font-size:11px;font-weight:600;}
.dep .body small{display:block;font-size:8px;color:var(--fade);margin-top:3px;
  font-family:var(--mono);letter-spacing:0.08em;}
.dep .eta{text-align:right;}
.dep .eta b{display:block;font-size:14px;font-weight:600;font-variant-numeric:tabular-nums;
  font-family:var(--mono);}
.dep .eta small{font-size:7px;color:var(--fade);text-transform:uppercase;letter-spacing:0.14em;
  font-family:var(--mono);}
#sidebar footer{margin-top:20px;padding-top:12px;border-top:1px solid var(--border);
  font-size:8px;color:var(--fade);font-family:var(--mono);letter-spacing:0.1em;
  text-transform:uppercase;line-height:1.6;}
.err{padding:14px;border:1px solid var(--coral-80);color:var(--coral-80);
  background:var(--coral-50);font-size:11px;font-family:var(--mono);letter-spacing:0.04em;}

@media (max-width:900px){
  #stage{right:0;bottom:300px;}
  #sidebar{top:auto;left:0;right:0;bottom:0;width:100%;height:300px;
    border-left:none;border-top:1px solid var(--border);}
  #radar{width:140px;height:140px;}
  #gauges{display:none;}
  #term{display:none;}
}
</style></head>
<body>

<div id="stage">
  <div id="scene"></div>
  <div id="vignette"></div>
  <div id="scanlines"></div>

  <svg id="svg-overlay" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <filter id="glow"><feGaussianBlur stdDeviation="2" result="b"/>
        <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
      </filter>
    </defs>
    <g id="rover-bracket" opacity="0" style="filter:url(#glow)">
      <path d="M-24,-24 L-24,-14 M-24,-24 L-14,-24
               M 24,-24 L 24,-14 M 24,-24 L 14,-24
               M-24, 24 L-24, 14 M-24, 24 L-14, 24
               M 24, 24 L 24, 14 M 24, 24 L 14, 24"
            stroke="#ff8a2c" stroke-width="1.5" fill="none"/>
      <circle cx="0" cy="0" r="30" stroke="#ff8a2c" stroke-width="0.6" fill="none"
              stroke-dasharray="2 3" opacity="0.55"/>
      <text id="bracket-label" x="30" y="-20" fill="#ffb060" font-size="9"
            font-family="JetBrains Mono, monospace" letter-spacing="0.14em">ROVER · CURIOSITY-C1</text>
      <line id="bracket-line" x1="28" y1="-18" x2="60" y2="-18"
            stroke="#ffb060" stroke-width="0.8" opacity="0.8"/>
    </g>
    <g id="target-bracket" opacity="0" style="filter:url(#glow)">
      <circle cx="0" cy="0" r="22" stroke="#4de5ff" stroke-width="1" fill="none"/>
      <circle cx="0" cy="0" r="14" stroke="#4de5ff" stroke-width="0.5" fill="none"
              stroke-dasharray="1 2"/>
      <line x1="-30" y1="0" x2="-20" y2="0" stroke="#4de5ff" stroke-width="1.2"/>
      <line x1="30" y1="0" x2="20" y2="0" stroke="#4de5ff" stroke-width="1.2"/>
      <line x1="0" y1="-30" x2="0" y2="-20" stroke="#4de5ff" stroke-width="1.2"/>
      <line x1="0" y1="30" x2="0" y2="20" stroke="#4de5ff" stroke-width="1.2"/>
      <text id="target-label" x="28" y="5" fill="#4de5ff" font-size="9"
            font-family="JetBrains Mono, monospace" letter-spacing="0.14em">TGT · DEPOSIT-C</text>
    </g>
  </svg>

  <div id="hud-top" class="panel">
    <h1 id="hud-title">SOL-WINDOW PLANNER</h1>
    <div class="sub" id="hud-sub">MISSION VIEW · MSLv2</div>
    <div class="row"><span>SOL</span><b id="s-sol">0.0</b></div>
    <div class="row"><span>τ opacity</span><b id="s-tau">—</b></div>
    <div class="row"><span>POSITION</span><b id="s-pos">—</b></div>
    <div class="row"><span>ELEV</span><b id="s-elev">— m</b></div>
    <div class="row"><span>HEADING</span><b id="s-head">—°</b></div>
    <div class="status drive" id="s-status">READY</div>
  </div>

  <div id="gauges">
    <div class="gauge panel cool">
      <div class="g-hd"><span>SOLAR ARRAY</span><b id="g-solar-txt">0 W/m²</b></div>
      <div class="g-bar"><div class="g-fill" id="g-solar" style="width:80%"></div>
        <div class="g-notch" style="left:60%"></div></div>
    </div>
    <div class="gauge panel good">
      <div class="g-hd"><span>BATTERY</span><b id="g-batt-txt">100%</b></div>
      <div class="g-bar"><div class="g-fill" id="g-batt" style="width:100%"></div></div>
    </div>
    <div class="gauge panel hot">
      <div class="g-hd"><span>DUST DENSITY</span><b id="g-dust-txt">0.5</b></div>
      <div class="g-bar"><div class="g-fill" id="g-dust" style="width:20%"></div>
        <div class="g-notch" style="left:33%"></div></div>
    </div>
  </div>

  <div id="term" class="panel">
    <span class="t-lbl">■ TELEMETRY</span>
    <div id="term-lines"></div>
  </div>

  <div id="legend" class="panel">
    <span class="lbl">■ LAYERS</span>
    <div><span class="dot" style="background:#ff5040"></span>PLANNED ROUTE</div>
    <div><span class="dot" style="background:#ffb060"></span>ROVER TRAIL</div>
    <div><span class="dot" style="background:#4de5ff"></span>H₂O DEPOSITS</div>
    <div><span class="dot" style="background:#5ff0a2"></span>ROVER ORIGIN</div>
    <div style="margin-top:6px;color:var(--fade);font-size:8px;letter-spacing:0.14em;">DRAG ORBIT · SCROLL ZOOM</div>
  </div>

  <div id="radar" class="panel">
    <span id="radar-label">■ SECTOR SCAN</span>
    <canvas id="radar-canvas" width="320" height="320"></canvas>
  </div>

  <div id="controls" class="panel">
    <button id="btn-play">▶ PLAY</button>
    <button id="btn-reset">↻ RESET</button>
    <input id="scrub" type="range" min="0" max="1000" value="0">
    <span class="sol-label" id="sol-label">SOL 0.0</span>
    <button id="btn-cam">📷 FLY</button>
  </div>

  <div id="tooltip"></div>
</div>

<aside id="sidebar">
  <header>
    <div>
      <div class="brand">SOL-WINDOW · LIVE</div>
      <h2 id="side-title">Mission Command</h2>
      <div class="sub" id="side-sub">Loading…</div>
    </div>
    <span id="pill">● LIVE</span>
  </header>
  <div id="side-content"></div>
  <footer>
    ■ READS demo/plan.json<br>
    ■ RE-RUN <b>python -m sol_window.demo</b> TO REFRESH
  </footer>
</aside>

<script type="importmap">
{"imports":{
  "three":"https://unpkg.com/three@0.160.0/build/three.module.js",
  "three/addons/":"https://unpkg.com/three@0.160.0/examples/jsm/"
}}
</script>

<script type="module">
import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {EffectComposer} from 'three/addons/postprocessing/EffectComposer.js';
import {RenderPass} from 'three/addons/postprocessing/RenderPass.js';
import {UnrealBloomPass} from 'three/addons/postprocessing/UnrealBloomPass.js';
import {ShaderPass} from 'three/addons/postprocessing/ShaderPass.js';
import {FilmPass} from 'three/addons/postprocessing/FilmPass.js';
import {OutputPass} from 'three/addons/postprocessing/OutputPass.js';

const D = __PAYLOAD__;
document.getElementById('hud-title').textContent = D.title.toUpperCase();
document.getElementById('hud-sub').textContent =
  `${D.route.length} WAYPOINTS · TGT ${D.deposits[0].name.split(' ')[0].toUpperCase()}`;

// ============================================================
// SCENE
// ============================================================
const stage = document.getElementById('scene');
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x2b1408);
scene.fog = new THREE.FogExp2(0x3a1a10, 0.0022);
function stageSize(){ return {w: stage.clientWidth, h: stage.clientHeight}; }

const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 6000);
camera.position.set(D.w*1.05, Math.max(D.w,D.h)*1.0, D.h*1.35);

const renderer = new THREE.WebGLRenderer({antialias:true, alpha:false, powerPreference:'high-performance'});
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.setSize(stageSize().w, stageSize().h);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.15;
stage.appendChild(renderer.domElement);
camera.aspect = stageSize().w/stageSize().h;
camera.updateProjectionMatrix();

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.target.set(D.w/2, D.h/2, 0);
controls.minDistance = 20;
controls.maxDistance = 1500;
controls.maxPolarAngle = Math.PI * 0.48;

// ============================================================
// LIGHTS
// ============================================================
scene.background = new THREE.Color(0x2b1408);  // dusky Mars sky base
const sun = new THREE.DirectionalLight(0xffd8a8, 2.2);
sun.position.set(D.w*0.9, D.h*1.3, D.w*0.7);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
sun.shadow.camera.left = -D.w*0.8; sun.shadow.camera.right = D.w*1.2;
sun.shadow.camera.top = D.h*1.2; sun.shadow.camera.bottom = -D.h*0.8;
sun.shadow.camera.near = 10; sun.shadow.camera.far = 2000;
sun.shadow.bias = -0.0006;
scene.add(sun);
scene.add(new THREE.AmbientLight(0x3a2418, 0.55));
const bounce = new THREE.HemisphereLight(0xffa860, 0x160a05, 0.65);
scene.add(bounce);
// cool rim from opposite side
const rim = new THREE.DirectionalLight(0x6080ff, 0.35);
rim.position.set(-D.w, D.h*0.4, -D.w*0.5);
scene.add(rim);

// ============================================================
// TERRAIN — game-style Mars surface: PBR + rich Mars albedo + AO + contour overlay
// ============================================================
const zScale = 0.75;
const geo = new THREE.PlaneGeometry(D.w, D.h, D.w-1, D.h-1);
geo.rotateX(-Math.PI/2);
geo.translate(D.w/2, D.h/2, 0);
const pos = geo.attributes.position;
for (let i=0; i<pos.count; i++){
  const x=i%D.w, z=Math.floor(i/D.w);
  pos.setY(i, (D.elev[z*D.w+x]-D.eMin)*zScale);
}
geo.computeVertexNormals();
const normals = geo.attributes.normal;

// Rich per-vertex Mars albedo: height blend + slope exposure + wind streaks + fake AO
const cTmp = new THREE.Color();
const cBasalt  = new THREE.Color(0x2a1108);   // dark valleys
const cRust    = new THREE.Color(0x8a3820);   // rusty midground
const cDust    = new THREE.Color(0xd0824a);   // warm dust plateau
const cSand    = new THREE.Color(0xe8a868);   // light sand patch
const cBedrock = new THREE.Color(0x5a2c18);   // exposed bedrock
const cRock    = new THREE.Color(0x120806);   // black rock
const colors = new Float32Array(pos.count*3);

for (let i=0; i<pos.count; i++){
  const x = i % D.w, z = Math.floor(i / D.w);
  const eV = D.elev[z*D.w+x], tcl = D.terrainClass[z*D.w+x];
  const norm = (eV - D.eMin) / Math.max(D.eMax - D.eMin, 1);
  const ny = normals.getY(i);
  const slope = 1.0 - ny;

  // Fake local AO from surrounding elevation (darker inside crevices)
  let occ = 0, occN = 0;
  for (let dz=-3; dz<=3; dz+=3) for (let dx=-3; dx<=3; dx+=3){
    if (dx===0 && dz===0) continue;
    const xx = Math.max(0, Math.min(D.w-1, x+dx));
    const zz = Math.max(0, Math.min(D.h-1, z+dz));
    occ += Math.max(0, D.elev[zz*D.w+xx] - eV);
    occN++;
  }
  const ao = Math.min(1, occ / occN / 12);
  const aoF = 1.0 - ao * 0.4;

  // Height blend: basalt → rust → dust
  const t1 = Math.max(0, Math.min(1, (norm - 0.15) * 1.7));
  const t2 = Math.max(0, Math.min(1, (norm - 0.55) * 2.1));
  cTmp.copy(cBasalt).lerp(cRust, t1).lerp(cDust, t2);

  // Steep slopes expose darker rocky substrate
  const steepMix = Math.min(1, Math.max(0, (slope - 0.20) * 2.5));
  cTmp.r = cTmp.r * (1 - steepMix*0.55) + 0.22*steepMix;
  cTmp.g = cTmp.g * (1 - steepMix*0.60) + 0.09*steepMix;
  cTmp.b = cTmp.b * (1 - steepMix*0.65) + 0.05*steepMix;

  // Aeolian wind streaks
  const streak = Math.sin(x*0.11 + z*0.03) * Math.sin(x*0.037 - z*0.09) * 0.5 + 0.5;
  cTmp.r *= 0.85 + streak*0.30;
  cTmp.g *= 0.90 + streak*0.22;
  cTmp.b *= 0.94 + streak*0.14;

  // Fine noise
  const hj = (((x*7 + z*13) * 2654435761) % 1024) / 1024;
  const jitter = 0.85 + hj*0.30;
  cTmp.r *= jitter; cTmp.g *= jitter; cTmp.b *= jitter;

  // Terrain class overrides
  if (tcl===2){ cTmp.lerp(cSand, 0.55); }
  if (tcl===1){ cTmp.lerp(cBedrock, 0.35); }
  if (tcl===3){ cTmp.lerp(cRock, 0.80); }

  // Apply AO
  cTmp.r *= aoF; cTmp.g *= aoF; cTmp.b *= aoF;

  colors[i*3]=cTmp.r; colors[i*3+1]=cTmp.g; colors[i*3+2]=cTmp.b;
}
geo.setAttribute('color', new THREE.BufferAttribute(colors, 3));

// Real PBR — lets sun/ambient sculpt the terrain like a game
const terrainMat = new THREE.MeshStandardMaterial({
  vertexColors: true, roughness: 0.97, metalness: 0.02, flatShading: false,
});
const terrainUniforms = {
  time: { value: 0 }, scanRadius: { value: 0 }, fogDensity: { value: 0.0035 },
  scanCenter: { value: new THREE.Vector2(D.w/2, D.h/2) },
};
const terrain = new THREE.Mesh(geo, terrainMat);
terrain.receiveShadow = true;
scene.add(terrain);

// ---- Topographic contour overlay (marching-squares lite, translucent orange) ----
{
  const step = (D.eMax - D.eMin) / 14;
  const linePts = [];
  const el = (r,c) => D.elev[Math.max(0,Math.min(D.h-1,r))*D.w + Math.max(0,Math.min(D.w-1,c))];
  const yAt = (r,c) => (el(r,c) - D.eMin) * zScale + 0.18;
  for (let level = D.eMin + step; level < D.eMax; level += step){
    for (let r=0; r<D.h-1; r+=2){
      for (let c=0; c<D.w-1; c+=2){
        const a = el(r,c), b = el(r,c+2), d = el(r+2,c);
        if ((a - level) * (b - level) < 0){
          const t = (level - a) / (b - a);
          linePts.push(new THREE.Vector3(c + t*2, yAt(r, c+t*2), r));
          linePts.push(new THREE.Vector3(c + t*2 + 1.2, yAt(r, c+t*2), r));
        }
        if ((a - level) * (d - level) < 0){
          const t = (level - a) / (d - a);
          linePts.push(new THREE.Vector3(c, yAt(r+t*2, c), r + t*2));
          linePts.push(new THREE.Vector3(c, yAt(r+t*2, c), r + t*2 + 1.2));
        }
      }
    }
  }
  const contourGeo = new THREE.BufferGeometry().setFromPoints(linePts);
  const contours = new THREE.LineSegments(contourGeo,
    new THREE.LineBasicMaterial({color:0xffa860, transparent:true, opacity:0.18}));
  scene.add(contours);
}

// ---- Mars sky dome (gradient sphere) ----
{
  const skyGeo = new THREE.SphereGeometry(Math.max(D.w,D.h)*3.5, 32, 24);
  const skyMat = new THREE.ShaderMaterial({
    side: THREE.BackSide, depthWrite: false, fog: false,
    uniforms:{
      topCol:    { value: new THREE.Color(0x1a0808) },
      midCol:    { value: new THREE.Color(0x5a2612) },
      horizonCol:{ value: new THREE.Color(0xd0824a) },
    },
    vertexShader:`varying vec3 vP;void main(){vP=position;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}`,
    fragmentShader:`
      uniform vec3 topCol, midCol, horizonCol;
      varying vec3 vP;
      void main(){
        float h = normalize(vP).y;
        vec3 c = mix(horizonCol, midCol, smoothstep(-0.05, 0.35, h));
        c = mix(c, topCol, smoothstep(0.35, 0.85, h));
        gl_FragColor = vec4(c, 1.0);
      }`
  });
  scene.add(new THREE.Mesh(skyGeo, skyMat));
}

// ---- Distant surrounding hill ring for horizon depth (BackSide dome, far away) ----
{
  const skirtR = Math.max(D.w, D.h) * 2.4;
  const seg = 128;
  const hillGeo = new THREE.CylinderGeometry(skirtR*0.98, skirtR*1.05, 60, seg, 4, true);
  const sp = hillGeo.attributes.position;
  for (let i=0; i<sp.count; i++){
    const x = sp.getX(i), z = sp.getZ(i);
    const a = Math.atan2(z, x);
    const bump = 22*Math.sin(a*7) + 15*Math.sin(a*13+1.3) + 9*Math.sin(a*23);
    if (sp.getY(i) > 10) sp.setY(i, sp.getY(i) + Math.abs(bump)*0.8);
  }
  hillGeo.computeVertexNormals();
  hillGeo.translate(D.w/2, -5, D.h/2);
  const hillMat = new THREE.MeshStandardMaterial({
    color: 0x3a1a10, roughness: 0.98, metalness: 0.0,
    side: THREE.BackSide, flatShading: true, fog: true,
  });
  scene.add(new THREE.Mesh(hillGeo, hillMat));
}

// ============================================================
// HELPERS
// ============================================================
function toWorld(row, col, lift=1){
  const rr=Math.max(0,Math.min(D.h-1,Math.round(row)));
  const cc=Math.max(0,Math.min(D.w-1,Math.round(col)));
  const y=(D.elev[rr*D.w+cc]-D.eMin)*zScale+lift;
  return new THREE.Vector3(col, y, row);
}

// ============================================================
// ROUTE — animated flowing shader tube
// ============================================================
const routePts = D.route.map(([r,c])=>toWorld(r,c,1.2));

// Build curve for smooth path
const curve = new THREE.CatmullRomCurve3(routePts, false, 'catmullrom', 0.15);
const tubeGeo = new THREE.TubeGeometry(curve, Math.max(64, routePts.length*2), 0.5, 8, false);

const routeMat = new THREE.ShaderMaterial({
  uniforms: { time:{value:0}, cA:{value:new THREE.Color(0xff5040)},
              cB:{value:new THREE.Color(0xffcc60)} },
  transparent: true,
  vertexShader: `
    varying float vU;
    void main(){
      vU = uv.x;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0);
    }`,
  fragmentShader: `
    uniform float time;
    uniform vec3 cA;
    uniform vec3 cB;
    varying float vU;
    void main(){
      float f = fract(vU * 22.0 - time * 0.9);
      float pulse = smoothstep(0.75, 1.0, f) + smoothstep(0.0, 0.15, 1.0-f) * 0.4;
      vec3 col = mix(cA, cB, pulse);
      float alpha = 0.55 + pulse * 0.45;
      gl_FragColor = vec4(col, alpha);
    }`
});
const routeTube = new THREE.Mesh(tubeGeo, routeMat);
scene.add(routeTube);

// dashed baseline route
const routeGeo = new THREE.BufferGeometry().setFromPoints(routePts);
const routeLine = new THREE.Line(routeGeo, new THREE.LineDashedMaterial({
  color:0xff8060, dashSize:1.8, gapSize:1.0, transparent:true, opacity:0.35,
}));
routeLine.computeLineDistances();
scene.add(routeLine);

// solid driven trail
const drivenGeo = new THREE.BufferGeometry();
drivenGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(routePts.length*3), 3));
drivenGeo.setDrawRange(0, 0);
const drivenLine = new THREE.Line(drivenGeo, new THREE.LineBasicMaterial({
  color:0xffb060, transparent:true, opacity:0.95,
}));
scene.add(drivenLine);

// waypoint dots colour-coded by sol
const waypointGroup = new THREE.Group();
D.route.forEach(([r,c], i) => {
  if (i % 3 !== 0) return;
  const sol = D.routeSols[i] || 0;
  const tauAtSol = D.tau[Math.min(sol, D.tau.length-1)] || 0.5;
  const color = tauAtSol > 1.0 ? 0xff5040 : (tauAtSol > 0.7 ? 0xffb060 : 0xffd7a8);
  const dot = new THREE.Mesh(
    new THREE.SphereGeometry(0.35, 8, 8),
    new THREE.MeshBasicMaterial({color, transparent:true, opacity:0.7})
  );
  dot.position.copy(toWorld(r, c, 1.6));
  waypointGroup.add(dot);
});
scene.add(waypointGroup);

// ============================================================
// DEPOSITS — holographic pillar + rotating data ring + beam
// ============================================================
const depMeshes = [];
D.deposits.forEach((d, idx) => {
  const g = new THREE.Group();
  const isWinner = idx === 0;
  const col = isWinner ? 0x5ff0a2 : 0x4de5ff;

  // core cone
  const cone = new THREE.Mesh(
    new THREE.ConeGeometry(1.6, 5.5, 16),
    new THREE.MeshStandardMaterial({
      color: col, emissive: col, emissiveIntensity: 1.3,
      roughness: 0.25, metalness: 0.7,
    })
  );
  cone.rotation.x = Math.PI;
  cone.position.y = 4.5;
  cone.castShadow = true;
  g.add(cone);

  // rotating data ring (torus with markers)
  const ring = new THREE.Group();
  const torus = new THREE.Mesh(
    new THREE.TorusGeometry(2.6, 0.09, 8, 48),
    new THREE.MeshBasicMaterial({color: col, transparent:true, opacity:0.85})
  );
  torus.rotation.x = Math.PI/2;
  ring.add(torus);
  // ring markers
  for (let k=0; k<12; k++){
    const a = (k/12)*Math.PI*2;
    const marker = new THREE.Mesh(
      new THREE.BoxGeometry(0.15, 0.35, 0.15),
      new THREE.MeshBasicMaterial({color: col})
    );
    marker.position.set(Math.cos(a)*2.6, 0, Math.sin(a)*2.6);
    ring.add(marker);
  }
  ring.position.y = 0.6;
  g.add(ring);

  // secondary pulse ring
  const pulseRing = new THREE.Mesh(
    new THREE.TorusGeometry(2.0, 0.14, 8, 32),
    new THREE.MeshBasicMaterial({color: col, transparent:true, opacity:0.5})
  );
  pulseRing.rotation.x = Math.PI/2;
  g.add(pulseRing);

  // vertical hologram beam (shader gradient)
  const beamMat = new THREE.ShaderMaterial({
    uniforms:{ time:{value:0}, col:{value: new THREE.Color(col)} },
    transparent: true, depthWrite: false, side: THREE.DoubleSide,
    vertexShader:`varying float vY;void main(){vY=uv.y;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}`,
    fragmentShader:`uniform float time;uniform vec3 col;varying float vY;
      void main(){
        float a = pow(1.0-vY, 2.5) * 0.55;
        float f = fract(vY*4.0 - time*0.5);
        a += smoothstep(0.85, 1.0, f) * 0.35;
        gl_FragColor = vec4(col, a);
      }`
  });
  const beam = new THREE.Mesh(
    new THREE.CylinderGeometry(0.4, 0.6, 60, 12, 1, true), beamMat
  );
  beam.position.y = 32;
  beam.userData.shader = beamMat;
  g.add(beam);

  g.position.copy(toWorld(d.row, d.col, 0.2));
  g.userData = d;
  scene.add(g);
  depMeshes.push(g);
});

// ============================================================
// START MARKER
// ============================================================
const startGroup = new THREE.Group();
const startCone = new THREE.Mesh(
  new THREE.ConeGeometry(1.5, 4.5, 12),
  new THREE.MeshStandardMaterial({color:0x5ff0a2, emissive:0x2a9060, emissiveIntensity:1.1})
);
startCone.rotation.x = Math.PI;
startCone.position.y = 4;
startGroup.add(startCone);
const startRing = new THREE.Mesh(
  new THREE.TorusGeometry(2.6, 0.14, 8, 24),
  new THREE.MeshBasicMaterial({color:0x5ff0a2, transparent:true, opacity:0.9})
);
startRing.rotation.x = Math.PI/2;
startGroup.add(startRing);
startGroup.position.copy(toWorld(D.start[0], D.start[1], 0.4));
scene.add(startGroup);

// ============================================================
// ROVER — Curiosity-inspired
// ============================================================
const rover = new THREE.Group();

// chassis
const body = new THREE.Mesh(
  new THREE.BoxGeometry(2.8, 1.1, 3.8),
  new THREE.MeshStandardMaterial({color:0xcbc0a8, metalness:0.75, roughness:0.35})
);
body.castShadow = true;
rover.add(body);
// side accent stripe
const stripe = new THREE.Mesh(
  new THREE.BoxGeometry(2.86, 0.15, 3.86),
  new THREE.MeshStandardMaterial({color:0xff8a2c, emissive:0x662010, emissiveIntensity:0.6})
);
stripe.position.y = 0.3;
rover.add(stripe);

// RTG (nuclear power unit) at rear
const rtg = new THREE.Mesh(
  new THREE.CylinderGeometry(0.35, 0.35, 1.4, 12),
  new THREE.MeshStandardMaterial({color:0x333333, metalness:0.8, roughness:0.5,
    emissive:0x502010, emissiveIntensity:0.3})
);
rtg.rotation.z = Math.PI/2;
rtg.position.set(0, 0.7, -2.3);
rover.add(rtg);
// heat fins on RTG
for (let k=0; k<8; k++){
  const fin = new THREE.Mesh(
    new THREE.BoxGeometry(0.06, 0.5, 1.2),
    new THREE.MeshStandardMaterial({color:0x555555, metalness:0.7})
  );
  const a = k/8 * Math.PI * 2;
  fin.position.set(Math.cos(a)*0.45, 0.7 + Math.sin(a)*0.45, -2.3);
  fin.rotation.z = a;
  rover.add(fin);
}

// solar-tech deck grid
const deck = new THREE.Mesh(
  new THREE.BoxGeometry(3.2, 0.1, 4.2),
  new THREE.MeshStandardMaterial({color:0x1a2545, metalness:0.5, roughness:0.15,
    emissive:0x0a1830, emissiveIntensity:0.4})
);
deck.position.y = 0.68;
rover.add(deck);
for (let i=1; i<5; i++){
  const g1 = new THREE.Mesh(
    new THREE.BoxGeometry(3.2, 0.12, 0.04),
    new THREE.MeshBasicMaterial({color:0x4a70a8})
  );
  g1.position.set(0, 0.7, -2.0 + i);
  rover.add(g1);
}

// six wheels
const wheelGeo = new THREE.CylinderGeometry(0.55, 0.55, 0.45, 14);
const wheelMat = new THREE.MeshStandardMaterial({color:0x151515, roughness:0.9, metalness:0.2});
const rimMat = new THREE.MeshStandardMaterial({color:0x888888, metalness:0.8});
const wheelPositions = [
  [-1.4,-0.85,-1.5],[1.4,-0.85,-1.5],
  [-1.4,-0.85, 0.0],[1.4,-0.85, 0.0],
  [-1.4,-0.85, 1.5],[1.4,-0.85, 1.5],
];
const wheels = [];
wheelPositions.forEach(([x,y,z]) => {
  const wh = new THREE.Group();
  const tyre = new THREE.Mesh(wheelGeo, wheelMat);
  tyre.rotation.z = Math.PI/2;
  wh.add(tyre);
  const hub = new THREE.Mesh(
    new THREE.CylinderGeometry(0.22, 0.22, 0.48, 8),
    rimMat
  );
  hub.rotation.z = Math.PI/2;
  wh.add(hub);
  wh.position.set(x,y,z);
  wh.castShadow = true;
  rover.add(wh);
  wheels.push(wh);
});

// mast + camera + laser
const mastGroup = new THREE.Group();
const mast = new THREE.Mesh(
  new THREE.CylinderGeometry(0.1, 0.12, 2.6, 8),
  new THREE.MeshStandardMaterial({color:0x8a8070, metalness:0.65})
);
mast.position.y = 1.3;
mastGroup.add(mast);
const head = new THREE.Mesh(
  new THREE.BoxGeometry(0.7, 0.55, 1.0),
  new THREE.MeshStandardMaterial({color:0x333333, metalness:0.7, roughness:0.4})
);
head.position.y = 2.7;
mastGroup.add(head);
// lens
const lens = new THREE.Mesh(
  new THREE.CylinderGeometry(0.18, 0.18, 0.15, 12),
  new THREE.MeshStandardMaterial({color:0x111111, metalness:0.9, roughness:0.15,
    emissive:0xff5030, emissiveIntensity:0.7})
);
lens.rotation.x = Math.PI/2;
lens.position.set(0, 2.7, 0.55);
mastGroup.add(lens);
mastGroup.position.set(0, 0.5, 1.2);
rover.add(mastGroup);

// laser beam from mast (ChemCam-inspired)
const laserGeo = new THREE.BufferGeometry();
laserGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array([
  0, 3.2, 1.75,
  0, 0.5, 22,
]), 3));
const laser = new THREE.Line(laserGeo, new THREE.LineBasicMaterial({
  color:0xff3010, transparent:true, opacity:0.55,
}));
rover.add(laser);

// robotic arm folded on side
const armPivot = new THREE.Group();
armPivot.position.set(1.4, 0.5, 1.6);
const arm1 = new THREE.Mesh(
  new THREE.BoxGeometry(0.15, 0.15, 1.6),
  new THREE.MeshStandardMaterial({color:0xaaaaaa, metalness:0.7})
);
arm1.position.z = 0.8;
armPivot.add(arm1);
const arm2 = new THREE.Mesh(
  new THREE.BoxGeometry(0.13, 0.13, 1.2),
  new THREE.MeshStandardMaterial({color:0x9a9a9a, metalness:0.7})
);
arm2.position.set(0, 0, 1.7);
arm2.rotation.x = -0.3;
armPivot.add(arm2);
rover.add(armPivot);

// beacon glow
const beacon = new THREE.Mesh(
  new THREE.SphereGeometry(0.28, 16, 16),
  new THREE.MeshBasicMaterial({color:0xffb060})
);
beacon.position.set(0, 1.1, 0);
rover.add(beacon);
const beaconLight = new THREE.PointLight(0xff8a2c, 1.8, 20);
beaconLight.position.set(0, 1.3, 0);
rover.add(beaconLight);

rover.position.copy(routePts[0]);
scene.add(rover);

// ============================================================
// DUST + STARS
// ============================================================
const dustGeo = new THREE.BufferGeometry();
const N_DUST = 6000;
const dustArr = new Float32Array(N_DUST*3);
for (let i=0; i<N_DUST; i++){
  dustArr[i*3]   = Math.random()*D.w*1.5 - D.w*0.25;
  dustArr[i*3+1] = Math.random()*120;
  dustArr[i*3+2] = Math.random()*D.h*1.5 - D.h*0.25;
}
dustGeo.setAttribute('position', new THREE.BufferAttribute(dustArr, 3));
const dustMat = new THREE.PointsMaterial({
  color:0xc06840, size:1.4, transparent:true, opacity:0.0, sizeAttenuation:true,
});
const dust = new THREE.Points(dustGeo, dustMat);
scene.add(dust);

const starGeo = new THREE.BufferGeometry();
const N_STAR = 1200;
const starArr = new Float32Array(N_STAR*3);
for (let i=0; i<N_STAR; i++){
  const r = 1800;
  const theta = Math.random()*Math.PI*2;
  const phi = Math.random()*Math.PI/2 + 0.05;
  starArr[i*3]   = D.w/2 + r*Math.sin(phi)*Math.cos(theta);
  starArr[i*3+1] = r*Math.cos(phi);
  starArr[i*3+2] = D.h/2 + r*Math.sin(phi)*Math.sin(theta);
}
starGeo.setAttribute('position', new THREE.BufferAttribute(starArr, 3));
const starMat = new THREE.PointsMaterial({color:0xffffff, size:1.6, transparent:true, opacity:0});
scene.add(new THREE.Points(starGeo, starMat));

// ============================================================
// POST-PROCESSING
// ============================================================
const composer = new EffectComposer(renderer);
composer.setPixelRatio(Math.min(devicePixelRatio, 2));
composer.setSize(stageSize().w, stageSize().h);
composer.addPass(new RenderPass(scene, camera));

const bloomPass = new UnrealBloomPass(
  new THREE.Vector2(stageSize().w, stageSize().h), 0.35, 0.25, 1.05
);
composer.addPass(bloomPass);

// Chromatic aberration shader (very subtle)
const chromaShader = {
  uniforms:{ tDiffuse:{value:null}, offset:{value: 0.0009}, time:{value:0}},
  vertexShader:`varying vec2 vUv;void main(){vUv=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}`,
  fragmentShader:`
    uniform sampler2D tDiffuse; uniform float offset; uniform float time;
    varying vec2 vUv;
    void main(){
      vec2 dir = vUv - 0.5;
      float d = length(dir);
      vec2 off = normalize(dir) * offset * d;
      float r = texture2D(tDiffuse, vUv + off).r;
      float g = texture2D(tDiffuse, vUv).g;
      float b = texture2D(tDiffuse, vUv - off).b;
      gl_FragColor = vec4(r,g,b,1.0);
    }`
};
composer.addPass(new ShaderPass(chromaShader));

composer.addPass(new FilmPass(0.08, 0.15, stageSize().h, false));
composer.addPass(new OutputPass());

// ============================================================
// UI / CONTROLS
// ============================================================
let progress = 0, playing = false, flying = false;
const scrub = document.getElementById('scrub');
const btnPlay = document.getElementById('btn-play');
btnPlay.onclick = () => { playing = !playing; btnPlay.textContent = playing?'❚❚ PAUSE':'▶ PLAY'; };
document.getElementById('btn-reset').onclick = () => { progress = 0; scrub.value = 0; updateScrubStyle(); };
document.getElementById('btn-cam').onclick = e => {
  flying = !flying; e.target.textContent = flying?'📷 ORBIT':'📷 FLY';
};
function updateScrubStyle(){
  scrub.style.setProperty('--p', (scrub.value/10) + '%');
}
scrub.oninput = () => {
  progress = scrub.value / 1000;
  playing = false; btnPlay.textContent = '▶ PLAY';
  updateScrubStyle();
};
updateScrubStyle();

// tooltip
const tooltip = document.getElementById('tooltip');
const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();
renderer.domElement.addEventListener('mousemove', e => {
  const rect = renderer.domElement.getBoundingClientRect();
  mouse.x = ((e.clientX-rect.left)/rect.width)*2 - 1;
  mouse.y = -((e.clientY-rect.top)/rect.height)*2 + 1;
  raycaster.setFromCamera(mouse, camera);
  const hits = raycaster.intersectObjects(depMeshes, true);
  if (hits.length){
    let g = hits[0].object;
    while (g.parent && !g.userData.name) g = g.parent;
    const d = g.userData;
    tooltip.innerHTML = `<b>${d.name.toUpperCase()}</b><br>DEPTH ${d.depth.toFixed(1)} M · YIELD ${Math.round(d['yield'])} KG/M²`;
    tooltip.style.left = (e.clientX+14)+'px';
    tooltip.style.top = (e.clientY+14)+'px';
    tooltip.style.display = 'block';
  } else tooltip.style.display = 'none';
});

// ============================================================
// RADAR MINIMAP
// ============================================================
const radarCanvas = document.getElementById('radar-canvas');
const rctx = radarCanvas.getContext('2d');
const RW = radarCanvas.width;
function drawRadar(sweepAngle, roverRC){
  rctx.clearRect(0,0,RW,RW);
  // background
  rctx.fillStyle = 'rgba(4,10,8,0.6)';
  rctx.fillRect(0,0,RW,RW);
  // rings
  rctx.strokeStyle = 'rgba(77,229,255,0.25)';
  rctx.lineWidth = 1;
  for (let k=1; k<=4; k++){
    rctx.beginPath();
    rctx.arc(RW/2, RW/2, (RW/2-6)*k/4, 0, Math.PI*2);
    rctx.stroke();
  }
  // crosshair
  rctx.beginPath();
  rctx.moveTo(RW/2, 4); rctx.lineTo(RW/2, RW-4);
  rctx.moveTo(4, RW/2); rctx.lineTo(RW-4, RW/2);
  rctx.stroke();
  // sweep
  const grd = rctx.createConicGradient(sweepAngle - Math.PI/2, RW/2, RW/2);
  grd.addColorStop(0, 'rgba(77,229,255,0.5)');
  grd.addColorStop(0.15, 'rgba(77,229,255,0)');
  grd.addColorStop(1, 'rgba(77,229,255,0)');
  rctx.fillStyle = grd;
  rctx.beginPath();
  rctx.moveTo(RW/2, RW/2);
  rctx.arc(RW/2, RW/2, RW/2-6, sweepAngle - Math.PI/2 - 1.2, sweepAngle - Math.PI/2);
  rctx.closePath();
  rctx.fill();

  const px = (row,col) => ({
    x: RW/2 + (col - D.w/2) * (RW/2-10) / (D.w/2),
    y: RW/2 + (row - D.h/2) * (RW/2-10) / (D.h/2),
  });

  // route ghost
  rctx.strokeStyle = 'rgba(255,138,44,0.35)';
  rctx.lineWidth = 1;
  rctx.beginPath();
  D.route.forEach(([r,c], i) => {
    const p = px(r,c); if (i===0) rctx.moveTo(p.x,p.y); else rctx.lineTo(p.x,p.y);
  });
  rctx.stroke();

  // deposits
  D.deposits.forEach((d, i) => {
    const p = px(d.row, d.col);
    rctx.fillStyle = i===0 ? '#5ff0a2' : '#4de5ff';
    rctx.beginPath(); rctx.arc(p.x, p.y, 4, 0, Math.PI*2); rctx.fill();
    // pulse ring
    rctx.strokeStyle = i===0 ? 'rgba(95,240,162,0.5)' : 'rgba(77,229,255,0.4)';
    rctx.beginPath();
    rctx.arc(p.x, p.y, 4 + 4*Math.abs(Math.sin(sweepAngle + i)), 0, Math.PI*2);
    rctx.stroke();
  });
  // start
  const s = px(D.start[0], D.start[1]);
  rctx.strokeStyle = '#5ff0a2';
  rctx.strokeRect(s.x-4, s.y-4, 8, 8);

  // rover
  const rr = px(roverRC.row, roverRC.col);
  rctx.fillStyle = '#ff8a2c';
  rctx.beginPath(); rctx.arc(rr.x, rr.y, 3.5, 0, Math.PI*2); rctx.fill();
  rctx.strokeStyle = 'rgba(255,138,44,0.6)';
  rctx.lineWidth = 1;
  rctx.beginPath();
  rctx.arc(rr.x, rr.y, 8 + 4*Math.sin(sweepAngle*2), 0, Math.PI*2);
  rctx.stroke();
}

// ============================================================
// SVG OVERLAY (rover bracket + target bracket)
// ============================================================
const roverBracket = document.getElementById('rover-bracket');
const targetBracket = document.getElementById('target-bracket');
const bracketLabel = document.getElementById('bracket-label');
const targetLabel = document.getElementById('target-label');
const bracketLine = document.getElementById('bracket-line');
targetLabel.textContent = `TGT · ${D.deposits[0].name.split(' ')[0].toUpperCase()}`;

function project(worldVec){
  const v = worldVec.clone().project(camera);
  return {
    x: (v.x + 1) / 2 * stageSize().w,
    y: (1 - v.y) / 2 * stageSize().h,
    behind: v.z > 1,
  };
}

function updateBrackets(){
  const size = stageSize();
  const svg = document.getElementById('svg-overlay');
  svg.setAttribute('viewBox', `0 0 ${size.w} ${size.h}`);
  svg.setAttribute('width', size.w); svg.setAttribute('height', size.h);
  const rp = project(rover.position.clone().add(new THREE.Vector3(0,1.5,0)));
  if (!rp.behind){
    roverBracket.setAttribute('transform', `translate(${rp.x} ${rp.y})`);
    roverBracket.setAttribute('opacity', 0.9);
    const dTgt = rover.position.distanceTo(depMeshes[0].position);
    bracketLabel.textContent = `ROVER · ${dTgt.toFixed(0)}M TO TGT`;
  } else roverBracket.setAttribute('opacity', 0);
  const tp = project(depMeshes[0].position.clone().add(new THREE.Vector3(0,4,0)));
  if (!tp.behind){
    targetBracket.setAttribute('transform', `translate(${tp.x} ${tp.y})`);
    targetBracket.setAttribute('opacity', 0.85);
  } else targetBracket.setAttribute('opacity', 0);
}

// ============================================================
// TELEMETRY / TERMINAL
// ============================================================
const termLines = document.getElementById('term-lines');
const termQueue = [
  ['SYS', 'MSL-V2 CORE ONLINE'],
  ['SYS', 'MOLA DEM TILE LOADED'],
  ['SYS', 'AI4MARS CLASSIFIER READY'],
  ['NAV', `PLAN LOCKED · ETA ${D.eta.toFixed(1)} SOLS`],
  ['NAV', `TARGET ${D.deposits[0].name.split(' ')[0].toUpperCase()}`],
  ['PWR', 'SOLAR ARRAY NOMINAL'],
];
function pushTerm(tag, msg){
  const line = document.createElement('div');
  line.className = 'line new';
  line.innerHTML = `<b>[${tag}]</b> ${msg}`;
  termLines.prepend(line);
  while (termLines.children.length > 9) termLines.removeChild(termLines.lastChild);
  setTimeout(()=>line.classList.remove('new'), 400);
}
termQueue.forEach((t,i) => setTimeout(()=>pushTerm(t[0], t[1]), i*400));

let lastSolLogged = -1;
let lastStatusLogged = '';
function maybeLog(sol, status, tau){
  const s = Math.floor(sol);
  if (s !== lastSolLogged){
    lastSolLogged = s;
    pushTerm('SOL', `${String(s).padStart(2,'0')} · τ ${tau.toFixed(2)}`);
  }
  if (status !== lastStatusLogged){
    lastStatusLogged = status;
    if (status === 'hold') pushTerm('WARN', 'SAFETY HOLD · DUST STORM');
    if (status === 'drive') pushTerm('NAV', 'RESUMING TRAVERSE');
    if (status === 'arrive') pushTerm('DONE', 'TGT REACHED · SAMPLING ICE');
  }
}

// ============================================================
// HUD UPDATE
// ============================================================
function updateHUD(sol, roverPos, heading){
  const ti = Math.min(D.tau.length-1, Math.max(0, Math.floor(sol)));
  const tv = D.tau[ti];
  document.getElementById('s-sol').textContent = sol.toFixed(1);
  document.getElementById('s-tau').textContent = tv.toFixed(2);
  document.getElementById('s-pos').textContent = `(${Math.round(roverPos.z)}, ${Math.round(roverPos.x)})`;
  document.getElementById('s-elev').textContent = Math.round(roverPos.y/zScale + D.eMin) + ' M';
  document.getElementById('s-head').textContent = (((heading*180/Math.PI)+360)%360).toFixed(0) + '°';
  const st = document.getElementById('s-status');
  let status = 'drive';
  if (progress >= 1){ status='arrive'; st.className = 'status arrive'; st.textContent = 'ARRIVED · SAMPLING ICE'; }
  else if (tv > 1.0){ status='hold'; st.className = 'status hold'; st.textContent = 'SAFETY HOLD · τ > 1.0'; }
  else { st.className = 'status drive'; st.textContent = 'DRIVING'; }
  document.getElementById('sol-label').textContent = `SOL ${sol.toFixed(1)}`;

  // gauges
  const solar = Math.max(0.1, Math.exp(-1.3*tv));
  document.getElementById('g-solar').style.width = (solar*100).toFixed(0)+'%';
  document.getElementById('g-solar-txt').textContent = Math.round(solar*590)+' W/m²';
  const batt = Math.max(0.2, 1 - (progress*0.4 + Math.max(0,tv-0.7)*0.15));
  document.getElementById('g-batt').style.width = (batt*100).toFixed(0)+'%';
  document.getElementById('g-batt-txt').textContent = Math.round(batt*100)+'%';
  const dustPct = Math.min(100, tv*66);
  document.getElementById('g-dust').style.width = dustPct.toFixed(0)+'%';
  document.getElementById('g-dust-txt').textContent = tv.toFixed(2);

  // atmospheric response
  dustMat.opacity = Math.max(0, Math.min(0.65, (tv-0.6)*1.4));
  const dark = Math.max(0, Math.min(1, (tv-0.5)*0.9));
  scene.background = new THREE.Color().setRGB(
    0.10*(1-dark*0.7), 0.04*(1-dark*0.5), 0.02
  );
  sun.intensity = Math.max(0.15, 1.4*Math.exp(-1.2*tv));
  starMat.opacity = dark*0.6;
  scene.fog.density = 0.0035 + dark*0.008;
  terrainUniforms.fogDensity.value = scene.fog.density;

  maybeLog(sol, status, tv);
}

// ============================================================
// SIDEBAR
// ============================================================
const pill = document.getElementById('pill');
const sideContent = document.getElementById('side-content');
const sideSub = document.getElementById('side-sub');

async function fetchPlan(){
  try {
    const r = await fetch('plan.json?t=' + Date.now(), {cache:'no-store'});
    if (!r.ok) throw new Error('HTTP ' + r.status);
    return await r.json();
  } catch (e){ return {_err: e.message}; }
}
function fmt(n, d=1){ return n.toFixed(d); }

function renderSidebar(p, currentSol){
  if (p._err){
    sideContent.innerHTML = `<div class="err">CANNOT READ <b>plan.json</b><br><br><small>${p._err}</small><br><br>IF FILE://, START SERVER:<br><code>python serve.py</code></div>`;
    pill.className = 'stale';
    pill.textContent = '● WAITING';
    return;
  }
  pill.className = '';
  pill.textContent = '● LIVE';
  const w = p.winner;
  sideSub.textContent = `START (${p.start.row}, ${p.start.col}) → ${w.name.split(' ')[0]}`;

  sideContent.innerHTML = `
    <div class="stats">
      <div class="stat"><b>${fmt(w.eta_sols)}</b><small>ETA SOLS</small></div>
      <div class="stat"><b>${fmt(w.distance_km)}</b><small>KM DRIVEN</small></div>
      <div class="stat"><b>${w.idle_sols}</b><small>SOLS IDLED</small></div>
      <div class="stat"><b>${Math.round(w.yield_kg_m2)}</b><small>KG/M² YIELD</small></div>
      <div class="stat"><b>${fmt(w.peak_tau, 2)}</b><small>PEAK τ</small></div>
      <div class="stat"><b>${w.waypoints}</b><small>WAYPOINTS</small></div>
    </div>

    <h3>Mission Timeline</h3>
    <div class="tl">${p.timeline.map(ev => `
      <div class="tl-row ${ev.status==='hold'?'hl':''} ${Math.floor(currentSol)===ev.sol?'current':''}">
        <span class="d"><b>SOL ${ev.sol}</b><small>τ ${fmt(ev.tau,2)}</small></span>
        <span class="body">
          <b>${ev.status==='hold' ? (ev.tau>1.3?'Storm peak':'Storm hold')
              : ev.status==='arrive' ? 'Arrival · sample ice'
              : ev.sol===0 ? 'Depart' : 'Continue traverse'}</b>
          waypoint (${ev.row}, ${ev.col})
        </span>
        <span class="pill ${ev.status}">${ev.status}</span>
      </div>`).join('')}</div>

    <h3>Ranked Deposits</h3>
    ${p.ranked_deposits.map((d,i)=>`
      <div class="dep ${i===0?'winner':''}">
        <span class="rank">${String(i+1).padStart(2,'0')}</span>
        <span class="body"><b>${d.name}</b><small>YIELD ${Math.round(d.yield_kg_m2)} KG/M² · ${fmt(d.distance_km)} KM</small></span>
        <span class="eta"><b>${fmt(d.eta_sols)}</b><small>SOLS</small></span>
      </div>`).join('')}
  `;
}

let currentSol = 0;
async function pollLoop(){
  const p = await fetchPlan();
  renderSidebar(p, currentSol);
  setTimeout(pollLoop, 2500);
}
pollLoop();

// ============================================================
// ANIMATION LOOP
// ============================================================
const clock = new THREE.Clock();
let heading = 0;

function animate(){
  const dt = clock.getDelta();
  const t = clock.elapsedTime;

  if (playing){
    progress += dt / (D.tau.length * 0.55);
    if (progress > 1){ progress = 1; playing = false; btnPlay.textContent = '▶ PLAY'; }
    scrub.value = progress * 1000;
    updateScrubStyle();
  }
  const iF = progress * (routePts.length - 1);
  const i0 = Math.floor(iF), i1 = Math.min(routePts.length-1, i0+1), tt = iF-i0;
  rover.position.lerpVectors(routePts[i0], routePts[i1], tt);
  rover.position.y += 1.4;
  if (i1 > i0){
    const dir = new THREE.Vector3().subVectors(routePts[i1], routePts[i0]);
    const targetH = Math.atan2(dir.x, dir.z);
    // smooth rotation
    let delta = targetH - heading;
    while (delta > Math.PI) delta -= Math.PI*2;
    while (delta < -Math.PI) delta += Math.PI*2;
    heading += delta * Math.min(1, dt*4);
    rover.rotation.y = heading;
  }
  wheels.forEach(w => {
    w.children.forEach(ch => ch.rotation.x += dt * 8 * (playing ? 1 : 0));
  });

  drivenGeo.setDrawRange(0, i0+1);
  const dp = drivenGeo.attributes.position.array;
  for (let k=0; k<=i0; k++){
    dp[k*3] = routePts[k].x;
    dp[k*3+1] = routePts[k].y + 0.3;
    dp[k*3+2] = routePts[k].z;
  }
  drivenGeo.attributes.position.needsUpdate = true;

  const sol = D.routeSols.length
    ? D.routeSols[Math.min(i0, D.routeSols.length-1)] + (i1>i0 ? tt*0.25 : 0)
    : progress * D.tau.length;
  currentSol = sol;
  updateHUD(sol, rover.position, heading);

  // dust drift
  const dparr = dustGeo.attributes.position.array;
  const wind = 8 + dustMat.opacity * 22;
  for (let i=0; i<N_DUST; i++){
    dparr[i*3] += dt * wind;
    if (dparr[i*3] > D.w*1.3) dparr[i*3] = -D.w*0.3;
  }
  dustGeo.attributes.position.needsUpdate = true;

  // beacon pulse
  beacon.scale.setScalar(1 + 0.35 * Math.sin(t*5));
  beaconLight.intensity = 1.5 + 0.6 * Math.sin(t*5);

  // deposit rings/beam
  depMeshes.forEach((g, i) => {
    const ring = g.children[1]; // rotating data ring
    ring.rotation.y = t*0.6 + i;
    const pulseRing = g.children[2];
    pulseRing.scale.setScalar(1 + 0.35 * Math.sin(t*2 + i));
    pulseRing.material.opacity = 0.4 + 0.35*Math.abs(Math.sin(t*2 + i));
    const beam = g.children[3];
    if (beam.userData.shader) beam.userData.shader.uniforms.time.value = t;
  });

  // terrain shader uniforms
  terrainUniforms.time.value = t;
  const maxR = Math.max(D.w, D.h) * 0.9;
  terrainUniforms.scanRadius.value = (t * 40) % maxR;
  routeMat.uniforms.time.value = t;

  // radar
  const roverRC = { row: rover.position.z, col: rover.position.x };
  drawRadar(t * 1.4, roverRC);

  // bracket overlays
  updateBrackets();

  // fly camera
  if (flying){
    controls.enabled = false;
    const look = rover.position.clone();
    const off = new THREE.Vector3(
      Math.cos(t*0.22)*26, 18,
      Math.sin(t*0.22)*26,
    );
    camera.position.copy(look.clone().add(off));
    camera.lookAt(look);
  } else {
    controls.enabled = true;
    controls.update();
  }
  composer.render();
  requestAnimationFrame(animate);
}
animate();

function resize(){
  const {w, h} = stageSize();
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  renderer.setSize(w, h);
  composer.setSize(w, h);
}
addEventListener('resize', resize);
</script>
</body></html>
"""
