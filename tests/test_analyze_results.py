"""Offline tests for failure triage and selective reruns."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "benchmark"))
from analyze_results import analyze, load_rows, write_triage
from run_suite import run


class TriageTests(unittest.TestCase):
    def test_truncation_and_format_are_separate(self):
        rows = [
            {"case_id": "goal-001", "mode": "off", "category": "goal_verification",
             "expected": "SUCCESS", "answer": "INCOMPLETE", "correct": False,
             "semantic_correct": False, "outcome": "incorrect_decision", "total_seconds": 1.0},
            {"case_id": "goal-001", "mode": "on", "category": "goal_verification",
             "expected": "SUCCESS", "answer": "SUCCESS", "correct": True,
             "semantic_correct": True, "outcome": "pass", "total_seconds": 10.0},
            {"case_id": "arithmetic-012", "mode": "off", "category": "arithmetic",
             "expected": "71", "answer": "61 + 10 = 71", "correct": False,
             "semantic_correct": True, "outcome": "format_failure", "total_seconds": 0.5},
            {"case_id": "arithmetic-012", "mode": "on", "category": "arithmetic",
             "expected": "71", "answer": "", "correct": False,
             "semantic_correct": False, "outcome": "no_final_at_limit",
             "total_seconds": 22.0},
        ]
        stats = analyze(rows)
        self.assertEqual(stats["modes"]["off"]["strict"], 0)
        self.assertEqual(stats["modes"]["off"]["semantic"], 1)
        self.assertEqual(stats["modes"]["on"]["strict"], 1)
        self.assertEqual(stats["retry_ids"], ["arithmetic-012"])
        self.assertEqual(stats["off_wrong_on_right"], ["goal-001"])
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "results.jsonl").write_text(
                "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
            report = write_triage(folder)
            self.assertEqual(report["retry_ids"], ["arithmetic-012"])
            self.assertIn("61 + 10 = 71", (folder / "triage.md").read_text(encoding="utf-8"))
            self.assertEqual((folder / "retry_thinking_case_ids.txt").read_text(encoding="utf-8"),
                             "arithmetic-012\n")
            self.assertEqual(len(load_rows(folder)), 4)

    def test_case_file_selects_only_requested_case(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ids = root / "select.txt"
            ids.write_text("goal-001\n", encoding="utf-8")
            args = SimpleNamespace(
                model="test-model", host="http://127.0.0.1:11434",
                modes="on", limit=None, case_file=str(ids), timeout=5,
                num_predict=2048, output_root=str(root / "runs"),
                resume=None, keep_going=False)
            def fake(**kwargs):
                return {"response": kwargs["case"].expected,
                        "total_duration": 1500000000,
                        "eval_duration": 1000000000,
                        "eval_count": 50}
            with patch("run_suite.query_ollama", side_effect=fake) as mocked:
                self.assertEqual(run(args), 0)
                self.assertEqual(mocked.call_count, 1)
            folder = next((root / "runs").iterdir())
            self.assertEqual(len(load_rows(folder)), 1)
            self.assertTrue((folder / "triage.md").exists())

    def test_unknown_case_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.txt"
            bad.write_text("some-invented-id\n", encoding="utf-8")
            args = SimpleNamespace(model="test-model", host="http://127.0.0.1:11434",
                                   modes="on", limit=None, case_file=str(bad),
                                   timeout=5, num_predict=64, output_root=tmp,
                                   resume=None, keep_going=False)
            with self.assertRaisesRegex(ValueError, "Unknown case IDs"):
                run(args)


if __name__ == "__main__":
    unittest.main()
