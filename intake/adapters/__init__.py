"""Intake adapters.

Each adapter exports an `ingest(beat, date, out_path) -> IngestResult` entry.
The caller (cli.py) owns the choice of source/date/out_path; adapters do not
inspect environment beyond what they need (HTTP user agent, timeouts).

Adapters MUST use `intake.hashing.content_id` for item IDs and MUST emit at
least one friction event per call (success or failure; empty-result ⇒ stuck).
"""

from dataclasses import dataclass


@dataclass
class IngestResult:
    source: str
    count: int
    deduped: int
    out_path: str

    def as_reason(self) -> str:
        base = f"{self.count} items"
        if self.deduped:
            base += f", {self.deduped} deduped"
        return base
