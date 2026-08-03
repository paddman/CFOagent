import json
import tempfile
import unittest
from pathlib import Path

from cfo_agent.cli import main
from cfo_agent.io import read_budget, read_cash13, read_financials


FINANCIALS = """period,revenue,cogs,opex,cash,receivables,payables,inventory,debt
2026-05,100,40,50,20,10,8,5,30
2026-06,120,45,55,25,12,9,6,28
"""

BUDGET = """period,account,actual,budget
2026-06,Revenue,120,100
2026-06,COGS,45,40
"""

CASH = """week,opening_cash,inflows,outflows,minimum_cash
W1,100,50,80,60
W2,,20,90,60
"""


class CliIOTests(unittest.TestCase):
    def test_csv_readers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            financials = root / "financials.csv"
            budget = root / "budget.csv"
            cash = root / "cash.csv"
            financials.write_text(FINANCIALS, encoding="utf-8")
            budget.write_text(BUDGET, encoding="utf-8")
            cash.write_text(CASH, encoding="utf-8")
            self.assertEqual(len(read_financials(financials)), 2)
            self.assertEqual(len(read_budget(budget)), 2)
            self.assertEqual(len(read_cash13(cash)), 2)

    def test_csv_error_contains_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.csv"
            path.write_text(
                "period,revenue,cogs,opex,cash\n2026-06,not-a-number,1,1,1\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, r":2:"):
                read_financials(path)

    def test_demo_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "board.md"
            status = main(
                [
                    "--home",
                    str(Path(tmp) / "home"),
                    "demo",
                    "--output",
                    str(output),
                ]
            )
            self.assertEqual(status, 0)
            self.assertTrue(output.is_file())
            self.assertIn("Board Pack", output.read_text(encoding="utf-8"))
            self.assertTrue((Path(tmp) / "home" / "audit.jsonl").is_file())

    def test_cash13_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            cash = Path(tmp) / "cash.csv"
            output = Path(tmp) / "cash.json"
            cash.write_text(CASH, encoding="utf-8")
            status = main(
                [
                    "cash13",
                    str(cash),
                    "--format",
                    "json",
                    "--output",
                    str(output),
                ]
            )
            self.assertEqual(status, 0)
            result = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(result["liquidity_status"], "BREACH")

    def test_skills_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "skills.json"
            status = main(
                [
                    "skills",
                    "IFRS 15 revenue recognition",
                    "--json",
                    "--output",
                    str(output),
                ]
            )
            self.assertEqual(status, 0)
            result = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(result["count"], 99)
            self.assertEqual(
                result["items"][0]["slug"],
                "revenue-recognition-ifrs15",
            )

    def test_policy_exit_code(self):
        self.assertEqual(main(["policy", "forecast"]), 0)
        self.assertEqual(main(["policy", "payment-release"]), 2)


if __name__ == "__main__":
    unittest.main()
