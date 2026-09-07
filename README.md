# OP-OS Knowledge Architecture

**Design study: a knowledge and reasoning layer for computational oral pathology that is
built to *discover*, not to *retrieve*.**

This repository contains an architecture specification, not a product. It answers a single
question: what is the strongest defensible design for the layer that sits above OP-OS's
vision system and biological state engine — the layer that holds what OP-OS knows, notices
when what it knows is wrong, and proposes what might be true instead.

The short version of the answer:

> **Do not put documents at the centre. Put a falsifiable, executable, quantitative model of
> tissue at the centre, and demote literature to evidence that constrains it.**
> Retrieval becomes a subroutine of inference rather than the boundary of reasoning.
> Discovery becomes an accounting problem: every unit of measured surprise must be
> attributed to a mechanism, to an instrument artefact, or to an explicitly maintained
> ledger of the unexplained.

## Read in this order

| Doc | Contents |
| --- | --- |
| [`docs/00-THESIS.md`](docs/00-THESIS.md) | Why RAG/GraphRAG/agentic-RAG is the wrong frame here; the seven load-bearing inversions; what "discovery" can and cannot mean for a machine |
| [`docs/01-ARCHITECTURE.md`](docs/01-ARCHITECTURE.md) | (A) Full architecture, all planes, dataflow from photon to promoted claim; the replacement for the OBSERVE→…→REPEAT loop |
| [`docs/02-DATA-STRUCTURES.md`](docs/02-DATA-STRUCTURES.md) | (B) Every core type, with schemas |
| [`docs/03-MEMORY-AND-WORLD-MODEL.md`](docs/03-MEMORY-AND-WORLD-MODEL.md) | (C) Memory architecture (D) World-model architecture as a federation of scoped executable models |
| [`docs/04-REASONING.md`](docs/04-REASONING.md) | (E) Reasoning architecture: the five reasoners, the epistemic type lattice, reasoning beyond retrieval |
| [`docs/05-DISCOVERY-ENGINE.md`](docs/05-DISCOVERY-ENGINE.md) | (F) Novelty/anomaly detection (G) Hypothesis generation (H) Evidence acquisition and experiment planning |
| [`docs/06-KNOWLEDGE-UPDATE-AND-SELF-IMPROVEMENT.md`](docs/06-KNOWLEDGE-UPDATE-AND-SELF-IMPROVEMENT.md) | (I) Knowledge update (J) Bounded self-improvement and the capability lattice |
| [`docs/07-SAFETY-PROVENANCE.md`](docs/07-SAFETY-PROVENANCE.md) | (K) Provenance, immutability, rollback, retraction propagation, clinical firewall |
| [`docs/08-ADVERSARIAL-REVIEW.md`](docs/08-ADVERSARIAL-REVIEW.md) | The attack on the above, and the v2 redesign that survives it |
| [`docs/09-FEASIBILITY-2026.md`](docs/09-FEASIBILITY-2026.md) | (L) What is real engineering today (M) What is unsolved research (and what is vapour) |
| [`docs/10-PROTOTYPE-AND-ROADMAP.md`](docs/10-PROTOTYPE-AND-ROADMAP.md) | (N) Minimal prototype (O) Staged path to autonomous discovery, with numeric promotion gates |
| [`docs/11-COMPUTE-AND-GPU.md`](docs/11-COMPUTE-AND-GPU.md) | Where a GPU belongs (the vision stack) and where it does not (all of this); sizing, hosting, and the file contract between the two halves |

## Runnable kernel

[`prototype/`](prototype/) is a dependency-free reference implementation of the mechanisms the
argument rests on: the epistemic type lattice, the hash-chained provenance DAG and SQLite
evidence log, the double-entry discrepancy ledger with anytime-valid evidence, the invariant
hunter, the confound tribunal, and the Calibration Range that measures all of it.

```bash
python3 prototype/demo.py                      # end-to-end walkthrough on planted ground truth

python3 prototype/cli.py synth  --out data     # a cohort in the real ingest format
python3 prototype/cli.py ingest --dir data     # per-object CSV -> canonical fields
python3 prototype/cli.py hunt                  # invariant hunter + tribunal
python3 prototype/cli.py range  --trials 20    # measured sensitivity and false-discovery rate
```

No GPU, no LLM, no vector store, no agent framework — see
[`docs/11-COMPUTE-AND-GPU.md`](docs/11-COMPUTE-AND-GPU.md) for why the knowledge layer needs
none of them and where the compute actually belongs. Everything here is deliberately
buildable-today code; everything the docs mark **RESEARCH** is absent on purpose.
