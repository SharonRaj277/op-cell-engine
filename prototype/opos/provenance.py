"""Hash-chained evidence log and acyclic provenance DAG (docs/07 §7.1).

The knowledge base is a materialised view over this log. Rollback is replay;
retraction propagation is replay with a source excluded.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone


def _h(*parts: str) -> str:
    return hashlib.sha256("\x1f".join(parts).encode()).hexdigest()[:16]


@dataclass(frozen=True)
class LogEntry:
    seq: int
    prev_hash: str
    kind: str
    payload: dict
    principal: str
    at: str

    @property
    def hash(self) -> str:
        return _h(str(self.seq), self.prev_hash, self.kind,
                  json.dumps(self.payload, sort_keys=True), self.principal, self.at)


class EvidenceLog:
    """Append-only, tamper-evident. Nothing is ever edited or deleted."""

    GENESIS = "0" * 16

    def __init__(self) -> None:
        self._entries: list[LogEntry] = []
        self._retracted: set[int] = set()

    def append(self, kind: str, payload: dict, principal: str = "system") -> LogEntry:
        prev = self._entries[-1].hash if self._entries else self.GENESIS
        e = LogEntry(len(self._entries), prev, kind, payload, principal,
                     datetime.now(timezone.utc).isoformat())
        self._entries.append(e)
        return e

    def retract(self, seq: int, principal: str) -> None:
        """Retraction is an append, never an edit."""
        self._retracted.add(seq)
        self.append("retraction", {"target_seq": seq}, principal)

    def verify(self) -> bool:
        prev = self.GENESIS
        for e in self._entries:
            if e.prev_hash != prev:
                return False
            prev = e.hash
        return True

    def replay(self, exclude: set[int] | None = None) -> list[LogEntry]:
        """Deterministic reconstruction input. `exclude` drives retraction propagation."""
        drop = (exclude or set()) | self._retracted
        return [e for e in self._entries if e.seq not in drop]

    def __len__(self) -> int:
        return len(self._entries)


class CycleError(Exception):
    """A belief may not become evidence for itself through any path."""


@dataclass
class ProvenanceDAG:
    """Edges point from a derived node to what it was derived from."""

    parents: dict[str, list[str]] = field(default_factory=dict)
    meta: dict[str, dict] = field(default_factory=dict)

    def add(self, node: str, derived_from: list[str], operator: str,
            operator_version: str, policy_version: str) -> None:
        # Reject on the transitive closure, not just immediate parents: a long chain
        # is exactly how self-reinforcement gets past a naive check.
        for p in derived_from:
            if node == p or self._reaches(p, node):
                raise CycleError(f"provenance cycle: {node} <- {p}")
        self.parents[node] = list(derived_from)
        self.meta[node] = {"operator": operator, "operator_version": operator_version,
                           "policy_version": policy_version}

    def _reaches(self, start: str, target: str) -> bool:
        seen, stack = set(), [start]
        while stack:
            n = stack.pop()
            if n == target:
                return True
            if n in seen:
                continue
            seen.add(n)
            stack.extend(self.parents.get(n, ()))
        return False

    def ancestors(self, node: str) -> set[str]:
        seen, stack = set(), list(self.parents.get(node, ()))
        while stack:
            n = stack.pop()
            if n in seen:
                continue
            seen.add(n)
            stack.extend(self.parents.get(n, ()))
        return seen

    def descendants_of(self, source: str) -> set[str]:
        """Everything that would be flagged if `source` were retracted."""
        return {n for n in self.parents if source in self.ancestors(n)}
