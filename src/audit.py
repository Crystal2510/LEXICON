"""
src/audit.py
Audit trail logger — every agent decision is one structured JSON entry.
This is the system's traceability proof. Cheap to build, invaluable to show.
"""
from __future__ import annotations
import json
from pathlib import Path
from src.models import AuditEntry


class AuditLogger:
    """Collects audit entries during a single product processing run."""

    def __init__(self) -> None:
        self._entries: list[AuditEntry] = []
        self._step_counter = 0

    def log(
        self,
        field: str,
        agent: str,
        action: str,
        input_summary: str,
        output_summary: str,
        result: str,
    ) -> AuditEntry:
        self._step_counter += 1
        entry = AuditEntry(
            step=self._step_counter,
            field=field,
            agent=agent,
            action=action,
            input_summary=input_summary[:300],   # keep logs compact
            output_summary=output_summary[:300],
            result=result,
        )
        self._entries.append(entry)
        return entry

    def entries_for_field(self, field: str) -> list[AuditEntry]:
        return [e for e in self._entries if e.field == field]

    def all_entries(self) -> list[AuditEntry]:
        return list(self._entries)

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = [e.model_dump() for e in self._entries]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
