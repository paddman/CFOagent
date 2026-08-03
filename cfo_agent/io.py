from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Callable, Iterable, TypeVar

from .models import BudgetLine, CashWeek, FinancialPeriod, decimal_json


T = TypeVar("T")


def _read_csv(path: str | Path, factory: Callable[[dict[str, str]], T]) -> list[T]:
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(source)
    rows: list[T] = []
    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"{source} has no CSV header")
        for line_number, raw in enumerate(reader, start=2):
            try:
                rows.append(factory(raw))
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{source}:{line_number}: {exc}") from exc
    if not rows:
        raise ValueError(f"{source} has no data rows")
    return rows


def read_financials(path: str | Path) -> list[FinancialPeriod]:
    return _read_csv(path, FinancialPeriod.from_mapping)


def read_budget(path: str | Path) -> list[BudgetLine]:
    return _read_csv(path, BudgetLine.from_mapping)


def read_cash13(path: str | Path) -> list[CashWeek]:
    return _read_csv(path, CashWeek.from_mapping)


def write_json(path: str | Path, payload: object) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(decimal_json(payload), ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    return destination


def write_rows(path: str | Path, fieldnames: Iterable[str], rows: Iterable[dict]) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames))
        writer.writeheader()
        writer.writerows(rows)
    return destination
