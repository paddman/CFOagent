from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Mapping


MONEY = Decimal("0.01")
ZERO = Decimal("0")


def money(value: Any, *, allow_none: bool = False) -> Decimal | None:
    if value is None or value == "":
        if allow_none:
            return None
        return ZERO
    if isinstance(value, Decimal):
        result = value
    else:
        text = str(value).strip().replace(",", "")
        if text.startswith("(") and text.endswith(")"):
            text = "-" + text[1:-1]
        try:
            result = Decimal(text)
        except (InvalidOperation, ValueError) as exc:
            raise ValueError(f"invalid monetary value: {value!r}") from exc
    return result.quantize(MONEY, rounding=ROUND_HALF_UP)


def percent(numerator: Decimal, denominator: Decimal) -> Decimal | None:
    if denominator == ZERO:
        return None
    return (numerator / denominator * Decimal("100")).quantize(
        MONEY, rounding=ROUND_HALF_UP
    )


def decimal_json(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, list):
        return [decimal_json(item) for item in value]
    if isinstance(value, tuple):
        return [decimal_json(item) for item in value]
    if isinstance(value, dict):
        return {key: decimal_json(item) for key, item in value.items()}
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
    def from_mapping(cls, row: Mapping[str, Any]) -> "FinancialPeriod":
        period = str(row.get("period", "")).strip()
        if not period:
            raise ValueError("period is required")
        return cls(
            period=period,
            revenue=money(row.get("revenue")),
            cogs=money(row.get("cogs")),
            opex=money(row.get("opex")),
            cash=money(row.get("cash")),
            receivables=money(row.get("receivables")),
            payables=money(row.get("payables")),
            inventory=money(row.get("inventory")),
            debt=money(row.get("debt")),
        )


@dataclass(frozen=True)
class BudgetLine:
    period: str
    account: str
    actual: Decimal
    budget: Decimal

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> "BudgetLine":
        period = str(row.get("period", "")).strip()
        account = str(row.get("account", "")).strip()
        if not period or not account:
            raise ValueError("period and account are required")
        return cls(
            period=period,
            account=account,
            actual=money(row.get("actual")),
            budget=money(row.get("budget")),
        )


@dataclass(frozen=True)
class CashWeek:
    week: str
    opening_cash: Decimal | None
    inflows: Decimal
    outflows: Decimal
    minimum_cash: Decimal = ZERO

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> "CashWeek":
        week = str(row.get("week", "")).strip()
        if not week:
            raise ValueError("week is required")
        return cls(
            week=week,
            opening_cash=money(row.get("opening_cash"), allow_none=True),
            inflows=money(row.get("inflows")),
            outflows=money(row.get("outflows")),
            minimum_cash=money(row.get("minimum_cash")),
        )


@dataclass(frozen=True)
class JournalLine:
    account: str
    debit: Decimal = ZERO
    credit: Decimal = ZERO
    entity: str = ""
    cost_center: str = ""
    description: str = ""

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> "JournalLine":
        account = str(row.get("account", "")).strip()
        if not account:
            raise ValueError("journal line account is required")
        return cls(
            account=account,
            debit=money(row.get("debit")),
            credit=money(row.get("credit")),
            entity=str(row.get("entity", "")).strip(),
            cost_center=str(row.get("cost_center", "")).strip(),
            description=str(row.get("description", "")).strip(),
        )


@dataclass(frozen=True)
class PolicyDecision:
    action: str
    allowed: bool
    requires_human: bool
    reason: str
