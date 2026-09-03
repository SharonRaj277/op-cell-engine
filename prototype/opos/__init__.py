"""OP-OS Kernel v0 — reference implementation of the spine.

Deliberately dependency-free. Deliberately small. Contains only the mechanisms the
architecture actually rests on:

    epistemics  — the epistemic type lattice and taint propagation
    provenance  — hash-chained evidence log and acyclic provenance DAG
    ledger      — the double-entry discrepancy ledger with anytime-valid evidence
    fields      — canonical-frame feature fields
    invariant   — the invariant hunter
    tribunal    — the confound tribunal

Nothing marked RESEARCH in docs/09-FEASIBILITY-2026.md appears here, on purpose.
"""
