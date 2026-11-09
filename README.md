# NET.Navi
Welcome to MMBN

## Project direction

NET.Navi is an offline-first, operator-controlled AI companion inspired by *Mega Man Battle Network*. The goal is a recognizable personal Navi with local intelligence, persistent user-managed memory, an original PET-style interface, authorized skill chips and measured, controlled learning. This repository has a **first desktop streaming-chat prototype**, but is not yet a complete assistant.

## Project documents

- [Phase Development](docs/PHASE_DEVELOPMENT.md) — three phases: Pokémon AI Laboratory (Nora.EXE), Local Intelligence Engine, and True NET.Navi; with milestone acceptance criteria.
- [NET.Navi Research and Reference](docs/NETNAVI_REFERENCE.md) — franchise concepts, source references and real-world capability translations.
- [Architecture and Engineering Roadmap](docs/ARCHITECTURE_AND_ROADMAP.md) — component boundaries, software interfaces, security controls, benchmark goals and implementation order.

## Local Qwen evaluation

- [Automated Qwen benchmark](tools/benchmark/README.md) — 100 narrow evaluation cases, thinking-on/off comparison, incremental results, resume support, and one-command local execution with `run-benchmark.cmd`.
- [Ollama smoke test](tools/benchmark/smoke_test.py) — single-case local Qwen correctness and speed check.
- [Regression tests](tests/test_smoke_test.py) — deterministic offline checks for the scoring logic. GitHub Actions does not train or run Qwen.

**Next milestone:** Run the frozen baseline locally, review failures, and develop a **separate** training dataset without leaking evaluation questions into training. The Nora.EXE Pokémon laboratory remains independent of NET.Navi's language model.

## Streaming chat prototype

- [Run NET.Navi locally or with opt-in cloud reasoning](docs/STREAMING_INFERENCE_MVP.md): fast/balanced/deep profiles, streamed answers, explicit backend choice and first-visible-text timing.
- Local-only by default; stronger cloud reasoning requires explicit `--backend cloud` or `--backend hybrid` and API credentials.

```powershell
ollama pull qwen3:0.6b
python apps/desktop/netnavi_cli.py --backend local --model qwen3:0.6b --profile fast
```

This is an inference and performance test shell, **not** the finished Android PET, memory system, skill executor or independent learning core.
