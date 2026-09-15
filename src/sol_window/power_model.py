"""Turn a τ (opacity) forecast into drive-metres available per sol."""
from __future__ import annotations
import numpy as np

MARS_SOLAR_TOA = 590.0        # W/m² top-of-atmosphere at ~1.52 AU
PANEL_AREA_M2 = 2.5           # rover solar array
PANEL_EFF = 0.28
DRIVE_W = 120.0               # watts consumed while driving
DRIVE_SPEED_MPS = 0.04        # ~144 m/h — realistic MER-class
SOL_DAYLIGHT_HRS = 10.0       # useful sunlight hours per sol (mid-latitudes)


def solar_flux(tau: np.ndarray) -> np.ndarray:
    """Simple Beer–Lambert with air-mass ~ 1.5 used to attenuate TOA flux."""
    return MARS_SOLAR_TOA * np.exp(-1.5 * tau)


def drive_metres_per_sol(tau_series: np.ndarray) -> np.ndarray:
    """For each sol in the horizon, how many metres CAN we drive?"""
    flux = solar_flux(tau_series)                          # W/m²
    gen_wh = flux * PANEL_AREA_M2 * PANEL_EFF * SOL_DAYLIGHT_HRS   # Wh/sol
    drive_hours = np.clip(gen_wh / DRIVE_W, 0, SOL_DAYLIGHT_HRS)
    # SAFETY HOLD: park entirely when tau > 1.0
    drive_hours = np.where(tau_series > 1.0, 0.0, drive_hours)
    return drive_hours * 3600.0 * DRIVE_SPEED_MPS         # metres/sol
