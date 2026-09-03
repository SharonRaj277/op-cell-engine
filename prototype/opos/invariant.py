"""The invariant hunter (docs/05 §G.3, Mode 2).

Conservation laws and structural relationships are not found by looking for
correlation. They are found by looking for combinations whose variance collapses:
if A(phi) and B(phi) each vary a great deal and g(A,B) barely varies at all, g is
capturing something neither feature does alone.

The grammar is restricted to dimensionless-monomial candidates -- products of integer
powers, scored in log space. That restriction is the design, not a shortcut: it makes
the search space small, the results interpretable, and dimensional pruning trivial.
"""
from __future__ import annotations

import itertools
import math
import statistics
from dataclasses import dataclass, field

from .fields import FeatureField


@dataclass(frozen=True)
class Candidate:
    weights: tuple[tuple[str, int], ...]   # (quantity, integer power)

    @property
    def complexity(self) -> int:
        return sum(abs(w) for _, w in self.weights)

    @property
    def components(self) -> tuple[str, ...]:
        return tuple(q for q, w in self.weights if w != 0)

    def evaluate(self, fields: dict[str, FeatureField]) -> list[float]:
        """log g(phi) = sum_i w_i * log X_i(phi)"""
        n = len(next(iter(fields.values())).grid)
        out = [0.0] * n
        for q, w in self.weights:
            lv = fields[q].log_values()
            for k in range(n):
                out[k] += w * lv[k]
        return out

    def noise_floor_var(self, fields: dict[str, FeatureField]) -> float:
        """Variance the candidate would have from measurement noise ALONE, assuming
        independent errors. A candidate whose observed variance falls well below this
        has correlated measurement error -- a manufactured invariant."""
        return sum((w ** 2) * (fields[q].sigma_log ** 2) for q, w in self.weights)

    def __str__(self) -> str:
        parts = []
        for q, w in self.weights:
            if w == 0:
                continue
            parts.append(f"{'+' if w > 0 else '-'}{abs(w) if abs(w) != 1 else ''}log {q}")
        s = " ".join(parts)
        return s[1:].strip() if s.startswith("+") else s


@dataclass
class InvariantResult:
    candidate: Candidate
    score: float
    median_variance_reduction: float
    median_within_var: float
    noise_floor_var: float
    cross_specimen_var: float
    n_specimens: int
    per_specimen_reduction: dict = field(default_factory=dict)


def enumerate_candidates(quantities: list[str], max_power: int = 1,
                         max_complexity: int = 2) -> list[Candidate]:
    """All dimensionless-monomial combinations of >=2 distinct quantities.

    Trivial invariants (g = X/X) are impossible by construction; degenerate ones are
    pruned by the >=2-distinct-components rule and by the complexity budget.
    """
    powers = [p for p in range(-max_power, max_power + 1)]
    out: list[Candidate] = []
    for k in (2, 3):
        for combo in itertools.combinations(sorted(quantities), k):
            for ws in itertools.product(powers, repeat=k):
                if any(w == 0 for w in ws):
                    continue
                if sum(abs(w) for w in ws) > max_complexity + k - 2:
                    continue
                # canonical sign: drop the global negation duplicate
                if ws[0] < 0:
                    continue
                out.append(Candidate(tuple(zip(combo, ws))))
    return out


def hunt(fields_by_specimen: dict[str, dict[str, FeatureField]],
         quantities: list[str],
         complexity_penalty: float = 0.35,
         min_specimens: int = 5) -> list[InvariantResult]:
    """Rank candidates by how far their phi-variance falls below their components'."""
    results: list[InvariantResult] = []
    for cand in enumerate_candidates(quantities):
        reductions, withins, levels = {}, [], []
        floor = 0.0
        for spec, fields in fields_by_specimen.items():
            if not all(q in fields for q in cand.components):
                continue
            g = cand.evaluate(fields)
            v_within = statistics.pvariance(g)
            floor = cand.noise_floor_var(fields)
            comp_var = statistics.fmean(
                [abs(w) * fields[q].phi_variance_log() for q, w in cand.weights])
            red = comp_var / max(v_within, 1e-12)
            reductions[spec] = red
            withins.append(v_within)
            levels.append(statistics.fmean(g))
        if len(reductions) < min_specimens:
            continue
        med_red = statistics.median(reductions.values())
        results.append(InvariantResult(
            candidate=cand,
            score=math.log(max(med_red, 1e-12)) - complexity_penalty * cand.complexity,
            median_variance_reduction=med_red,
            median_within_var=statistics.median(withins),
            noise_floor_var=floor,
            cross_specimen_var=statistics.pvariance(levels) if len(levels) > 1 else 0.0,
            n_specimens=len(reductions),
            per_specimen_reduction=reductions,
        ))
    results.sort(key=lambda r: r.score, reverse=True)
    return results
