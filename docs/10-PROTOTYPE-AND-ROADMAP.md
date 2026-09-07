# 10 — (N) The minimal prototype, (O) The path to autonomous discovery

## N — OP-OS Kernel v0

### N.1 The organising decision: build the spine, and build literature last

The instinct in 2026 is to start with retrieval over papers, because it demos well in a week.
Do the opposite. **Literature ingestion is the least valuable and most error-prone layer, and it
is the only one that produces impressive-looking output before it works.** The spine — metadata,
frames, sealed predictions, ledger, tribunal, types — produces nothing demo-able for months and
is the entire basis of every later claim.

Concretely: v0 has *no* literature ingestion. It has a hand-curated set of perhaps 30 mechanism
cards written by a pathologist and a modeller together. That is enough to seed the federation,
and it removes the largest source of silent corruption from the period when the system's own
behaviour is still being characterised.

### N.2 Phase 0 — metadata discipline (the unglamorous prerequisite)

Nothing downstream works without this, and it cannot be retrofitted because it is about data that
was never recorded.

- Every slide: scanner, objective, mpp, colour profile, focus metric, scan date.
- Every block: fixative, fixation delay and duration, processor run, embedding date.
- Every section: microtome, thickness, cutting session, operator, date.
- Every stain: protocol, lot, stainer, run, date.
- Every pipeline run: version hash of every model.
- Control tissue in every batch; phantom/calibration slides on a schedule.
- Every read: rater, date, context, and whether it was blinded.

If a department cannot commit to this, the honest recommendation is not to build the rest. This
is the single highest-leverage sentence in the repository.

### N.3 Scope of v0

One tissue system, one stain, one question family:

- **Tissue**: oral stratified squamous epithelium, H&E.
- **Frame**: φ (normalised basal→surface depth), lateral arc length s, local thickness h.
- **Features**: 8–12 well-defined per-nucleus quantities (area, elongation, chromatin texture
  moments, N:C ratio, neighbour distance and count, local density, orientation coherence).
- **Cohort**: normal / hyperplasia / OED grades / OSCC, with the diagnostic label treated as a
  noisy rater observation from day one, not as truth.
- **Question family**: how do feature fields vary with φ, and what combinations of them are
  invariant across specimens?

### N.4 Six modules

```
opos/
├── evidence/       append-only hash-chained log; content-addressed blobs; replay
├── measure/        instrument registry; nuisance capture; measurement models; QC
├── frame/          canonical frame fitting; φ assignment; field lifting with uncertainty
├── kernel/         sealed prediction register; scorer; discrepancy ledger; attributor
├── discover/       structure scoring; invariant hunter; confound tribunal; dossier builder
└── epistemics/     type lattice; taint propagation; provenance DAG; scope algebra; gates
```

Six modules, no LLM, no knowledge graph, no retrieval, no agent framework. The reference
implementation of `epistemics/`, `kernel/` (ledger + e-values), and `discover/` (invariant hunter
+ tribunal) is in [`prototype/`](../prototype/) and runs on stdlib Python.

The world model in v0 is a set of hierarchical field models plus the 30 hand-written cards. The
"reasoning layer" is the scorer, the attributor, and the tribunal. That is enough to do real
science, and it is deliberately less than the architecture in `01`.

### N.5 Milestones

| M | Deliverable | Success criterion |
| --- | --- | --- |
| M0 | Metadata capture live | ≥95% of new specimens have complete instrument metadata |
| M1 | Frames + fields | Frame-fit residual within tolerance on ≥90% of ROIs; φ reproducible across serial sections within a stated bound |
| M2 | Measurement models | Each feature has a calibrated bias/variance model with repeat-scan and inter-scanner data |
| M3 | Sealed prediction loop | Every incoming specimen is predicted before analysis; predictions sealed and scored; reliability diagrams produced |
| M4 | Ledger live | Balance invariant holds; attribution intervals computed; unexplained accounts accumulating |
| M5 | Calibration Range | Sensitivity vs effect size and empirical FDR measured for the invariant hunter, on injected phenomena and pure nulls |
| M6 | Tribunal | Injected synthetic artefacts caught at a measured rate; specificity reported |
| M7 | First dossier | One complete Finding Dossier end to end, most likely a scope narrowing or a refutation |

M5 before M7 is not negotiable. A discovery pipeline whose false-discovery rate has never been
measured should not be allowed to emit a finding.

### Measured M5 operating characteristics (synthetic)

From `python3 prototype/cli.py range --trials 20`, 30 specimens per cohort. `coupling` is the
strength of the planted relationship: 1.0 means the two features share a differentiation rate
exactly, 0.0 means nothing was planted at all.

| Condition | Trials | Sensitivity | False discovery | Artefact kill |
| --- | --- | --- | --- | --- |
| coupling 1.00 | 20 | 100% | 0% | 100% |
| coupling 0.90 | 20 | 100% | 0% | 100% |
| coupling 0.75 | 20 | 100% | 5% | 100% |
| coupling 0.50 | 20 | 50% | 15% | 100% |
| pure null (nothing planted) | 20 | — | 5% | — |

Read honestly, this says three things. The pipeline is reliable down to roughly 0.75 coupling and
loses half its sensitivity by 0.50 — that is the detection limit, and it should be quoted whenever
the system reports finding nothing. The planted artefact was destroyed in every single trial,
which is the tribunal working as designed. And the pure-null false-discovery rate is 5%, not 0% —
one cohort in twenty yields a surviving candidate with nothing planted in it, which is the number
that belongs in a dossier rather than a derived guarantee (`08 A12`).

These figures are an **upper bound on real performance**, and it is important not to quote them as
if they were not. The synthetic cohorts have a correctly-specified noise model, exactly the nuisance
channels the tribunal knows about, and no unmeasured confounding. Real tissue supplies all three of
those problems, so the first task on real data is to re-measure this table, not to assume it.

### N.6 What v0 will most likely produce first

In order of likelihood, and all of them are worth having:

1. **Scanner and stain-lot artefacts** the lab did not know it had. (Near-certain. The ledger is
   a QC system before it is anything else.)
2. **Frame-fitting failure modes** in rete-rich and tangentially-cut regions.
3. **Scope narrowings** of textbook claims: true, but only in part of the φ range or part of the
   cohort.
4. **Failed replications** of published morphometric relationships.
5. **Candidate invariants**, most of which will die in the tribunal on the shared-denominator
   channel.
6. **One surviving candidate relationship**, eventually, if the tissue is generous.

A team that is disappointed by items 1–4 has misunderstood the value of the system.

## O — From prototype to autonomous discovery

Six autonomy levels. Each gate is a **measured** number from the Calibration Range and the
settled-investigation history, not a judgement call.

### A0 — Instrumented (v0)
Predicts, scores, posts to the ledger. Humans read the ledger. No hypotheses generated.
*Gate to A1:* prediction calibration within tolerance across ≥3 strata; balance invariant holding
for ≥6 months; metadata completeness ≥95%.

### A1 — Anomaly reporting
Ledger accounts escalate to human-readable anomaly reports with structure scores and stratum
profiles. Still no hypotheses.
*Gate to A2:* tribunal specificity on injected artefacts ≥ a pre-set threshold (start at 0.9);
measured FDR on pure-null Range runs below the stated target; ≥20 anomalies triaged by humans
with agreement on the triage verdict ≥ some pre-registered κ.

### A2 — Hypothesis proposal
Generators run; hypotheses are proposed with explicit priors and discriminating predictions.
Humans select what to pursue. The LLM enters the system here, and only here, behind the gauntlet.
*Gate to A3:* ≥70% of proposed hypothesis sets judged by domain experts to contain the eventually
correct explanation; mechanism-theatre rate ≈0 under template-only rendering; novelty checks
validated against a human literature search on ≥30 cases.

### A3 — Autonomous prioritisation
The system chooses which investigations to run, allocates alpha and specimen budget within
human-set caps, and emits work orders. Humans execute and approve every promotion.
*Gate to A4:* portfolio decisions match expert prioritisation at an agreed rate; alpha accounting
audited clean; no promotion in the period found to be an artefact on later review.

### A4 — Closed passive loop
Bets committed and settled automatically from the routine prediction stream, with human sign-off
only at promotion. Active probes still require human execution — a constraint of pathology, not
of the design.
*Gate to A5:* a track record. ≥5 findings promoted, externally replicated, and surviving
independent scrutiny; measured FDR stable; zero clinical-firewall violations.

### A5 — Closed active loop
The system commissions physical experiments within a standing protocol and budget: recuts,
restains, rescans, IHC panels, blinded re-reads. Prospective collection and anything touching
patient care remains human-authorised, permanently.

### What never becomes autonomous

Independent of level: T4 changes (gates, scorer, type lattice, tribunal, Range), ontology
enactment, clinical-surface promotion, envelope widening, and anything involving patient contact.
These are not stages on the way to full autonomy. They are the parts that make the autonomy of
everything else safe, and a system that eventually absorbs them has not matured — it has removed
its own referee.

### Honest timeline

With a serious team (4–6 engineers, a pathologist, a statistician, and genuine lab cooperation):

- **A0**: 9–15 months, dominated by metadata discipline and frame validation, not by code.
- **A1**: +6 months.
- **A2**: +9 months.
- **A3**: +12 months, and only with a measured track record behind it.
- **A4–A5**: beyond a realistic planning horizon, and appropriate to treat as a direction rather
  than a plan.

The first genuine, externally-replicated novel finding is a 3–5 year proposition, and the
intermediate outputs — QC, refutations, scope corrections, calibrated abstention — have to carry
the project until then. Any plan that depends on a discovery in year one is not a plan.
