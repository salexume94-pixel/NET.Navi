# NET.Navi
Welcome to MMBN

## Project direction

NET.Navi is an offline-first, operator-controlled AI companion inspired by *Mega Man Battle Network*. The goal is a recognizable personal Navi with local intelligence, persistent user-managed memory, an original PET-style interface, authorized skill chips and measured, controlled learning. This repository is in the **planning phase**, not a complete assistant.

## Project documents

- [Phase Development](docs/PHASE_DEVELOPMENT.md) — three phases: Pokémon AI Laboratory (Nora.EXE), Local Intelligence Engine, and True NET.Navi; with milestone acceptance criteria.
- [NET.Navi Research and Reference](docs/NETNAVI_REFERENCE.md) — franchise concepts, source references and real-world capability translations.
- [Architecture and Engineering Roadmap](docs/ARCHITECTURE_AND_ROADMAP.md) — component boundaries, software interfaces, security controls, benchmark goals and implementation order.

## Local Qwen evaluation

- [Ollama benchmark smoke test](tools/benchmark/README.md) — local Qwen3-0.6B correctness and speed check, using only Python's standard library.
- [Regression tests](tests/test_smoke_test.py) — deterministic offline checks for the scoring logic. GitHub Actions does not train or run Qwen.

**Next milestone:** Expand the measured Qwen baseline with held-out evaluation cases while keeping Nora.EXE's Pokémon learning laboratory independent of the NET.Navi language model.
