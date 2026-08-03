from decimal import Decimal
import unittest

from cfo_agent.accounting import (
    aging_bucket,
    close_checklist,
    reconcile_balances,
    validate_journal,
)
from cfo_agent.models import JournalLine


class AccountingTests(unittest.TestCase):
    def test_balanced_journal(self):
        result = validate_journal(
            [
                JournalLine.from_mapping({"account": "Cash", "debit": 100}),
                JournalLine.from_mapping({"account": "Revenue", "credit": 100}),
            ]
        )
        self.assertTrue(result["balanced"])
        self.assertEqual(result["errors"], [])

    def test_unbalanced_journal(self):
        result = validate_journal(
            [
                JournalLine.from_mapping({"account": "Cash", "debit": 100}),
                JournalLine.from_mapping({"account": "Revenue", "credit": 90}),
            ]
        )
        self.assertFalse(result["balanced"])
        self.assertTrue(result["errors"])

    def test_journal_requires_two_lines(self):
        with self.assertRaises(ValueError):
            validate_journal([JournalLine.from_mapping({"account": "Cash", "debit": 1})])

    def test_reconciliation(self):
        result = reconcile_balances(
            {"AR": Decimal("100.00"), "AP": 50},
            {"AR": Decimal("99.995"), "AP": 45},
            tolerance=Decimal("0.01"),
        )
        by_account = {row["account"]: row for row in result}
        self.assertTrue(by_account["AR"]["reconciled"])
        self.assertFalse(by_account["AP"]["reconciled"])

    def test_close_checklist(self):
        result = close_checklist("2026-06")
        self.assertEqual(len(result), 10)
        self.assertTrue(all(item["status"] == "open" for item in result))

    def test_aging_buckets(self):
        self.assertEqual(aging_bucket(0), "current")
        self.assertEqual(aging_bucket(1), "1-30")
        self.assertEqual(aging_bucket(31), "31-60")
        self.assertEqual(aging_bucket(61), "61-90")
        self.assertEqual(aging_bucket(91), "90+")


if __name__ == "__main__":
    unittest.main()
