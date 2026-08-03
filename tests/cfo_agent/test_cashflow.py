import unittest

from cfo_agent.cashflow import forecast_cash13, render_cash13_markdown
from cfo_agent.models import CashWeek


class CashflowTests(unittest.TestCase):
    def test_roll_forward_and_breach(self):
        weeks = [
            CashWeek.from_mapping(
                {
                    "week": "W1",
                    "opening_cash": 100,
                    "inflows": 50,
                    "outflows": 80,
                    "minimum_cash": 60,
                }
            ),
            CashWeek.from_mapping(
                {
                    "week": "W2",
                    "opening_cash": "",
                    "inflows": 20,
                    "outflows": 90,
                    "minimum_cash": 60,
                }
            ),
        ]
        result = forecast_cash13(weeks)
        self.assertEqual(result["schedule"][0]["closing_cash"], 70.0)
        self.assertEqual(result["schedule"][1]["opening_cash"], 70.0)
        self.assertEqual(result["schedule"][1]["closing_cash"], 0.0)
        self.assertEqual(result["liquidity_status"], "BREACH")
        self.assertEqual(result["breach_weeks"], ["W2"])

    def test_first_week_requires_opening_cash(self):
        week = CashWeek.from_mapping(
            {"week": "W1", "inflows": 1, "outflows": 1, "minimum_cash": 0}
        )
        with self.assertRaises(ValueError):
            forecast_cash13([week])

    def test_maximum_thirteen_weeks(self):
        weeks = [
            CashWeek.from_mapping(
                {
                    "week": f"W{i}",
                    "opening_cash": 100 if i == 0 else "",
                    "inflows": 1,
                    "outflows": 1,
                }
            )
            for i in range(14)
        ]
        with self.assertRaises(ValueError):
            forecast_cash13(weeks)

    def test_markdown_contains_schedule(self):
        result = forecast_cash13(
            [
                CashWeek.from_mapping(
                    {
                        "week": "W1",
                        "opening_cash": 100,
                        "inflows": 20,
                        "outflows": 10,
                        "minimum_cash": 50,
                    }
                )
            ]
        )
        text = render_cash13_markdown(result)
        self.assertIn("13-Week Cash Forecast", text)
        self.assertIn("W1", text)
        self.assertIn("OK", text)


if __name__ == "__main__":
    unittest.main()
