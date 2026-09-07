"""Ingestion: per-object segmentation output -> canonical feature fields.

This is the boundary where the metadata gate lives. A specimen whose instrument state
is incomplete is REFUSED, not warned about: without it the confound tribunal cannot
rule on the channels that matter, so nothing downstream of that specimen could ever be
promoted. `No metadata, no discovery` has to be enforced by the code that accepts data,
because by the time anyone notices it is missing the slides have been cut.

Input contract (CSV, wide):
    objects.csv    specimen_id, object_id, phi, <quantity columns...>
    specimens.csv  specimen_id, scanner_id, scanner_model, mpp, objective,
                   stain_protocol, stain_lot, fixation_delay_h, section_thickness_um,
                   lab_id, pipeline_version, <any further covariates>
    quantities.csv quantity, mask_source, sigma_log
"""
from __future__ import annotations

import csv
import math
import statistics
from dataclasses import dataclass
from pathlib import Path

from .fields import FeatureField

#: The channels the tribunal needs to be able to stratify on. Not negotiable.
REQUIRED_METADATA = (
    "scanner_id", "scanner_model", "mpp", "objective",
    "stain_protocol", "stain_lot", "fixation_delay_h",
    "section_thickness_um", "lab_id", "pipeline_version",
)


class MetadataGate(Exception):
    """A specimen was refused at ingest for incomplete instrument state."""


@dataclass
class QuantitySpec:
    quantity: str
    mask_source: str
    sigma_log: float


def read_quantities(path: str | Path) -> dict[str, QuantitySpec]:
    out = {}
    with open(path, newline="") as fh:
        for row in csv.DictReader(fh):
            out[row["quantity"]] = QuantitySpec(row["quantity"], row["mask_source"],
                                                float(row["sigma_log"]))
    return out


def read_specimens(path: str | Path, strict: bool = True) -> dict[str, dict]:
    out, refused = {}, []
    with open(path, newline="") as fh:
        for row in csv.DictReader(fh):
            sid = row["specimen_id"]
            missing = [k for k in REQUIRED_METADATA if not row.get(k, "").strip()]
            if missing:
                refused.append((sid, missing))
                if strict:
                    continue
            out[sid] = {k: v for k, v in row.items() if k != "specimen_id"}
    if refused and strict:
        head = ", ".join(f"{s} (missing {'/'.join(m)})" for s, m in refused[:3])
        raise MetadataGate(
            f"{len(refused)} specimen(s) refused for incomplete instrument state: {head}"
            f"{' ...' if len(refused) > 3 else ''}. Capture it or pass --lax, and note "
            "that nothing ingested under --lax can clear a promotion gate.")
    return out


def lift_to_fields(objects_csv: str | Path, specimens: dict[str, dict],
                   quantities: dict[str, QuantitySpec],
                   n_bins: int = 20, min_objects_per_bin: int = 3
                   ) -> dict[str, dict[str, tuple[FeatureField, list[int]]]]:
    """Bin per-object measurements into phi and take the log-space mean per bin.

    Log space because the features are positive and multiplicative in behaviour, and
    because the invariant hunter works in log space -- lifting there keeps one
    representation from end to end rather than converting at the point of search.
    """
    grid = [(i + 0.5) / n_bins for i in range(n_bins)]
    acc: dict[str, dict[str, list[list[float]]]] = {}

    with open(objects_csv, newline="") as fh:
        for row in csv.DictReader(fh):
            sid = row["specimen_id"]
            if sid not in specimens:
                continue
            try:
                phi = float(row["phi"])
            except (KeyError, ValueError):
                continue
            if not 0.0 <= phi <= 1.0:
                continue
            b = min(int(phi * n_bins), n_bins - 1)
            for q in quantities:
                raw = row.get(q, "").strip()
                if not raw:
                    continue
                try:
                    v = float(raw)
                except ValueError:
                    continue
                if v <= 0:
                    continue
                acc.setdefault(sid, {}).setdefault(q, [[] for _ in range(n_bins)])
                acc[sid][q][b].append(math.log(v))

    out: dict[str, dict[str, tuple[FeatureField, list[int]]]] = {}
    for sid, per_q in acc.items():
        for q, bins in per_q.items():
            if sum(1 for b in bins if len(b) >= min_objects_per_bin) < n_bins:
                continue                       # incomplete phi coverage: drop the field
            mean = [math.exp(statistics.fmean(b)) for b in bins]
            n = [len(b) for b in bins]
            spec = quantities[q]
            # sampling error shrinks with objects per bin; the measurement model floor
            # does not. Both are carried, never dropped.
            sigma = max(spec.sigma_log,
                        spec.sigma_log / math.sqrt(max(1, min(n))))
            f = FeatureField(q, sid, grid, mean, sigma, spec.mask_source, specimens[sid])
            out.setdefault(sid, {})[q] = (f, n)
    return out


def ingest(store, objects_csv, specimens_csv, quantities_csv,
           n_bins: int = 20, strict: bool = True) -> tuple[int, int]:
    quantities = read_quantities(quantities_csv)
    specimens = read_specimens(specimens_csv, strict=strict)
    lifted = lift_to_fields(objects_csv, specimens, quantities, n_bins=n_bins)
    n_fields = 0
    for sid, per_q in lifted.items():
        store.put_specimen(sid, specimens[sid])
        for _q, (f, n) in per_q.items():
            store.put_field(f, n)
            n_fields += 1
    return len(lifted), n_fields
