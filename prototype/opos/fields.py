"""Feature fields over the canonical tissue frame (docs/02 §2.4).

A feature is a FUNCTION of normalised epithelial depth phi, with uncertainty and with
the instrument state that produced it attached. Collapsing to a per-slide scalar is
how the field currently loses the relationships it is looking for.
"""
from __future__ import annotations

import math
import statistics
from dataclasses import dataclass


@dataclass
class FeatureField:
    quantity: str
    specimen: str
    grid: list[float]              # phi knots, 0 = basement membrane, 1 = surface
    values: list[float]            # f(phi), strictly positive for log-space work
    sigma_log: float               # measurement sd in log space, from the measurement model
    mask_source: str               # which segmentation mask this was derived from
    stratum: dict                  # nuisance channel values (scanner, stain lot, lab, ...)

    def log_values(self) -> list[float]:
        return [math.log(v) for v in self.values]

    def phi_variance_log(self) -> float:
        return statistics.pvariance(self.log_values())


def slope_vs_phi(f: FeatureField) -> float:
    """Ordinary least-squares slope of the field against phi."""
    xs, ys = f.grid, f.values
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs) or 1e-12
    return num / den
