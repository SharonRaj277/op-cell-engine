"""The double-entry discrepancy ledger and anytime-valid evidence (docs/05 §F.2-F.3).

Every unit of surprise is posted to exactly one account: MECHANISM, NUISANCE, or
UNEXPLAINED. The books must balance. What matters about an unexplained account is not
its balance but whether its growth is structured.
"""
from __future__ import annotations

import math
import statistics
from collections import defaultdict
from dataclasses import dataclass, field


class BalanceError(Exception):
    """Surprise was silently discarded. The kernel halts rather than proceed."""


@dataclass(frozen=True)
class Posting:
    specimen: str
    quantity: str
    total_surprise: float          # nats
    to_mechanism: float
    to_nuisance: float
    to_unexplained: float
    account_key: str
    signed_residual: float         # direction matters for the structure score
    sigma: float                   # measurement sd, from the measurement model
    stratum: dict                  # nuisance channel values for this specimen

    def check(self, tol: float = 1e-9) -> None:
        s = self.to_mechanism + self.to_nuisance + self.to_unexplained
        if abs(s - self.total_surprise) > tol:
            raise BalanceError(
                f"{self.specimen}/{self.quantity}: {s:.6f} posted vs "
                f"{self.total_surprise:.6f} observed")


class EProcess:
    """A test martingale for a one-sided sign test.

    Under the null that the residual sign is a fair coin, E[e] = 1 at every time, so
    the process may be inspected continuously and stopped at any threshold without
    correction. This is why the architecture uses e-values rather than p-values: the
    system never stops looking.
    """

    def __init__(self, lam: float = 0.5) -> None:
        self.lam = lam
        self.e = 1.0
        self.n = 0

    def update(self, success: bool) -> float:
        self.e *= 1.0 + self.lam * (1.0 if success else -1.0)
        self.n += 1
        return self.e


@dataclass
class UnexplainedAccount:
    key: str
    balance: float = 0.0
    postings: list = field(default_factory=list)
    e_process: EProcess = field(default_factory=EProcess)

    def post(self, p: Posting) -> None:
        self.balance += p.to_unexplained
        self.postings.append(p)
        self.e_process.update(p.signed_residual > 0)

    # --- structure score components (docs/05 §F.3) -------------------------------

    def directionality(self) -> float:
        """Anytime-valid evidence that the error is systematically signed.

        e > 1 is evidence for a systematic direction; e << 1 is evidence against one,
        i.e. the account is accumulating unmodelled VARIANCE rather than bias. That
        distinction routes the account to a different discovery mode.
        """
        return self.e_process.e

    def stratum_concentration(self) -> dict:
        """SIGNED mean residual per level of each nuisance channel, scaled by the
        residual RMS.

        Signed, not absolute: a batch effect that pushes one scanner up and the other
        down is symmetric in magnitude, so an absolute-value test cancels it exactly
        and reports nothing. That mistake is easy to make and it silently disables the
        highest-yield channel in the tribunal.
        """
        out: dict[str, dict] = {}
        if not self.postings:
            return out
        rms = math.sqrt(statistics.fmean([p.signed_residual ** 2 for p in self.postings]))
        rms = rms or 1e-9
        chans: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
        for p in self.postings:
            for ch, val in p.stratum.items():
                chans[ch][str(val)].append(p.signed_residual)
        for ch, levels in chans.items():
            means = {lv: statistics.fmean(v) for lv, v in levels.items() if len(v) >= 5}
            if len(means) > 1:
                spread = max(means.values()) - min(means.values())
                out[ch] = {"means": means, "relative_spread": spread / rms}
        return out

    def noise_floor_ratio(self) -> float:
        """Residual RMS relative to what the measurement model says is possible."""
        if not self.postings:
            return 0.0
        rms = math.sqrt(statistics.fmean([p.signed_residual ** 2 for p in self.postings]))
        sigma = statistics.fmean([p.sigma for p in self.postings])
        return rms / sigma if sigma > 0 else float("inf")


class Ledger:
    def __init__(self) -> None:
        self.accounts: dict[str, UnexplainedAccount] = {}
        self.mechanism_total = 0.0
        self.nuisance_total = 0.0
        self.observed_total = 0.0

    def post(self, p: Posting) -> None:
        p.check()
        self.observed_total += p.total_surprise
        self.mechanism_total += p.to_mechanism
        self.nuisance_total += p.to_nuisance
        acct = self.accounts.setdefault(p.account_key, UnexplainedAccount(p.account_key))
        acct.post(p)

    def close(self, tol: float = 1e-6) -> None:
        unexplained = sum(a.balance for a in self.accounts.values())
        total = self.mechanism_total + self.nuisance_total + unexplained
        if abs(total - self.observed_total) > tol:
            raise BalanceError(f"ledger does not balance: {total} vs {self.observed_total}")

    def summary(self) -> str:
        unexplained = sum(a.balance for a in self.accounts.values())
        return (f"surprise {self.observed_total:8.2f} nats  ="
                f"  mechanism {self.mechanism_total:7.2f}"
                f" + nuisance {self.nuisance_total:7.2f}"
                f" + unexplained {unexplained:7.2f}")
