# 05 — (F) Novelty & anomaly, (G) Hypothesis generation, (H) Evidence acquisition

---

## Part F — The novelty and anomaly detector

### F.1 Why ML anomaly detection is the wrong tool

Standard anomaly detection scores an instance against a density model and flags outliers. It is
stateless, per-instance, and unattributed. Science is about *systematic residual*: a single
surprising slide is noise, and a small bias that recurs in the same direction across 400 slides
is a discovery. The architecture must therefore accumulate and attribute, not flag.

### F.2 Surprise, and its decomposition

For each sealed prediction and its realisation, the kernel computes surprise with a strictly
proper scoring rule (log score for densities, CRPS for functional field predictions), in nats.
Total specimen surprise is then decomposed by a constrained attribution fit:

```
S_total  =  S_mechanism  +  S_nuisance  +  S_unexplained

S_mechanism  : surprise absorbed by re-fitting existing card parameters WITHIN their priors
S_nuisance   : surprise absorbed by the measured nuisance covariates via the measurement models
S_unexplained: the orthogonal remainder — posted to a keyed ledger account
```

Implementation is a hierarchical decomposition (nested model comparison, or a
Shapley attribution over the three account groups when the accounts are not nested). Two
disciplines make it trustworthy:

- **Balance invariant.** The three terms must sum to the total, checked every close. If they do
  not, the attributor is discarding evidence and the kernel halts rather than proceeding.
- **Attribution is conservative toward nuisance.** Where mechanism and nuisance can both explain
  a component, it is posted to nuisance. Deliberately biased against discovery. The cost is
  missed findings; the benefit is that the ledger's unexplained accounts are worth reading.

### F.3 From residual to signal: the structure score

An account's *balance* means little; its **structure** is everything. Five tests, each cheap:

| Test | Question | Statistic |
| --- | --- | --- |
| Directionality | Is the error systematically signed? | Sign-test e-process (test martingale) — anytime-valid |
| Frame structure | Is it organised in φ, or scattered? | Autocorrelation / smoothness of residual vs φ against a permutation null |
| Stratum concentration | Is it concentrated in one scanner, lab, lot, operator? | Mutual information between residual magnitude and each nuisance channel |
| Temporal stability | Does it persist across time windows, or drift? | Split-window reproduction; drift detector |
| Noise floor | Is it larger than the measurement model says it can be? | Ratio to propagated measurement variance |

Stratum concentration is the highest-yield test and it is also the one that most often says
*artefact*. That asymmetry is the design working correctly.

An account is escalated only when directionality and frame structure are strong, stratum
concentration is *low*, temporal stability holds, and the effect exceeds the noise floor.

### F.4 The Confound Tribunal

The formal proceeding in which the system attempts, in good faith and at its full ability, to
destroy its own candidate finding. **Prior: it is an artefact.** Escalation requires surviving
all applicable channels:

| Channel | Attack |
| --- | --- |
| Scanner / optics | Stratified re-analysis; re-scan a subset on a different scanner |
| Stain lot & protocol | Stratify by lot; test on restained sections |
| Fixation & processing | Regress against fixation delay/duration, block age, processor run |
| Section geometry | Thickness and cutting-obliquity covariates; serial-section replication |
| Segmentation bias | **Re-measure with an independent segmenter and with human annotation** |
| Frame-fit bias | Perturb the φ-fitting model; does the relationship move with the frame? |
| Shared denominators | Are the two features derived from the same mask, manufacturing correlation? Test with independently derived measurements |
| Selection | How did these specimens enter the cohort? Referral bias, block availability, case difficulty |
| Label noise | Does the effect survive when labels are modelled as noisy rather than true? |
| Annotator drift | Time-ordered rater effects |
| Analytic degrees of freedom | **Specification curve**: re-run across all defensible analytic choices; report the whole distribution, not the best cell |
| Negative controls | Does the same "effect" appear where it must not — permuted labels, irrelevant tissue, synthetic null fields? |
| Positive controls | Does the pipeline recover a *known* effect of comparable size in the same data? If not, the pipeline is not powered to be believed |

Verdicts: `KILLED(channel)` · `SURVIVES` · `SURVIVES_WITH_UNRESOLVED(channels)` ·
`UNDECIDABLE(missing metadata)`. The last is common early on and is a finding about the lab, not
about the tissue: it names exactly which metadata must start being captured.

The tribunal transcript — including every attack that *failed* to kill the candidate — is part
of the dossier. A finding is only as strong as the seriousness of the attacks it survived, and
publishing the attacks is what lets a human judge that.

### F.5 Triage: your section-3 question, answered as a decision procedure

An unexplained observation is routed by *discriminating tests*, not by an LLM's opinion:

| Verdict | Discriminating test |
| --- | --- |
| **Measurement error** | Fails QC; not reproduced on re-measurement of the same physical section; magnitude within instrument tolerance; concentrated in one instrument stratum |
| **Known phenomenon, differently expressed** | Novelty check after unit/definition normalisation finds an equivalent card or claim; or an existing card reproduces it once its parameters are re-fit within priors |
| **Unresolved contradiction** | Two existing claims with intersecting scope disagree here; the observation sits between them → route to moderator mining |
| **Model incomplete** | Structured residual, survives tribunal, but explicable by adding a *known* variable currently absent from the card's inputs |
| **Insufficient evidence** | Structure score fails to separate from the permutation null at the current n; power analysis returns the n required → park with a resume condition, do not discard |
| **Candidate novel phenomenon** | Structured, survives full tribunal, survives instrument swap, not found in corpus, and no existing card can absorb it under re-parameterisation |

Note that five of six routes are unglamorous, and that is the expected distribution. A system
whose triage returns "candidate novel phenomenon" often is miscalibrated, and F.7 measures
exactly that.

### F.6 Novelty is relative to a corpus, and says so

The novelty check normalises units, feature definitions, and scope, then searches the indexed
corpus and the card registry. Its output type is `NOT_FOUND_IN_CORPUS(corpus_version,
coverage_estimate)` — never "novel". Coverage is estimated honestly (indexed venues, date range,
languages, access) and is reported with every claim of novelty. The most likely explanation for
apparent novelty in a domain with a century of descriptive literature is that the relevant paper
is from 1974, in German, and not indexed.

### F.7 The Calibration Range

You cannot trust a discovery engine you have not measured. The Range is a permanent subsystem
that injects **known phenomena into perturbed real data** and measures what the system does:

- Synthetic φ-relationships of known effect size planted into resampled real fields.
- Synthetic *artefacts* planted (fake scanner effects, fake stain-lot shifts) that the tribunal
  must catch.
- Ablated literature: cards removed from the base, then the system asked to rediscover them.
- Pure-null runs: no planted signal at all; every "discovery" is a false one.

Outputs: sensitivity by effect size, empirical false-discovery rate, tribunal specificity, and
calibration of stated confidence. These numbers are the promotion gates in `10-PROTOTYPE`. A
discovery system without a measured FDR is not a scientific instrument, it is a rumour mill.

---

## Part G — The hypothesis generator

### G.1 Enumerate boring first, and make it mandatory

The hypothesis set for any anomaly is generated in a fixed order, and the interesting kinds are
not generated until the boring ones have been instantiated and given explicit priors:

```
1. artefact             (instrument, process, pipeline, selection)      ← highest prior
2. known_restated       (existing card/claim under another name/units)
3. parameterisation     (existing card, wrong parameters)
4. scope_narrowing      (existing card, narrower envelope than believed)
5. missing_variable     (known but unmodelled covariate)
6. novel_relation       (new empirical regularity among measured quantities)
7. novel_mechanism      (new generative process)                        ← lowest prior
```

Priors are explicit numbers, logged, and themselves calibrated against the Range's history. A
generator that cannot state its prior is not permitted to propose.

### G.2 Four generators, one gauntlet

**1. Structural.** Combinatorial edits to the model graph: add a missing edge; introduce a
latent common cause; introduce a moderator; split a card by stratum; merge two cards. Cheap,
exhaustive over a bounded neighbourhood, and it covers kinds 3–5 almost completely.

**2. Symbolic regression / program synthesis over the DSL.** Searches the typed grammar
(`04 §4.4`) for programs that explain the residual field, under an MDL penalty and with
dimensional constraints pruning the space hard. This is the engine for kind 6 and it is mature
technology — sparse identification and genetic-programming symbolic regression are off-the-shelf
in 2026. The domain contribution is the *typed, dimensioned, physiologically-constrained grammar*
that keeps the search from returning uninterpretable overfits.

**3. Analogical.** Structure-mapping from other epithelial systems and other organs. Output is
capped at `SPECULATIVE` and exists to seed the search, not to justify belief.

**4. LLM proposal.** The broadest generator, over literature and the state of the investigation.
Its unique value is *coverage* — it will propose the known phenomenon under an unfamiliar name,
which is exactly the check that most matters and the thing the other three generators cannot do.
Its output goes through the same gauntlet as everything else and is capped at `SPECULATIVE`
until independent evidence attaches.

### G.3 The three discovery modes, as algorithms

**Mode 1 — Residual mining.** Ledger accounts → structure score → tribunal → hypotheses.
Covered above.

**Mode 2 — Invariant hunting.** *This is the direct answer to your section-9 requirement, and
the most valuable algorithm in the document.*

The insight: conservation laws and structural relationships are found not by looking for
correlation, but by looking for **combinations whose variance collapses**. If `A(φ)` varies 3×
across specimens and `B(φ)` varies 3× across specimens, but `g(A, B, φ)` varies 1.05×, then `g`
is capturing something the individual features are not.

```
for each specimen s: fields A_s(φ), B_s(φ), C_s(φ), ...   (with uncertainty)
enumerate candidate combinations g from the typed DSL, complexity-bounded, dimensionally valid
for each g:
    v_within  = Var_φ [ g_s(φ) ]                      averaged over s   # φ-invariance
    v_between = Var_s [ mean_φ g_s(φ) ]                                 # specimen-invariance
    v_null    = variance expected from measurement noise alone (from the measurement models)
    score(g)  = log( Var of components / max(v_within, v_null) ) − λ · complexity(g)
rank; keep g with score above threshold AND v_within not explained by measurement noise
cross-validate by specimen (leave-cohort-out), then by instrument (leave-scanner-out)
→ tribunal (shared-denominator channel is mandatory here) → Investigation
```

Two traps this algorithm must dodge, both handled explicitly:

- **Trivial invariants.** `A/A = 1`. Pruned by requiring `g` to depend non-degenerately on ≥2
  independently-measured quantities and by the MDL penalty.
- **Manufactured invariants.** If `A` and `B` share a segmentation mask, correlated measurement
  error creates a spurious low-variance ratio. This is *the* dominant false positive in
  computational pathology invariant hunting, and it is why the shared-denominator tribunal
  channel and the independent-segmenter swap are non-negotiable.

Your hypothetical — "Feature A changes with φ, Feature B changes with φ, their relationship is
unexpectedly stable, existing knowledge does not explain it" — is exactly `score(g)` being high
for `g = log A − log B` with no card in the federation predicting it. The system's output is
then a typed, scoped, sealed, tribunal-tested `CONJECTURED` candidate relationship with
discriminating predictions attached. Not a claim. A candidate with a way to kill it.

**Mode 3 — Moderator mining from contradiction.** When two claims with provably intersecting
scopes disagree:

```
find covariate set M (measured, or derivable from the frame) such that
    claim_1 holds on {M ∈ R1}  and  claim_2 holds on {M ∈ R2},  R1 ∩ R2 = ∅
subject to: M declared before the search where possible; R found by a constrained
            partition search with strict cross-validation and a permutation null
if found: propose scope narrowing for BOTH claims + a new moderator relation
```

This converts the literature's mess into structure, and it is the cheapest genuine-discovery
route in the whole system because it requires no new tissue — only better bookkeeping about
what everyone already published.

### G.4 Deriving predictions that discriminate

A prediction implied by every live hypothesis is worthless. The planner selects prediction
targets maximising expected discrimination:

```
score(target) = E[ information gain about the hypothesis posterior | measuring target ]  /  cost
              ≈ mutual information between the hypothesis index and the target's outcome
```

For a two-hypothesis contest this is the expected log Bayes factor; for more, expected entropy
reduction over the hypothesis posterior. Targets that all hypotheses agree on are discarded
regardless of how confirmatory they look.

---

## Part H — The evidence acquisition loop

### H.1 The five sources, ordered by cost

| Source | Cost | Latency | Strength | Use |
| --- | --- | --- | --- | --- |
| **Passive harvest** | ~0 | days–weeks | High (pre-registered) | Default. The routine specimen stream settles most bets for free |
| **Literature** | Low | hours | Weak, uncontrolled scope | Priors, novelty check, competing mechanisms |
| **Archival probe** | Low–medium | days | High | Re-analyse existing blocks/slides; recut, restain, rescan |
| **Active probe** | High | weeks | High | New stains/IHC, blinded re-reads, external cohort exchange |
| **Prospective** | Very high | months–years | Highest | Only for findings that have already survived everything else |

The ordering is the policy: **never spend tissue on a question the prediction stream will answer
for free.** Most discovery-agent designs invert this and go straight to experiment planning,
which in pathology means going straight to the most expensive and slowest possible option.

### H.2 The portfolio manager

Investigations compete for four genuinely scarce resources, and one of them is not physical:

```
budget = { tissue_units, wetlab_slots, pathologist_minutes, ALPHA }
```

**Statistical alpha is a conserved resource and must be budgeted like tissue.** A system that
tests continuously without accounting for it will produce discoveries at exactly the rate its
uncorrected multiplicity implies.

Allocation is a bounded knapsack over expected value of information:

```
VOI(inv) = E[ Δ entropy over the model federation ]  ×  downstream_utility(inv)
           ─────────────────────────────────────────────────────────────────
                              expected cost vector · price
```

with diversification constraints (no single investigation may consume more than a fixed
fraction of any budget line), a floor for exploratory work, and mandatory reserve for
replication of already-promoted findings — because re-testing what you already believe is the
first thing an under-resourced system stops doing and the first thing it should not.

### H.3 Anytime-valid statistics, because the system never stops looking

Fixed-sample p-values are invalid under continuous monitoring, and this system monitors
continuously by construction. The whole statistical layer is therefore built on **e-values and
test martingales**:

- Each sealed prediction contributes a likelihood-ratio factor to an e-process.
- Evidence accumulates multiplicatively; the process may be inspected at any time, and stopping
  when it crosses a threshold is valid without correction. This is precisely the property the
  architecture needs and the reason to prefer e-values over p-values here — it is not stylistic.
- Portfolio-level false-discovery control uses **e-BH**: e-values merge by averaging, so
  FDR across all live investigations is controllable without knowing their dependence structure.
- Alpha budget is denominated in e-value thresholds and deducted at *data access* time.

This is mature, implementable statistics, and it is the single technical choice that makes
"continuous autonomous discovery" epistemically legitimate rather than a p-hacking engine with
extra steps.

### H.4 Experiment planning in a domain where the lab is human

Realistic pathology experiments are work orders, not robot instructions:

`recut deeper levels` · `restain with an independent lot` · `rescan on scanner B` ·
`image at 40× instead of 20×` · `apply IHC panel P` · `pull an archival cohort matching scope S` ·
`blinded re-read by two pathologists with a consensus panel` · `serial sections for
frame-perturbation testing` · `prospective collection with protocol P`

Each is emitted as a structured plan with its cost vector, the sealed discriminating predictions
it will settle, the decision rule, and the expected information gain. A human approves and
executes. **This is not a limitation to be engineered away.** Human execution is a natural rate
limiter and a second review point, and the honest version of "autonomous scientific discovery"
in pathology for the foreseeable future is a system that autonomously *decides what is worth
doing* and hands it to people who do it.
