"""Matplotlib visualisation — the demo money shot."""
from __future__ import annotations
import matplotlib.pyplot as plt
import numpy as np


def plot_plan(elev, tclass, tau, route, deposits, start, save=None):
    fig = plt.figure(figsize=(12, 6))

    # LEFT: terrain + route
    ax1 = fig.add_subplot(1, 2, 1)
    ax1.imshow(elev, cmap="terrain")
    sand = np.where(tclass == 2)
    ax1.scatter(sand[1], sand[0], s=1, c="khaki", alpha=0.3, label="sand")
    rocks = np.where(tclass == 3)
    ax1.scatter(rocks[1], rocks[0], s=6, c="k", label="rocks")

    ys = [p[0] for p in route.path]
    xs = [p[1] for p in route.path]
    ax1.plot(xs, ys, "r-", lw=2, label="planned route")
    ax1.scatter([start[1]], [start[0]], marker="^", s=120, c="white",
                edgecolors="k", label="start")
    for _, d in deposits.iterrows():
        ax1.scatter([d.col], [d.row], marker="*", s=140, c="cyan",
                    edgecolors="k")
        ax1.annotate(d["name"].split(" ")[0], (d.col, d.row),
                     color="white", fontsize=8)
    ax1.legend(loc="lower right", fontsize=8)
    ax1.set_title("Route on MOLA + AI4Mars overlay")

    # RIGHT: τ time series + drive-hours actually used
    ax2 = fig.add_subplot(1, 2, 2)
    sols = np.arange(len(tau))
    ax2.bar(sols, tau, color="sandybrown", alpha=0.7, label="τ per sol")
    used = [route.sols.count(s) for s in sols]
    ax2.step(sols, np.array(used) / max(max(used), 1) * tau.max(),
             where="mid", color="crimson", lw=2, label="driving activity")
    ax2.axvspan(7, 10, color="red", alpha=0.15, label="dust storm")
    ax2.set_xlabel("Sol")
    ax2.set_ylabel("τ (opacity)")
    ax2.set_title(f"ETA {route.eta_sols:.1f} sols · {route.total_m/1000:.1f} km"
                  f" · idled {route.idle_sols} sols")
    ax2.legend(loc="upper right", fontsize=8)

    plt.tight_layout()
    if save:
        plt.savefig(save, dpi=140)
    return fig
