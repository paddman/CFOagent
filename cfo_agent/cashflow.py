from __future__ import annotations

from decimal import Decimal
from typing import Sequence

from .models import CashWeek, ZERO, decimal_json


def forecast_cash13(weeks: Sequence[CashWeek]) -> dict[str, object]:
    if not weeks:
        raise ValueError("at least one cash week is required")
    if len(weeks) > 13:
        raise ValueError("forecast cannot exceed 13 weeks")

    schedule = []
    closing: Decimal | None = None
    breach_weeks: list[str] = []
    lowest_cash: Decimal | None = None

    for index, week in enumerate(weeks):
        if index == 0:
            if week.opening_cash is None:
                raise ValueError("the first week requires opening_cash")
            opening = week.opening_cash
        else:
            opening = closing if week.opening_cash is None else week.opening_cash
        assert opening is not None
        closing = opening + week.inflows - week.outflows
        breach = closing < week.minimum_cash
        if breach:
            breach_weeks.append(week.week)
        lowest_cash = closing if lowest_cash is None else min(lowest_cash, closing)
        schedule.append(
            decimal_json(
                {
                    "week": week.week,
                    "opening_cash": opening,
                    "inflows": week.inflows,
                    "outflows": week.outflows,
                    "net_cash_flow": week.inflows - week.outflows,
                    "closing_cash": closing,
                    "minimum_cash": week.minimum_cash,
                    "breach": breach,
                }
            )
        )

    serialized = decimal_json(schedule)
    return decimal_json(
        {
            "schedule": serialized,
            "weeks": serialized,
            "ending_cash": closing or ZERO,
            "lowest_cash": lowest_cash or ZERO,
            "breach_weeks": breach_weeks,
            "liquidity_status": "BREACH" if breach_weeks else "OK",
        }
    )


def render_cash_report(forecast: dict[str, object]) -> str:
    lines = [
        "# 13-Week Cash Forecast",
        "",
        f"**Liquidity status:** {forecast['liquidity_status']}",
        f"**Ending cash:** {forecast['ending_cash']:,.2f}",
        f"**Lowest cash:** {forecast['lowest_cash']:,.2f}",
        "",
        "| Week | Opening | Inflows | Outflows | Closing | Minimum | Status |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    schedule = forecast.get("schedule") or forecast.get("weeks") or []
    for row in schedule:
        status = "BREACH" if row["breach"] else "OK"
        lines.append(
            f"| {row['week']} | {row['opening_cash']:,.2f} | "
            f"{row['inflows']:,.2f} | {row['outflows']:,.2f} | "
            f"{row['closing_cash']:,.2f} | {row['minimum_cash']:,.2f} | "
            f"{status} |"
        )
    if forecast["breach_weeks"]:
        lines.extend(
            [
                "",
                "## Required management actions",
                "",
                "- Confirm timing and collectability of the largest inflows.",
                "- Freeze non-essential cash outflows pending an authorized review.",
                "- Validate undrawn facilities, covenant headroom, and funding lead time.",
                "- Escalate payment prioritization to an authorized human approver.",
            ]
        )
    return "\n".join(lines) + "\n"


def render_cash13_markdown(forecast: dict[str, object]) -> str:
    return render_cash_report(forecast)
