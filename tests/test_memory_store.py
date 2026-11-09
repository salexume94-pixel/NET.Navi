"""Offline memory and privacy tests; no model service or API key required."""
from __future__ import annotations

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from apps.desktop import netnavi_cli
from core.inference.runtime import Metrics, Route
from core.memory.store import MAX_CONTENT, MemoryStore, memory_context


class MemoryStoreTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.dbfile = Path(self.directory.name) / "app" / "memory.sqlite3"
        self.store = MemoryStore(self.dbfile)
        self.addCleanup(self.store.close)

    def test_persists_across_restarts(self):
        note = self.store.add("My favorite color is green", "preference")
        with MemoryStore(self.dbfile) as reloaded:
            self.assertEqual(reloaded.list()[0], note)
            self.assertEqual(reloaded.count(), 1)

    def test_add_explicit_kind_and_timestamps(self):
        note = self.store.add("My dog is Zelda")
        self.assertEqual(note.kind, "fact")
        self.assertEqual(len(note.id), 32)
        self.assertIn("T", note.created_at)
        self.assertEqual(note.created_at, note.updated_at)

    def test_search_retrieves_relevant_notes_only(self):
        liked = self.store.add("My favorite color is green", "preference")
        self.store.add("My childhood city was Boston")
        self.assertEqual(self.store.search("What is my favorite color?"), [liked])
        self.assertEqual(self.store.search("I just said hi"), [])

    def test_search_literal_sql_wildcards(self):
        note = self.store.add("Favorite game is Tetris_99")
        self.store.add("A different game uses TetrisABC99")
        self.assertEqual(self.store.search("Tetris_99"), [note])

    def test_search_returns_no_notes_for_stopwords(self):
        self.store.add("Secret topic")
        self.assertEqual(self.store.search("What can you tell me?"), [])

    def test_edit_by_prefix_preserves_id_and_kind(self):
        note = self.store.add("Color is red", "preference")
        edited = self.store.edit(note.id[:8], "Color is blue")
        self.assertEqual(edited.id, note.id)
        self.assertEqual(edited.kind, "preference")
        self.assertEqual(edited.text, "Color is blue")
        self.assertEqual(self.store.search("Color blue"), [edited])
        self.assertEqual(self.store.search("Color red"), [edited])  # 'color' still matches

    def test_delete_one_by_prefix_and_clear_all(self):
        one = self.store.add("One")
        self.store.add("Two")
        self.store.delete(one.id[:8])
        self.assertEqual(self.store.count(), 1)
        self.assertEqual(self.store.clear(), 1)
        self.assertEqual(self.store.count(), 0)

    def test_invalid_data_and_ids_rejected(self):
        for bad in ("", " ", "x" * (MAX_CONTENT + 1), "bad\x00data"):
            with self.subTest(bad=bad[:10]), self.assertRaises(ValueError):
                self.store.add(bad)
        with self.assertRaises(ValueError):
            self.store.add("test", "secret")
        for ident in ("123", "not an id", "0" * 8):
            with self.subTest(ident=ident), self.assertRaises(ValueError):
                self.store.delete(ident)

    def test_export_user_requested_only_does_not_overwrite(self):
        self.store.add("Saved locally", "fact")
        dest = Path(self.directory.name) / "my notes.json"
        self.store.export_json(dest)
        payload = json.loads(dest.read_text(encoding="utf-8"))
        self.assertEqual(payload["version"], 1)
        self.assertEqual(payload["memories"][0]["text"], "Saved locally")
        with self.assertRaises(FileExistsError):
            self.store.export_json(dest)

    def test_database_is_local_and_writes_no_other_files(self):
        self.store.add("A local fact")
        self.assertTrue(self.dbfile.is_file())
        self.assertEqual(self.dbfile.parent.name, "app")

    def test_memory_prompt_does_not_change_absent_recall(self):
        self.assertEqual(memory_context("Hello", []), "Hello")

    def test_memory_prompt_marks_saved_notes_as_untrusted(self):
        note = self.store.add("My favorite color is green")
        ctx = memory_context("What color do I like?", [note])
        self.assertIn("UNTRUSTED", ctx)
        self.assertIn("My favorite color is green", ctx)
        self.assertTrue(ctx.endswith("What color do I like?"))

    def test_failed_update_does_not_modify_note(self):
        note = self.store.add("Keep me")
        with self.assertRaises(ValueError):
            self.store.edit(note.id[:8], "")
        self.assertEqual(self.store.list()[0].text, "Keep me")


class ChatMemoryPrivacyTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.dbfile = Path(self.directory.name) / "memory.sqlite3"
        self.store = MemoryStore(self.dbfile)
        self.addCleanup(self.store.close)
        self.store.add("My favorite color is green")
        self.history = [{"role": "system", "content": "No action claims"}]

    def test_local_can_use_relevant_saved_memory(self):
        messages = netnavi_cli.prepare_messages(
            self.history, "What is my favorite color?", Route("local", "fast", "q"), self.store
        )
        self.assertIn("green", messages[-1]["content"])

    def test_cloud_does_not_get_saved_notes_by_default(self):
        messages = netnavi_cli.prepare_messages(
            self.history, "What is my favorite color?", Route("cloud", "deep", "g"), self.store
        )
        self.assertNotIn("green", json.dumps(messages))

    def test_cloud_requires_separate_optin_for_saved_notes(self):
        messages = netnavi_cli.prepare_messages(
            self.history, "What is my favorite color?", Route("cloud", "deep", "g"),
            self.store, share_memory_with_cloud=True,
        )
        self.assertIn("green", messages[-1]["content"])

    def test_session_history_does_not_leak_notes_on_later_cloud_turn(self):
        calls = []
        def fake_generate(messages, route, on_text):
            calls.append((messages, route.backend))
            return "OK", Metrics(route, 0.01, 0.02, 2, {})
        with patch("builtins.input", side_effect=[
            "What is my favorite color?", "Debug a difficult error", "/exit"
        ]), patch("apps.desktop.netnavi_cli.generate", side_effect=fake_generate), \
             redirect_stdout(io.StringIO()):
            self.assertEqual(netnavi_cli.main([
                "--backend", "hybrid", "--cloud-model", "g", "--memory-db", str(self.dbfile)
            ]), 0)
        self.assertEqual([mode for _, mode in calls], ["local", "cloud"])
        self.assertIn("green", json.dumps(calls[0][0]))
        self.assertNotIn("green", json.dumps(calls[1][0]))
        self.assertNotIn("What is my favorite color?", json.dumps(calls[1][0]))

    def test_memory_derived_local_reply_never_replays_to_cloud(self):
        calls = []
        def fake_generate(messages, route, on_text):
            calls.append((messages, route.backend))
            answer = "Your favorite color is green" if route.backend == "local" else "Reviewed"
            return answer, Metrics(route, 0.01, 0.02, len(answer), {})
        with patch("builtins.input", side_effect=[
            "What is my favorite color?", "Debug a difficult error", "/exit"
        ]), patch("apps.desktop.netnavi_cli.generate", side_effect=fake_generate), \
             redirect_stdout(io.StringIO()):
            self.assertEqual(netnavi_cli.main([
                "--backend", "hybrid", "--cloud-model", "g", "--memory-db", str(self.dbfile)
            ]), 0)
        self.assertIn("green", json.dumps(calls[0][0]))
        self.assertNotIn("green", json.dumps(calls[1][0]))

    def test_model_reply_does_not_create_memory(self):
        def fake_generate(messages, route, on_text):
            return "Please remember this detail", Metrics(route, 0.01, 0.02, 27, {})
        with patch("apps.desktop.netnavi_cli.generate", side_effect=fake_generate), \
             redirect_stdout(io.StringIO()):
            self.assertEqual(netnavi_cli.main([
                "--backend", "local", "--once", "Hello", "--memory-db", str(self.dbfile)
            ]), 0)
        self.assertEqual(self.store.count(), 1)

    def test_clear_requires_exact_confirmation(self):
        with redirect_stdout(io.StringIO()):
            netnavi_cli.execute_command("/clear-memories", self.store)
        self.assertEqual(self.store.count(), 1)
        with redirect_stdout(io.StringIO()):
            netnavi_cli.execute_command("/clear-memories CONFIRM", self.store)
        self.assertEqual(self.store.count(), 0)

    def test_commands_manage_notes_without_model(self):
        with redirect_stdout(io.StringIO()):
            self.assertTrue(netnavi_cli.execute_command("/prefer I like puzzle games", self.store))
            note = next(n for n in self.store.list() if n.kind == "preference")
            self.assertTrue(netnavi_cli.execute_command("/edit " + note.id[:8] + " I like action games", self.store))
            self.assertTrue(netnavi_cli.execute_command("/memories", self.store))
            self.assertTrue(netnavi_cli.execute_command("/forget " + note.id[:8], self.store))
        self.assertEqual(self.store.count(), 1)
        self.assertFalse(netnavi_cli.execute_command("hello", self.store))


if __name__ == "__main__":
    unittest.main()
