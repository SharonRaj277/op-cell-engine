"""Persistent substrate: SQLite-backed evidence log, specimens, fields, predictions.

The knowledge base is a materialised view over the evidence log (docs/00 I7), so the
log is the only table that must never be edited. Everything else can be rebuilt from
it, which is what makes rollback a replay and retraction propagation a re-derivation.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .fields import FeatureField
from .provenance import LogEntry, _h

SCHEMA = """
CREATE TABLE IF NOT EXISTS evidence_log (
  seq INTEGER PRIMARY KEY, prev_hash TEXT NOT NULL, hash TEXT NOT NULL,
  kind TEXT NOT NULL, payload TEXT NOT NULL, principal TEXT NOT NULL, at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS specimens (
  specimen_id TEXT PRIMARY KEY, metadata TEXT NOT NULL, log_seq INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS fields (
  specimen_id TEXT NOT NULL, quantity TEXT NOT NULL, grid TEXT NOT NULL,
  mean TEXT NOT NULL, n TEXT NOT NULL, sigma_log REAL NOT NULL,
  mask_source TEXT NOT NULL, log_seq INTEGER NOT NULL,
  PRIMARY KEY (specimen_id, quantity));
CREATE TABLE IF NOT EXISTS predictions (
  id INTEGER PRIMARY KEY AUTOINCREMENT, specimen_id TEXT NOT NULL, quantity TEXT NOT NULL,
  sealed_at TEXT NOT NULL, content_hash TEXT NOT NULL, predictor TEXT NOT NULL,
  distribution TEXT NOT NULL, settled INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS postings (
  id INTEGER PRIMARY KEY AUTOINCREMENT, specimen_id TEXT NOT NULL, quantity TEXT NOT NULL,
  account TEXT NOT NULL, total REAL NOT NULL, mechanism REAL NOT NULL,
  nuisance REAL NOT NULL, unexplained REAL NOT NULL, signed_residual REAL NOT NULL);
"""


class Store:
    def __init__(self, path: str | Path = "opos.db") -> None:
        self.path = str(path)
        self.db = sqlite3.connect(self.path)
        self.db.executescript(SCHEMA)
        self.db.commit()

    # --- evidence log --------------------------------------------------------

    def append(self, kind: str, payload: dict, principal: str = "system") -> LogEntry:
        row = self.db.execute("SELECT seq, hash FROM evidence_log "
                              "ORDER BY seq DESC LIMIT 1").fetchone()
        seq = (row[0] + 1) if row else 0
        prev = row[1] if row else "0" * 16
        e = LogEntry(seq, prev, kind, payload, principal,
                     datetime.now(timezone.utc).isoformat())
        self.db.execute(
            "INSERT INTO evidence_log (seq, prev_hash, hash, kind, payload, principal, at)"
            " VALUES (?,?,?,?,?,?,?)",
            (e.seq, e.prev_hash, e.hash, e.kind, json.dumps(e.payload, sort_keys=True),
             e.principal, e.at))
        self.db.commit()
        return e

    def verify(self) -> bool:
        prev = "0" * 16
        for seq, prev_hash, h, kind, payload, principal, at in self.db.execute(
                "SELECT seq, prev_hash, hash, kind, payload, principal, at "
                "FROM evidence_log ORDER BY seq"):
            if prev_hash != prev:
                return False
            expect = _h(str(seq), prev_hash, kind, payload, principal, at)
            if expect != h:
                return False
            prev = h
        return True

    def log_size(self) -> int:
        return self.db.execute("SELECT COUNT(*) FROM evidence_log").fetchone()[0]

    # --- specimens and fields ------------------------------------------------

    def put_specimen(self, specimen_id: str, metadata: dict) -> None:
        e = self.append("observation", {"specimen": specimen_id, "instrument": metadata})
        self.db.execute("INSERT OR REPLACE INTO specimens VALUES (?,?,?)",
                        (specimen_id, json.dumps(metadata, sort_keys=True), e.seq))
        self.db.commit()

    def put_field(self, f: FeatureField, n: list[int]) -> None:
        e = self.append("measurement", {"specimen": f.specimen, "quantity": f.quantity,
                                        "n_objects": sum(n),
                                        "mask_source": f.mask_source})
        self.db.execute("INSERT OR REPLACE INTO fields VALUES (?,?,?,?,?,?,?,?)",
                        (f.specimen, f.quantity, json.dumps(f.grid), json.dumps(f.values),
                         json.dumps(n), f.sigma_log, f.mask_source, e.seq))
        self.db.commit()

    def fields_by_specimen(self) -> dict[str, dict[str, FeatureField]]:
        meta = {sid: json.loads(m) for sid, m in
                self.db.execute("SELECT specimen_id, metadata FROM specimens")}
        out: dict[str, dict[str, FeatureField]] = {}
        for sid, q, grid, mean, _n, sig, mask, _seq in self.db.execute(
                "SELECT * FROM fields ORDER BY specimen_id, quantity"):
            out.setdefault(sid, {})[q] = FeatureField(
                q, sid, json.loads(grid), json.loads(mean), sig, mask, meta.get(sid, {}))
        return out

    # --- kernel records ------------------------------------------------------

    def seal_prediction(self, specimen_id: str, quantity: str, predictor: str,
                        distribution: dict) -> str:
        blob = json.dumps(distribution, sort_keys=True)
        at = datetime.now(timezone.utc).isoformat()
        content_hash = _h(specimen_id, quantity, predictor, blob, at)
        self.db.execute(
            "INSERT INTO predictions (specimen_id, quantity, sealed_at, content_hash,"
            " predictor, distribution) VALUES (?,?,?,?,?,?)",
            (specimen_id, quantity, at, content_hash, predictor, blob))
        self.append("sealed_prediction", {"specimen": specimen_id, "quantity": quantity,
                                          "predictor": predictor, "hash": content_hash})
        self.db.commit()
        return content_hash

    def record_posting(self, p) -> None:
        self.db.execute(
            "INSERT INTO postings (specimen_id, quantity, account, total, mechanism,"
            " nuisance, unexplained, signed_residual) VALUES (?,?,?,?,?,?,?,?)",
            (p.specimen, p.quantity, p.account_key, p.total_surprise, p.to_mechanism,
             p.to_nuisance, p.to_unexplained, p.signed_residual))
        self.db.commit()

    def close(self) -> None:
        self.db.close()
