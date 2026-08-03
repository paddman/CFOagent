from decimal import Decimal
import unittest

from cfo_agent.analytics import (
    budget_variance,
    detect_anomalies,
    scenario_analysis,
    summarize_financials,
)
from cfo_agent.models import BudgetLine, FinancialPeriod


class AnalyticsTests(unittest.TestCase):
    def setUp(self):
        self.periods = [
            FinancialPeriod.from_mapping(
                {
                    "period": "2026-05",
                    "revenue": 100,
                    "cogs": 40,
                    "opex": 50,
                    "cash": 20,
                    "receivables": 10,
                    "payables": 8,
                    "inventory": 5,
                    "debt": 30,
                }
            ),
            FinancialPeriod.from_mapping(
                {
                    "period": "2026-06",
                    "revenue": 120,
                    "cogs": 45,
                    "opex": 55,
                    "cash": 25,
                    "receivables": 12,
                    "payables": 9,
                    "inventory": 6,
                    "debt": 28,
                }
            ),
        ]

    def test_summary_core_metrics(self):
        result = summarize_financials(self.periods)
        self.assertEqual(result["latest_period"], "2026-06")
        self.assertEqual(result["gross_profit"], 75.0)
        self.assertEqual(result["ebitda"], 20.0)
        self.assertEqual(result["net_debt"], 3.0)
        self.assertAlmostEqual(result["revenue_growth_pct"], 20.0)

    def test_summary_requires_data(self):
        with self.assertRaises(ValueError):
            summarize_financials([])

    def test_budget_variance_and_materiality(self):
        rows = [
            BudgetLine.from_mapping(
                {"period": "2026-06", "account": "Cloud", "actual": 120, "budget": 100}
            ),
            BudgetLine.from_mapping(
                {"period": "2026-07", "account": "Cloud", "actual": 90, "budget": 100}
            ),
        ]
        result = budget_variance(rows)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["variance"], 10.0)
        self.assertFalse(result[0]["material"])

    def test_anomaly_detection(self):
        result = detect_anomalies([9, 10, 10, 11, 100])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["index"], 4)

    def test_anomaly_detection_small_sample(self):
        self.assertEqual(detect_anomalies([1, 2]), [])

    def test_scenario_analysis(self):
        result = scenario_analysis(
            100,
            40,
            30,
            {
                "base": {
                    "revenue_growth_pct": 10,
                    "gross_margin_delta_pct": 2,
                    "opex_growth_pct": 5,
                }
            },
        )
        self.assertEqual(result[0]["scenario"], "base")
        self.assertAlmostEqual(result[0]["revenue"], 110.0)
        self.assertAlmostEqual(result[0]["gross_profit"], 46.2)
        self.assertAlmostEqual(result[0]["opex"], 31.5)
        self.assertAlmostEqual(result[0]["ebitda"], 14.7)


if __name__ == "__main__":
    unittest.main()
