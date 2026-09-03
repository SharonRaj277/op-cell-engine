# 09 — (L) What can be built in 2026, (M) What is research

Four honesty levels are used throughout:

- **BUILD** — ordinary engineering; the techniques are mature and the risk is schedule risk.
- **HARD** — buildable, but the difficulty is organisational or data-collection, not algorithmic.
  These are the ones that actually kill projects.
- **RESEARCH** — an open problem. Partial results exist; a solution does not.
- **VAPOUR** — currently unachievable, and claiming otherwise is dishonest.

## L — The buildable system

| Component | Status | Notes |
| --- | --- | --- |
| Append-only hash-chained evidence log; bitemporal store | **BUILD** | Event sourcing. Weeks, not months. |
| Content-addressed WSI/ROI/mask storage | **BUILD** | Standard. |
| Instrument metadata capture and registry | **HARD** | Trivial code; requires changing lab practice, LIS integration, and sustained discipline. This is the actual gating item for the entire architecture. |
| Canonical epithelial frame (φ) fitting | **BUILD** | Basement-membrane segmentation → distance/level-set normalisation. Established in the literature; needs careful validation on rete-rich and tangentially-cut regions. |
| Feature fields `f(φ)` with uncertainty | **BUILD** | Binning or GP regression over per-object measurements. |
| Measurement models (bias/variance vs instrument) | **HARD** | Requires deliberate calibration data: phantom slides, serial sections, repeat scans, inter-scanner panels, manual annotation subsets. Cheap per unit, tedious, and nobody wants to do it. |
| Sealed prediction register with trusted timestamps | **BUILD** | Hashing plus an anchoring service. Days. |
| Proper scoring rules; calibration monitoring | **BUILD** | CRPS, log score, reliability diagrams. |
| Discrepancy ledger + attribution + balance invariant | **BUILD** | Nested model comparison / Shapley over accounts. |
| Attribution intervals over a decomposition family | **BUILD** | More compute, same code. |
| Structure scoring (e-processes, permutation nulls, stratum MI) | **BUILD** | Standard statistics. |
| Confound tribunal (stratification, specification curve, negative/positive controls) | **BUILD** for the code, **HARD** for the metadata it depends on | The channel list is the easy part. |
| Instrument-swap replication + independence audit | **HARD** | Needs a second scanner, a second segmenter with disjoint training data, and annotator time. Organisational, not technical. |
| Archival back-testing | **HARD** | Needs archive access and a pipeline for old blocks. Highest value per unit of effort in the whole plan. |
| Invariant hunter (typed symbolic regression over fields) | **BUILD** | PySR/SINDy-class methods are mature. The domain work is the dimensioned grammar and the null models. |
| Residual miner | **BUILD** | |
| Contradiction/moderator miner | **BUILD** given scoped claims; **RESEARCH** for the scope extraction that feeds it | |
| Epistemic type lattice with propagation and taint | **BUILD** | It is a type system. A few hundred lines; see `prototype/`. |
| Provenance DAG with acyclicity and replay | **BUILD** | |
| Scope predicate algebra | **BUILD** for the algebra; **HARD** for populating scopes accurately | |
| Mechanism-card DSL, compiler, dimensional checker | **BUILD** | Small typed language; the restriction *is* the design. |
| Hierarchical Bayesian field models | **BUILD** | Stan / NumPyro / PyMC. |
| Held-out-fitted predictor ensembles (leave-lab/scanner/time-block-out) | **BUILD** | Compute cost only. |
| e-values, test martingales, e-BH | **BUILD** | Mature; implementations exist. |
| Calibration Range (synthetic phenomenon injection, measured FDR) | **BUILD** | Deserves a dedicated engineer. Nothing else in the plan is trustworthy without it. |
| LLM proposal engine behind a deterministic gauntlet | **BUILD** | The gauntlet is the work; the LLM is a component. |
| Literature → claims + effect sizes extraction | **BUILD** at ~70–85% with human review | Good enough to be useful, not good enough to be trusted unreviewed. |
| Literature → *validity envelope* extraction | **RESEARCH** | See M1. |
| Template-generated finding statements | **BUILD** | And strictly better than free generation. |
| Clinical firewall as a separate materialised view | **BUILD** | |
| Portfolio prioritisation (ordinal) | **BUILD** | |
| Within-investigation experimental design (max expected discrimination) | **BUILD** | Bayesian optimal experimental design, well-established for small hypothesis sets. |
| Work-order emission for human-executed experiments | **BUILD** | |
| T0/T1 self-improvement with canarying | **BUILD** | Contextual bandits with logged rewards. |
| Capability lattice enforcement (no write path to T4) | **BUILD** | Architecture and CI, not cleverness. |

**Summary: the spine is entirely buildable in 2026.** Every component of the minimal prototype in
`10-PROTOTYPE-AND-ROADMAP.md` is BUILD or HARD. Nothing on the critical path is RESEARCH — and
the HARD items are all *laboratory process* items, which is why the roadmap treats metadata
capture as phase 0 rather than as a prerequisite someone will get to later.

## M — The research problems

### M1. Validity-envelope extraction from literature — **RESEARCH**
Reconstructing a machine-checkable scope from a methods section requires reading what an author
*did not say*: cohort selection criteria, staining protocol details, magnification, the
operational definition behind a named feature. Current models produce confident, wrong
envelopes. Partial mitigations exist (fail-closed defaults, `SCOPE_UNVERIFIED` propagation,
human review of scope-critical claims), and the system is designed to survive being bad at this
— which is the correct engineering response to an unsolved problem on a non-critical path.

### M2. Causal discovery from observational tissue data — **RESEARCH, arguably VAPOUR**
Constraint- and score-based causal discovery assumes faithfulness, sufficiency, and i.i.d.
sampling. Tissue data violates all three: massive unmeasured confounding (genetics, exposure,
processing), strong spatial dependence, and selection at every step from referral to block
choice. The architecture's response is to refuse the claim rather than to attempt the method:
observational causal statements are capped at `CONJECTURED` by the type system. Elevation requires
intervention, a defensible natural experiment, or longitudinal data with a tested exclusion
restriction. **Do not build a causal discovery module for OP-OS v1.** It would produce
confident, wrong DAGs, and they would be believed.

### M3. Novel *mechanism* synthesis — **RESEARCH**
Generating a new relation among measured quantities is tractable (symbolic regression). Generating
a new *generative process* — a biological mechanism, in the sense a cell biologist means it — from
morphological data alone is not. It is also partly a definitional problem: without molecular
observables, "mechanism" is not identifiable from morphology, and a program that fits is a
phenomenological model wearing mechanistic vocabulary. Hence the `mechanism_class` field and the
prohibition on mechanistic verbs without interventional evidence.

### M4. Automatic ontology revision — **RESEARCH, and deliberately excluded**
A system that changes its own categories retroactively reinterprets its entire history. The
technical problem (concept drift, category splitting/merging with migration) is open; the safety
problem is worse. Human enactment is the position, and it is not a placeholder for a future
autonomous version.

### M5. Open-ended discovery — **RESEARCH**
Everything here discovers *within a fixed measurement space and a fixed representational
vocabulary*. A system that invents genuinely new observables — that decides to start measuring
something nobody has named — is not achievable with this architecture or, as far as anyone can
demonstrate, with any current one. The honest framing: OP-OS can discover new *relations*; it
cannot discover new *variables* outside its representational vocabulary. Expanding that
vocabulary is a human act.

### M6. Drift versus discovery — **FUNDAMENTAL LIMITATION**
As established in `08 A8`. Archival back-testing and physical control tissue are strong partial
defences. A slow real change in the referred population and slow drift in an unmeasured process
channel remain confusable in principle.

### M7. Calibrated uncertainty on out-of-distribution specimens — **RESEARCH**
Conformal prediction gives coverage guarantees under exchangeability, which is exactly what
fails when it matters. Out-of-envelope abstention is the practical substitute and it is a
retreat, not a solution.

### M8. Real value-of-information over scientific outcomes — **RESEARCH**
Requires a utility function over possible discoveries. Ordinal prioritisation with revealed
preference learning is the buildable substitute.

## Explicitly vapour

Things that would be dishonest to promise, listed so that nobody in a funding conversation
promises them:

- A system that autonomously discovers and validates new pathology without humans.
- A system that establishes causation from retrospective slide archives.
- A system whose novelty verdicts mean "new to science" rather than "absent from an index".
- A system that safely rewrites its own ontology.
- A system whose stated confidence is trustworthy without a measured calibration history.
- Any claim that the architecture is "AGI-level". It is a scientific instrument with good
  bookkeeping, and that is a higher compliment than it sounds.
