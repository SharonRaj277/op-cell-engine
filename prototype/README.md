# OP-OS Kernel v0 — reference implementation

Dependency-free Python 3.11+. No numpy, no GPU, no LLM, no vector store, no agent framework.

```bash
python3 prototype/demo.py                       # end-to-end walkthrough

python3 prototype/cli.py synth  --out data      # write a cohort in the ingest format
python3 prototype/cli.py ingest --dir data      # per-object CSV -> canonical fields (SQLite)
python3 prototype/cli.py hunt                   # invariant hunter + confound tribunal
python3 prototype/cli.py range  --trials 20     # measure the pipeline against planted truth
```

## What is here

| Module | Implements | Doc |
| --- | --- | --- |
| `opos/epistemics.py` | Epistemic type lattice, taint propagation, promotion gates | `docs/02 §2.1`, `docs/06 §I.4` |
| `opos/provenance.py` | Hash-chained evidence log, acyclic provenance DAG, retraction propagation | `docs/07 §7.1` |
| `opos/ledger.py` | Double-entry discrepancy ledger, balance invariant, e-processes, structure scoring | `docs/05 §F.2–F.3` |
| `opos/fields.py` | Feature fields over the canonical frame | `docs/02 §2.4` |
| `opos/invariant.py` | Invariant hunter over dimensionless-monomial candidates | `docs/05 §G.3 Mode 2` |
| `opos/tribunal.py` | Confound tribunal: shared-measurement, noise-floor, materiality, mismatched-pairing, permutation and stratification channels | `docs/05 §F.4` |
| `opos/calibration.py` | The Calibration Range: plants known phenomena and artefacts, measures sensitivity and false-discovery rate | `docs/05 §F.7`, `docs/10 M5` |
| `opos/synthetic.py` | Parameterised cohort generator, shared by the demo and the Range | — |
| `opos/store.py` | SQLite evidence log (hash-chained), specimens, fields, sealed predictions, postings | `docs/07 §7.1` |
| `opos/ingest.py` | Per-object CSV → canonical fields, with the metadata gate | `docs/10 §N.2` |
| `cli.py` | `synth` · `ingest` · `hunt` · `range` · `demo` | `docs/11 §11.5` |

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

## The metadata gate is enforced, not advised

A specimen whose instrument state is incomplete is refused at ingest:

```
REFUSED AT THE METADATA GATE
  5 specimen(s) refused for incomplete instrument state: S000 (missing stain_lot) ...
  Capture it or pass --lax, and note that nothing ingested under --lax can clear a
  promotion gate.
```

Without scanner, stain lot, fixation and pipeline version the confound tribunal has no channels
to stratify on, so nothing derived from that specimen could ever be promoted. Enforcing it at
the point data is accepted is the only place it can be enforced — by the time anyone notices it
is missing, the slides have been cut.

## The Range found a real defect in this code

Building the Calibration Range before trusting the hunter was not a formality. Measured on
pure-null cohorts — nothing planted, so every survivor is a false discovery — the first version
of the pipeline reported a **100% false-discovery rate**. Two fixes, both now in the tribunal:

1. **The φ-permutation null was the wrong null.** It tests whether a feature has φ-structure,
   which every biological field does, rather than whether the *within-specimen pairing* is what
   makes the combination flat. The `mismatched_pairing` channel breaks the pairing instead —
   feature A from one specimen, feature B from another. Null FDR fell to 33%.
2. **Multiplicity was unaccounted.** Four candidates were tried at a 5% cutoff each. Dividing the
   alpha budget across the candidates examined, plus a materiality floor calibrated on the Range,
   took it to 0%.

That sequence is the argument for the whole subsystem: reasoning did not find either defect, and
measurement found both in the first run.

## What is deliberately absent

Everything marked **RESEARCH** in `docs/09-FEASIBILITY-2026.md`: causal discovery, envelope
extraction from literature, mechanism synthesis, ontology revision. Also absent: the LLM
proposal engine, the model federation, the portfolio manager, and the self-improvement layer —
all phase-2, per `docs/08 A9`.
