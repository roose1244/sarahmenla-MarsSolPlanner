"""Interactive 3D visualisation of the plan.

Renders:
  - Mars terrain as a 3D surface (colour = elevation, opacity dimmed on sand/rocks)
  - The planned route as a red line hovering just above the surface
  - Water-deposit pins as cyan star markers with hover tooltips
  - A start marker

Output is a self-contained HTML file the judges can rotate/zoom in a browser.
"""
from __future__ import annotations
import numpy as np
import plotly.graph_objects as go
from pathlib import Path


def render_3d(elev, tclass, route, deposits, start, tau,
              save: str | Path = "demo/plan_3d.html",
              title: str = "Sol-Window Planner — interactive 3D"):
    H, W = elev.shape

    # 1) Terrain surface -----------------------------------------------------
    surf = go.Surface(
        z=elev, colorscale="YlOrBr", showscale=False,
        contours={"z": {"show": True, "usecolormap": True, "highlightcolor": "orange",
                        "project": {"z": True}}},
        lighting=dict(ambient=0.55, diffuse=0.7, specular=0.15),
        name="Mars terrain",
    )

    # 2) Route as a 3D line just above the surface --------------------------
    ys = np.array([p[0] for p in route.path])
    xs = np.array([p[1] for p in route.path])
    zs = np.array([elev[r, c] for r, c in route.path]) + 3.0  # lifted 3 m
    sols = np.array(route.sols)
    hover = [f"Sol {s}<br>(row {r}, col {c})<br>z={z:.0f} m"
             for s, r, c, z in zip(sols, ys, xs, zs)]
    route_line = go.Scatter3d(
        x=xs, y=ys, z=zs, mode="lines+markers",
        line=dict(color="crimson", width=6),
        marker=dict(size=2.5, color=sols, colorscale="Reds",
                    showscale=True,
                    colorbar=dict(title="Sol", thickness=12, x=1.0)),
        hovertext=hover, hoverinfo="text",
        name="Planned route",
    )

    # 3) Deposit pins -------------------------------------------------------
    dep_hover = [f"{r['name']}<br>Depth {r.depth_m:.1f} m<br>"
                 f"Yield {r.yield_kg_m2:.0f} kg/m²"
                 for _, r in deposits.iterrows()]
    dep_z = np.array([elev[int(r.row), int(r.col)] for _, r in deposits.iterrows()]) + 8
    deposit_pins = go.Scatter3d(
        x=deposits.col, y=deposits.row, z=dep_z,
        mode="markers+text",
        marker=dict(size=8, color="cyan", symbol="diamond",
                    line=dict(color="black", width=1)),
        text=[n.split(" ")[0] for n in deposits["name"]],
        textposition="top center", textfont=dict(color="white", size=11),
        hovertext=dep_hover, hoverinfo="text",
        name="Water deposits",
    )

    # 4) Start marker -------------------------------------------------------
    sr, sc = start
    start_marker = go.Scatter3d(
        x=[sc], y=[sr], z=[elev[sr, sc] + 8],
        mode="markers+text",
        marker=dict(size=9, color="lime", symbol="diamond",
                    line=dict(color="black", width=1)),
        text=["START"], textposition="top center",
        textfont=dict(color="white", size=11),
        name="Rover start",
    )

    fig = go.Figure(data=[surf, route_line, deposit_pins, start_marker])
    fig.update_layout(
        title=dict(text=f"{title}<br><sup>ETA {route.eta_sols:.1f} sols · "
                        f"{route.total_m/1000:.1f} km · idled {route.idle_sols} sols "
                        f"through storms</sup>",
                   x=0.5),
        template="plotly_dark",
        scene=dict(
            xaxis_title="col (px)", yaxis_title="row (px)", zaxis_title="elev (m)",
            aspectmode="manual", aspectratio=dict(x=1, y=1, z=0.25),
            camera=dict(eye=dict(x=1.6, y=-1.6, z=1.2)),
            bgcolor="black",
        ),
        margin=dict(l=0, r=0, t=70, b=0),
        legend=dict(x=0.02, y=0.98, bgcolor="rgba(0,0,0,0.4)"),
    )
    Path(save).parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(save, include_plotlyjs="cdn", full_html=True)
    return save
