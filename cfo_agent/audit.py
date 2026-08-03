from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import decimal_json
from .policy import redact_sensitive


GENESIS = "0" * 64


def _canonical(record: dict[str, Any]) -> bytes:
    payload = {key: value for key, value in record.items() if key != "hash"}
    return json.dumps(
        decimal_json(payload), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


class AuditLog:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _records(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        records = []
        for line_number, line in enumerate(
            self.path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid audit record on line {line_number}") from exc
        return records

    def append(
        self,
        event: str,
        *,
        actor: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        records = self._records()
        previous_hash = records[-1]["hash"] if records else GENESIS
        safe_payload = {
            key: redact_sensitive(str(value)) if isinstance(value, str) else value
            for key, value in (payload or {}).items()
        }
        record: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "actor": actor,
            "payload": decimal_json(safe_payload),
            "previous_hash": previous_hash,
        }
        record["hash"] = hashlib.sha256(_canonical(record)).hexdigest()
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        return record

    def verify(self) -> dict[str, Any]:
        records = self._records()
        expected_previous = GENESIS
        for index, record in enumerate(records):
            if record.get("previous_hash") != expected_previous:
                return {
                    "valid": False,
                    "record_index": index,
                    "reason": "previous hash mismatch",
                }
            expected_hash = hashlib.sha256(_canonical(record)).hexdigest()
            if record.get("hash") != expected_hash:
                return {
                    "valid": False,
                    "record_index": index,
                    "reason": "record hash mismatch",
                }
            expected_previous = record["hash"]
        return {"valid": True, "record_count": len(records), "head": expected_previous}
