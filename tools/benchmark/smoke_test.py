"""Run a local Ollama smoke test for NET.Navi.

Requires a local Ollama server and the qwen3:0.6b model.
No third-party Python packages required.
"""
import json
import re
import sys
import urllib.error
import urllib.request

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen3:0.6b"
EXPECTED = "INCOMPLETE"


def normalize_label(answer: str) -> str | None:
    """Accept a single decision with optional terminal punctuation only."""
    match = re.fullmatch(r"\s*(SUCCESS|INCOMPLETE)\s*[.!]?\s*", answer, re.IGNORECASE)
    return match.group(1).upper() if match else None


def is_correct(answer: str, expected: str) -> bool:
    """Never reward a verbose, contradictory, or unknown status."""
    predicted = normalize_label(answer)
    target = normalize_label(expected)
    return predicted is not None and target is not None and predicted == target


def evaluate() -> int:
    payload = {
        "model": MODEL,
        "prompt": (
            "Goal: Exit a house. You moved west but remain inside. "
            "Is the objective complete? Answer SUCCESS or INCOMPLETE."
        ),
        "stream": False,
        "think": False,
        "options": {"temperature": 0, "num_predict": 80},
    }
    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    # Direct loopback access; avoid proxy settings that can break localhost.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(request, timeout=120) as response:
            result = json.load(response)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        print(f"ERROR: Ollama is unreachable at {OLLAMA_URL}: {exc}", file=sys.stderr)
        print("Start Ollama and check: curl.exe --noproxy '*' http://127.0.0.1:11434/api/tags", file=sys.stderr)
        return 2
    except (ValueError, KeyError, TypeError) as exc:
        print(f"ERROR: Invalid Ollama response: {exc}", file=sys.stderr)
        return 2

    answer = str(result.get("response", "")).strip()
    if not answer:
        print("ERROR: Ollama returned an empty response.", file=sys.stderr)
        return 2
    duration_seconds = result.get("total_duration", 0) / 1e9
    eval_seconds = result.get("eval_duration", 0) / 1e9
    tokens = result.get("eval_count", 0)
    passed = is_correct(answer, EXPECTED)

    print("MODEL:", MODEL)
    print("ANSWER:", answer)
    print("EXPECTED:", EXPECTED)
    print("RESULT:", "PASS" if passed else "FAIL")
    print(f"TIME: {duration_seconds:.2f}s")
    if eval_seconds > 0:
        print(f"SPEED: {tokens / eval_seconds:.2f} tokens/sec")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(evaluate())
