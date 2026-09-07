"""The Calibration Range (docs/05 §F.7, roadmap milestone M5).

You cannot trust a discovery engine you have not measured. The Range plants known
phenomena and known artefacts in cohorts the kernel has never seen, runs the full
hunt-and-tribunal pipeline, and reports three numbers:

    sensitivity        how often a planted relationship is found AND survives
    false discovery    how often a pure-null cohort yields a surviving candidate
    artefact kill rate how often a planted artefact is correctly destroyed

These are the promotion gates in docs/10. A discovery pipeline whose false-discovery
rate has never been measured should not be allowed to emit a finding, which is why
M5 precedes M7 in the roadmap and why this module exists before any literature layer.
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass, field

from .invariant import hunt
from .synthetic import CohortSpec, generate
from .tribunal import run_invariant_tribunal

QUANTITIES = ["nc_ratio", "nuclear_area", "chromatin", "neighbour_dist"]

#: A survivor counts as the planted relationship if it relates chromatin to the
#: nc_ratio/nuclear_area pair, which are collinear proxies for the same underlying
#: differentiation gradient. Anything else surviving is a false discovery.
_TRUE_SET = {"nc_ratio", "nuclear_area", "chromatin"}


def _classify(components: tuple) -> str:
    cs = set(components)
    if not cs <= _TRUE_SET:
        return "false"
    if "chromatin" in cs and cs & {"nc_ratio", "nuclear_area"}:
        return "true"
    return "artefact"        # nc_ratio vs nuclear_area alone: the manufactured one


@dataclass
class TrialResult:
    found_true: bool
    n_false_survivors: int
    artefact_survived: bool
    top_candidate: str
    top_classification: str


@dataclass
class ConditionResult:
    name: str
    n_trials: int
    trials: list = field(default_factory=list)

    @property
    def sensitivity(self) -> float:
        return statistics.fmean([1.0 if t.found_true else 0.0 for t in self.trials])

    @property
    def false_discovery_rate(self) -> float:
        """Fraction of trials in which at least one non-planted candidate survived."""
        return statistics.fmean([1.0 if t.n_false_survivors else 0.0 for t in self.trials])

    @property
    def artefact_kill_rate(self) -> float:
        return statistics.fmean([0.0 if t.artefact_survived else 1.0 for t in self.trials])


def run_trial(spec: CohortSpec, top_k: int = 4, n_perm: int = 40,
              alpha: float = 0.05, min_reduction: float = 12.0,
              channels: tuple = ("scanner", "stain_lot")) -> TrialResult:
    fields, _, _ = generate(spec)
    results = hunt(fields, QUANTITIES, min_specimens=min(5, spec.n_specimens))
    found_true, n_false, artefact_survived = False, 0, False
    top_cand, top_cls = "-", "-"

    for rank, res in enumerate(results[:top_k]):
        cls = _classify(res.candidate.components)
        if rank == 0:
            top_cand, top_cls = str(res.candidate), cls
        rec = run_invariant_tribunal(res, fields, list(channels), n_perm=n_perm,
                                     alpha=alpha / top_k,   # spend the budget once
                                     min_reduction=min_reduction)
        if not rec.verdict.startswith("SURVIVES"):
            continue
        if cls == "true":
            found_true = True
        elif cls == "artefact":
            artefact_survived = True
        else:
            n_false += 1
    return TrialResult(found_true, n_false, artefact_survived, top_cand, top_cls)


def run_range(n_trials: int = 12, n_specimens: int = 30,
              couplings: tuple = (1.0, 0.9, 0.75, 0.5, 0.0),
              base_seed: int = 5000, top_k: int = 4,
              n_perm: int = 40, alpha: float = 0.05,
              min_reduction: float = 12.0) -> list[ConditionResult]:
    """Sweep the planted effect size. coupling=0.0 with area_coupling=0.0 is the
    pure-null condition: nothing is planted, so anything that survives is false."""
    out = []
    for c in couplings:
        null = (c == 0.0)
        cond = ConditionResult(
            name=("pure null (nothing planted)" if null else f"coupling {c:.2f}"),
            n_trials=n_trials)
        for t in range(n_trials):
            spec = CohortSpec(n_specimens=n_specimens, coupling=c,
                              area_coupling=0.0 if null else 1.0,
                              inject_shared_mask=not null,
                              seed=base_seed + 977 * t + int(1000 * c))
            cond.trials.append(run_trial(spec, top_k=top_k, n_perm=n_perm,
                                         alpha=alpha, min_reduction=min_reduction))
        out.append(cond)
    return out


def report(conditions: list[ConditionResult]) -> str:
    lines = [f"  {'condition':<32}{'trials':>7}{'sensitivity':>13}"
             f"{'false disc.':>13}{'artefact kill':>15}",
             f"  {'-' * 80}"]
    for c in conditions:
        planted = "pure null" not in c.name
        sens = f"{c.sensitivity:>12.0%}" if planted else f"{'n/a':>12}"
        kill = f"{c.artefact_kill_rate:>14.0%}" if planted else f"{'n/a':>14}"
        lines.append(f"  {c.name:<32}{c.n_trials:>7}{sens}"
                     f"{c.false_discovery_rate:>12.0%}{kill}")
    return "\n".join(lines)
