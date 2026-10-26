# NET.Navi
Welcome to MMBN

## Project direction

NET.Navi is an offline-first, operator-controlled AI companion inspired by *Mega Man Battle Network*. The goal is a recognizable personal Navi with local intelligence, persistent user-managed memory, an original PET-style interface, authorized skill chips and measured, controlled learning. The **full companion is still in development**.

## Android GGUF launcher (first implementation)

- [Android launcher source and build steps](mobile/android/README.md) — import a quantized GGUF, load it via a local arm64 llama.cpp CPU runtime, and chat through an original PET-inspired Android interface.
- [Android APK workflow](.github/workflows/android-launcher.yml) — reproducible debug APK artifact build when GitHub Actions is available.
- The Android source is **not yet device-build-verified**. There is no prebuilt APK or bundled model in this repository. The launcher is a standalone local inference prototype, not yet the full permissioned NET.Navi agent.

## Project documents

- [Phase Development](docs/PHASE_DEVELOPMENT.md) — three phases: Pokémon AI Laboratory (Nora.EXE), Local Intelligence Engine, and True NET.Navi; with milestone acceptance criteria.
- [NET.Navi Research and Reference](docs/NETNAVI_REFERENCE.md) — franchise concepts, source references and real-world capability translations.
- [Architecture and Engineering Roadmap](docs/ARCHITECTURE_AND_ROADMAP.md) — component boundaries, software interfaces, security controls, benchmark goals and implementation order.

## Local Qwen evaluation

- [Automated Qwen benchmark](tools/benchmark/README.md) — 100 narrow evaluation cases, thinking-on/off comparison, incremental results, resume support, and one-command local execution with `run-benchmark.cmd`.
- [Ollama smoke test](tools/benchmark/smoke_test.py) — single-case local Qwen correctness and speed check.
- [Regression tests](tests/test_smoke_test.py) — deterministic offline checks for the scoring logic. GitHub Actions does not train or run Qwen.

**Next benchmark milestone:** Run the frozen baseline locally, review failures, and develop a **separate** training dataset without leaking evaluation questions into training. The Nora.EXE Pokémon laboratory remains independent of NET.Navi's language model.
