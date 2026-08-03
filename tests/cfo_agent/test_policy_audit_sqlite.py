import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from cfo_agent.audit import AuditLog
from cfo_agent.policy import evaluate_action, redact_sensitive
from cfo_agent.sqlite import query_read_only, validate_read_only_sql


class PolicyAuditSQLiteTests(unittest.TestCase):
    def test_read_only_action_is_allowed(self):
        decision = evaluate_action("forecast")
        self.assertTrue(decision.allowed)
        self.assertFalse(decision.requires_human)

    def test_payment_requires_human(self):
        decision = evaluate_action("payment release")
        self.assertFalse(decision.allowed)
        self.assertTrue(decision.requires_human)
        approved = evaluate_action("payment release", authorized=True)
        self.assertTrue(approved.allowed)
        self.assertTrue(approved.requires_human)

    def test_blocked_action_stays_blocked(self):
        decision = evaluate_action("disable audit log", authorized=True)
        self.assertFalse(decision.allowed)
        self.assertTrue(decision.requires_human)

    def test_unknown_action_defaults_to_review(self):
        decision = evaluate_action("teleport-cash")
        self.assertFalse(decision.allowed)
        self.assertTrue(decision.requires_human)

    def test_redaction(self):
        text = "mail finance@example.com account 1234567890123"
        redacted = redact_sensitive(text)
        self.assertNotIn("finance@example.com", redacted)
        self.assertNotIn("1234567890123", redacted)
        self.assertIn("[REDACTED_EMAIL]", redacted)

    def test_audit_chain_and_tamper_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "audit.jsonl"
            log = AuditLog(path)
            first = log.append("analysis", actor="tester", payload={"value": 1})
            second = log.append("report", actor="tester", payload={"value": 2})
            self.assertEqual(second["previous_hash"], first["hash"])
            self.assertTrue(log.verify()["valid"])

            rows = path.read_text(encoding="utf-8").splitlines()
            record = json.loads(rows[0])
            record["payload"]["value"] = 999
            rows[0] = json.dumps(record, sort_keys=True)
            path.write_text("\n".join(rows) + "\n", encoding="utf-8")
            self.assertFalse(log.verify()["valid"])

    def test_sql_validation(self):
        self.assertEqual(validate_read_only_sql("SELECT 1;"), "SELECT 1")
        self.assertEqual(
            validate_read_only_sql("WITH x AS (SELECT 1 AS n) SELECT n FROM x"),
            "WITH x AS (SELECT 1 AS n) SELECT n FROM x",
        )
        with self.assertRaises(ValueError):
            validate_read_only_sql("DELETE FROM ledger")
        with self.assertRaises(ValueError):
            validate_read_only_sql("SELECT 1; DROP TABLE ledger")

    def test_read_only_sqlite_query(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "finance.db"
            connection = sqlite3.connect(db)
            connection.execute("CREATE TABLE ledger(account TEXT, amount REAL)")
            connection.executemany(
                "INSERT INTO ledger VALUES (?, ?)",
                [("Cash", 100.0), ("Revenue", 250.0)],
            )
            connection.commit()
            connection.close()

            rows = query_read_only(
                db,
                "SELECT account, amount FROM ledger ORDER BY account",
            )
            self.assertEqual([row["account"] for row in rows], ["Cash", "Revenue"])

    def test_sqlite_row_limit_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "empty.db"
            sqlite3.connect(db).close()
            with self.assertRaises(ValueError):
                query_read_only(db, "SELECT 1", row_limit=0)


if __name__ == "__main__":
    unittest.main()
