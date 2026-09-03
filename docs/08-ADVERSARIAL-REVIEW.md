# 08 — Adversarial review, and the v2 redesign

Written as a hostile reviewer whose goal is to kill the architecture in `01`–`07`. Where an
attack lands, the fix is folded into v2 at the end. Where it lands and there is no fix, it is
recorded as a limitation.

---

## A1 — "Almost nothing here is new."

Component by component:

| Component | Prior art |
| --- | --- |
| Provenanced, versioned claim store | Nanopublications; PROV-O; W3C provenance; scientific claim graphs since ~2010 |
| Evidence hierarchy + confidence | GRADE, and every evidence-based-medicine framework |
| Executable knowledge with scorecards | Model registries, MLOps, and the entire tradition of mechanistic modelling |
| Discrepancy ledger | Residual analysis. Statistics, 1920s onward |
| Confound tribunal | Negative controls (Lipsitch et al.), specification-curve analysis (Simonsohn), multiverse analysis (Steegen) |
| Invariant hunting | Eureqa, AI Feynman, SINDy, conserved-quantity discovery by variance minimisation |
| Anomaly → hypothesis → experiment loop | Robot Scientist (King et al., Adam 2004 / Eve 2015). Twenty years old, and it did close the loop |
| Anytime-valid statistics | Test martingales, e-values, e-BH (Vovk, Shafer, Ramdas, Grünwald, Wang) |
| Epistemic type propagation | Information-flow type systems; taint tracking |
| Pre-registration | Clinical trials, 2005 |
| Knowledge as a view over an immutable log | Event sourcing; datomic-style bitemporal stores |

**Verdict: the attack lands.** No component is novel. The response is to stop claiming
otherwise. What is defensible is the *composition*, plus three specific choices that are not
standard practice in computational pathology:

1. **Prediction-first ingestion of the routine clinical stream** — turning a hospital's existing
   throughput into thousands of pre-registered experiments a year at zero marginal cost. The
   pieces are old; nobody does this.
2. **Conservation of surprise** — forcing every unit of prediction error to be attributed, so
   that "unexplained" is an accumulating balance rather than a transient flag.
3. **Instrument invariance as a promotion gate** — no finding exists until it survives a change
   of measurement pathway.

Everything else in this repository is engineering around those three, plus honest bookkeeping.
That is a smaller claim than "AGI-level knowledge architecture" and it is a true one.

## A2 — "You will build all of this and discover nothing."

The base rate of genuinely novel quantitative morphological relationships in a well-studied
tissue may be very low. It is entirely possible to run this system for three years and produce
only artefacts and re-derivations.

**The attack lands, and it changes the justification.** The system must not be justified on
expected novel discoveries. It must be justified on outputs that are near-certain:

- **Refutation and scope narrowing** of existing claims. High base rate — much of the descriptive
  pathology literature was established on small cohorts with unstated envelopes, and a
  quantitative system will find that many claims hold more narrowly than stated. This is real,
  publishable, useful, and nearly guaranteed.
- **Quality control.** The ledger and drift monitor are a first-rate lab QC system whether or not
  anything is ever discovered. Scanner drift, stain-lot shifts, and annotator drift all show up
  as ledger structure.
- **Calibrated abstention.** A model that reliably says "out of envelope" has direct clinical
  value.
- **Discovery** is then upside, not the business case.

## A3 — "Your instrument-swap defence does not give you independence."

The sharpest attack in the review. `I5` requires reproduction through an independent measurement
pathway, but:

- Two segmentation models trained on overlapping public data (in practice, everything sees TCGA
  and the same handful of nuclei datasets) share inductive biases. Swapping them is not
  independence, it is correlated replication.
- The φ frame is itself fitted by a model. If frame fitting is biased as a function of tissue
  state, every field is distorted in a correlated way — and both "independent" segmenters
  inherit the same frame.
- Human annotators are trained on the same textbooks and have shared priors.

**The attack lands hard.** v2 fixes:

- Independence is *audited and typed*, not assumed: an `IndependenceAudit` records training-data
  overlap, architecture family, and shared preprocessing between the two pathways, and a swap
  through a non-independent pathway is recorded as `WEAK_SWAP` and does not clear the gate.
- Prefer **physical** perturbation over model perturbation: re-cut, re-stain, re-scan, change
  magnification, change fixation. Physics is more independent than another network.
- The **frame is perturbed as its own channel**: re-fit φ with a different frame model and with
  a deliberately mis-specified one; a relationship that moves with the frame is a frame artefact.
- **Archival back-testing** (see A8) as a further independence axis.

## A4 — "Prediction-first ingestion is circular."

The predicting model was fit on prior specimens from the same lab, the same scanners, the same
stain protocols, and often the same patients' prior blocks. It has already absorbed the batch
structure, so "surprise" is measured relative to a model that shares confounders with the test
case. Sealed pre-registration does not fix confounding; it only fixes post-hoc storytelling.

**The attack lands.** v2 fix: predictions used for *discovery* (as opposed to QC) must come from
models fit under an explicit exclusion — leave-lab-out, leave-scanner-out, leave-time-block-out,
leave-patient-out — chosen to break the confounding path being tested. The kernel therefore
maintains an ensemble of held-out-fitted predictors, not one. This costs compute and reduces
predictive sharpness; both are acceptable prices.

## A5 — "The ledger's balance invariant is fake precision."

Decomposing surprise into mechanism / nuisance / unexplained is not unique. Nested model
comparison depends on ordering; Shapley attribution over non-nested accounts is one arbitrary
choice among many. The books balance by construction, which proves nothing.

**The attack lands.** v2 fix: attribution is computed under a *family* of decompositions
(different orderings, different nuisance model specifications, different priors) and the ledger
stores an **attribution interval**, not a point. Escalation requires the unexplained component to
remain material across the whole family — a specification curve applied to attribution itself.
The balance invariant is retained but demoted to what it actually is: a cheap integrity check
that nothing is being silently dropped, not evidence of correctness.

## A6 — "Where can it still hallucinate?"

Six surfaces survive the gauntlet, and only three of them are commonly acknowledged:

1. **Scope extraction from methods sections.** The hardest and most consequential. An LLM will
   confidently produce an envelope the paper never specified. Mitigation: `SCOPE_UNVERIFIED`
   propagates permanently; scope-critical claims require human confirmation; conflicting scopes
   default to `NOT_COMPARABLE`, which is the safe direction.
2. **Unit and definition normalisation.** "Nuclear area" in µm² at 40× after a specific
   segmentation is not the same quantity as an author's "nuclear size" scored ordinally. Silent
   coercion here corrupts everything downstream. Mitigation: normalisation is a typed,
   human-reviewable mapping, and unmapped terms fail closed.
3. **LLM-authored simulators that encode the answer.** A card can pass the sanity check by
   effectively memorising the training specimens. Mitigation: parameter budget tied to specimen
   count, restricted non-Turing-complete DSL, and sanity checks run on held-out strata only.
4. **Mechanism theatre.** The most insidious. The formal object is a two-parameter monotone
   curve; the prose says "chromatin condensation is kinetically coupled to cytoplasmic
   maturation." The prose asserts a mechanism the mathematics does not contain, and a human
   reading the dossier believes the prose. Mitigation in v2: **rendered statements are generated
   from the formal object by template, not written freely**, and any causal or mechanistic verb
   requires `mechanism_class ≥ mechanistic` plus an interventional evidence link. Free-text
   narration of findings is removed from the system's output path entirely.
5. **The novelty verdict.** Corpus coverage is always incomplete; "not found" is a statement
   about the index. Mitigated by typing, never eliminated.
6. **The ontology mapping.** Mapping a measured phenotype onto a named diagnostic category is an
   act of interpretation that the system performs constantly and cannot validate internally.

## A7 — "It will self-reinforce, just more slowly."

Two paths survive the acyclicity check:

- **Federation blind spots.** Surprise is defined relative to the model federation. A stable
  misspecification shared across all cards is invisible: it produces no surprise, so it never
  posts, so it is never investigated. The system cannot see what it is uniformly wrong about.
- **Finite tribunal channels.** A confounder not on the channel list cannot be ruled out, and its
  effects are promoted as findings. The channel list is written by humans who share the field's
  blind spots.

**Both land.** v2 fixes:

- **Model holidays.** Periodically score the specimen stream against a deliberately weak
  nonparametric baseline (a specimen-level empirical distribution with no mechanism structure)
  and compare residual structure. Where the federation is *worse* than the naive baseline in some
  region, it is imposing structure that is not there. This is how a model finds out what it is
  uniformly wrong about — it cannot introspect its way there.
- **An open `UNKNOWN_CHANNEL` nuisance account** with explicit prior mass, so that "we ruled out
  every channel we thought of" never reads as "we ruled out everything."
- **Adversarial channel review** on a schedule: an outside human is asked, specifically, what
  confounder the channel list is missing. Budgeted like any other resource.

## A8 — "You cannot distinguish drift from discovery."

Both look identical in the prediction stream: a systematic, structured, persistent departure
from the model. Nuisance metadata helps only for channels that are measured, and drift in an
unmeasured channel is indistinguishable from a real change in the tissue population.

**The attack largely lands.** It is a genuine epistemic limitation, not an engineering gap. Two
partial defences in v2:

- **Archival back-testing.** A real relationship between tissue quantities should hold in blocks
  cut ten years ago on different equipment by different staff. A drift artefact should not. This
  is the single most decisive cheap test available in a department with an archive, and it is
  worth building the pipeline for archival specimens specifically to get it.
- **Physical control tissue.** Control blocks processed in every batch give a direct, measured
  drift signal that is independent of the specimen population.

Residual limitation, stated plainly: a slow real change in the referred patient population and a
slow drift in an unmeasured process channel remain confusable, and no amount of internal
machinery resolves it.

## A9 — "This is thirty person-years and will never be finished."

Ten planes, eight memory strata, five reasoners, thirteen tribunal channels. Real teams building
this ship nothing.

**The attack lands.** The response is the ordering, not a reduction in ambition. Roughly 20% of
the design carries 80% of the value, and it is a specific 20%:

> **The spine**: evidence log · instrument metadata capture · canonical frame and fields ·
> sealed prediction register · discrepancy ledger · confound tribunal · epistemic type lattice.

The federation, the five reasoners, the portfolio manager, and the self-improvement layer are all
deferrable. `10-PROTOTYPE-AND-ROADMAP.md` builds only the spine.

## A10 — "The AGI vocabulary is doing no work."

Correct. Terms deleted in v2, each replaced by something falsifiable:

| Deleted | Replacement | Why |
| --- | --- | --- |
| "self-evolving" | scoped parameter and policy updating under gates | Names the actual mechanism |
| "world model" | model federation with declared envelopes | The monolith was never buildable |
| "AGI-level" | (removed) | Claims capability the design does not have |
| "autonomous discovery" | autonomous *prioritisation*; human-executed validation | Describes what actually happens |
| "understands" | predicts, within a stated envelope, with measured calibration | Falsifiable |

## A11 — "Value of information is a fantasy of quantification."

Computing `E[Δ entropy] × utility / cost` requires a utility function over possible discoveries
that nobody can write down. Any number produced will be arbitrary dressed as principled.

**The attack lands.** v2 fix: VOI is demoted from an optimisation objective to a **coarse ordinal
prioritisation heuristic** with human-set weights over a small number of buckets, plus a logged
decision record so the T1 policy learner can improve the ranking from revealed preference over
time. The mathematical form is retained only for the *within-investigation* case, choosing among
discriminating measurements, where the utility genuinely is entropy reduction over a defined
hypothesis set and the computation is legitimate.

## A12 — "Your FDR guarantee does not hold."

The hypothesis family is data-dependent and adaptively chosen; e-BH controls FDR under stated
conditions that an adaptive, human-in-the-loop portfolio does not obviously satisfy.

**The attack lands.** v2 position: the guarantee is treated as a *heuristic target*, and the
actual false-discovery rate is **measured** on the Calibration Range rather than derived. If the
Range says the empirical FDR at a given threshold is 22%, that is the number that goes in the
dossier, whatever the theory says. Derived guarantees inform the design; measured rates inform
the claims.

## A13 — "So can it actually discover anything?"

The honest answer, with the boundary drawn sharply:

**Yes**, for: new quantitative regularities among measured quantities; invariants; moderators
that reconcile conflicting literature; refutations and scope corrections; associations with
outcome given linked data; and reproducible phenotypes that fit no existing category. All of
these require human confirmation, and all of them are real knowledge that did not previously
exist.

**No**, for: anything requiring an observable the system does not have; causal claims from
observational tissue data; and novel *mechanisms* as opposed to novel *relations*.

The right historical analogy is not "AI discovers new physics." It is Breslow measuring melanoma
thickness and finding it predicted survival better than the prevailing categorical scheme — a
quantitative regularity in morphology, found by systematic measurement and honest statistics.
This architecture is a machine for doing that continuously, at scale, with the bookkeeping done
correctly. That is a worthwhile machine and it does not require any AGI.

The most likely first genuine outputs are unglamorous: *"this widely cited relationship holds
only in buccal mucosa above φ=0.4, and not at all on our restained sections."*

---

## v2 — the redesign after the attack

Fourteen changes, all folded into the documents above:

1. **No monolithic world model.** A federation of scoped, individually falsifiable models plus a
   consistency checker. *(pre-empted in `03`)*
2. **Held-out-fitted predictors.** Discovery-grade predictions come from models fit with explicit
   leave-lab / leave-scanner / leave-time-block exclusions. *(A4)*
3. **Attribution intervals, not point attributions.** A decomposition family; escalation requires
   robustness across it. *(A5)*
4. **Independence audits on instrument swaps.** Training-data overlap and architecture family are
   recorded; non-independent swaps are `WEAK_SWAP` and do not clear the gate. Physical
   perturbation preferred over model swap. *(A3)*
5. **Frame perturbation as a mandatory tribunal channel.** *(A3)*
6. **Archival back-testing** as a standard channel and the primary drift/discovery discriminator.
   *(A8)*
7. **Model holidays** against a nonparametric baseline, to find uniform misspecification. *(A7)*
8. **An open `UNKNOWN_CHANNEL` account** with prior mass, plus scheduled external adversarial
   channel review. *(A7)*
9. **Template-generated finding statements.** Free-text narration removed from the output path;
   mechanistic and causal verbs gated on `mechanism_class` and interventional evidence. *(A6.4)*
10. **VOI demoted** to ordinal prioritisation outside the within-investigation case. *(A11)*
11. **FDR measured, not derived**, on the Calibration Range; measured numbers go in dossiers.
    *(A12)*
12. **The business case is refutation, scope narrowing, and QC.** Discovery is upside. *(A2)*
13. **AGI vocabulary removed** throughout. *(A10)*
14. **Build the spine only.** Federation, reasoners, portfolio, and self-improvement are all
    phase-2+. *(A9)*

None of the fourteen weakens the core. Eleven of them make it harder to fool, and three of them
make it smaller.
