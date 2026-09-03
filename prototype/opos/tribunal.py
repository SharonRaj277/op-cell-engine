"""The Confound Tribunal (docs/05 §F.4).

A formal proceeding whose explicit purpose is to destroy the system's own candidate
finding, using the system's full ability. The prior is that the candidate is an
artefact. Escalation requires surviving every applicable channel, and the transcript
of everything that FAILED to kill the candidate travels with the finding.
"""
from __future__ import annotations

import random
import statistics
from collections import defaultdict
from dataclasses import dataclass, field

from .fields import FeatureField
from .invariant import Candidate, InvariantResult


@dataclass
class ChannelResult:
    channel: str
    verdict: str            # SURVIVES | KILLED | UNDECIDABLE
    detail: str


@dataclass
class TribunalRecord:
    verdict: str = "SURVIVES"
    channels: list = field(default_factory=list)

    def add(self, r: ChannelResult) -> None:
        self.channels.append(r)
        if r.verdict == "KILLED" and not self.verdict.startswith("KILLED"):
            self.verdict = f"KILLED({r.channel})"   # the FIRST kill is the reason
        elif r.verdict == "UNDECIDABLE" and self.verdict == "SURVIVES":
            self.verdict = "SURVIVES_WITH_UNRESOLVED"

    def transcript(self) -> str:
        return "\n".join(f"      {c.channel:<22} {c.verdict:<12} {c.detail}"
                         for c in self.channels)


def shared_measurement_channel(cand: Candidate,
                               fields_by_specimen: dict) -> ChannelResult:
    """The dominant false positive in computational-pathology invariant hunting.

    Two features derived from the same segmentation mask share their measurement
    error, which manufactures a low-variance ratio out of nothing.
    """
    any_fields = next(iter(fields_by_specimen.values()))
    sources = {any_fields[q].mask_source for q in cand.components}
    if len(sources) < len(cand.components):
        return ChannelResult("shared_measurement", "KILLED",
                             f"components share mask source {sorted(sources)}; "
                             "correlated measurement error manufactures the invariant")
    return ChannelResult("shared_measurement", "SURVIVES",
                         f"independent mask sources {sorted(sources)}")


def noise_floor_channel(res: InvariantResult) -> ChannelResult:
    """Variance BELOW the independent-error floor is physically impossible unless the
    errors are correlated. A sharper version of the shared-measurement test."""
    if res.noise_floor_var <= 0:
        return ChannelResult("noise_floor", "UNDECIDABLE", "no measurement model available")
    ratio = res.median_within_var / res.noise_floor_var
    if ratio < 0.35:
        return ChannelResult("noise_floor", "KILLED",
                             f"observed phi-variance is {ratio:.2f}x the independent-error "
                             "floor; errors must be correlated")
    return ChannelResult("noise_floor", "SURVIVES",
                         f"observed/floor = {ratio:.2f}, consistent with independent errors")


def permutation_channel(cand: Candidate, fields_by_specimen: dict,
                        observed: float, n_perm: int = 200,
                        seed: int = 7) -> ChannelResult:
    """Shuffle phi within one component. A real functional relationship dies; an
    artefact of scale or of shared level survives."""
    rng = random.Random(seed)
    victim = cand.components[0]
    null = []
    for _ in range(n_perm):
        reds = []
        for fields in fields_by_specimen.values():
            if not all(q in fields for q in cand.components):
                continue
            shuffled = dict(fields)
            f = fields[victim]
            perm = list(f.values)
            rng.shuffle(perm)
            shuffled[victim] = FeatureField(f.quantity, f.specimen, f.grid, perm,
                                            f.sigma_log, f.mask_source, f.stratum)
            g = cand.evaluate(shuffled)
            comp = statistics.fmean([abs(w) * shuffled[q].phi_variance_log()
                                     for q, w in cand.weights])
            reds.append(comp / max(statistics.pvariance(g), 1e-12))
        null.append(statistics.median(reds))
    beat = sum(1 for v in null if v >= observed)
    if beat > 0.05 * n_perm:
        return ChannelResult("permutation_null", "KILLED",
                             f"{beat}/{n_perm} permutations reach the observed reduction")
    return ChannelResult("permutation_null", "SURVIVES",
                         f"{beat}/{n_perm} permutations reach it (observed "
                         f"reduction {observed:.1f}x)")


def stratification_channel(channel: str, res: InvariantResult,
                           fields_by_specimen: dict, min_n: int = 5,
                           min_reduction: float = 3.0) -> ChannelResult:
    """Recompute within each level of a nuisance channel. An effect present in only
    one level is a property of that instrument, not of the tissue."""
    by_level: dict[str, list[float]] = defaultdict(list)
    for spec, red in res.per_specimen_reduction.items():
        fields = fields_by_specimen[spec]
        level = str(next(iter(fields.values())).stratum.get(channel, "?"))
        by_level[level].append(red)
    usable = {lv: v for lv, v in by_level.items() if len(v) >= min_n}
    if len(usable) < 2:
        return ChannelResult(f"stratify:{channel}", "UNDECIDABLE",
                             "fewer than two levels with sufficient n")
    meds = {lv: statistics.median(v) for lv, v in usable.items()}
    failing = [lv for lv, m in meds.items() if m < min_reduction]
    detail = ", ".join(f"{lv}: {m:.1f}x (n={len(usable[lv])})" for lv, m in sorted(meds.items()))
    if failing:
        return ChannelResult(f"stratify:{channel}", "KILLED",
                             f"absent in level(s) {failing} -- {detail}")
    return ChannelResult(f"stratify:{channel}", "SURVIVES", detail)


def run_invariant_tribunal(res: InvariantResult, fields_by_specimen: dict,
                           channels: list[str]) -> TribunalRecord:
    rec = TribunalRecord()
    rec.add(shared_measurement_channel(res.candidate, fields_by_specimen))
    rec.add(noise_floor_channel(res))
    rec.add(permutation_channel(res.candidate, fields_by_specimen,
                                res.median_variance_reduction))
    for ch in channels:
        rec.add(stratification_channel(ch, res, fields_by_specimen))
    return rec


# --- association testing, with the same adversarial posture ----------------------

def association_by_stratum(values: dict, labels: dict, strata: dict,
                           channel: str | None = None) -> dict:
    """Mean difference in a per-specimen quantity between label groups, overall and
    within each level of a nuisance channel."""
    groups: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for spec, v in values.items():
        level = "ALL" if channel is None else str(strata[spec].get(channel, "?"))
        groups[level][labels[spec]].append(v)
        groups["ALL"][labels[spec]].append(v)
    out = {}
    for level, g in groups.items():
        if len(g) == 2 and all(len(v) >= 3 for v in g.values()):
            (_, a), (_, b) = sorted(g.items())
            out[level] = statistics.fmean(b) - statistics.fmean(a)
    return out
