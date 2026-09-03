# 04 — (E) Reasoning architecture

## 4.1 The organising rule

> **The generative model proposes. It never disposes. Nothing an LLM writes enters any store.**

Every candidate structure — hypothesis, mechanism card, scope, extraction from a paper — is
emitted as a *proposal* and must survive a deterministic gauntlet before it exists as anything
more than `SPECULATIVE`. This is what makes hallucination structurally survivable rather than
merely mitigated: a hallucinated mechanism either fails to compile, fails to reproduce known
data, fails identifiability, or fails the statistics. Fluency buys it nothing.

```
LLM / generator ──► PROPOSAL
                       │
   ┌───────────────────▼────────────────────────────────────────────┐
   │ THE GAUNTLET (deterministic, versioned, human-signed)          │
   │                                                                │
   │ 1. PARSE        into the typed DSL                             │
   │ 2. TYPE-CHECK   entities/quantities exist in the ontology      │
   │ 3. DIMENSIONS   dimensional analysis; units must balance       │
   │ 4. COMPILE      to an executable forward simulator             │
   │ 5. SANITY       reproduces already-known data in its envelope?  │
   │ 6. IDENTIFY     are its parameters identifiable from available  │
   │                 measurements? (profile-likelihood flatness)     │
   │ 7. NOVELTY      equivalent to an existing card under unit and   │
   │                 definition normalisation? → merge, not create   │
   │ 8. DISCRIMINATE does it predict anything a sibling does not?    │
   │                 if not, it is not a hypothesis, it is a synonym │
   │ 9. STATISTICS   pre-registered test, e-value, tribunal          │
   └───────────────────┬────────────────────────────────────────────┘
                       ▼
              typed, provenanced object  (≤ CONJECTURED until evidence attaches)
```

Stages 1–8 are cheap and deterministic and kill the overwhelming majority of proposals. Stage 9
is the expensive one, which is exactly why the cheap filters come first.

## 4.2 Five reasoners

Different questions need different machines. A single LLM doing all five is the design that
produces confident nonsense at every one of them.

**1. Deductive / symbolic.** Unit and dimensional algebra, monotonicity and constraint
propagation, interval arithmetic, and lightweight theorem checking over the model federation.
Its highest-value job is **consistency auditing**: does a proposed card violate a conservation
constraint? Stratified epithelium in homeostasis gives a real one — basal proliferation must
balance surface desquamation, so a card predicting sustained cell-density increase at fixed
thickness with no compensating flux is *inconsistent*, and can be rejected before any data is
consulted. Output type: `DERIVED`, with a proof term.

**2. Probabilistic.** Hierarchical Bayesian inference and probabilistic programming over the
field and population models: parameter posteriors, model comparison, predictive distributions,
and — critically — the *calibrated intervals* the kernel seals. Output type: `INFERRED`, with
anytime-valid bounds.

**3. Causal.** Operates only over explicit causal sketches with declared assumptions. Does
identifiability analysis (is this effect estimable from the available observables at all?),
back-door/front-door reasoning, sensitivity analysis to unmeasured confounding, and
counterfactual queries. Output type: `CONJECTURED` from observational data, ceiling enforced by
the lattice; `INFERRED` only under intervention or a defensible natural experiment.

**4. Analogical / structural.** Structure-mapping between tissue systems, and between the local
model and literature-derived cards from other organs. Genuinely useful as a *generator* of
candidates — cervical, oesophageal and oral stratified epithelium share differentiation
programmes, so a card that works in one is a strong proposal for another. Output type:
`SPECULATIVE`, permanently, until tested locally. Analogy is a source of hypotheses and never a
source of belief.

**5. Abductive.** Inference to the best explanation, and the engine of `05-DISCOVERY-ENGINE.md`.
Explicitly enumerates the *space* of explanations, not the best one, and always instantiates the
boring alternatives first (artefact, known-restated, mis-parameterisation) before the
interesting ones.

An **arbiter** routes queries, combines outputs, and — the part that matters — refuses to
combine outputs whose scopes do not intersect, returning `NOT_COMPARABLE` instead of a
confident synthesis. Most systems' worst answers come from silently unifying incomparable
things.

## 4.3 Reasoning beyond retrieved documents — mechanism by mechanism

Your eleven requirements, each with the concrete machinery, and an honest status.

| Requirement | Mechanism | Status |
| --- | --- | --- |
| Combine multiple known facts | Composition of mechanism cards in the DSL; the composed program is executed, and the composition itself is type/dimension-checked. Not text concatenation. | **Build** |
| Identify latent relationships | Invariant hunter over field combinations + sparse regression over the residual field (`05 §5.3`) | **Build** |
| Counterfactual reasoning | Interventional queries on causal sketches with declared assumptions; sensitivity analysis reported alongside every answer | **Build (typed CONJECTURED)** |
| Construct competing hypotheses | Sibling cards over a shared signature; abductive enumeration with mandatory boring alternatives | **Build** |
| Reason over mechanisms | Cards are executable, so "reasoning over a mechanism" is running it, perturbing it, and composing it | **Build** |
| Identify missing variables | Residual field that is structured but orthogonal to all measured covariates ⇒ propose a latent; the latent's *shared* loading across features implies a specific correlation structure, which is testable | **Build (weak but real)** |
| Derive consequences | Forward simulation + symbolic propagation of constraints | **Build** |
| Mathematically test consistency | Dimensional analysis, conservation constraints, monotonicity, boundary conditions at φ=0 and φ=1 | **Build** |
| Search for disconfirming evidence | **Disconfirmation-first retrieval**: the retrieval objective is inverted — query for the strongest available refutation, and score retrieval on refutations found, not on relevance | **Build** |
| Distinguish correlation from causation | Enforced by the type lattice; causal claims from observational data are structurally capped at `CONJECTURED` | **Build (enforcement); RESEARCH (actual causal discovery)** |
| Know when reasoning is underdetermined | §4.5 | **Build (partially)** |

**Disconfirmation-first retrieval** deserves a note. Standard RAG retrieves what is most similar
to the claim, which is a machine for building a supportive case. Flipping the objective —
retrieve the passages, datasets, and strata most likely to *contradict* the claim, and treat "no
refutation found after honest search" as the evidence rather than "supporting passages found" —
changes what retrieval is for. It is a small change to implement and a large change to the
system's epistemic character.

## 4.4 The typed DSL

Mechanism cards compile to a small, deliberately restricted, dimensioned language. Restriction
is the point: a language expressive enough to be Turing-complete is a language in which the LLM
can hide arbitrary lookup tables and pass the sanity check by memorising the answer.

```
program   := field_expr | dist_expr
field_expr:= const<unit>
           | param(name, prior, unit)
           | phi                                   -- canonical depth coordinate
           | covariate(name)                       -- specimen/instrument covariate, declared
           | f(field_expr)   where f ∈ {exp, log, logit, pow_k, sigmoid, monotone_spline}
           | field_expr ⊕ field_expr,  ⊕ ∈ {+,−,×,÷}
           | integrate_phi(field_expr) | d_dphi(field_expr)
           | neighbourhood(field_expr, radius<µm>)  -- spatial coupling
dist_expr := Normal(field_expr, field_expr)
           | Gamma(...) | Beta(...) | NegBinom(...)
           | Mixture([...], weights)
constraint:= monotone(field_expr, phi, ↑|↓)
           | boundary(field_expr, phi=0|1, value)
           | conserves(quantity)
           | dimension(field_expr, dim)
```

Every node is dimensioned; `d_dphi` divides units by the (dimensionless) φ; `neighbourhood`
carries a length scale in µm which the type checker requires to be resolvable at the declared
magnification — a card that requires 0.2 µm coupling cannot be declared valid on a 0.5 µm/px
scan, and the compiler says so.

Parameter counts are bounded relative to the evidence available: the compiler refuses cards
whose parameter count exceeds a budget derived from the specimen count in their envelope. This
is a cheap structural defence against a generator that "explains" everything by adding terms.

## 4.5 Knowing when it does not know

Three distinct failures, three distinct detectors, three distinct honest outputs. Conflating
them is the core sin of retrieval-based systems, which have exactly one failure mode ("no
relevant documents") and one behaviour (answer anyway).

**1. Out of scope.** No card's validity envelope covers the query. Detected by the envelope
algebra. Response: *"I have no model valid for this specimen class"* — plus, usefully, the
nearest envelopes and what would be needed to extend one.

**2. Underdetermined.** Multiple models in the equivalence class fit the data and imply
materially different answers. Detected by: enumerating the sibling set, checking whether their
predictive distributions separate on any *available* observable, and — for parametric cards —
profile-likelihood flatness indicating non-identifiable parameters; for causal sketches,
Markov-equivalence-class size. Response: *"Both X and Y are consistent with everything I can
measure; they differ on Z, which I cannot currently measure. Measuring Z would resolve it."*
That last sentence is the most valuable output the system can produce and almost no deployed
system produces it.

**3. Anomalous.** Data is in scope but the model predicts it badly. Detected by the kernel's
surprise score against sealed predictions. Response: *"This is within my envelope and I got it
wrong"* — which posts to the ledger and may open an Investigation.

The three are reported separately and never blended, because the appropriate human response to
each is completely different: extend coverage, acquire a new observable, or investigate.
