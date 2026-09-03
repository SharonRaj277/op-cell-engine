# OP-OS Kernel v0 — reference implementation

Dependency-free Python 3.11+. No numpy, no LLM, no vector store, no agent framework.

```bash
python3 prototype/demo.py
```

## What is here

| Module | Implements | Doc |
| --- | --- | --- |
| `opos/epistemics.py` | Epistemic type lattice, taint propagation, promotion gates | `docs/02 §2.1`, `docs/06 §I.4` |
| `opos/provenance.py` | Hash-chained evidence log, acyclic provenance DAG, retraction propagation | `docs/07 §7.1` |
| `opos/ledger.py` | Double-entry discrepancy ledger, balance invariant, e-processes, structure scoring | `docs/05 §F.2–F.3` |
| `opos/fields.py` | Feature fields over the canonical frame | `docs/02 §2.4` |
| `opos/invariant.py` | Invariant hunter over dimensionless-monomial candidates | `docs/05 §G.3 Mode 2` |
| `opos/tribunal.py` | Confound tribunal: shared-measurement, noise-floor, permutation, stratification channels | `docs/05 §F.4` |

## What the demo plants, and what the kernel does with it

The generator plants four things in 80 synthetic oral-epithelium specimens. The kernel is told
none of them.

| Planted | Kernel's verdict |
| --- | --- |
| **A real relationship** — N:C ratio and chromatin density decay with φ at a rate shared within each specimen but varying 2.5× between specimens, so `log(nc) − log(chromatin)` is flat in φ | Found by the invariant hunter at ~60× variance reduction; survives all four tribunal channels; blocked at the promotion gate until an instrument swap is supplied |
| **A manufactured invariant** — nuclear area shares a segmentation mask with the N:C ratio, so their errors are correlated | Scores *highest* of all candidates (3000×) and is killed on the shared-measurement channel, with the noise-floor channel independently confirming that the variance is below what independent errors permit |
| **A confounded association** — orientation-coherence gradient looks like a dysplasia marker, but dysplastic cases were preferentially run on the newer scanner | Naive effect −0.115/φ; +0.003 within scanner strata; `KILLED(stratify:scanner)` |
| **An undeclared nuisance channel** — the attributor knows about stain lot but not about the scanner's effect on orientation coherence | The ledger escalates the account, and the tribunal's stratification catches what attribution missed. Layered defence, not a single filter |

Two implementation details in here are worth more than the rest of the code, because both are
easy to get wrong in a way that silently disables the defence:

- **The stratum concentration test is signed, not absolute.** A batch effect that pushes one
  scanner up and the other down is symmetric in magnitude; an absolute-value test cancels it
  exactly and reports nothing.
- **The noise-floor channel checks variance from below.** A candidate whose observed φ-variance
  falls *below* the independent-error floor cannot be real — the measurement errors must be
  correlated. This catches manufactured invariants even when the mask provenance is unavailable.

## What is deliberately absent

Everything marked **RESEARCH** in `docs/09-FEASIBILITY-2026.md`: causal discovery, envelope
extraction from literature, mechanism synthesis, ontology revision. Also absent: the LLM
proposal engine, the model federation, the portfolio manager, and the self-improvement layer —
all phase-2, per `docs/08 A9`.
