# NET.Navi Qwen smoke test

This is a **local Ollama API smoke test**, not model training. Its small prompt checks whether Qwen correctly labels a still-incomplete objective. A result like `INCOMPLETE.` passes despite the final period; false or ambiguous labels do not pass.

## Run locally (Windows PowerShell)

Ensure Ollama is running and `qwen3:0.6b` is installed, then from the repository root:

```powershell
.\.venv\Scripts\python.exe tools\benchmark\smoke_test.py
```

The script uses the Python standard library and connects directly to `127.0.0.1:11434` without system HTTP proxies. Exit code 0 means PASS, 1 means wrong answer, and 2 means a connection or response error.

Run the scoring regression tests without Ollama:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

GitHub Actions runs the offline tests only. Running live model inference needs a reachable Ollama service and its model, such as on your Windows laptop. The test is one example, not a measure of Qwen's general reasoning accuracy.
