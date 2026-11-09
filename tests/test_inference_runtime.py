"""Offline behavioral tests: no Ollama service or cloud key required."""
from __future__ import annotations
import io
import json
import unittest
from unittest.mock import patch

from core.inference.runtime import (
    InferenceError, Route, StreamEvent, bounded_messages, cloud_stream,
    generate, local_stream, select_route,
)


class MockResponse:
    def __init__(self, lines):
        self.lines = [line.encode("utf-8") for line in lines]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def __iter__(self):
        return iter(self.lines)


HISTORY = [
    {"role": "system", "content": "System"},
    {"role": "user", "content": "Hello"},
]


class RouterTests(unittest.TestCase):
    def test_offline_default_route(self):
        self.assertEqual(select_route("write code", "local", "deep", "qwen3:0.6b", "gpt-model").backend, "local")

    def test_cloud_only_when_explicitly_selected(self):
        self.assertEqual(select_route("Hi", "cloud", "fast", "q", "g").backend, "cloud")
        self.assertEqual(select_route("Hi", "hybrid", "balanced", "q", "g").backend, "local")
        self.assertEqual(select_route("Debug this error", "hybrid", "balanced", "q", "g").backend, "cloud")
        self.assertEqual(select_route("Hi", "hybrid", "deep", "q", "g").backend, "cloud")
        self.assertEqual(select_route("Debug this", "hybrid", "fast", "q", "g").backend, "local")

    def test_no_automatic_fallback_to_cloud(self):
        with self.assertRaises(InferenceError):
            select_route("debug", "hybrid", "deep", "q", "")

    def test_invalid_profile_rejected(self):
        with self.assertRaises(ValueError):
            select_route("anything", "local", "turbo", "q")

    def test_prunes_whole_turns(self):
        history = [HISTORY[0], {"role":"user", "content":"x"*150},
                   {"role":"assistant", "content":"y"*150},
                   {"role":"user", "content":"next"}]
        self.assertEqual(bounded_messages(history, max_chars=50), [history[0], history[-1]])

    def test_too_long_user_request_rejected_not_truncated(self):
        with self.assertRaises(InferenceError):
            bounded_messages(HISTORY, max_chars=5)


class LocalStreamingTests(unittest.TestCase):
    def test_streaming_and_budget(self):
        lines = [json.dumps({"message":{"content":"Hello"}, "done":False})+"\n",
                 json.dumps({"message":{"content":" world"}, "done":False})+"\n",
                 json.dumps({"message":{"content":""}, "done":True, "eval_count":3})+"\n"]
        route = Route("local", "fast", "qwen3:0.6b")
        with patch("core.inference.runtime._open_json_stream", return_value=MockResponse(lines)) as call:
            events = list(local_stream(HISTORY, route))
        self.assertEqual("".join(e.text for e in events), "Hello world")
        self.assertEqual(events[-1].usage["eval_count"], 3)
        body = call.call_args.args[1]
        self.assertFalse(body["think"])
        self.assertTrue(body["stream"])
        self.assertEqual(body["options"]["num_predict"], 256)
        self.assertEqual(body["keep_alive"], "10m")

    def test_deep_enables_thinking(self):
        with patch("core.inference.runtime._open_json_stream", return_value=MockResponse([json.dumps({"done":True})])) as call:
            list(local_stream(HISTORY, Route("local", "deep", "q")))
        self.assertTrue(call.call_args.args[1]["think"])

    def test_failed_or_incomplete_stream(self):
        with patch("core.inference.runtime._open_json_stream", return_value=MockResponse([json.dumps({"done":False})])):
            with self.assertRaises(InferenceError):
                list(local_stream(HISTORY, Route("local", "balanced", "q")))

    def test_remote_host_forbidden(self):
        with self.assertRaises(InferenceError):
            list(local_stream(HISTORY, Route("local", "fast", "q"), host="http://elsewhere:11434"))


class CloudStreamingTests(unittest.TestCase):
    def test_sse_stream_and_privacy_settings(self):
        lines = ['event: response.output_text.delta\n',
                 'data: '+json.dumps({"type":"response.output_text.delta", "delta":"Yes"})+'\n',
                 '\n',
                 'data: '+json.dumps({"type":"response.completed", "response":{"usage":{"input_tokens":3}}})+'\n',
                 'data: [DONE]\n']
        with patch("core.inference.runtime._open_json_stream", return_value=MockResponse(lines)) as call:
            events = list(cloud_stream(HISTORY, Route("cloud", "deep", "gpt-test"), api_key="dummy"))
        self.assertEqual(events[0].text, "Yes")
        self.assertEqual(events[-1].usage["input_tokens"], 3)
        self.assertEqual(call.call_args.args[0], "https://api.openai.com/v1/responses")
        payload = call.call_args.args[1]
        self.assertFalse(payload["store"])
        self.assertEqual(payload["reasoning"]["effort"], "high")
        self.assertEqual(payload["input"], HISTORY[1:])

    def test_cloud_requires_key(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY":""}):
            with self.assertRaises(InferenceError):
                list(cloud_stream(HISTORY, Route("cloud", "fast", "gpt-test")))

    def test_incomplete_response_fails_not_success(self):
        lines = ['data: '+json.dumps({"type":"response.incomplete"})+'\n']
        with patch("core.inference.runtime._open_json_stream", return_value=MockResponse(lines)):
            with self.assertRaises(InferenceError):
                list(cloud_stream(HISTORY, Route("cloud", "fast", "g"), api_key="dummy"))


class GenerateTests(unittest.TestCase):
    def test_metrics_and_output_callback(self):
        def fake_stream(*args, **kwargs):
            yield StreamEvent("text", text="one ")
            yield StreamEvent("text", text="two")
            yield StreamEvent("done", usage={"eval_count": 2})
        chunks = []
        with patch("core.inference.runtime.local_stream", fake_stream):
            text, metrics = generate(HISTORY, Route("local", "fast", "q"), on_text=chunks.append)
        self.assertEqual(text, "one two")
        self.assertEqual(chunks, ["one ", "two"])
        self.assertIsNotNone(metrics.first_token_seconds)
        self.assertEqual(metrics.usage["eval_count"], 2)

    def test_empty_final_is_error(self):
        def fake_stream(*args, **kwargs):
            yield StreamEvent("done", usage={})
        with patch("core.inference.runtime.local_stream", fake_stream):
            with self.assertRaises(InferenceError):
                generate(HISTORY, Route("local", "fast", "q"))


if __name__ == "__main__":
    unittest.main()
