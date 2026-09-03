# 00 — Thesis: why the document-centric stack is the wrong foundation

## 0.1 The request, restated precisely

You asked for a knowledge layer that can discover. Discovery, operationally, is the event in
which a system's expectations fail in a way that is *reproducible*, *structured*, and
*irreducible to known nuisances* — and then survives an attempt to explain it away. Every
component of the architecture below exists to make that event detectable, countable,
and trustworthy. Nothing exists to make question-answering nicer.

That single reframing kills most of the conventional stack immediately, and it is worth being
explicit about why rather than waving at "RAG is not enough."

## 0.2 Why RAG, GraphRAG, agentic RAG and knowledge graphs are the wrong *foundation*

They are not useless. Every one of them appears somewhere in this architecture as a
**subsystem**. The claim is narrower and stronger: none of them can be the *centre*, because
of four structural mismatches.

**1. They are architectures over assertions, and OP-OS's primary data is not assertions.**
A retrieval system's atom is a passage; a knowledge graph's atom is a triple. OP-OS's atom is
a *measurement of a physical specimen under an instrument* — 40,000 nuclei with morphometry,
positions, and a normalised epithelial depth φ, produced by segmentation model v3.1.2 on a
scanner with a particular point-spread function. There is no faithful lowering of that into
`(dysplasia, hasFeature, nuclearPleomorphism)`. The lowering discards exactly the quantitative
structure in which a new relationship would live. **You cannot discover `A(φ)/B(φ) ≈ const` in
a triple store, because the triple store never held `A(φ)`.**

**2. Retrieval maximises similarity; discovery lives in dissimilarity.**
Nearest-neighbour retrieval is a machine for finding the parts of the corpus that look most
like what you already said. It is structurally the wrong instrument for "nothing in my
knowledge explains this." A retriever that returns nothing relevant is indistinguishable, in a
RAG system, from a retriever that is broken. In OP-OS that must be a *first-class positive
signal* with its own downstream pipeline.

**3. Text-derived knowledge has no truth-conditions the system can check.**
"Basal cell hyperchromasia is a feature of dysplasia" cannot be tested by any computation the
system can run. It can only be re-retrieved. Knowledge that cannot generate a prediction over
measurable quantities is epistemically inert — it can be cited, never confirmed, never
refuted, never improved. A discovery engine built out of inert knowledge cannot discover.

**4. Conflicts in a graph are flat; conflicts in pathology are almost always about scope.**
Two papers "contradicting" each other on nuclear area in oral dysplasia usually differ in
cohort, stain protocol, magnification, tumour site, or the operational definition of the
feature. A knowledge graph that stores this as `claim_A CONTRADICTS claim_B` has destroyed the
information that matters, which is *the moderator variable that separates them*. Worse: that
destroyed information is one of the richest available veins of genuine discovery.

A fifth, practical mismatch: RAG's failure mode is fluent plausible text, and the only defence
is a human reading it. That defence does not scale to a system that is supposed to run
continuously over every specimen the lab produces.

## 0.3 The inversion

Standard stack:

```
documents → chunks → embeddings → retrieval → LLM → answer
                                                 ↑
                                          reasoning bounded here
```

OP-OS stack:

```
specimens → measurements → canonical fields → executable models → predictions
                                                    ↑        ↓
                                literature ─── constrains   compared against reality
                                                             ↓
                                                    discrepancy ledger
                                                             ↓
                                                  attribution / discovery
```

Literature does not sit upstream feeding the reasoner. It sits *sideways*, supplying priors,
candidate mechanisms, and scope information to a model whose actual authority comes from
measured specimens. **Papers grant priors; measurements grant posteriors.**

## 0.4 The seven load-bearing inversions

Everything in this repository follows from these. If you reject one, large parts of the
architecture collapse — that is the point of listing them separately.

### I1. Predict before you look. Every specimen is a pre-registered experiment.

The single highest-value structural decision in the design. Before OP-OS runs its full
analysis on an incoming case, the world model emits a **sealed, timestamped, content-addressed
prediction** over the quantities it will subsequently measure — with calibrated intervals.
Only then is the case analysed, and the prediction scored.

Consequences, all of them large:

- Every routine clinical or research specimen becomes a free, properly pre-registered test of
  every model the system holds, at zero marginal cost. A lab doing 3,000 cases a year is
  running 3,000 pre-registered experiments a year that it currently throws away.
- Surprise becomes *measurable* rather than *asserted*. "This observation is outside my
  explanatory model" acquires a number instead of being a phrase an LLM emits.
- Post-hoc storytelling is structurally prevented. You cannot fit the explanation to the data
  when the prediction was sealed before the data existed.
- The prediction stream *is* the distribution-shift monitor, the model-quality monitor, and the
  anomaly detector — one mechanism serving three purposes, which is how you can tell it is the
  right mechanism.

Everyone in this field is building retrospective analysis. Prediction-first ingestion is cheap,
boring engineering that converts an entire clinical workflow into a scientific instrument.

### I2. Knowledge is executable or it is only descriptive.

The unit of knowledge is not a triple or a chunk. It is a **Mechanism Card**: a typed,
parameterised, *runnable* fragment that consumes a specimen context and emits a distribution
over measurable quantities, plus an explicit validity envelope, provenance, competing
siblings, and a live predictive scorecard. Assertions that cannot be compiled into a predictive
form are retained as `DESCRIPTIVE` and are never allowed to carry inferential weight alone.

This is what makes the knowledge base self-correcting: a card that stops predicting starts
losing status automatically, without anyone deciding to distrust it.

### I3. Surprise is conserved. Discovery is double-entry bookkeeping.

Adopted wholesale from accounting, and it is the organising metaphor of the whole system.
Every unit of prediction error on every specimen must be *posted* to exactly one of three
accounts:

- **Mechanism** — attributed to a known mechanism operating as expected but mis-parameterised.
- **Nuisance** — attributed to an instrument or process channel (scanner, stain lot, fixation,
  section thickness, cutting obliquity, annotator, segmenter version).
- **Unexplained** — the residual ledger.

Nothing is allowed to evaporate. The books do not close until every discrepancy is attributed.
Machine-learning anomaly detection is stateless and per-instance; science is about *systematic,
accumulating residual*. The ledger makes the accumulation explicit, persistent, queryable, and
auditable — and a discovery is precisely a ledger account whose balance grows structurally
rather than randomly.

### I4. The null hypothesis is always the microtome.

In computational pathology, the overwhelming majority of apparently novel quantitative
relationships are batch effects: scanner colour response, stain lot, fixation delay, block
age, section thickness, cutting angle, laboratory, annotator drift, and — most insidiously —
the segmentation model's own inductive biases. A discovery architecture without a first-class
adversarial confounder model is a false-discovery generator with good UX.

So: no residual is promoted to *candidate phenomenon* until it has survived a **Confound
Tribunal** whose explicit job is to kill it using nuisance variables, with the prior weighted
firmly toward "this is an artefact."

### I5. A finding must survive a change of instrument.

The sharpest version of I4, and the one most specific to OP-OS. OP-OS's own vision model
*defines* the features it measures. A relationship between "nuclear area" and φ may be a
property of segmentation model v3.1.2's boundary bias as a function of chromatin density, not
a property of oral epithelium. This is not hypothetical; it is the default outcome.

Therefore: **every promotable finding must be reproduced through a measurement pathway that is
independent of the one that discovered it** — a different segmenter, a different magnification,
a different stain, a different scanner, or human annotation. Instrument invariance is a
promotion *gate*, not a nice-to-have. Every claim is stored bound to the exact measurement-model
version that produced it, and a claim that has never been reproduced off its originating
instrument is typed as such, permanently and visibly.

### I6. Scope is part of the claim, and contradiction is a discovery signal.

Every claim carries an explicit machine-checkable **scope predicate** over tissue type, site,
stain, cohort, φ range, magnification, instrument, and feature definition. Two claims are only
in contradiction if their scopes provably intersect. When two well-evidenced claims conflict
inside an overlapping scope, the correct system behaviour is not "flag conflict" — it is
**search for the moderator variable that separates them**, which is a hypothesis-generation
trigger in its own right. Contradiction mining is the third discovery engine in the system,
alongside residual mining and invariant hunting.

### I7. The knowledge base is a materialised view, never a source of truth.

The only authoritative store is an append-only, hash-chained **Evidence Log**. The knowledge
base — cards, claims, parameters, scores — is a deterministic function of `(evidence log,
policy version, model version)` and can always be recomputed from scratch.

This turns three hard problems into one easy one. Rollback is replay. Retraction propagation is
replay with one source removed. "How did the system come to believe this?" is a query over an
immutable DAG. Knowledge corruption stops being catastrophic and becomes repairable, which is
the precondition for allowing any autonomy at all.

## 0.5 What "discovery" can honestly mean here

A boundary must be stated up front, because the whole document is dishonest without it.

**The system can discover anything expressible as a relation among quantities it can measure.
It can discover nothing that requires an observable it does not have.**

OP-OS will not discover a signalling pathway. It has no molecular observables. What it can
genuinely discover — and these are real, publishable, historically precedented classes of
finding — are:

1. **New quantitative regularities**: a relationship between measurable morphological or
   architectural quantities that is not described in the literature. (Historically: Breslow
   depth, Gleason patterns, mitotic indices — all of them are exactly this class of finding,
   discovered by humans staring at slides.)
2. **Invariants**: functional combinations that hold stable across specimens whose components
   vary widely. These are the highest-value class and the one your φ example describes.
3. **Moderators**: the hidden variable that reconciles two conflicting literatures.
4. **Refutations and scope corrections**: an established claim that fails to replicate, or that
   holds only within a narrower envelope than stated. Undervalued and much more attainable than
   novel positive findings.
5. **Prognostic/associative structure**: a measured relationship to outcome not previously
   reported. Requires linked outcomes data; state this as an explicit dependency.
6. **Anomalous entities**: a reproducible cell/architecture phenotype that does not fit any
   category in the working ontology.

What it cannot do without new research (developed in `09-FEASIBILITY-2026.md`): establish
*causation* from observational tissue data, synthesise genuinely novel *biological mechanisms*
rather than novel relations, or revise its own ontology safely.

One more honesty constraint, enforced in the type system: **novelty relative to an indexed
corpus is not novelty in the world.** The system may only ever emit `NOT_FOUND_IN_CORPUS(v)`,
never "new to science." That distinction is a type, not a caveat in prose.

## 0.6 What the system actually is

Strip the AGI vocabulary — and it should be stripped; `08-ADVERSARIAL-REVIEW.md` does it
deliberately. What remains is not smaller than the ambition, it is more achievable than it:

> **A continuously-running, self-calibrating scientific instrument that turns a pathology
> laboratory's routine throughput into a stream of pre-registered experiments against an
> explicit, executable, versioned model of tissue — and that is honest, in a
> machine-checkable way, about which of its outputs are measured, derived, inferred,
> conjectured, or unknown.**

That system does not need to be an AGI to produce knowledge that did not previously exist. It
needs to be relentless, calibrated, and unable to lie to itself. The remainder of this
repository is about making it unable to lie to itself.
