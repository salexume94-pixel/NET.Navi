"""Run a resumable 100-case local Qwen benchmark in thinking on/off modes."""
from __future__ import annotations
import argparse
import csv
import datetime as dt
import json
import re
import statistics
import sys
import urllib.error
import urllib.request
from pathlib import Path
from cases import Case, build_cases

BENCHMARK_VERSION = "v1-template-100"
LABELS = {
    "goal_verification": {"SUCCESS", "INCOMPLETE", "UNVERIFIED"},
    "navigation": {"NORTH", "SOUTH", "EAST", "WEST", "OBSERVE"},
    "recovery": {"ALTERNATE", "OBSERVE", "BACKTRACK", "ASK_OPERATOR"},
    "authorization": {"ALLOW", "DENY", "ASK"},
}

def score_answer(case: Case, answer: str) -> bool:
    """Check one answer; tolerate harmless final punctuation, not explanations."""
    normalized = answer.strip().removesuffix(".").removesuffix("!").strip().upper()
    if case.category in LABELS:
        return normalized in LABELS[case.category] and normalized == case.expected.upper()
    if case.category == "arithmetic":
        return re.fullmatch(r"[-+]?\d+", normalized) is not None and int(normalized) == int(case.expected)
    raise ValueError(f"Unknown category: {case.category}")

def query_ollama(*, host: str, model: str, case: Case, think: bool,
                 timeout: int, num_predict: int) -> dict:
    request_data = {
        "model": model,
        "prompt": ("You are being evaluated. Use only the facts in the question. "
                   "Follow the requested answer format exactly.\n\n" + case.prompt),
        "stream": False,
        "think": think,
        "options": {"temperature": 0, "seed": 42, "num_predict": num_predict},
    }
    req = urllib.request.Request(
        host.rstrip("/") + "/api/generate", method="POST",
        data=json.dumps(request_data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    # Bypass proxies for the loopback-only Ollama API.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(req, timeout=timeout) as response:
        data = json.load(response)
    if not isinstance(data, dict) or not isinstance(data.get("response"), str):
        raise ValueError("Ollama response is missing response text")
    return data

def record(case: Case, mode: str, model: str, response: dict) -> dict:
    answer = response["response"]
    total_seconds = float(response.get("total_duration") or 0) / 1e9
    eval_seconds = float(response.get("eval_duration") or 0) / 1e9
    eval_count = int(response.get("eval_count") or 0)
    return {
        "case_id": case.case_id, "category": case.category, "model": model,
        "mode": mode, "prompt": case.prompt, "expected": case.expected,
        "answer": answer, "correct": score_answer(case, answer),
        "total_seconds": round(total_seconds, 4),
        "tokens_per_second": round(eval_count / eval_seconds, 2) if eval_seconds else None,
        "generated_tokens": eval_count,
        "prompt_tokens": int(response.get("prompt_eval_count") or 0),
        "status": "ok", "error": None,
    }

def load_previous(path: Path) -> dict[tuple[str, str], dict]:
    existing = {}
    if not path.exists():
        return existing
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            entry = json.loads(line)
            key = (entry["case_id"], entry["mode"])
            if key in existing:
                raise ValueError(f"Duplicate case/mode in resume file: {key}")
            existing[key] = entry
    return existing

def summarize(results: list[dict], *, version: str, model: str, modes: list[str]) -> dict:
    summary = {"benchmark_version": version, "model": model,
               "notes": "Mostly template-derived cases, not a general intelligence or safety score.",
               "modes": {}}
    for mode in modes:
        group = [r for r in results if r["mode"] == mode]
        ok = [r for r in group if r["status"] == "ok"]
        durations = [r["total_seconds"] for r in ok]
        speeds = [r["tokens_per_second"] for r in ok if r["tokens_per_second"] is not None]
        by_category = {}
        for category in sorted({r["category"] for r in group}):
            subset = [r for r in group if r["category"] == category]
            by_category[category] = {
                "attempted": len(subset), "correct": sum(r["correct"] is True for r in subset),
                "errors": sum(r["status"] != "ok" for r in subset),
            }
        summary["modes"][mode] = {
            "attempted": len(group),
            "correct": sum(r["correct"] is True for r in group),
            "errors": len(group) - len(ok),
            "accuracy": round(sum(r["correct"] is True for r in group) / len(group), 4) if group else None,
            "median_response_seconds": round(statistics.median(durations), 3) if durations else None,
            "median_tokens_per_second": round(statistics.median(speeds), 2) if speeds else None,
            "by_category": by_category,
        }
    return summary

def save_reports(out_dir: Path, records: list[dict], *, model: str,
                 modes: list[str], selected_cases: list[Case]) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = summarize(records, version=BENCHMARK_VERSION, model=model, modes=modes)
    summary["expected_requests"] = len(selected_cases) * len(modes)
    summary["completed_requests"] = len(records)
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    if records:
        fields = ["case_id", "category", "mode", "model", "expected", "answer", "correct",
                  "status", "total_seconds", "tokens_per_second", "generated_tokens",
                  "prompt_tokens", "error"]
        with (out_dir / "results.csv").open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(records)
    return summary

def run(args: argparse.Namespace) -> int:
    cases = build_cases(seed=42)
    cases = cases[:args.limit] if args.limit is not None else cases
    modes = ["off", "on"] if args.modes == "both" else [args.modes]
    out_dir = (Path(args.resume) if args.resume else
               Path(args.output_root) / dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    out_dir.mkdir(parents=True, exist_ok=True)
    meta_path = out_dir / "config.json"
    meta = {"benchmark_version": BENCHMARK_VERSION, "model": args.model,
            "case_ids": [c.case_id for c in cases], "modes": modes,
            "host": args.host, "num_predict": args.num_predict}
    if meta_path.exists():
        if json.loads(meta_path.read_text(encoding="utf-8")) != meta:
            raise ValueError("Resume configuration doesn't match existing run; use original flags")
    else:
        meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    path = out_dir / "results.jsonl"
    previous = load_previous(path)
    expected_keys = {(c.case_id, m) for c in cases for m in modes}
    if not set(previous).issubset(expected_keys):
        raise ValueError("Resume file contains unexpected case IDs or modes")
    count = len(expected_keys)
    print(f"Running {len(cases)} cases in {len(modes)} mode(s): {count} requests. Reports: {out_dir}", flush=True)
    print("Each response is saved immediately. Ctrl+C interrupts; use --resume to continue.", flush=True)
    try:
        with path.open("a", encoding="utf-8") as output:
            for case in cases:
                for mode in modes:
                    key = (case.case_id, mode)
                    if key in previous:
                        continue
                    try:
                        response = query_ollama(host=args.host, model=args.model, case=case,
                            think=mode == "on", timeout=args.timeout,
                            num_predict=args.num_predict)
                        item = record(case, mode, args.model, response)
                    except (urllib.error.URLError, OSError, TimeoutError, ValueError, KeyError, TypeError) as exc:
                        item = {"case_id": case.case_id, "category": case.category,
                            "mode": mode, "model": args.model, "prompt": case.prompt,
                            "expected": case.expected, "answer": "", "correct": False,
                            "status": "error", "error": str(exc), "total_seconds": None,
                            "tokens_per_second": None, "generated_tokens": None,
                            "prompt_tokens": None}
                    output.write(json.dumps(item, ensure_ascii=False) + "\n")
                    output.flush()
                    previous[key] = item
                    verdict = ("PASS" if item["correct"] else "FAIL") if item["status"] == "ok" else "ERROR"
                    print(f"[{len(previous)}/{count}] {case.case_id} ({mode}): {verdict}", flush=True)
                    if item["status"] == "error" and not args.keep_going:
                        print(f"Stopped after error: {item['error']}", file=sys.stderr)
                        save_reports(out_dir, list(previous.values()), model=args.model,
                                     modes=modes, selected_cases=cases)
                        return 2
    except KeyboardInterrupt:
        save_reports(out_dir, list(previous.values()), model=args.model,
                     modes=modes, selected_cases=cases)
        extra = f" --limit {args.limit}" if args.limit is not None else ""
        print(f'Interrupted. Resume: python tools/benchmark/run_suite.py --resume "{out_dir}" --modes {args.modes}{extra}')
        return 130
    summary = save_reports(out_dir, list(previous.values()), model=args.model,
                           modes=modes, selected_cases=cases)
    for mode, entry in summary["modes"].items():
        print(f"{mode}: {entry['correct']}/{entry['attempted']} correct, "
              f"{entry['errors']} errors, median {entry['median_response_seconds']}s, "
              f"{entry['median_tokens_per_second']} tok/s")
    print(f"Results: {out_dir / 'results.csv'}\nSummary: {out_dir / 'summary.json'}")
    return 0 if all(entry["errors"] == 0 for entry in summary["modes"].values()) else 2

def make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", default="qwen3:0.6b")
    p.add_argument("--host", default="http://127.0.0.1:11434")
    p.add_argument("--modes", choices=["off", "on", "both"], default="both")
    p.add_argument("--limit", type=int, default=None, help="First N shuffled cases for a quick trial")
    p.add_argument("--timeout", type=int, default=120, help="Seconds per request")
    p.add_argument("--num-predict", type=int, default=192, help="Max generated tokens per request")
    p.add_argument("--output-root", default="reports/benchmark")
    p.add_argument("--resume", default=None, help="Existing run directory")
    p.add_argument("--keep-going", action="store_true", help="Continue after API errors")
    return p

if __name__ == "__main__":
    parser = make_parser()
    arguments = parser.parse_args()
    if arguments.limit is not None and not (1 <= arguments.limit <= 100):
        parser.error("--limit must be from 1 to 100")
    if arguments.timeout < 1 or arguments.num_predict < 1:
        parser.error("--timeout and --num-predict must be positive")
    try:
        raise SystemExit(run(arguments))
    except (ValueError, OSError) as error:
        parser.exit(2, f"ERROR: {error}\n")
