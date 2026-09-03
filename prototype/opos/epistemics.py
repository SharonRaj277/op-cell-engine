"""The epistemic type lattice (docs/02 §2.1).

Not a confidence score: an ordered lattice with propagation rules borrowed from
information-flow type systems. The output of a reasoning step can never be stronger
than its weakest input, and the ceiling for each operator is fixed by the operator,
not by the caller.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Flag, IntEnum, auto


class Epistemic(IntEnum):
    REFUTED = 0
    SPECULATIVE = 1
    CONJECTURED = 2
    REPORTED = 3
    INFERRED = 4
    DERIVED = 5
    MEASURED = 6
    ESTABLISHED = 7

    def __str__(self) -> str:          # pragma: no cover - cosmetic
        return self.name


class Flags(Flag):
    NONE = 0
    SINGLE_INSTRUMENT = auto()
    SINGLE_SITE = auto()
    SYSTEM_AUTHORED = auto()
    CONFOUND_UNRESOLVED = auto()
    SCOPE_UNVERIFIED = auto()
    SUPERSEDED = auto()
    RETRACTED_SOURCE = auto()
    NON_REPLAYABLE_EXACT = auto()
    WEAK_SWAP = auto()


class Operator(IntEnum):
    DEDUCTION = 1
    STATISTICAL = 2
    ABDUCTION = 3
    ANALOGY = 4
    LLM_GENERATION = 5
    MEASUREMENT = 6


#: Hard ceilings. An operator can never produce a claim stronger than this, whatever
#: its inputs. LLM_GENERATION's ceiling is what makes hallucination survivable.
CEILING = {
    Operator.DEDUCTION: Epistemic.DERIVED,
    Operator.STATISTICAL: Epistemic.INFERRED,
    Operator.ABDUCTION: Epistemic.CONJECTURED,
    Operator.ANALOGY: Epistemic.SPECULATIVE,
    Operator.LLM_GENERATION: Epistemic.SPECULATIVE,
    Operator.MEASUREMENT: Epistemic.MEASURED,
}


@dataclass
class Typed:
    """Anything that carries epistemic status."""

    name: str
    level: Epistemic
    flags: Flags = Flags.NONE
    inputs: tuple = ()
    operator: Operator | None = None

    def __repr__(self) -> str:         # pragma: no cover - cosmetic
        fl = "" if self.flags is Flags.NONE else f" [{self.flags}]"
        return f"<{self.name}: {self.level.name}{fl}>"


def combine(name: str, inputs: list[Typed], operator: Operator) -> Typed:
    """The propagation rule. Weakest link, then the operator's ceiling.

    Flags propagate by union: SINGLE_INSTRUMENT and CONFOUND_UNRESOLVED are contagious,
    which is the intended behaviour -- a conclusion drawn from single-instrument evidence
    is itself single-instrument evidence.
    """
    if operator is Operator.MEASUREMENT and not inputs:
        return Typed(name, Epistemic.MEASURED, Flags.NONE, (), operator)
    if not inputs:
        raise ValueError("non-measurement operators require inputs")

    weakest = min(i.level for i in inputs)
    level = Epistemic(min(weakest, CEILING[operator]))

    flags = Flags.NONE
    for i in inputs:
        flags |= i.flags
    if operator is Operator.LLM_GENERATION:
        flags |= Flags.SYSTEM_AUTHORED | Flags.NON_REPLAYABLE_EXACT

    return Typed(name, level, flags, tuple(inputs), operator)


@dataclass
class Gate:
    """A promotion gate (docs/06 §I.4). Refuses rather than warns."""

    target: Epistemic
    requires_sealed_test: bool = False
    requires_tribunal_survival: bool = False
    requires_instrument_swap: bool = False
    min_e_value: float = 0.0

    def check(self, claim: Typed, *, sealed: bool = False, tribunal: str = "",
              swap: str = "", e_value: float = 0.0) -> tuple[bool, list[str]]:
        why: list[str] = []
        if self.requires_sealed_test and not sealed:
            why.append("no sealed pre-registered test")
        if self.requires_tribunal_survival and tribunal != "SURVIVES":
            why.append(f"tribunal verdict is {tribunal or 'ABSENT'}, not SURVIVES")
        if self.requires_instrument_swap and swap != "STRONG":
            why.append(f"instrument swap is {swap or 'ABSENT'}, not STRONG")
        if e_value < self.min_e_value:
            why.append(f"e-value {e_value:.2f} below threshold {self.min_e_value:.2f}")
        if claim.level < Epistemic.CONJECTURED:
            why.append(f"claim is only {claim.level.name}")
        if Flags.SYSTEM_AUTHORED in claim.flags and self.target > Epistemic.CONJECTURED:
            why.append("system-authored content cannot be promoted without external evidence")
        return (not why), why
