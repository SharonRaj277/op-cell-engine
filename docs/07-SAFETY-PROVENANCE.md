# 07 — (K) Safety, provenance, and the clinical firewall

## 7.1 The provenance spine

Every object in every plane carries a `ProvenanceRef` into a single DAG whose leaves are
evidence-log entries. Four properties are enforced at write time, not audited afterwards:

1. **Acyclicity.** A write creating a cycle is rejected. No belief may become evidence for itself
   through any path, however long. This is the structural defence against self-reinforcement,
   and it must be checked on the transitive closure, not just on the immediate parents.
2. **Completeness.** Every derived object names its operator, operator version, policy version,
   and an inputs hash. An object whose provenance does not resolve to the log is not readable by
   any plane.
3. **Determinism.** Replaying the recorded operator at the recorded version on the recorded
   inputs must reproduce the object's hash. Non-deterministic operators (LLM calls, stochastic
   fits) must record their seed and their full output, and are marked `NON_REPLAYABLE_EXACT` —
   which caps the epistemic type of everything downstream at `CONJECTURED` unless a deterministic
   verifier re-establishes the result.
4. **Signature.** Human judgements and policy changes are signed by a principal. "The system
   decided" is never an acceptable provenance for a T2–T4 change.

Property 3 has a consequence worth stating: **anything an LLM touched is non-replayable, and the
architecture makes that visible in the type system rather than forgettable.** That is the correct
treatment of a stochastic component in a scientific instrument.

## 7.2 Immutability, rollback, audit

- **Evidence log**: append-only, hash-chained, periodically anchored (external timestamping
  service or a notarised digest) so that retroactive tampering is detectable rather than merely
  discouraged.
- **Rollback**: is replay to an earlier epistemic time, not a restore from backup. `as_of()` is a
  first-class query.
- **Audit**: any claim answers, mechanically, "which specimens, which papers, which humans, which
  policy versions, which model versions produced this, and what would change if any one of them
  were removed." The last clause — leave-one-source-out sensitivity — is computable by replay and
  is the single most useful audit output.

## 7.3 The sealed prediction register

Trusted timestamping is what makes pre-registration meaningful rather than claimed. Predictions
are hashed and their digests periodically anchored externally. The register is append-only and
its contents cannot be edited after sealing, including by an administrator. If the system could
edit sealed predictions, every discovery claim in the architecture would be worthless, so this is
the one component where "we trust our own ops team" is not an acceptable design.

## 7.4 The clinical firewall

OP-OS produces two categorically different kinds of output and they must not share a surface:

```
     RESEARCH SURFACE                          CLINICAL SURFACE
 ────────────────────────────────      ────────────────────────────────
  everything ≥ SPECULATIVE              ONLY: ESTABLISHED, or MEASURED
  hypotheses, dossiers, anomalies       with a validated, human-ratified
  candidate relationships               card inside a verified envelope
  novelty flags, invariants
                                        no hypotheses, no conjectures,
  clearly labelled as research           no anomalies as findings,
  not for clinical decisions             no system-generated relationships
```

Enforcement is architectural: the clinical surface renders from a *separate materialised view*
that is filtered at construction, so a rendering bug cannot leak a conjecture into a report. A
type check at display time is not sufficient — the wrong data must not be in the view at all.

Additional rules on the clinical side: no out-of-envelope extrapolation, ever (out-of-scope
returns abstention, not a guess); every displayed quantity carries its measurement uncertainty;
and anomaly detection may surface *"this case is unusual relative to my model"* as a flag for
human attention, which is legitimate and useful, but never as an interpretation.

Regulatory framing follows from the same split: the research plane is not a medical device; any
clinical surface is, and inherits the full validation, change-control, and post-market
surveillance burden. Keeping the boundary architectural rather than procedural is what keeps the
research system's velocity from being hostage to the device system's change control.

## 7.5 Adversarial exposure

A system that autonomously ingests literature has an attack surface, and it is not theoretical —
predatory and fabricated papers exist in volume, and paper mills are an active industry.

| Threat | Defence |
| --- | --- |
| Fabricated or paper-mill literature | Source reputation as an explicit prior; local measurement outranks external claims (I.3); no single source can move a card past `REPORTED` |
| Prompt injection via document text | Extraction runs in a sandbox with no tool access; extracted content is data, never instruction; the gauntlet is deterministic and unaffected by text content |
| Poisoning via contributed datasets | Every dataset is a scoped source with its own reputation and its own leave-one-out sensitivity; contributions cannot bypass the tribunal |
| Autophagy | Indelible `SYSTEM_AUTHORED` stamp; refusal to ingest at any remove |
| Silent instrument drift | Continuous calibration monitoring; phantom slides and control tissue in every batch; drift detector on the prediction stream |
| Insider edit of the log | Hash chain + external anchoring; append-only storage; signed principals |

Note the pattern: no defence relies on detecting bad content by reading it. Each one relies on
structure — reputation priors, evidence ordering, sandboxing, hashing — because content-based
detection of adversarial text is not a solved problem and should not be load-bearing.

## 7.6 Privacy

Specimen data is patient data. The architecture's replay requirement and the right to erasure are
in genuine tension, and the resolution has to be designed in: identifiers live in a separate,
mutable, access-controlled store, and the evidence log holds only pseudonymous references and
measurements. Erasure removes the linkage and the images; the measurements survive as
de-identified evidence, and replay continues to work. Decide this before the log is built, because
it cannot be retrofitted to an append-only structure.

## 7.7 Failure modes the architecture accepts

Honesty requires naming what this design does *not* protect against:

- **A systematically biased instrument that is biased everywhere.** Instrument-swap replication
  catches instrument-*specific* artefacts. A bias shared by every scanner and every segmenter in
  existence — a property of H&E itself, say — is invisible to the tribunal.
- **A wrong ontology.** If the categories are wrong, everything scoped by them is wrong in a way
  no amount of internal consistency will reveal.
- **Correlated human error.** Consensus panels drawn from one training tradition share priors;
  the label-noise model captures disagreement, not shared error.
- **Publication bias in the corpus.** The system's priors inherit the literature's selective
  reporting, and it has no way to observe what was never published.

Each of these is a reason for external validation and outside collaboration, not a reason for
more internal machinery.
