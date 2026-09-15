"""One tiny smoke test — the pipeline must run end-to-end."""
from sol_window import data_io, cost_map, power_model, planner


def test_pipeline_runs():
    elev = data_io.load_elevation(shape=(64, 64))
    tclass = data_io.load_terrain_class(shape=(64, 64))
    tau = data_io.load_tau_forecast(10)
    cost = cost_map.build_cost(elev, tclass)
    dmps = power_model.drive_metres_per_sol(tau)
    r = planner.plan(cost, (2, 2), (60, 60), dmps)
    assert r is not None
    assert r.eta_sols >= 0
    assert len(r.path) > 1
