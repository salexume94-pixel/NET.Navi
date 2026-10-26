"""Analyze benchmark logs without rerunning Ollama; generate triage and retry list."""
import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path


def load_rows(path):
    source = path / "results.jsonl" if path.is_dir() else path
    if not source.exists() and path.is_dir():
        source = path / "results.csv"
    if not source.exists():
        raise FileNotFoundError(source)
    if source.suffix == ".jsonl":
        rows = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines()
                if line.strip()]
    elif source.suffix == ".csv":
        with source.open(newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.DictReader(handle))
    else:
        raise ValueError("Expected results.jsonl or results.csv")
    if len(set((r.get("case_id"), r.get("mode")) for r in rows)) != len(rows):
        raise ValueError("Duplicate case/mode rows")
    return rows


def yes(value):
    return value is True or (isinstance(value, str) and value.lower() == "true")


def quantile(values, q):
    if not values:
        return None
    values = sorted(values)
    pos = (len(values) - 1) * q
    low, high = math.floor(pos), math.ceil(pos)
    return values[low] + (values[high] - values[low]) * (pos - low)


def analyze(rows):
    result = {"modes": {}, "retry_ids": [], "off_wrong_on_right": [], "off_right_on_wrong": []}
    paired = defaultdict(dict)
    for row in rows:
        paired[row["case_id"]][row["mode"]] = row
    for case_id, pair in paired.items():
        if "off" in pair and "on" in pair:
            off, on = yes(pair["off"].get("correct")), yes(pair["on"].get("correct"))
            if not off and on:
                result["off_wrong_on_right"].append(case_id)
            elif off and not on:
                result["off_right_on_wrong"].append(case_id)
    result["retry_ids"] = sorted({
        r["case_id"] for r in rows
        if r["mode"] == "on" and r.get("outcome") == "no_final_at_limit"
    })
    for mode in ("off", "on"):
        group = [r for r in rows if r.get("mode") == mode]
        times = [float(r["total_seconds"]) for r in group if r.get("total_seconds") not in (None, "")]
        categories = {}
        for category in sorted({r["category"] for r in group}):
            subset = [r for r in group if r["category"] == category]
            categories[category] = {
                "total": len(subset),
                "strict": sum(yes(r.get("correct")) for r in subset),
                "semantic": sum(yes(r.get("semantic_correct")) for r in subset),
            }
        result["modes"][mode] = {
            "total": len(group),
            "strict": sum(yes(r.get("correct")) for r in group),
            "semantic": sum(yes(r.get("semantic_correct")) for r in group),
            "p50": quantile(times, 0.5),
            "p90": quantile(times, 0.9),
            "outcomes": Counter(r.get("outcome") or "unknown" for r in group),
            "categories": categories,
        }
    return result


def cell(value, limit=120):
    text = str(value or "").replace("\n", " ").replace("\r", " ").replace("|", "/")
    return text[:limit] + "..." if len(text) > limit else text


def write_triage(run_path):
    rows = load_rows(run_path)
    report = analyze(rows)
    directory = run_path if run_path.is_dir() else run_path.parent
    lines = ["# NET.Navi benchmark triage", "",
             "This analyzes saved results without any new inference. The questions are mostly templates and are not a real-world autonomy/safety benchmark.",
             "", "## Accuracy and latency", "",
             "| Mode | Strict | Content | Median seconds | P90 seconds |",
             "|---|---:|---:|---:|---:|"]
    for mode, data in report["modes"].items():
        t50 = f'{data["p50"]:.2f}' if data["p50"] is not None else "n/a"
        t90 = f'{data["p90"]:.2f}' if data["p90"] is not None else "n/a"
        lines.append(f'| {mode} | {data["strict"]}/{data["total"]} | {data["semantic"]}/{data["total"]} | {t50} | {t90} |')
    lines += ["", "## Strict scores by category", "",
              "| Category | OFF | ON |", "|---|---:|---:|"]
    category_names = sorted(set(report["modes"]["off"]["categories"]) | set(report["modes"]["on"]["categories"]))
    for category in category_names:
        entries = [report["modes"][mode]["categories"].get(category) for mode in ("off", "on")]
        format_entries = [f'{e["strict"]}/{e["total"]}' if e else "n/a" for e in entries]
        lines.append(f'| {category} | {format_entries[0]} | {format_entries[1]} |')
    lines += ["", "## Failure types", "", "| Mode | Outcome | Count |", "|---|---|---:|"]
    for mode, data in report["modes"].items():
        for outcome, count in sorted(data["outcomes"].items()):
            lines.append(f"| {mode} | {outcome} | {count} |")
    lines += ["", "## Thinking mode at token cap", "",
              f'{len(report["retry_ids"])} cases need targeted reruns with a larger token budget.',
              ", ".join(report["retry_ids"]) or "(none)",
              "", "## Mode disagreements", "",
              f'OFF wrong, ON correct: {len(report["off_wrong_on_right"])}',
              f'OFF correct, ON wrong: {len(report["off_right_on_wrong"])}',
              "", "## Failed answers to inspect", "",
              "| Case | Mode | Classification | Expected | Answer |",
              "|---|---|---|---|---|"]
    for r in rows:
        if yes(r.get("correct")):
            continue
        lines.append("| " + " | ".join(cell(r.get(k)) for k in
                        ("case_id", "mode", "outcome", "expected", "answer")) + " |")
    lines += ["", "Do not add the held-out benchmark prompts to a training dataset.", ""]
    (directory / "triage.md").write_text("\n".join(lines), encoding="utf-8")
    (directory / "retry_thinking_case_ids.txt").write_text(
        "\n".join(report["retry_ids"]) + ("\n" if report["retry_ids"] else ""),
        encoding="utf-8",
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", help="Run directory or results file; default is newest report")
    args = parser.parse_args()
    if args.path:
        path = Path(args.path)
    else:
        root = Path("reports") / "benchmark"
        candidates = sorted(
            (p for p in root.iterdir() if p.is_dir() and (p / "results.jsonl").is_file()),
            key=lambda p: p.name, reverse=True,
        ) if root.exists() else []
        if not candidates:
            parser.error("No benchmark reports found")
        path = candidates[0]
    report = write_triage(path)
    folder = path if path.is_dir() else path.parent
    print(f"Triage report: {folder / 'triage.md'}")
    print(f"Thinking truncated cases: {len(report['retry_ids'])}")
    print(f"Retry list: {folder / 'retry_thinking_case_ids.txt'}")
    for mode, data in report["modes"].items():
        print(f'{mode}: strict {data["strict"]}/{data["total"]}, '
              f'content {data["semantic"]}/{data["total"]}, '
              f'p90 {data["p90"]:.2f}s' if data["p90"] is not None
              else f'{mode}: no timing data')


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as err:
        raise SystemExit(f"ERROR: {err}")
