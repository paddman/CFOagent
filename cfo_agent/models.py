from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from typing import Any


ZERO = Decimal("0")
HUNDRED = Decimal("100")


def money(value: Any, *, field: str = "value") -> Decimal:
    """Convert a CSV/API value to Decimal without binary floating-point drift."""
    if value is None or value == "":
        return ZERO
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value).replace(",", "").strip())
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field} must be numeric, got {value!r}") from exc


def decimal_json(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, list):
        return [decimal_json(item) for item in value]
    if isinstance(value, tuple):
        return [decimal_json(item) for item in value]
    if isinstance(value, dict):
        return {key: decimal_json(item) for key, item in value.items()}
    if hasattr(value, "__dataclass_fields__"):
        return decimal_json(asdict(value))
    return value


@dataclass(frozen=True)
class FinancialPeriod:
    period: str
    revenue: Decimal
    cogs: Decimal
    opex: Decimal
    cash: Decimal
    receivables: Decimal = ZERO
    payables: Decimal = ZERO
    inventory: Decimal = ZERO
    debt: Decimal = ZERO

    @classmethod
    def from_mapping(cls, row: dict[str, Any]) -> "FinancialPeriod":
        period = str(row.get("period") or row.get("date") or "").strip()
        if not period:
            raise ValueError("period is required")
        return cls(
            period=period,
            revenue=money(row.get("revenue"), field="revenue"),
            cogs=money(row.get("cogs"), field="cogs"),
            opex=money(row.get("opex"), field="opex"),
            cash=money(row.get("cash"), field="cash"),
            receivables=money(row.get("receivables"), field="receivables"),
            payables=money(row.get("payables"), field="payables"),
            inventory=money(row.get("inventory"), field="inventory"),
            debt=money(row.get("debt"), field="debt"),
        )


@dataclass(frozen=True)
class BudgetLine:
    period: str
    account: str
    actual: Decimal
    budget: Decimal

    @classmethod
    def from_mapping(cls, row: dict[str, Any]) -> "BudgetLine":
        period = str(row.get("period") or "").strip()
        account = str(row.get("account") or "").strip()
        if not period or not account:
            raise ValueError("period and account are required")
        return cls(
            period=period,
            account=account,
            actual=money(row.get("actual"), field="actual"),
            budget=money(row.get("budget"), field="budget"),
        )


@dataclass(frozen=True)
class CashWeek:
    week: str
    inflows: Decimal
    outflows: Decimal
    opening_cash: Decimal | None = None
    minimum_cash: Decimal = ZERO

    @classmethod
    def from_mapping(cls, row: dict[str, Any]) -> "CashWeek":
        week = str(row.get("week") or row.get("period") or "").strip()
        if not week:
            raise ValueError("week is required")
        opening_raw = row.get("opening_cash")
        opening = None if opening_raw in (None, "") else money(opening_raw, field="opening_cash")
        return cls(
            week=week,
            inflows=money(row.get("inflows"), field="inflows"),
            outflows=money(row.get("outflows"), field="outflows"),
            opening_cash=opening,
            minimum_cash=money(row.get("minimum_cash"), field="minimum_cash"),
        )


@dataclass(frozen=True)
class JournalLine:
    account: str
    debit: Decimal = ZERO
    credit: Decimal = ZERO
    memo: str = ""

    @classmethod
    def from_mapping(cls, row: dict[str, Any]) -> "JournalLine":
        account = str(row.get("account") or "").strip()
        if not account:
            raise ValueError("account is required")
        return cls(
            account=account,
            debit=money(row.get("debit"), field="debit"),
            credit=money(row.get("credit"), field="credit"),
            memo=str(row.get("memo") or ""),
        )


@dataclass(frozen=True)
class PolicyDecision:
    action: str
    allowed: bool
    requires_human: bool
    reason: str
