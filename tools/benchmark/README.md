# NET.Navi local Qwen benchmarks

This is a **repeatable evaluation harness**, not weight training and not a verified autonomous gameplay test. It evaluates 100 deterministic, **mostly template-derived** questions on five narrow skills (20 per category): goal verification, navigation, recovery, action authorization, and arithmetic. Expected answers are supplied by the benchmark, **never by model claims**. Strict grading accepts one exact label or integer with optional final punctuation. The resulting score is not a general intelligence or safety metric.

The harness makes loopback HTTP requests to local Ollama with Python's standard library, bypassing HTTP proxy settings. Prompts, expected labels, Qwen responses, thinking modes, timing, token counts, and grading are saved locally in `reports/benchmark/<UTC-run-ID>/` as `results.jsonl`, `results.csv`, `config.json`, and `summary.json`. The reports are git-ignored and **not automatically uploaded**.

## Windows PowerShell

With Ollama running and `qwen3:0.6b` installed, from the repository root:

```powershell
# Quick trial: 10 shuffled cases with thinking OFF and ON (20 requests)
.\run-benchmark.cmd quick

# Full suite: 100 cases with thinking OFF and ON (200 requests)
.\run-benchmark.cmd
```

Or run directly for more control:

```powershell
.\.venv\Scripts\python.exe tools\benchmark\run_suite.py --limit 10 --modes off
.\.venv\Scripts\python.exe tools\benchmark\run_suite.py --modes both
```

The script saves each result immediately. Ctrl+C interrupts safely. On connection errors, it saves a partial summary and stops unless `--keep-going` is supplied. Resume a run without repeating finished cases:

```powershell
.\.venv\Scripts\python.exe tools\benchmark\run_suite.py --resume "reports\benchmark\<RUN-FOLDER>" --modes both
```

If resuming a smaller run, repeat its `--limit 10`. Repeat any changed `--model`, `--host`, or `--num-predict` flags. Resume configuration is checked.

**Accuracy** is correct labels divided by all attempted requests (errors separately counted); **median response time** and **median tokens per second** are calculated from Ollama-reported durations for completed responses only. The `think` parameter is the only intended mode difference. The default 1024-token cap may still constrain thinking-on results. Some models may not support thinking. These 100 related template cases do not establish broader reasoning capability. Don't train on this frozen evaluation set; build a separate training dataset.

Use `.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v` for offline tests or the existing `smoke_test.py` for a single-case API check. GitHub Actions only runs deterministic offline tests. GitHub-hosted runners cannot connect to your laptop's localhost Ollama server and do not run or fine-tune the model.


## Diagnosing thinking-mode failures

A previous 192-token trial produced **nine empty final answers out of ten thinking-mode requests**, each at 192 generated tokens. These were not proven reasoning failures: generation was likely consumed by thinking. The default budget is now **1024 tokens per request**, including thinking output. Use `--num-predict 2048` if the model still fails to finish, but note that this increases CPU time. The report records Ollama's `done_reason`, the length of its `thinking` field (not the reasoning text itself), `no_final_answers`, and `at_limit_no_final`.

The report deliberately separates **strict accuracy** (correct answer in requested format) from **semantic accuracy** (including an arithmetic equation with the correct result). For example, `61 + 10 = 71` is content-correct but format-invalid when the prompt demands `71` alone. Blank answers are tracked separately from API errors. For apples-to-apples comparisons, don't mix old 192-token runs with the new 1024-token baseline.
