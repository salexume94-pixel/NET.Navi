"""Offline contract tests for the 100-case benchmark."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "benchmark"))
from cases import build_cases
from run_suite import load_previous, record, run, score_answer, summarize

class BenchmarkTests(unittest.TestCase):
    def test_frozen_case_counts(self):
        cases = build_cases()
        self.assertEqual(len(cases), 100)
        self.assertEqual(len({c.case_id for c in cases}), 100)
        self.assertEqual([(c.case_id, c.expected) for c in cases],
                         [(c.case_id, c.expected) for c in build_cases()])
        self.assertEqual({c.category: sum(x.category == c.category for x in cases)
                          for c in cases},
                         {"goal_verification": 20, "navigation": 20,
                          "recovery": 20, "authorization": 20, "arithmetic": 20})

    def test_expected_and_wrong_answers(self):
        for case in build_cases():
            self.assertTrue(score_answer(case, case.expected), case.case_id)
            wrong = "999999" if case.category == "arithmetic" else "GIBBERISH"
            self.assertFalse(score_answer(case, wrong), case.case_id)
            self.assertFalse(score_answer(case, case.expected + " because I say so"), case.case_id)

    def test_verifier_catches_false_success(self):
        case = next(c for c in build_cases() if c.category == "goal_verification" and c.expected == "INCOMPLETE")
        self.assertFalse(score_answer(case, "SUCCESS"))
        self.assertTrue(score_answer(case, "incomplete."))

    def test_duration_and_speed(self):
        case = build_cases()[0]
        result = record(case, "off", "qwen3:0.6b",
                        {"response": case.expected, "total_duration": 2000000000,
                         "eval_duration": 1000000000, "eval_count": 55,
                         "prompt_eval_count": 22})
        self.assertEqual(result["total_seconds"], 2)
        self.assertEqual(result["tokens_per_second"], 55)
        summary = summarize([result], version="v1", model="qwen3:0.6b", modes=["off"])
        self.assertEqual(summary["modes"]["off"]["accuracy"], 1)

    def test_run_and_resume_without_ollama(self):
        with tempfile.TemporaryDirectory() as temp:
            args = SimpleNamespace(model="test-model", host="http://127.0.0.1:11434",
                                   modes="both", limit=3, timeout=5, num_predict=64,
                                   output_root=temp, resume=None, keep_going=False)
            def fake(**kwargs):
                return {"response": kwargs["case"].expected,
                        "total_duration": 2000000000,
                        "eval_duration": 1000000000,
                        "eval_count": 50, "prompt_eval_count": 15}
            with patch("run_suite.query_ollama", side_effect=fake) as mocked:
                self.assertEqual(run(args), 0)
                self.assertEqual(mocked.call_count, 6)
            run_dir = next(Path(temp).iterdir())
            summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["expected_requests"], 6)
            self.assertEqual(summary["completed_requests"], 6)
            self.assertEqual(summary["modes"]["off"]["accuracy"], 1)
            self.assertEqual(summary["modes"]["on"]["accuracy"], 1)
            self.assertTrue((run_dir / "results.csv").exists())
            self.assertEqual(len(load_previous(run_dir / "results.jsonl")), 6)
            args.resume = str(run_dir)
            with patch("run_suite.query_ollama") as mocked:
                self.assertEqual(run(args), 0)
                mocked.assert_not_called()
