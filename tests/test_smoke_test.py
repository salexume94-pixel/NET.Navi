"""Offline regression tests: no Ollama or model downloads required."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "benchmark"))
from smoke_test import is_correct, normalize_label


class StatusScoringTests(unittest.TestCase):
    def test_terminal_period_is_accepted(self):
        self.assertTrue(is_correct("INCOMPLETE.", "INCOMPLETE"))

    def test_exclamation_mark_is_accepted(self):
        self.assertTrue(is_correct(" incomplete! ", "INCOMPLETE"))

    def test_bare_expected_status_is_accepted(self):
        self.assertTrue(is_correct("INCOMPLETE", "INCOMPLETE"))

    def test_false_success_is_rejected(self):
        self.assertFalse(is_correct("SUCCESS", "INCOMPLETE"))

    def test_explanation_is_not_silently_counted_correct(self):
        self.assertFalse(is_correct("INCOMPLETE, because the agent is still inside.", "INCOMPLETE"))

    def test_contradictory_statuses_are_rejected(self):
        self.assertFalse(is_correct("SUCCESS. INCOMPLETE.", "INCOMPLETE"))

    def test_empty_and_unknown_are_rejected(self):
        self.assertIsNone(normalize_label(""))
        self.assertIsNone(normalize_label("UNKNOWN"))
        self.assertFalse(is_correct("", "INCOMPLETE"))


if __name__ == "__main__":
    unittest.main()
