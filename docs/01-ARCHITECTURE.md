# 01 — (A) The architecture

## 1.1 Ten planes

The system is layered by *epistemic role*, not by technology. A plane may only depend on planes
below it, and may only write upward through a typed interface. This is what makes the
provenance guarantees in `07-SAFETY-PROVENANCE.md` enforceable rather than aspirational.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ P9  META / CALIBRATION      calibration range · policy learner · meta-memory   │
│                             synthetic-phenomenon injection · FDR accounting    │
├──────────────────────────────────────────────────────────────────────────────┤
│ P8  GOVERNANCE              epistemic type lattice · promotion gates           │
│                             capability lattice · clinical firewall · audit     │
├──────────────────────────────────────────────────────────────────────────────┤
│ P7  ACQUISITION             literature compiler · evidence broker              │
│                             experiment planner · VOI portfolio · alpha budget  │
├──────────────────────────────────────────────────────────────────────────────┤
│ P6  DISCOVERY               residual miner · invariant hunter                  │
│                             contradiction miner · entity-anomaly miner         │
│                             → Investigation Portfolio                          │
├──────────────────────────────────────────────────────────────────────────────┤
│ P5  INFERENCE               deductive · probabilistic · causal · analogical ·  │
│                             abductive reasoners │ LLM proposal engine          │
│                             typed compiler + verifier (the gauntlet)           │
├──────────────────────────────────────────────────────────────────────────────┤
│ P4  RECONCILIATION KERNEL   sealed prediction register · scorer                │
│                             discrepancy ledger (double-entry) · attributor     │
│                             confound tribunal · drift monitor                  │
├──────────────────────────────────────────────────────────────────────────────┤
│ P3  MODEL (WORLD MODEL)     federation of scoped executable models:            │
│                             mechanism cards · field models · population models │
│                             causal sketches · ontology · consistency checker   │
├──────────────────────────────────────────────────────────────────────────────┤
│ P2  REPRESENTATION          specimen state graph · canonical tissue frame (φ)  │
│                             feature fields · entity resolution · embeddings    │
├──────────────────────────────────────────────────────────────────────────────┤
│ P1  MEASUREMENT             instrument registry · measurement models           │
│                             nuisance capture · QC · uncertainty propagation    │
├──────────────────────────────────────────────────────────────────────────────┤
│ P0  SUBSTRATE               evidence log (append-only, hash-chained)           │
│                             content-addressed blob store · object store        │
└──────────────────────────────────────────────────────────────────────────────┘
        ▲ provenance spine threads vertically through every plane ▲
```

Two rules give the structure its teeth:

- **Upward-only writes, downward-only reads.** P6 cannot write to P3; it can only submit a
  promotion request that P8 adjudicates. P5 cannot write to P0; only P1 and P7 append evidence.
- **P9 may never modify P4 or P8.** The learner may not modify its own referee. This is the
  single most important safety invariant in the system and it is enforced structurally, by
  making the scorer, the ledger, the gates, and the type lattice a separately-versioned,
  human-signed artefact that the self-improvement loop has no write path to.

## 1.2 What each plane is for

### P0 — Substrate
Append-only **Evidence Log**: every raw observation, every ingested document, every human
judgement, every policy change, as a hash-chained record. Content-addressed blob store for
WSIs, ROIs, masks. The knowledge base is downstream of this and rebuildable from it (I7).

### P1 — Measurement
The plane everyone skips, and the reason most computational-pathology "discoveries" are wrong.
It contains:

- **Instrument registry.** Scanner make/model/calibration, objective, stain protocol and lot,
  fixation delay and duration, section thickness, microtome, lab, operator, date, and the exact
  version hash of every model in the vision stack.
- **Measurement models.** For each feature, an explicit model of how the instrument distorts it:
  bias and variance as functions of tissue and instrument state. `nuclear_area` is not a tissue
  property; it is a property of tissue *and* segmenter *and* focus *and* section thickness. The
  measurement model is what lets the system reason about the difference.
- **Nuisance capture.** Every one of the above recorded as a first-class covariate on every
  measurement, mandatorily. If a nuisance channel is not captured, the tribunal cannot rule on
  it, and nothing downstream of it can ever be promoted. *No metadata, no discovery* — enforced
  by the gate, not by discipline.
- **Uncertainty propagation.** Every measurement carries a variance and a provenance to its
  measurement model.

### P2 — Representation
Turns objects into **fields over a canonical frame**. Central object: the **Canonical Tissue
Frame**, which assigns every point a normalised coordinate — for oral epithelium, φ ∈ [0,1]
from basement membrane to surface, plus lateral arc-length s, plus local thickness h and rete
geometry. Cell/nucleus objects are then lifted to **feature fields** `f(φ, s)` with uncertainty
bands, per specimen.

This is the representational decision that makes your section-9 requirement tractable. A
relationship "between architecture, depth and morphology" is a relationship *between functions
of φ*. Representing it as anything else — a triple, a scalar summary per slide, an embedding —
throws away the object you are trying to discover.

### P3 — Model
The world model. Deliberately **not** one model: a *federation* of scoped, individually
falsifiable models with declared validity envelopes, plus a consistency checker that looks for
disagreement between models whose envelopes overlap. See `03-MEMORY-AND-WORLD-MODEL.md` for
why the monolith is both unlearnable and untestable.

### P4 — Reconciliation Kernel
The always-on heart. Predicts, scores, attributes, and maintains the ledger. Everything else in
the system is either feeding it or reacting to it.

### P5 — Inference
Five reasoners plus a generative proposal engine behind a hard typed boundary: **the LLM never
writes to any store.** It emits candidate structures that must compile, type-check, simulate,
and survive statistics before they exist as anything but a proposal.

### P6 — Discovery
Four miners that read the ledger, the model federation, and the field store, and open
**Investigations** — persistent, resumable case files that are the unit of scientific work.

### P7 — Acquisition
Where evidence comes from: the literature compiler (documents → candidate mechanism cards with
scope), the passive harvest of the routine specimen stream, and the active experiment planner.
Above them the **portfolio manager** allocates the four scarce resources — tissue, wet-lab
capacity, pathologist attention, and *statistical alpha* — by expected information gain per unit
cost.

### P8 — Governance
The type lattice, the promotion gates, the capability lattice, the human review surfaces, and
the clinical firewall that keeps conjecture out of anything a clinician sees.

### P9 — Meta
Calibration: is the system's uncertainty honest? Is its false-discovery rate what it claims?
Contains the **Calibration Range**, a proving ground in which known phenomena are injected into
perturbed data so that discovery rate and false-discovery rate can be *measured* rather than
hoped for. Also the policy learner, which improves retrieval, reasoning and experiment-selection
strategies within the bounds of the capability lattice.

## 1.3 The control loop, and why yours is not it

Your proposed loop:

```
OBSERVE → REPRESENT → COMPARE → DETECT ANOMALY → EXPLAIN → FAIL → HYPOTHESISE
→ PREDICT → SEEK EVIDENCE → DESIGN TEST → UPDATE → REPEAT
```

It is a good description of one investigation. It is a poor architecture, for five reasons:

1. **It observes before it predicts.** Comparison after the fact is unfalsifiable and invites
   post-hoc storytelling. Prediction must be sealed first (I1).
2. **It explains before it attacks.** Generating explanations before attempting refutation
   anchors the system on its first story and wastes reasoning on artefacts. In this domain, most
   anomalies are the microtome (I4); attempt the kill first, it is far cheaper.
3. **It is single-threaded.** Real science is a *portfolio* of concurrent investigations at
   different maturities competing for scarce resources. The hard problem is not running the
   loop; it is choosing which loop to run next with a finite tissue and alpha budget. A
   sequential loop has no place to put that decision.
4. **It treats anomaly as the only trigger.** Discovery is at least as often triggered by
   *invariance* (a stable combination), *unification* (two mechanisms turning out to be one),
   *contradiction* (a literature conflict), or *structural gap* (a region of specimen space the
   model has no card for). One trigger, one discovery engine, and you lose three-quarters of the
   yield.
5. **"Derive predictions" is under-specified in the way that matters.** A prediction shared by
   all live hypotheses is worthless. What you need is the prediction that maximally *separates*
   them, which is an experimental-design objective, not a derivation.

### The replacement

Two coupled processes: a **continuous kernel** and a **scheduled portfolio**.

```
════════════ CONTINUOUS (every specimen, no human, no decisions) ═══════════════

  incoming specimen
        │
   ┌────▼─────┐   sealed, timestamped, content-addressed, before any analysis
   │ PREDICT  │───────────────────────────────► Prediction Register (immutable)
   └────┬─────┘
   ┌────▼─────┐   vision stack + canonical frame + field lift + nuisance capture
   │ MEASURE  │
   └────┬─────┘
   ┌────▼─────┐   calibrated scoring: surprise, interval coverage, e-values
   │  SCORE   │
   └────┬─────┘
   ┌────▼─────────────────────────────────────────────────────┐
   │ ATTRIBUTE   every unit of surprise posted to exactly one: │
   │   → MECHANISM (known, mis-parameterised)                  │
   │   → NUISANCE  (instrument/process channel)                │
   │   → UNEXPLAINED (residual ledger account)                 │
   └────┬──────────────────────────────────────────────────────┘
        │ ledger account balance crosses a structured-growth threshold
        ▼
════════════ SCHEDULED (investigation portfolio, resource-bounded) ═════════════

   ┌ FRAME ────────── state the discrepancy as a formal target: which quantity,
   │                  which scope, which magnitude, which frame
   ├ ATTACK ───────── Confound Tribunal FIRST. Prior = artefact. Stratify, negative
   │                  controls, instrument swap, specification curve. Most die here.
   ├ HYPOTHESISE ──── survivors only. Competing explanations, always including
   │                  "known phenomenon expressed differently" and "model
   │                  incomplete but not novel". LLM proposes; compiler disposes.
   ├ DISCRIMINATE ─── derive predictions that maximally SEPARATE live hypotheses
   │                  (expected KL / Bayes-factor gain), not merely follow from them
   ├ COMMIT ───────── seal discriminating predictions; allocate alpha and specimen
   │                  budget from the portfolio; register the bet
   ├ HARVEST ──────── mostly PASSIVE: the routine prediction stream settles the bet
   │      or PROBE ── ACTIVE only when passive power is insufficient: order stain,
   │                  recut, cohort pull, prospective collection
   ├ SWAP ─────────── mandatory independent-instrument replication (I5)
   └ SETTLE ───────── promote / refute / narrow scope / park with reason
        │
        ▼
   Finding Dossier → human adjudication → knowledge update (replayable)
```

The kernel never stops and never asks permission — it only predicts, scores, and posts.
The portfolio is where every decision, cost, and risk lives. Separating them is what allows the
system to run continuously at scale without running out of statistical validity: **looking is
free, betting is budgeted.**

### Investigation triggers (all six, not just anomaly)

| Trigger | Miner | Signal |
| --- | --- | --- |
| Anomaly | Residual miner | An unexplained ledger account grows structurally, not randomly |
| Invariance | Invariant hunter | A functional combination has variance far below its components across specimens |
| Contradiction | Contradiction miner | Two well-evidenced claims with provably intersecting scopes disagree |
| Unification | Consistency checker | Two cards with different signatures make identical predictions across the overlap |
| Structural gap | Coverage analyser | A region of specimen/scope space has no card with a valid envelope |
| External | Literature compiler | An ingested claim conflicts with local measurement, or fills a known gap |

## 1.4 End-to-end: photon to promoted claim

Walking your section-9 example through the whole stack, concretely.

**1. Acquire.** Slide scanned. P1 records scanner, objective, stain lot, fixation interval,
section thickness, cutting session, operator, and the version hashes of every vision model.
Blob content-addressed into P0; an `ObservationRecord` is appended to the evidence log.

**2. Predict (sealed).** *Before* segmentation output is available to any downstream consumer,
P4 asks the model federation for its predictive distribution over the standard measurement
panel for this specimen class — including `A(φ)` (say N:C ratio) and `B(φ)` (say chromatin
texture density) as functional predictions with bands. The prediction is hashed, timestamped,
and written to the immutable register.

**3. Measure.** Vision stack segments; P2 fits the canonical frame, computes φ per nucleus,
lifts to fields `A(φ)`, `B(φ)` with per-φ uncertainty from the measurement models.

**4. Score.** P4 compares. Suppose `A(φ)` and `B(φ)` are each individually mispredicted — wide
specimen-to-specimen variation the model does not capture. Surprise is large.

**5. Attribute.** The attributor tries mechanism accounts (mis-parameterised differentiation
gradient) and nuisance accounts (stain lot affects chromatin density measurement). Neither
absorbs the residual. It posts to unexplained account `U:oral-epithelium/A,B/φ-profile`.

**6. Trigger.** Two miners fire on the same substrate. The residual miner sees the account
growing across 60 specimens. Independently, the invariant hunter — searching for combinations
with low within-specimen φ-variance and low cross-specimen variance — finds that while `A` and
`B` each vary by 3× across specimens, `log A(φ) − log B(φ)` is flat in φ and its slope is
stable across specimens. **The ratio's φ-dependence cancels.** An Investigation opens.

**7. Attack.** Tribunal. Stratify by scanner, stain lot, lab, fixation interval, block age,
segmenter version, and case difficulty. Test whether the invariance is an artefact of shared
denominators (`A` and `B` both derived from the same segmentation mask — a *real* and common
trap: correlated measurement error manufactures spurious invariants). Run negative controls:
does the same cancellation appear on tissue types where no shared gradient should exist? Run
a specification curve over 40 defensible analytic choices. Most candidates die here; suppose
this one survives with the shared-mask concern flagged as unresolved.

**8. Hypothesise.** Because a shared-mask artefact is still live, the first hypotheses are
boring by design: (h1) shared segmentation denominator; (h2) both features are monotone
functions of a single latent maturation coordinate, so the ratio is coordinate-free —
i.e. the invariance is a *reparameterisation invariance*, which would be a genuine but modest
structural finding; (h3) known phenomenon under another name — the literature compiler
searches for anything equivalent under unit and definition normalisation; (h4) a coupled
process (chromatin condensation locked to cytoplasmic accumulation during differentiation),
which would be the interesting result.

**9. Discriminate.** These four make *different* predictions. Only h1 predicts the invariance
vanishes under independent segmentation. h2 predicts it survives any monotone
reparameterisation of φ but breaks where maturation is non-monotone (dysplasia, candidal
infection). h4 predicts a specific perturbation response and a lag structure in longitudinal
specimens. The planner picks the prediction set with maximum expected Bayes-factor separation
per unit cost.

**10. Commit.** Sealed. Alpha budget allocated from the portfolio. Specimen quota reserved from
the held-out vault.

**11. Harvest / Probe.** Most of it harvests passively: the next 200 routine cases settle h2 vs
h4 through the ordinary prediction stream at zero cost. h1 requires a probe — re-measure a
sample with an independent segmenter and with manual annotation.

**12. Swap.** Mandatory. Reproduce on a different scanner, different stain batch, different
magnification, and a second segmentation model. Instrument invariance holds or the finding dies
regardless of statistical significance.

**13. Settle.** Suppose h1 is refuted, h4 outperforms h2 with an e-value crossing the
pre-registered threshold and replication in the swap set. The system emits a **Finding
Dossier**: the claim with an explicit scope predicate, the full provenance DAG, the sealed
predictions and when they were sealed, the tribunal transcript including everything that failed
to kill it, the surviving alternatives, the effect size with anytime-valid intervals, the alpha
spent, and the specific experiment that would most efficiently refute it next.

**14. Update.** A human adjudicates. On approval, a signed evidence-log entry records the
promotion; the mechanism card is created at type `INFERRED_LOCAL`, scoped to oral epithelium
under the tested envelope, and enters the prediction stream — where it will begin to be scored
against every future specimen, and can lose its status without anyone deciding to distrust it.

Note what the system did *not* do at any point: assert a biological mechanism, write to its own
knowledge base autonomously, or present a conjecture as pathology.
