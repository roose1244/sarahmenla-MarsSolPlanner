"""Static per-cell traverse cost (metres of 'effective distance' per cell)."""
from __future__ import annotations
import numpy as np

CELL_M = 20.0  # metres per raster cell — 5×5 km area over a 256² grid

# AI4Mars class → energy multiplier (unitless)
TERRAIN_MULT = {0: 1.0,   # soil (nominal)
                1: 1.3,   # bedrock
                2: 2.5,   # sand — high slip
                3: 9.9}   # big rock — effectively impassable


def slope_deg(elev: np.ndarray, cell_m: float = CELL_M) -> np.ndarray:
    gy, gx = np.gradient(elev, cell_m)
    return np.degrees(np.arctan(np.hypot(gx, gy)))


def build_cost(elev: np.ndarray, tclass: np.ndarray,
               slope_hard_limit_deg: float = 25.0) -> np.ndarray:
    """Cost per cell. Impassable cells get np.inf."""
    slope = slope_deg(elev)
    slope_cost = 1.0 + (slope / 5.0) ** 2   # smooth up to ~5°, steep after

    mult = np.vectorize(TERRAIN_MULT.get)(tclass).astype(np.float32)
    cost = CELL_M * slope_cost * mult

    cost[slope > slope_hard_limit_deg] = np.inf
    cost[tclass == 3] = np.inf   # big rocks
    return cost.astype(np.float32)
