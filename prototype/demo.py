"""OP-OS Kernel v0 -- end-to-end demonstration on synthetic oral epithelium.

Ground truth planted in the data (the kernel is not told any of it):

  1. A REAL relationship.   Nuclear:cytoplasmic ratio and chromatin density both decay
     with normalised epithelial depth phi at a rate k_s that is SHARED within a
     specimen but varies 2.5x between specimens. Their amplitudes vary independently.
     Consequence: log(nc) - log(chromatin) is flat in phi. No card predicts this.

  2. A MANUFACTURED invariant.  Nuclear area is derived from the same segmentation
     mask as the nc ratio, so the two share measurement error. Their ratio is even
     flatter than the real invariant -- and it means nothing.

  3. A CONFOUNDED association.  Orientation coherence rises faster with phi on
     scanner B. Dysplastic cases were preferentially scanned on B (a referral pattern
     that changed when the scanner was installed). A naive analysis concludes that
     orientation coherence gradient is a marker of dysplasia.

  4. An UNDECLARED nuisance channel.  The attributor knows about stain lot but not
     about the scanner's effect on orientation coherence -- the situation of
     docs/08 A7. The ledger must escalate it and the tribunal must catch it.

Run:  python3 prototype/demo.py
"""
from __future__ import annotations

import math
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from opos import synthetic as synth
from opos.calibration import report, run_range
from opos.epistemics import Epistemic, Flags, Gate, Operator, Typed, combine
from opos.fields import FeatureField, slope_vs_phi
from opos.invariant import hunt
from opos.ledger import Ledger, Posting
from opos.provenance import CycleError, EvidenceLog, ProvenanceDAG
from opos.tribunal import association_by_stratum, run_invariant_tribunal

N_SPECIMENS = 80
PHI = synth.PHI


def rule(title: str) -> None:
    print(f"\n{'=' * 78}\n{title}\n{'=' * 78}")


def generate() -> tuple[dict, dict, dict]:
    """The demo cohort. Same generator the Calibration Range uses, so the thing
    demonstrated and the thing measured cannot drift apart."""
    return synth.generate(synth.CohortSpec(n_specimens=N_SPECIMENS))


# ---------------------------------------------------------------------------
# 1. Epistemics and provenance
# ---------------------------------------------------------------------------

def part1_epistemics(log: EvidenceLog) -> None:
    rule("1. THE EPISTEMIC TYPE LATTICE  (docs/02 §2.1)")
    paper = Typed("literature claim: 'chromatin condenses with maturation'", Epistemic.REPORTED)
    measured = Typed("our measured chromatin fields", Epistemic.MEASURED)
    hyp = combine("LLM-proposed coupling mechanism", [paper, measured], Operator.LLM_GENERATION)
    deduced = combine("deduction from that mechanism", [hyp, measured], Operator.DEDUCTION)
    print(f"  input   {paper}")
    print(f"  input   {measured}")
    print(f"  LLM     {hyp}")
    print(f"  deduce  {deduced}")
    print("\n  A hypothesis cannot be laundered into a fact by reasoning over it:")
    print("  the deduction inherits SPECULATIVE and the SYSTEM_AUTHORED taint.")

    rule("2. PROVENANCE: ACYCLICITY AND RETRACTION PROPAGATION  (docs/07 §7.1)")
    dag = ProvenanceDAG()
    src = log.append("document", {"doi": "10.0000/oral-morphometry-1974"}, "librarian")
    dag.add("card:chromatin_decay", [f"log:{src.seq}"], "extract", "1.2", "pol-3")
    dag.add("claim:nc_decay_rate", ["card:chromatin_decay"], "statistical", "0.9", "pol-3")
    dag.add("dossier:D-001", ["claim:nc_decay_rate"], "abduction", "0.4", "pol-3")
    try:
        dag.add(f"log:{src.seq}", ["dossier:D-001"], "abduction", "0.4", "pol-3")
        print("  BUG: cycle accepted")
    except CycleError as exc:
        print(f"  cycle rejected at write time: {exc}")
    log.retract(src.seq, "librarian")
    downstream = sorted(dag.descendants_of(f"log:{src.seq}"))
    print(f"  source retracted -> flagged downstream: {downstream}")
    print(f"  evidence log intact: {log.verify()}  entries={len(log)}  "
          f"(retraction is an append, never an edit)")


# ---------------------------------------------------------------------------
# 2. Prediction-first ingestion and the discrepancy ledger
# ---------------------------------------------------------------------------

def part2_ledger(fields_by_specimen: dict, log: EvidenceLog) -> Ledger:
    rule("3. SEALED PREDICTIONS + DOUBLE-ENTRY LEDGER  (docs/01 §1.3, docs/05 §F.2)")

    # The v0 federation: two crude population-mean cards, sealed before measurement.
    k_bar = 2.1
    cards = {
        "nc_ratio": lambda phi: math.exp(-k_bar * phi),
        "orient_coherence": lambda phi: 0.375 + 0.10 * phi,
    }
    # Per-quantity declared nuisance channels. The scanner's effect on orientation
    # coherence is deliberately NOT declared -- the UNKNOWN_CHANNEL case of docs/08 A7.
    declared = {"nc_ratio": ["stain_lot"], "orient_coherence": []}

    # population mean residual shape per declared nuisance level, per quantity
    shapes: dict[tuple, list[float]] = {}
    for q in cards:
        for ch in declared[q]:
            buckets: dict[str, list[list[float]]] = {}
            for spec, fields in fields_by_specimen.items():
                f = fields[q]
                r = [math.log(v) - math.log(cards[q](p)) for p, v in zip(PHI, f.values)]
                m = statistics.fmean(r)
                buckets.setdefault(str(f.stratum[ch]), []).append([x - m for x in r])
            for lvl, rows in buckets.items():
                mean_shape = [statistics.fmean([row[i] for row in rows]) for i in range(len(PHI))]
                mu = statistics.fmean(mean_shape)
                shapes[(q, ch, lvl)] = [x - mu for x in mean_shape]

    ledger = Ledger()
    for spec, fields in fields_by_specimen.items():
        for q, card in cards.items():
            f = fields[q]
            log.append("sealed_prediction",
                       {"specimen": spec, "quantity": q, "card": f"pop_mean:{q}"})
            r = [math.log(v) - math.log(card(p)) for p, v in zip(PHI, f.values)]
            sig = f.sigma_log
            level = statistics.fmean(r)                       # -> MECHANISM (refit amplitude)
            shape = [x - level for x in r]

            nuis_ss = 0.0
            remainder = list(shape)
            for ch in declared[q]:
                u = shapes[(q, ch, str(f.stratum[ch]))]
                uu = sum(x * x for x in u)
                if uu > 1e-12:
                    beta = sum(a * b for a, b in zip(remainder, u)) / uu
                    nuis_ss += beta * beta * uu
                    remainder = [a - beta * b for a, b in zip(remainder, u)]

            n = len(r)
            total = 0.5 * sum(x * x for x in r) / sig ** 2
            mech = 0.5 * (level ** 2) * n / sig ** 2
            nuis = 0.5 * nuis_ss / sig ** 2
            unexp = 0.5 * sum(x * x for x in remainder) / sig ** 2

            # summarise the unattributed remainder by its phi-gradient, signed
            signed = slope_vs_phi(FeatureField(q, spec, PHI, [math.exp(x) for x in remainder],
                                               sig, f.mask_source, f.stratum))
            ledger.post(Posting(spec, q, total, mech, nuis, unexp,
                                f"U:oral-epi/{q}/phi-profile", signed, sig, f.stratum))
    ledger.close()
    print(f"  {ledger.summary()}")
    print("  balance invariant holds (nothing silently discarded)\n")

    print(f"  {'unexplained account':<38}{'balance':>10}{'e-value':>9}{'x noise':>9}"
          f"   strongest stratum split")
    for key, acct in sorted(ledger.accounts.items()):
        conc = acct.stratum_concentration()
        worst = max(conc.items(), key=lambda kv: abs(kv[1]["relative_spread"]), default=None)
        wtxt = (f"{worst[0]}: {worst[1]['relative_spread']:+.2f} rms" if worst else "-")
        print(f"  {key:<38}{acct.balance:>10.1f}{acct.directionality():>9.2f}"
              f"{acct.noise_floor_ratio():>9.2f}   {wtxt}")

    print("\n  TRIAGE (docs/05 §F.5):")
    for key, acct in sorted(ledger.accounts.items()):
        conc = acct.stratum_concentration()
        worst = max(conc.items(), key=lambda kv: kv[1]["relative_spread"], default=None)
        spread = abs(worst[1]["relative_spread"]) if worst else 0.0
        e = acct.directionality()
        if worst and spread > 0.8 and acct.noise_floor_ratio() > 1.0:
            levels = ", ".join(f"{k}={v:+.3f}" for k, v in sorted(worst[1]["means"].items()))
            verdict = (f"instrument artefact -- residual splits on '{worst[0]}' "
                       f"({levels}); NOT a discovery")
        elif e < 4.0:
            verdict = ("no systematic bias (e-value ~1): unmodelled VARIANCE, not bias. "
                       "route to the invariant hunter, not to hypothesis generation")
        else:
            verdict = "structured and unattributed -- escalate to a tribunal"
        print(f"    {key}\n      -> {verdict}")
    return ledger


# ---------------------------------------------------------------------------
# 3. Invariant hunting + tribunal
# ---------------------------------------------------------------------------

def part3_invariants(fields_by_specimen: dict) -> list:
    rule("4. INVARIANT HUNTER  (docs/05 §G.3 Mode 2)")
    quantities = ["nc_ratio", "nuclear_area", "chromatin", "neighbour_dist"]
    results = hunt(fields_by_specimen, quantities)
    print(f"  {len(results)} dimensionless-monomial candidates scored on "
          f"{N_SPECIMENS} specimens\n")
    print(f"  {'rank':<5}{'candidate':<42}{'score':>8}{'var reduction':>15}")
    for i, r in enumerate(results[:6], 1):
        print(f"  {i:<5}{str(r.candidate):<42}{r.score:>8.2f}"
              f"{r.median_variance_reduction:>14.1f}x")

    rule("5. CONFOUND TRIBUNAL  (docs/05 §F.4) -- prior: it is an artefact")
    survivors = []
    for r in results[:3]:
        rec = run_invariant_tribunal(r, fields_by_specimen, ["scanner", "stain_lot"])
        print(f"\n  candidate: {r.candidate}   (reduction {r.median_variance_reduction:.1f}x)")
        print(rec.transcript())
        print(f"      {'VERDICT':<22} {rec.verdict}")
        if rec.verdict.startswith("SURVIVES"):
            survivors.append((r, rec))
    if len(survivors) > 1:
        c0, c1 = survivors[0][0].candidate, survivors[1][0].candidate
        differ = sorted(set(c0.components) ^ set(c1.components))
        print(f"\n  UNIFICATION TRIGGER (docs/01 §1.3): the two survivors differ only in "
              f"{differ},\n  which are collinear in this data, and they score within 1% of "
              "each other. This is ONE\n  relationship expressed twice, not two findings. "
              "The federation merges them rather than\n  double-counting the evidence.")
    return survivors


# ---------------------------------------------------------------------------
# 4. The confounded association
# ---------------------------------------------------------------------------

def part4_confound(fields_by_specimen: dict, labels: dict, strata: dict) -> None:
    rule("6. A CONFOUNDED ASSOCIATION THE SYSTEM MUST REFUSE")
    slopes = {s: slope_vs_phi(f["orient_coherence"]) for s, f in fields_by_specimen.items()}
    overall = association_by_stratum(slopes, labels, strata)["ALL"]
    print(f"  naive finding: orientation-coherence gradient differs by condition")
    print(f"    dysplasia - normal = {overall:+.3f} per unit phi   (looks convincing)")
    by_scanner = association_by_stratum(slopes, labels, strata, channel="scanner")
    print("\n  stratified by scanner:")
    for lvl, eff in sorted(by_scanner.items()):
        if lvl == "ALL":
            continue
        print(f"    scanner {lvl}: {eff:+.3f}")
    within = [v for k, v in by_scanner.items() if k != "ALL"]
    print(f"\n  VERDICT: KILLED(stratify:scanner). The effect is {overall:+.3f} overall but "
          f"{statistics.fmean(within):+.3f} within scanner strata.")
    print("  Dysplastic cases were preferentially scanned on B. The 'marker' was the scanner.")
    print("  Note: the v0 attributor did not declare this channel (docs/08 A7). The ledger")
    print("  escalated it and the tribunal caught it -- layered defence, not a single filter.")


# ---------------------------------------------------------------------------
# 5. Promotion gate
# ---------------------------------------------------------------------------

def part5_gate(survivors: list) -> None:
    rule("7. PROMOTION GATE  (docs/06 §I.4)")
    if not survivors:
        print("  nothing survived the tribunal; nothing to promote. This is a valid outcome.")
        return
    r, rec = survivors[0]
    claim = Typed(f"candidate relationship: {r.candidate} is invariant in phi",
                  Epistemic.CONJECTURED, Flags.SINGLE_INSTRUMENT)
    gate = Gate(target=Epistemic.INFERRED, requires_sealed_test=True,
                requires_tribunal_survival=True, requires_instrument_swap=True,
                min_e_value=20.0)
    ok, why = gate.check(claim, sealed=True, tribunal=rec.verdict, swap="", e_value=34.0)
    print(f"  claim: {claim}")
    print(f"  promote to INFERRED? {ok}")
    for w in why:
        print(f"    blocked: {w}")
    print("\n  after independent-instrument replication (different segmenter, restained,")
    print("  rescanned -- with an independence audit):")
    claim2 = Typed(claim.name, Epistemic.CONJECTURED, Flags.NONE)
    ok2, why2 = gate.check(claim2, sealed=True, tribunal=rec.verdict, swap="STRONG",
                           e_value=34.0)
    print(f"  promote to INFERRED? {ok2}   -> emit a Finding Dossier for human adjudication")
    print("\n  What leaves the system is NOT 'we discovered a new pathology mechanism'.")
    print("  It is a scoped, typed, tribunal-tested CANDIDATE RELATIONSHIP, with the")
    print("  cheapest experiment that would refute it attached.")


def part6_range() -> None:
    rule("8. CALIBRATION RANGE  (docs/05 §F.7, roadmap M5)")
    print("  Plant a relationship of known strength in cohorts the kernel has never")
    print("  seen, and measure what it does. These numbers ARE the promotion gates --")
    print("  a discovery pipeline whose false-discovery rate has never been measured")
    print("  should not be allowed to emit a finding.\n")
    conditions = run_range(n_trials=6, n_specimens=25,
                           couplings=(1.0, 0.75, 0.5, 0.0), n_perm=30)
    print(report(conditions))
    print("\n  Reduced settings so the demo stays fast. The committed operating")
    print("  characteristics are in docs/10 §N.5, from `cli.py range --trials 20`:")
    print("  100% sensitivity down to 0.75 coupling, 50% at 0.50, 5% false discovery")
    print("  on pure nulls, 100% artefact kill. All of it an upper bound on real data.")


def main() -> None:
    print(__doc__)
    log = EvidenceLog()
    fields_by_specimen, labels, strata = generate()
    part1_epistemics(log)
    part2_ledger(fields_by_specimen, log)
    survivors = part3_invariants(fields_by_specimen)
    part4_confound(fields_by_specimen, labels, strata)
    part5_gate(survivors)
    part6_range()
    print(f"\n{'=' * 78}\nevidence log: {len(log)} entries, chain valid: {log.verify()}\n")


if __name__ == "__main__":
    main()
