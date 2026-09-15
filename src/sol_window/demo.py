"""End-to-end CLI. This is what you run in the demo.

    python -m sol_window.demo
"""
from __future__ import annotations
import argparse
from pathlib import Path
from . import data_io, cost_map, power_model, planner, viz, viz3d, viz_three, viz_dashboard, results, llm_agent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="10,10", help="row,col start pixel")
    ap.add_argument("--horizon-sols", type=int, default=20)
    ap.add_argument("--query", default="Find shallow water within 20 sols, avoid storms.")
    ap.add_argument("--out", default="demo/plan.png")
    ap.add_argument("--out-3d", default="demo/plan_3d.html")
    ap.add_argument("--out-three", default="demo/plan_three.html")
    ap.add_argument("--no-3d", action="store_true", help="skip 3D HTML render")
    ap.add_argument("--no-three", action="store_true", help="skip Three.js render")
    args = ap.parse_args()

    start = tuple(int(x) for x in args.start.split(","))

    print(">> Loading data layers …")
    elev = data_io.load_elevation()
    tclass = data_io.load_terrain_class()
    tau = data_io.load_tau_forecast(args.horizon_sols)
    deposits = data_io.load_water_deposits()

    print(">> Building cost map …")
    cost = cost_map.build_cost(elev, tclass)
    drive_m_per_sol = power_model.drive_metres_per_sol(tau)

    print(">> Planning …")
    ranked = planner.rank_deposits(cost, start, deposits, drive_m_per_sol)
    if not ranked:
        print("!! No reachable deposit — relax constraints or extend horizon.")
        return

    top = ranked[0]
    print(f">> Winner: {top['name']}  ETA {top['route'].eta_sols:.1f} sols")

    print(">> Writing live results (demo/plan.json) …")
    payload = results.build_payload(
        elev=elev, tclass=tclass, tau=tau,
        ranked=ranked, start=start, query=args.query,
    )
    results.write_json(payload, "demo/plan.json")

    print(">> Narrating …")
    print(llm_agent.narrate_plan(args.query, ranked, tau))

    print(">> Rendering …")
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    viz.plot_plan(elev, tclass, tau, top["route"], deposits, start, save=args.out)
    print(f">> Wrote {args.out}")

    if not args.no_3d:
        print(">> Rendering interactive 3D …")
        viz3d.render_3d(elev, tclass, top["route"], deposits, start, tau,
                        save=args.out_3d)
        print(f">> Wrote {args.out_3d}  (open in a browser)")

    if not args.no_three:
        print(">> Rendering WebGL Three.js scene …")
        viz_three.render_three(elev, tclass, tau, top["route"], deposits, start,
                               save=args.out_three)
        print(f">> Wrote {args.out_three}  (open in a browser for the hero demo)")

    print(">> Writing live dashboard …")
    viz_dashboard.write("demo/dashboard.html")
    print(">> Wrote demo/dashboard.html  (open in a browser — auto-refreshes)")


if __name__ == "__main__":
    main()
