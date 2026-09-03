# 06 — (I) Knowledge update, (J) Bounded self-improvement

---

## Part I — The knowledge-update mechanism

### I.1 The pipeline

```
source (paper | guideline | dataset | local measurement | human judgement | finding dossier)
   │
   ├─► 1. INGEST      append raw to evidence log; content-address; autophagy check
   ├─► 2. EXTRACT     claims + quantities + effect sizes + units          [LLM, capped SPECULATIVE]
   ├─► 3. SCOPE       reconstruct the validity envelope from methods sections
   │                  missing scope ⇒ SCOPE_UNVERIFIED flag, never a silent default
   ├─► 4. NORMALISE   units, dimensions, feature definitions → ontology terms
   ├─► 5. COMPILE     attempt to produce an executable card; failures stay DESCRIPTIVE
   ├─► 6. RESOLVE     dedupe/merge against existing knowledge under normalisation
   ├─► 7. RECONCILE   envelope algebra → CONSISTENT | NOT_COMPARABLE |
   │                  DEFINITION_MISMATCH | CONTRADICTION_IN_OVERLAP
   ├─► 8. WEIGH       evidence hierarchy → proposed epistemic type and flags
   ├─► 9. GATE        promotion gate by target type (see I.4)
   └─►10. COMMIT      signed evidence-log entry; knowledge base recomputed as a view
```

Step 3 is where most systems fail. A claim extracted without its envelope is worse than no
claim: it will be applied outside the conditions under which it was established, and it will
generate false contradictions with everything else. Scope extraction is genuinely hard
(`09-FEASIBILITY-2026.md` puts it at partial), which is why `SCOPE_UNVERIFIED` is a permanent,
propagating flag rather than a to-do.

### I.2 Never overwrite. Six typed transitions.

| Transition | What happens | Gate |
| --- | --- | --- |
| **Reinforce** | Evidence count and posterior update; type may rise if independence criteria met | Automatic |
| **Reparameterise** | Card parameters move within priors | Automatic |
| **Narrow** | Envelope contracts to where the card actually works | Automatic + notify |
| **Fork** | A sibling card is created for a sub-envelope; both live; router arbitrates | Automatic |
| **Supersede** | New card dominates old across the whole envelope | Human sign-off |
| **Refute** | Card moves to `REFUTED`, retained forever, still queryable | Human sign-off |

Deletion does not appear in the table. `REFUTED` and `SUPERSEDED` knowledge is retained because
(a) provenance replay requires it, (b) the history of what the system believed and why is itself
data for the meta-layer, and (c) refuted claims recur in new literature and must be recognised
rather than re-learned.

AGM-style belief revision — the classical formalism — is a poor fit and is deliberately not
used: it maintains consistency by *contraction*, i.e. by deleting beliefs, whereas this system's
value depends on holding contradictions explicitly, scoped, until a moderator resolves them.
Consistency is not a goal state here; it is a signal.

### I.3 The evidence hierarchy, adapted for a lab that measures

Standard evidence hierarchies (GRADE and relatives) rank study designs. They need one
domain-specific amendment that changes a lot:

```
1. Local measurement, in-envelope, instrument-swap replicated        ← highest
2. Multi-site replication in-envelope
3. Local measurement, in-envelope, single instrument
4. External study, in-envelope, large and pre-registered
5. External study, envelope overlapping but not contained
6. Guideline / consensus statement                       (high authority, low specificity)
7. Single external study, envelope unverified
8. Case report / expert opinion
9. System-generated conjecture                                       ← lowest, and never rises
   without independent evidence attaching
```

The amendment is that **your own in-envelope measurement outranks a larger external study whose
envelope only partially overlaps yours.** This inverts the usual instinct to defer to the bigger
paper, and it is correct: a 5,000-case study on colonic mucosa scanned on different hardware is
weaker evidence about *your* oral epithelium measurements than 60 of your own specimens. Getting
this right is what stops the system from being talked out of its own data by the literature —
which is the failure mode of every retrieval-centric design.

### I.4 Promotion gates

| Target type | Required |
| --- | --- |
| `SPECULATIVE` | Compiles and type-checks. Nothing else. |
| `CONJECTURED` | + explicit prior, + discriminating predictions derived, + novelty check run |
| `INFERRED` | + sealed pre-registered test, + e-value past pre-specified threshold, + tribunal `SURVIVES`, + within alpha budget |
| `INFERRED` w/o `SINGLE_INSTRUMENT` | + instrument-swap replication (I5) |
| `MEASURED` | + traceable to specimens and calibrated instruments, + QC passed |
| `DERIVED` | + machine-checked proof term from stronger inputs |
| `ESTABLISHED` | + human ratification, + external corroboration, + review board sign-off |
| Anything clinically visible | + the clinical firewall in `07-SAFETY-PROVENANCE.md` |

### I.5 Retraction and correction propagate by replay

When a source is retracted, corrected, or found fraudulent, or when a bug is found in a
pipeline version, the response is not a patch. It is:

```
mark source RETRACTED in the evidence log (append, never edit)
→ query the provenance DAG for the transitive closure of everything downstream
→ flag all of it RETRACTED_SOURCE
→ replay knowledge construction from the log with that source excluded
→ diff old view against new view
→ report the diff: what the system believed only because of the retracted source
```

This is only possible because of I7, and it is the strongest practical argument for building the
evidence log first. The diff — "here is everything we believed for the wrong reason" — is a
capability essentially no knowledge system has today, and it is nearly free once the log exists.

---

## Part J — Self-improvement, bounded

### J.1 The capability lattice

Self-modification is not one thing. Five tiers, each with a different authority, and the
boundary between them is a code boundary, not a policy:

| Tier | What may change | Authority | Reversal |
| --- | --- | --- | --- |
| **T0** | Card parameters within priors; scope narrowing; scorecards; ledger balances | Autonomous, continuous | Automatic (replay) |
| **T1** | Retrieval strategies, attribution heuristics, hypothesis priors, experiment-selection policy | Autonomous within canary + Range gates | Automatic (policy version rollback) |
| **T2** | New mechanism cards; new siblings; scope *widening*; new derived quantities | Human review of dossier | Log-level revert |
| **T3** | Ontology amendments; new entity/relation/quantity types; new measurement models | Human enactment; system may only propose | Requires re-derivation |
| **T4** | Promotion gates, epistemic type lattice, scorer, tribunal, alpha policy, the Calibration Range itself | **Human only. The system has no write path.** | N/A |

**T4 is the whole safety story in one row.** The learner may not modify its own referee. Every
reward-hacking and Goodhart failure available to a self-improving system runs through some form
of editing the evaluator, and the defence is architectural: the scorer, the gates, the type
lattice and the Range live in a separately-versioned, signed artefact that no code path
reachable from P5–P9 can write to. Not a permission check — no write path.

### J.2 What T1 learning actually is

Episodic memory (L4) is a labelled dataset about the system's own behaviour, and the honest
supervised problems in it are modest but real:

- **Retrieval policy.** Which query formulations found evidence that changed a posterior?
  Reward = posterior movement, not relevance judgement.
- **Attribution heuristics.** Which nuisance channels actually absorbed surprise historically?
  Learn the channel ordering per feature family.
- **Hypothesis priors.** The Range and settled investigations give ground truth on how often
  each hypothesis *kind* was correct. These priors are learnable and directly improve triage.
- **Experiment-selection policy.** Which planned probes actually moved posteriors per unit cost?
  A contextual-bandit problem with genuinely observed rewards.
- **Reasoning tactic selection.** Which reasoner to route which query shape to.

Every T1 change is deployed by **canary**: the new policy runs in shadow alongside the incumbent
on the same stream, both are evaluated on the Calibration Range and on held-out settled
investigations, and promotion requires a pre-specified improvement with no regression in
false-discovery rate. A T1 policy that improves discovery rate while degrading FDR is rejected
automatically — that particular trade is the one a naive optimiser will always try to make.

### J.3 The ontology is proposed, never enacted

Ontology changes retroactively reinterpret the entire history: split a category and every past
claim scoped by it becomes ambiguous. So T3 is human-enacted, permanently, and the system's role
is to build the case:

- "Category `moderate dysplasia` has bimodal residual structure in three independent strata;
  proposed split, with the discriminating measurements, the affected claim set, the migration
  plan for existing scopes, and the replay diff if enacted."

That dossier is enormously valuable and completely safe, because a proposal is not a change.

### J.4 What the system may never do to itself

Stated as hard invariants, checked in CI, and each one exists because of a specific known
failure mode:

1. Modify the scorer, gates, type lattice, tribunal, or Calibration Range. *(Goodhart)*
2. Widen its own validity envelopes without human review. *(silent scope creep — the most likely
   route to clinical harm)*
3. Re-ingest `SYSTEM_AUTHORED` content as evidence. *(autophagy / model collapse)*
4. Delete or edit anything in the evidence log. *(loss of replay)*
5. Spend alpha or specimen budget beyond its allocation. *(silent multiplicity)*
6. Promote anything to a clinically-visible surface. *(clinical firewall)*
7. Create a provenance cycle. *(self-reinforcing belief)*
8. Raise the epistemic type of a claim using only its own generated content. *(hypothesis
   laundering)*
