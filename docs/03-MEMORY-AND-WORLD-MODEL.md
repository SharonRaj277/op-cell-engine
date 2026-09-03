# 03 — (C) Memory architecture, (D) World-model architecture

## Part C — Memory

Memory is stratified by *what it is for*, and each stratum has a different mutability,
retention, and access-accounting policy. A single vector index is not a memory architecture.

### C.1 The eight strata

| # | Stratum | Contents | Mutability | Purpose |
| --- | --- | --- | --- | --- |
| L0 | **Evidence Log** | Every observation, document, human judgement, policy change | Append-only, hash-chained, signed | The only source of truth (I7) |
| L1 | **Object store** | Cells, nuclei, regions: geometry, morphometry, position, embeddings | Immutable per pipeline version | The measured world |
| L2 | **Field store** | Canonical frames and `FeatureField`s per specimen | Immutable per frame version | The representation discovery operates on |
| L3 | **Semantic memory** | Mechanism cards, claims, ontology, scopes, parameters | Versioned, replayable | What the system believes |
| L4 | **Episodic memory** | Every prediction, score, posting, decision, tribunal, investigation | Append-only | Audit, and the training set for L5 |
| L5 | **Procedural memory** | Retrieval strategies, reasoning tactics, attribution heuristics, experiment policies | Versioned, learnable within bounds | How the system works |
| L6 | **Working memory** | Active investigation case files | Mutable, checkpointed | Long-horizon focus |
| L7 | **Meta-memory** | Calibration curves, per-stratum error profiles, FDR history | Derived, recomputed | Knowing where it is reliably wrong |

Two more structures cut across them.

### C.2 The Held-Out Vault and specimen access accounting

The failure mode that kills autonomous discovery systems is not hallucination. It is **silent
multiple testing**: a system that can look at the same cohort ten thousand times will find
something in it, and no amount of downstream rigour repairs that.

So specimens are a *budgeted resource with access accounting*:

```
Vault
├── EXPLORATORY pool     unlimited looks; nothing promoted from here, ever
├── CONFIRMATORY pool    per-specimen look budget; every read logged against a Commitment
└── SEALED pool          zero reads until a Commitment is registered and the decision rule fixed
                         rotates into CONFIRMATORY on a schedule; freshly accessioned cases
                         enter here automatically
```

Every read of confirmatory or sealed data is an evidence-log entry naming the Commitment it
serves. The alpha budget is deducted at read time, not at publication time. A miner that wants
to browse gets the exploratory pool and knows that nothing it finds there can be promoted
without a fresh sealed test.

This is the structure that converts "the system looked at a lot of data" from a liability into
an asset, and there is no way to bolt it on later — access accounting has to be in the storage
layer from day one.

### C.3 The autophagy firewall

Every artefact the system authors — hypotheses, dossiers, summaries, drafts, anything rendered
into natural language — is stamped `SYSTEM_AUTHORED` indelibly, in content and in metadata.
The literature compiler refuses to ingest anything carrying that stamp, at any remove, including
via a human intermediary who pasted it into a report.

Without this, a system that writes and then reads is a closed loop that will converge to
confident nonsense within a few cycles. The stamp is cheap; the failure is not recoverable.

### C.4 Bitemporality: two clocks that must never be conflated

Every fact carries two time axes:

- **Biological time** — when the phenomenon occurred in the specimen or patient: excision date,
  lesion age, longitudinal visit index, time-since-intervention.
- **Epistemic time** — when the system came to believe it, and until when it believed it.

"Nuclear area increased between visit 1 and visit 3" and "we believed X between March and
September" are different statements and conflating them is how temporal knowledge graphs
produce nonsense. Queries specify both: `as_of(epistemic=T1, biological=T2)`. Rollback is a
query on the epistemic axis; longitudinal reasoning is a query on the biological axis.

### C.5 Forgetting

Nothing in L0–L4 is ever deleted; retraction and refutation are *state transitions*, not
deletions. What is bounded is **indexing and attention**: hot indices cover the active envelope,
cold storage holds the rest, and the portfolio bounds how many investigations are live. The
system forgets by de-prioritising, never by destroying, because destruction breaks replay and
replay is the entire safety story.

---

## Part D — The world model

### D.1 There is no world model. There is a federation.

The instinct is one large generative model of tissue. Reject it, for three reasons:

1. **Unlearnable.** The joint distribution over tissue architecture, cellular organisation,
   morphology, spatial relations, and instrument state, conditioned on disease, cohort and site,
   is not identifiable from the data volumes any single pathology department will ever hold.
2. **Untestable.** A monolith cannot be falsified, only tuned. When it mispredicts you learn
   nothing about *which* belief was wrong. Falsifiability requires modularity.
3. **Unattributable.** The ledger's whole function is assigning surprise to a *specific*
   account. A monolith gives you one account and therefore no discovery signal.

So: **a registry of overlapping, scoped, individually falsifiable models**, plus a consistency
checker that treats disagreement between models with intersecting envelopes as a first-class
trigger. This is the single largest correction the adversarial review (`08`) forces, and it is
made here pre-emptively.

```
                     ┌────────────────────────┐
                     │  Model Federation      │
                     │  (registry + router)   │
                     └───────────┬────────────┘
     ┌──────────────┬────────────┼─────────────┬───────────────┐
     ▼              ▼            ▼             ▼               ▼
 Field models  Mechanism    Population    Causal         Measurement
 f(φ) with     cards        models        sketches       models
 random        (executable, (cohort-level (DAG + explicit (instrument →
 effects       parametric)  distributions) assumptions)   observable)
     │              │            │             │               │
     └──────────────┴────────────┴─────────────┴───────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │ Consistency checker      │  disagreement in overlapping
                    │ + envelope algebra       │  envelopes → Investigation
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │ Ontology (human-governed)│  operational definitions,
                    │ + label-noise model      │  quantities, units, dimensions
                    └──────────────────────────┘
```

### D.2 The five model families

**1. Field models.** Hierarchical Bayesian models of `f(φ)` — Gaussian processes or monotone
splines with specimen-level and batch-level random effects, and instrument terms entering
explicitly. These carry most of the predictive weight in practice and are entirely buildable
today. They are what produce the sealed predictions in the kernel.

**2. Mechanism cards.** Executable, parameterised, dimensioned programs (§2.5). A card such as
"progressive chromatin condensation during terminal differentiation" is a function from
`(specimen context, φ)` to a distribution over chromatin texture, with parameters that have
priors from literature and posteriors from local data.

**3. Population models.** Cohort-level distributions: how do card parameters vary across
patients, sites, and conditions? This is where "normal variation" is defined, and therefore
where "abnormal" acquires meaning.

**4. Causal sketches.** Explicit DAG fragments with their identifying assumptions written down
as machine-checkable objects. Crucial constraint: **a causal sketch derived from observational
tissue data is typed `CONJECTURED`, never higher, regardless of how good the fit is.** Elevation
requires intervention, a natural experiment with a defensible identification strategy, or
longitudinal data with a stated and tested exclusion restriction. The system may reason
causally; it may not *claim* causality from association. This is enforced by the type lattice,
not by a policy document.

**5. Measurement models.** The instrument as part of the model. `observed = M(true, instrument)`
with `M` learned from calibration data (phantom slides, serial sections, repeat scans,
inter-scanner panels, manual annotation subsets). This family is what makes I5 computable rather
than merely aspirational: to ask "would this survive a different instrument?" you need a model
of the instrument.

### D.3 The ontology, and why diagnostic labels are not ground truth

The ontology is **human-governed**; the system may propose amendments and may never enact them
(see the capability lattice in `06`). It holds entities, quantities with units and dimensions,
relation types, and — the load-bearing part — **operational definitions**: `nuclear_area` is not
a concept, it is a specific measurement procedure bound to a pipeline version.

The domain-specific correction that matters most: **pathology's diagnostic labels are noisy
measurements of a latent state, not ground truth.** Inter-observer agreement on oral epithelial
dysplasia grading is famously modest. A system that treats "moderate dysplasia" as a fact will
spend its life discovering properties of pathologist behaviour.

Therefore every categorical label enters through a label model:

```python
@dataclass
class LabelObservation:
    latent: LatentStateRef        # the thing the label is about
    label: CategoryId
    rater: RaterId                # human or model
    rater_model: RaterErrorModel  # confusion structure, drift, calibration over time
    context: ReadingContext       # what else the rater could see; order effects
```

Consensus panels, repeat readings, and known rater confusion structure are all first-class.
This costs real effort and it is not optional: without it, half the system's "discoveries" will
be findings about reporting habits.

### D.4 Model revision: how the federation changes

Revision is never an overwrite. It is one of five typed transitions, each with its own gate:

| Transition | Trigger | Gate |
| --- | --- | --- |
| **Reparameterise** | Scorecard degrades but structure holds | Automatic; kernel-level; logged |
| **Narrow scope** | Card fails in an identifiable stratum only | Automatic with notification; the most common and most valuable update |
| **Add sibling** | A competing card outperforms in part of the envelope | Automatic; both retained, router arbitrates |
| **Supersede** | A sibling dominates across the whole envelope with e-value past threshold | Human sign-off; old card retained as `SUPERSEDED` |
| **Structural amendment** | New entity, quantity, relation type, or ontology change | Human sign-off, always; system may only propose |

Scope narrowing deserves emphasis. It is the cheapest, safest, most frequent, and most
scientifically honest form of learning available — "this is true, but only here" — and almost no
knowledge system implements it because a triple store has nowhere to put the qualifier.
Getting this one transition right is worth more than any amount of hypothesis generation.
