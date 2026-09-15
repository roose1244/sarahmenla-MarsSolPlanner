"""Live dashboard: one HTML file that reads demo/plan.json every 2 s and
re-renders the mission-timeline + stats. No re-generation needed after tweaks —
just refresh the browser, or leave it open and it auto-refreshes.
"""
from __future__ import annotations
from pathlib import Path


HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Sol-Window Planner · Live Dashboard</title>
<style>
  :root {
    --bg: #0f0806; --panel: #1a0f0a; --border: #6b3f22;
    --text: #e8d7b7; --text-dim: #c9a37c; --text-fade: #a07a55;
    --accent: #ffb060; --route: #ff5040;
    --coral-50: #3a1a10; --coral-80: #ff9b83;
    --green-50: #123420; --green-80: #8ff0b2;
    --blue-50: #0f2036; --blue-80: #8fc0ff;
  }
  * { box-sizing: border-box; }
  html, body { margin:0; padding:0; background:var(--bg); color:var(--text);
               font-family:-apple-system, BlinkMacSystemFont, "Segoe UI",
               Helvetica, Arial, sans-serif; }
  .wrap { max-width: 900px; margin: 0 auto; padding: 24px; }
  header { display:flex; justify-content:space-between; align-items:center;
           padding-bottom:16px; border-bottom:1px solid var(--border); }
  h1 { margin:0; font-size:18px; font-weight:600; color:#ffd7a8;
       letter-spacing:0.02em; }
  .sub { font-size:12px; color:var(--text-dim); margin-top:4px; }
  .live-pill { padding:5px 12px; border-radius:999px; font-size:11px;
               font-weight:600; letter-spacing:0.08em; text-transform:uppercase;
               background:var(--green-50); color:var(--green-80);
               border:1px solid #1f5030; }
  .live-pill.stale { background:var(--coral-50); color:var(--coral-80); }
  .stats { display:grid; grid-template-columns:repeat(5, 1fr); gap:12px;
           margin: 20px 0 24px; }
  .stat { padding:14px; background:var(--panel); border:1px solid var(--border);
          border-radius:10px; text-align:center; }
  .stat b { display:block; font-size:22px; font-weight:600; color:#ffd7a8;
            font-variant-numeric:tabular-nums; }
  .stat small { display:block; margin-top:4px; font-size:11px;
                color:var(--text-dim); text-transform:uppercase;
                letter-spacing:0.05em; }
  h2 { font-size:14px; font-weight:600; margin: 20px 0 10px;
       color:var(--text); }
  .rows { display:grid; gap:3px; }
  .row { display:grid; grid-template-columns: 90px 1fr 80px;
         align-items:center; gap:14px; padding:10px 12px;
         background:var(--panel); border:1px solid var(--border);
         border-radius:8px; }
  .row .d b { display:block; font-weight:600; font-size:13px; }
  .row .d small { display:block; font-size:11px; color:var(--text-dim);
                  margin-top:3px; font-variant-numeric:tabular-nums; }
  .row .body b { display:block; font-weight:600; font-size:13px; }
  .row .body small { display:block; font-size:11px; color:var(--text-dim);
                     margin-top:3px; }
  .row .pill { justify-self:end; font-size:10px; font-weight:700;
               padding:5px 12px; border-radius:999px; letter-spacing:0.08em;
               text-transform:uppercase; }
  .pill.drive  { background:var(--blue-50);  color:var(--blue-80);  }
  .pill.hold   { background:var(--coral-50); color:var(--coral-80);
                 animation:pulse 1.6s ease-in-out infinite; }
  .pill.arrive { background:var(--green-50); color:var(--green-80); }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.55} }
  .row.hl { border-color:#8a4020; background:linear-gradient(0deg,
              rgba(255,80,64,0.05), rgba(255,80,64,0.05)), var(--panel); }
  .dep { display:grid; grid-template-columns:36px 1fr 90px;
         align-items:center; gap:14px; padding:10px 12px;
         background:var(--panel); border:1px solid var(--border);
         border-radius:8px; }
  .dep .rank { text-align:center; font-size:16px; font-weight:600;
               color:var(--text-dim); }
  .dep.winner { border-color:#1f5030; }
  .dep.winner .rank { color:var(--green-80); }
  .dep .body b { display:block; font-weight:600; font-size:13px; }
  .dep .body small { display:block; font-size:11px; color:var(--text-dim);
                     margin-top:3px; }
  .dep .eta { text-align:right; }
  .dep .eta b { display:block; font-size:15px; font-weight:600;
                font-variant-numeric:tabular-nums; }
  .dep .eta small { font-size:10px; color:var(--text-dim);
                    text-transform:uppercase; letter-spacing:0.05em; }
  footer { margin-top: 20px; padding-top: 12px;
           border-top:1px solid var(--border); font-size:11px;
           color:var(--text-fade); font-variant-numeric:tabular-nums; }
  code { background:#000; padding:1px 5px; border-radius:3px;
         color:var(--accent); font-size:11px; }
  .err { padding:16px; border:1px solid var(--coral-80);
         border-radius:8px; color:var(--coral-80); background:var(--coral-50); }
  @media (max-width: 640px) {
    .stats { grid-template-columns:repeat(2, 1fr); }
  }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div>
      <h1 id="title">Sol-Window Planner · Live</h1>
      <div class="sub" id="subtitle">Loading …</div>
    </div>
    <span class="live-pill" id="pill">● LIVE</span>
  </header>

  <div id="content"></div>

  <footer>
    Reads <code>demo/plan.json</code> · re-run <code>python -m sol_window.demo</code>
    to refresh · this page auto-polls every 2 s
  </footer>
</div>

<script>
const el = (id) => document.getElementById(id);
let lastMtime = 0;

async function fetchPlan() {
  try {
    const res = await fetch('plan.json?t=' + Date.now(), {cache:'no-store'});
    if (!res.ok) throw new Error('HTTP ' + res.status);
    return await res.json();
  } catch (e) {
    return { _err: e.message };
  }
}

function fmt(n, d=1) { return (Math.round(n * Math.pow(10, d)) / Math.pow(10, d)).toFixed(d); }

function render(p) {
  if (p._err) {
    el('content').innerHTML = `<div class="err">
      Cannot read <code>plan.json</code> yet — run
      <code>python -m sol_window.demo</code> first.
      <br><small>${p._err}</small>
    </div>`;
    el('pill').className = 'live-pill stale';
    el('pill').textContent = '● WAITING';
    return;
  }
  el('pill').className = 'live-pill';
  el('pill').textContent = '● LIVE';

  const w = p.winner;
  el('subtitle').textContent =
    `Start (${p.start.row}, ${p.start.col}) → ${w.name} · horizon ${p.horizon_sols} sols`;

  let html = `
    <div class="stats">
      <div class="stat"><b>${fmt(w.eta_sols)}</b><small>ETA sols</small></div>
      <div class="stat"><b>${fmt(w.distance_km)}</b><small>km driven</small></div>
      <div class="stat"><b>${w.idle_sols}</b><small>sols idled</small></div>
      <div class="stat"><b>${Math.round(w.yield_kg_m2)}</b><small>kg/m² yield</small></div>
      <div class="stat"><b>${fmt(w.peak_tau, 2)}</b><small>peak τ</small></div>
    </div>

    <h2>Sol-by-sol timeline</h2>
    <div class="rows">
      ${p.timeline.map(ev => `
        <div class="row ${ev.status === 'hold' ? 'hl' : ''}">
          <span class="d">
            <b>Sol ${ev.sol}</b>
            <small>τ ${fmt(ev.tau, 2)}</small>
          </span>
          <span class="body">
            <b>${ev.status === 'hold'
                ? (ev.tau > 1.3 ? 'Storm peak — remain anchored'
                   : 'Dust storm — safety hold engaged')
                : ev.status === 'arrive'
                ? 'Arrival · begin ice sampling'
                : ev.sol === 0 ? 'Depart start pad'
                : 'Continue traverse'}</b>
            <small>waypoint (row ${ev.row}, col ${ev.col})${
              ev.status === 'hold' ? ' · panels dimmed, thermal loop nominal' :
              ev.status === 'arrive' ? ` · ${Math.round(w.yield_kg_m2)} kg/m² shallow ice` :
              ''
            }</small>
          </span>
          <span class="pill ${ev.status}">${ev.status}</span>
        </div>
      `).join('')}
    </div>

    <h2>Ranked deposit targets</h2>
    <div class="rows">
      ${p.ranked_deposits.map((d, i) => `
        <div class="dep ${i === 0 ? 'winner' : ''}">
          <span class="rank">${i + 1}</span>
          <span class="body">
            <b>${d.name}</b>
            <small>row ${d.row}, col ${d.col} · yield ${Math.round(d.yield_kg_m2)} kg/m² · ${fmt(d.distance_km)} km</small>
          </span>
          <span class="eta">
            <b>${fmt(d.eta_sols)}</b>
            <small>sols</small>
          </span>
        </div>
      `).join('')}
    </div>
  `;
  el('content').innerHTML = html;
}

async function tick() {
  const p = await fetchPlan();
  render(p);
}
tick();
setInterval(tick, 2000);
</script>
</body>
</html>
"""


def write(save: str = "demo/dashboard.html"):
    Path(save).parent.mkdir(parents=True, exist_ok=True)
    Path(save).write_text(HTML)
    return save
