"""OP-OS Kernel v0 command line.

    python3 prototype/cli.py synth   --out data/          write a synthetic cohort as CSV
    python3 prototype/cli.py ingest  --db opos.db --dir data/
    python3 prototype/cli.py hunt    --db opos.db
    python3 prototype/cli.py range   --trials 20
    python3 prototype/cli.py demo

`synth` exists so the ingest path can be exercised end to end before any real
segmentation output arrives -- the CSV contract is the same either way.
"""
from __future__ import annotations

import argparse
import csv
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from opos import synthetic as synth
from opos.calibration import QUANTITIES, report, run_range
from opos.ingest import MetadataGate, ingest
from opos.invariant import hunt
from opos.store import Store
from opos.tribunal import run_invariant_tribunal

MASKS = {"nc_ratio": "seg_v3_nuc_cyto", "nuclear_area": "seg_v3_nuc_cyto",
         "chromatin": "texture_v2", "neighbour_dist": "seg_v3_centroids",
         "orient_coherence": "orient_v1"}


def cmd_synth(args: argparse.Namespace) -> int:
    """Emit a synthetic cohort in the real ingest format: per-object rows, not fields."""
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    fields, labels, _ = synth.generate(synth.CohortSpec(n_specimens=args.specimens))
    rng = random.Random(args.seed)
    quantities = list(MASKS)

    with open(out / "quantities.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["quantity", "mask_source", "sigma_log"])
        for q in quantities:
            w.writerow([q, MASKS[q], 0.03 if q == "orient_coherence" else 0.05])

    with open(out / "specimens.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        cols = ["specimen_id", "scanner_id", "scanner_model", "mpp", "objective",
                "stain_protocol", "stain_lot", "fixation_delay_h",
                "section_thickness_um", "lab_id", "pipeline_version", "condition"]
        w.writerow(cols)
        for sid, per_q in fields.items():
            st = next(iter(per_q.values())).stratum
            scanner = st["scanner"]
            w.writerow([sid, f"SCN-{scanner}",
                        "Aperio GT450" if scanner == "A" else "Hamamatsu S360",
                        0.263 if scanner == "A" else 0.220, 40,
                        "H&E-std-v2", st["stain_lot"], 6.0, 4.0, st["lab"],
                        "seg_v3.1.2+frame_v0.9", labels[sid]])

    # scatter each binned field back into plausible per-object rows
    n_obj = args.objects_per_bin
    with open(out / "objects.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["specimen_id", "object_id", "phi"] + quantities)
        oid = 0
        for sid, per_q in fields.items():
            grid = per_q["nc_ratio"].grid
            for bi, phi in enumerate(grid):
                for _ in range(n_obj):
                    jitter = rng.uniform(-0.02, 0.02)
                    row = [sid, f"{sid}-o{oid}", round(min(max(phi + jitter, 0.0), 1.0), 5)]
                    for q in quantities:
                        base = per_q[q].values[bi]
                        row.append(round(base * math.exp(rng.gauss(0, 0.12)), 6))
                    w.writerow(row)
                    oid += 1
    print(f"wrote {out}/objects.csv, specimens.csv, quantities.csv "
          f"({len(fields)} specimens, {oid} objects)")
    return 0


def cmd_ingest(args: argparse.Namespace) -> int:
    d = Path(args.dir)
    store = Store(args.db)
    try:
        n_spec, n_fields = ingest(store, d / "objects.csv", d / "specimens.csv",
                                  d / "quantities.csv", n_bins=args.bins,
                                  strict=not args.lax)
    except MetadataGate as exc:
        print(f"REFUSED AT THE METADATA GATE\n  {exc}")
        return 2
    print(f"ingested {n_spec} specimens, {n_fields} fields into {args.db}")
    print(f"evidence log: {store.log_size()} entries, chain valid: {store.verify()}")
    return 0


def cmd_hunt(args: argparse.Namespace) -> int:
    store = Store(args.db)
    fields = store.fields_by_specimen()
    if not fields:
        print(f"no fields in {args.db} -- run `ingest` first")
        return 2
    present = {q for per_q in fields.values() for q in per_q}
    quantities = [q for q in QUANTITIES if q in present]
    print(f"{len(fields)} specimens, quantities {quantities}\n")
    results = hunt(fields, quantities)
    print(f"  {'rank':<5}{'candidate':<44}{'score':>8}{'reduction':>12}")
    for i, r in enumerate(results[:5], 1):
        print(f"  {i:<5}{str(r.candidate):<44}{r.score:>8.2f}"
              f"{r.median_variance_reduction:>11.1f}x")
    print()
    for r in results[:args.top]:
        rec = run_invariant_tribunal(r, fields, ["scanner_id", "stain_lot"],
                                     n_perm=args.perm, alpha=0.05 / args.top)
        print(f"  candidate: {r.candidate}")
        print(rec.transcript())
        print(f"      {'VERDICT':<22} {rec.verdict}\n")
    return 0


def cmd_range(args: argparse.Namespace) -> int:
    print("Calibration Range -- measuring the discovery pipeline against planted truth\n")
    conditions = run_range(n_trials=args.trials, n_specimens=args.specimens,
                           n_perm=args.perm)
    print(report(conditions))
    return 0


def cmd_demo(_args: argparse.Namespace) -> int:
    import demo
    demo.main()
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="opos", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("synth", help="write a synthetic cohort in the ingest format")
    s.add_argument("--out", default="data"); s.add_argument("--specimens", type=int, default=60)
    s.add_argument("--objects-per-bin", type=int, default=25)
    s.add_argument("--seed", type=int, default=7)
    s.set_defaults(fn=cmd_synth)

    s = sub.add_parser("ingest", help="lift per-object CSV into canonical fields")
    s.add_argument("--db", default="opos.db"); s.add_argument("--dir", default="data")
    s.add_argument("--bins", type=int, default=20)
    s.add_argument("--lax", action="store_true",
                   help="accept specimens with incomplete instrument state (nothing "
                        "ingested this way can clear a promotion gate)")
    s.set_defaults(fn=cmd_ingest)

    s = sub.add_parser("hunt", help="run the invariant hunter and tribunal on a store")
    s.add_argument("--db", default="opos.db"); s.add_argument("--top", type=int, default=3)
    s.add_argument("--perm", type=int, default=100)
    s.set_defaults(fn=cmd_hunt)

    s = sub.add_parser("range", help="measure sensitivity and false-discovery rate")
    s.add_argument("--trials", type=int, default=12)
    s.add_argument("--specimens", type=int, default=30)
    s.add_argument("--perm", type=int, default=40)
    s.set_defaults(fn=cmd_range)

    sub.add_parser("demo", help="the full end-to-end walkthrough").set_defaults(fn=cmd_demo)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
