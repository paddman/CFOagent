"""CFOAgent deterministic finance operating system."""

from .analytics import (
    budget_variance,
    detect_anomalies,
    scenario_analysis,
    summarize_financials,
)
from .cashflow import forecast_cash13
from .router import route_task
from .skills import SKILLS, search_skills

__all__ = [
    "SKILLS",
    "budget_variance",
    "detect_anomalies",
    "forecast_cash13",
    "route_task",
    "scenario_analysis",
    "search_skills",
    "summarize_financials",
]

__version__ = "0.3.0"
