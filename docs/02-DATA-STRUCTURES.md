# 02 — (B) Internal data structures

Written as typed Python for precision, not as an implementation commitment. Every type carries
`id` (content-addressed), `created_at`, and `evidence_log_seq`; these are elided below.

## 2.1 The epistemic type lattice

The most important type in the system. Not a confidence number — a *lattice with propagation
rules*, borrowed from information-flow security rather than from knowledge representation.

```python
class Epistemic(IntEnum):
    """Ordered. Reasoning output can never exceed the minimum of its inputs."""
    REFUTED        = 0   # actively disconfirmed; retained forever, never deleted
    SPECULATIVE    = 1   # generated, no supporting evidence, not yet contradicted
    CONJECTURED    = 2   # system-generated hypothesis with a plausibility argument
    REPORTED       = 3   # asserted in literature; NOT independently verified here
    INFERRED       = 4   # statistical estimate from data, with anytime-valid bounds
    DERIVED        = 5   # deductive consequence of stronger claims, with a proof term
    MEASURED       = 6   # this lab's data, traceable to specimens and instruments
    ESTABLISHED    = 7   # consensus/guideline, high evidence tier, human-ratified
```

Orthogonal flags, because they compose independently of strength:

```python
class Flags(Flag):
    NONE                  = 0
    SINGLE_INSTRUMENT     = auto()  # never reproduced off originating measurement pathway
    SINGLE_SITE           = auto()
    SYSTEM_AUTHORED       = auto()  # indelible: blocks re-ingestion as literature (§autophagy)
    CONFOUND_UNRESOLVED   = auto()  # a tribunal channel could not be ruled out
    SCOPE_UNVERIFIED      = auto()  # envelope asserted by extraction, not tested
    SUPERSEDED            = auto()
    RETRACTED_SOURCE      = auto()  # upstream evidence retracted; awaiting replay
```

**Propagation rule (enforced in the kernel, not by convention):**

```python
def combine(inputs: list[Typed], op: Operator) -> Epistemic:
    base = min(i.level for i in inputs)
    if op is Operator.DEDUCTION:      return min(base, Epistemic.DERIVED)
    if op is Operator.STATISTICAL:    return min(base, Epistemic.INFERRED)
    if op is Operator.ABDUCTION:      return min(base, Epistemic.CONJECTURED)
    if op is Operator.ANALOGY:        return min(base, Epistemic.SPECULATIVE)
    if op is Operator.LLM_GENERATION: return Epistemic.SPECULATIVE   # hard ceiling
    raise Unreachable
```

Three consequences worth stating explicitly, because they are the anti-hallucination guarantee:
a conjecture can never be laundered into a fact by passing through reasoning; an LLM-authored
statement can never rise above `SPECULATIVE` without independent evidence attaching to it; and
any chain of inference is only as strong as its weakest link, computed rather than asserted.

Flags propagate by union — `SINGLE_INSTRUMENT` is contagious, which is exactly right.

## 2.2 Scope predicates and the envelope algebra

```python
@dataclass(frozen=True)
class Scope:
    """Machine-checkable validity envelope. The thing text-RAG cannot represent."""
    tissue:        Constraint[TissueType]        # e.g. oral squamous epithelium
    site:          Constraint[AnatomicSite]      # buccal, lateral tongue, floor of mouth...
    species:       Constraint[Species]
    condition:     Constraint[ConditionCode]     # normal, hyperplasia, OED grade, OSCC...
    stain:         Constraint[StainProtocol]     # H&E, and which protocol/lot family
    instrument:    Constraint[InstrumentClass]   # scanner class, objective, resolution band
    pipeline:      Constraint[PipelineVersion]   # segmenter + frame-fitter version range
    phi_range:     Interval                      # e.g. [0.05, 0.95] — excludes frame artefacts
    cohort:        Constraint[CohortDescriptor]  # age/sex/exposure/geography where relevant
    feature_defs:  dict[str, FeatureDefId]       # the operational definition of every term
    caveats:       list[str]                     # human-readable, non-load-bearing
```

The algebra is what makes contradiction meaningful:

```python
def intersects(a: Scope, b: Scope) -> Tri:          # TRUE / FALSE / UNKNOWN
def subsumes(a: Scope, b: Scope) -> Tri
def contradiction(c1: Claim, c2: Claim) -> Verdict:
    if intersects(c1.scope, c2.scope) is not TRUE:
        return Verdict.NOT_COMPARABLE          # ← the common case, and it is not a conflict
    if not comparable_definitions(c1, c2):
        return Verdict.DEFINITION_MISMATCH     # ← also not a conflict; often a discovery lead
    if incompatible_values(c1, c2):
        return Verdict.CONTRADICTION_IN_OVERLAP  # ← rare, valuable, opens an Investigation
    return Verdict.CONSISTENT
```

`UNKNOWN` intersection is a first-class outcome and must not be silently coerced to either
answer; unresolvable scope is itself a finding about the literature.

## 2.3 Observation and measurement

```python
@dataclass(frozen=True)
class InstrumentState:
    scanner_id: str; scanner_model: str; objective: float; mpp: float
    colour_profile_hash: str; focus_metric: float
    stain_protocol: str; stain_lot: str; stainer_id: str
    fixation_delay_h: float; fixation_duration_h: float; fixative: str
    section_thickness_um: float; microtome_id: str; cutting_session: str
    block_id: str; block_age_days: int; lab_id: str; operator_id: str
    pipeline: PipelineVersion            # every model hash in the vision stack
    acquired_at: datetime

@dataclass(frozen=True)
class Measurement:
    quantity: QuantityId                 # typed, with units and dimension
    value: float
    sigma: float                         # from the measurement model, not from the data
    measurement_model: MeasurementModelId
    instrument: InstrumentStateId
    qc: QCVerdict
```

`Measurement` deliberately has no "raw value" field without a measurement model. A number
without an instrument attached is not admissible anywhere in the system.

## 2.4 Canonical frame and fields — the representation that makes §9 possible

```python
@dataclass
class CanonicalFrame:
    """Diffeomorphism from tissue pixels to normalised biological coordinates."""
    kind: Literal["stratified_epithelium", "glandular", "stromal", ...]
    phi: Callable[[Point], float]        # 0 = basement membrane, 1 = surface
    s:   Callable[[Point], float]        # lateral arc length along the BM
    thickness: Callable[[float], float]  # local epithelial thickness h(s)
    rete: ReteGeometry                   # peg depth/period/asymmetry
    fit_residual: float                  # frame quality; gates everything downstream
    frame_model: FrameModelVersion

@dataclass
class FeatureField:
    """A feature as a FUNCTION of canonical coordinates, with uncertainty. The atom of
    quantitative discovery in OP-OS."""
    quantity: QuantityId
    specimen: SpecimenId
    frame: CanonicalFrameId
    grid: list[float]                    # φ knots
    mean: list[float]                    # f(φ)
    sigma: list[float]                   # measurement + sampling uncertainty
    n: list[int]                         # objects contributing per bin
    representation: Literal["binned", "gp", "spline", "monotone_spline"]
    nuisance: InstrumentStateId          # carried, never dropped
```

Scalar summaries (`mean nuclear area for this slide`) are *derived views* over fields and are
never the primary record. Collapsing to scalars early is how the field currently loses the
discoveries it is looking for.

## 2.5 Mechanism Card — the unit of knowledge

```python
@dataclass
class MechanismCard:
    signature: Signature                 # inputs → outputs, typed, dimensioned
    scope: Scope
    form: Program                        # EXECUTABLE. Typed DSL; see 04-REASONING §4.4
    params: ParameterBlock               # priors + posteriors + fit history
    predicts: list[QuantityId]           # what it stakes claims on
    epistemic: Epistemic
    flags: Flags
    provenance: ProvenanceRef            # DAG node; complete lineage to evidence log
    siblings: list[CardId]               # competing explanations of the SAME signature
    scorecard: Scorecard                 # live predictive performance, per stratum
    mechanism_class: Literal["descriptive", "phenomenological", "mechanistic", "causal"]
    retirement: Retirement | None
```

```python
@dataclass
class Scorecard:
    """Why the knowledge base is self-correcting without anyone deciding to distrust a card."""
    n_predictions: int
    crps: RunningStat                    # proper scoring rule, lower is better
    interval_coverage: dict[float, float]  # nominal → empirical (calibration)
    log_score_vs_baseline: RunningStat
    e_value: float                       # anytime-valid evidence against the card
    per_stratum: dict[StratumKey, RunningStat]   # where it fails matters more than that it does
    last_scored: datetime
```

A card with a decaying scorecard is automatically demoted by the kernel; a card whose e-value
against it crosses the retirement threshold is retired to `REFUTED` and kept forever. Knowledge
that stops predicting stops counting. **This is the mechanism that makes the base self-cleaning
and it does not exist in any retrieval architecture.**

Descriptive claims that cannot be compiled still exist, but in a strictly weaker form:

```python
@dataclass
class Claim:
    subject: EntityRef; predicate: RelationId; object: EntityRef | Quantity
    scope: Scope; epistemic: Epistemic; flags: Flags
    provenance: ProvenanceRef
    supports: list[ClaimId]; conflicts: list[ClaimId]
    compilable: bool                     # if False, may never carry inferential weight alone
```

## 2.6 The discrepancy ledger — double-entry

```python
@dataclass(frozen=True)
class Posting:
    """Every unit of surprise is posted. Debits must equal credits."""
    prediction: PredictionId
    quantity: QuantityId
    surprise: float                      # in nats, from the proper scoring rule
    account: Account                     # MECHANISM(card) | NUISANCE(channel) | UNEXPLAINED(key)
    attributor: AttributorVersion
    residual_after: float                # what this account could NOT absorb
    specimen: SpecimenId
    nuisance: InstrumentStateId

@dataclass
class UnexplainedAccount:
    key: str                             # e.g. "U:oral-epi/NC-ratio/phi-profile"
    balance: float                       # accumulated unattributed surprise (nats)
    n_postings: int
    structure_score: float               # is growth STRUCTURED or random? see 05 §5.2
    e_process: float                     # anytime-valid evidence that this is systematic
    stratum_profile: dict[StratumKey, float]   # is it concentrated in one scanner? one lab?
    first_seen: datetime; investigations: list[InvestigationId]
```

The balance-equals-zero invariant (`total surprise == Σ mechanism + Σ nuisance + Σ unexplained`)
is checked on every close. It is a cheap, brutal integrity test: if the books do not balance, the
attributor is silently discarding evidence.

## 2.7 Sealed predictions and commitments

```python
@dataclass(frozen=True)
class SealedPrediction:
    sealed_at: datetime                  # trusted timestamp
    content_hash: str                    # hash of the full predictive distribution
    predictor: ModelFederationVersion
    target: PredictionTarget             # specimen + quantity + frame, or cohort-level
    distribution: PredictiveDist          # full distribution, not a point
    rationale_cards: list[CardId]         # which cards staked what
    settled: SettlementRecord | None
```

```python
@dataclass
class Commitment:
    """A registered scientific bet. The anti-p-hacking primitive."""
    investigation: InvestigationId
    hypotheses: list[HypothesisId]        # the live set at commit time
    discriminating_predictions: list[SealedPredictionId]
    decision_rule: DecisionRule           # e-value threshold, pre-specified, immutable
    alpha_budget: AlphaAllocation         # drawn from the portfolio's finite pool
    specimen_quota: SpecimenQuota         # draws from the held-out vault, accounted
    committed_at: datetime; sealed_by: PrincipalId
```

## 2.8 Hypotheses and investigations

```python
@dataclass
class Hypothesis:
    statement: str                        # human-readable, non-load-bearing
    formal: Program | StructuralClaim      # load-bearing; must compile
    kind: Literal["artefact", "known_restated", "parameterisation",
                  "scope_narrowing", "missing_variable", "novel_relation",
                  "novel_mechanism"]
    epistemic: Epistemic                  # ≤ CONJECTURED by construction
    prior: float                          # explicit, justified, logged
    posterior: RunningPosterior
    predictions: list[DerivedPrediction]
    generator: GeneratorRef               # which engine proposed it, at what version
    novelty: NoveltyVerdict               # NOT_FOUND_IN_CORPUS(v) — never "new to science"

@dataclass
class Investigation:
    """The unit of scientific work. Persistent, resumable, auditable, closable."""
    trigger: Trigger                      # anomaly | invariance | contradiction |
                                          # unification | gap | external
    target: FormalTarget
    stage: Stage                          # FRAME…SETTLE
    hypotheses: list[HypothesisId]
    tribunal: TribunalRecord              # every attempt to kill it, successful or not
    commitments: list[CommitmentId]
    budget_spent: ResourceLedger          # tissue, alpha, wet-lab, pathologist minutes
    voi: float                            # expected information gain per unit cost
    status: Literal["active","parked","promoted","refuted","abandoned"]
    park_reason: str | None               # zombies are closed with a reason, not forgotten
```

## 2.9 Provenance

```python
@dataclass(frozen=True)
class EvidenceLogEntry:
    seq: int
    prev_hash: str                        # hash chain; tamper-evident
    kind: Literal["observation","document","human_judgement","policy",
                  "promotion","retraction","instrument_calibration"]
    payload_hash: str
    principal: PrincipalId                # who/what, with signature
    at: datetime

@dataclass(frozen=True)
class ProvenanceNode:
    derived_from: list[ProvenanceRef]     # DAG edges only — cycles rejected at write time
    operator: Operator
    operator_version: str
    policy_version: str
    inputs_hash: str                      # determinism check: replay must reproduce
```

The cycle rejection is not bureaucratic. It is what prevents a belief from becoming evidence
for itself through a long enough chain — the dominant self-reinforcement failure mode of any
system that writes what it infers back into what it reads.

## 2.10 What a finding looks like when it leaves the system

```python
@dataclass
class FindingDossier:
    claim: Claim | MechanismCard
    scope: Scope
    effect: EffectEstimate                # with anytime-valid intervals
    sealed_predictions: list[SealedPredictionId]   # and when they were sealed
    tribunal: TribunalRecord              # everything that FAILED to kill it
    surviving_alternatives: list[HypothesisId]     # what else is still consistent
    instrument_swap: SwapRecord           # which independent pathways reproduced it
    alpha_spent: float
    provenance: ProvenanceGraph           # complete, replayable
    novelty: NoveltyVerdict
    next_best_refutation: ExperimentPlan  # how to kill it most cheaply, offered proactively
    epistemic: Epistemic; flags: Flags
```

Offering the cheapest refutation alongside the finding is not decoration — it is the structural
difference between a system that advocates for its results and one that does science.
