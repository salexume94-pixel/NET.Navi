# Phase Development

**Project:** NET.Navi  
**Repository:** [salexume94-pixel/NET.Navi](https://github.com/salexume94-pixel/NET.Navi)  
**Branch:** \`main\`  
**Status:** Planning (not yet implemented)  
**Last reviewed:** 2026-10-25

> **Development order:** First prove autonomous learning in a safe game environment. Next build a fast, accurate, offline-capable local intelligence engine. Finally combine those tested systems into a useful real-world NET.Navi. Do not confuse a research prototype with a completed feature.

## Three-phase overview

### Phase 1: Pokémon AI Laboratory
**Use Nora.EXE to experiment with reinforcement learning, visual perception, planning, memory, and autonomous decision-making.**

**Codebase:** Existing [Nora.EXE](https://github.com/salexume94-pixel/Nora.EXE) repository. It remains a separate experiment rather than being copied wholesale into the NET.Navi app.

**Purpose:** Develop and verify a reliable observe → decide → act → verify → learn loop while working with a bounded, reversible environment. Pokémon is an effective testbed because navigation, menu operation, battling, resource management, and story progression offer measurable success/failure outcomes.

**Workstreams:**
1. **Perception:** identify screen mode, text, symbols, menus, world location, battle HUD and current selection. Combine OCR, pixel-pattern matching, spatial keyboard maps, game-state evidence and confidence thresholds.
2. **Action control:** send legal, time-bounded game inputs; release buttons; verify inputs; record frame/action/result pairs; detect repeated unchanged screens.
3. **Planning:** hierarchical goals (start game → complete naming → receive starter → follow story → heal → travel → battle); break them into interruptible subtasks.
4. **Reward design:** reward real story milestones, successful legal navigation, completed objectives and battles; penalize invalid inputs, loops, repeated unproductive observations and unjustified retries. Avoid reward hacking such as farming actions with no progression.
5. **Memory:** retain verified maps, successful menu routines, battle strategy and observed story flags, including confidence and provenance.
6. **RL methods:** start with deterministic routines, episodic memory and tabular/bandit policies where feasible; introduce a compact neural policy only when the state space warrants it. Keep Qwen weights unchanged for this first experiment.
7. **Evaluation:** run deterministic replay plus unseen scenarios, track task completion, path efficiency, crash frequency, no-progress events and model calls.

**Phase 1 deliverables:**
- Versioned observation/action/episode schemas.
- Reusable state recognition and menu-navigation components.
- Bounded planner with failure recovery.
- Story-progression-aware reward definition.
- Training/evaluation dataset and replay harness.
- Exportable **learning architecture and interface contracts**, not Pokémon-specific behavior baked into the general assistant.
- A written evaluation report with evidence, failures and known limitations.

**Exit criteria (proposed, must be measured):**
- Completes naming and onboarding from a fresh save without operator input across at least 10 test attempts.
- Recovers from known menu and navigation stalls without an endless loop.
- Demonstrates improvement over a frozen rule-based baseline on held-out tasks and seeds.
- Records objective, action, verified state change and reward component for every training episode.
- Produces a clean list of portable abstractions for Phase 2.

**Do not advance solely because it completed one lucky run.**

---

### Phase 2: Local Intelligence Engine
**Optimize Qwen for fast, accurate responses. Develop persistent memory, lightweight neural networks, adaptive reasoning, and verified learning.**

**Codebase:** Reusable engine modules developed in NET.Navi with lessons and contracts transferred from Phase 1, not direct dependence on the Nora.EXE app.

**Purpose:** Build a capable and honest local AI core for older PCs and Android phones without requiring constant cloud inference.

**Workstreams:**
1. **Model comparison:** benchmark Qwen3-0.6B and Qwen3.5-0.8B on actual target hardware. Verify runtime compatibility and compare CPU/GPU backends, quantization, cold/warm load, memory, thermals, accuracy and responsiveness.
2. **Fast response path:** streaming, bounded output, prompt caching if supported, sensible context limits, retrieval, short deterministic answers when tools suffice, and fewer unnecessary model calls.
3. **Adaptive reasoning:** quick/normal/deliberate routes by task difficulty, confidence and failure signals; enforce timeouts, maximum attempts, cancellation and no-progress detection.
4. **Persistent local memory:** structured user preferences, explicit facts, verified external knowledge, episodic task history and successful procedures. Provide inspection, corrections, selective deletion, backup and export.
5. **Specialist learning:** import Phase 1's verified observation→action→outcome framework; use contextual decision policies and small specialist RL neural networks for narrow tasks. Distinguish memory updates from neural-weight changes.
6. **Accuracy and verification:** clearly mark unsupported claims; use deterministic validators and source provenance when available. Never treat the model stating “success” as evidence that a task was completed.
7. **Local-only defaults:** one chosen offline model, no silent online substitute; optional network services must be explicitly configured later.
8. **Engine security:** independent tool permissions, a sandboxed learning environment, versioned policy artifacts, regression testing and rollback.

**Phase 2 deliverables:**
- Local inference library and model configuration profiles.
- Repeatable mobile and laptop benchmark suite.
- SQLite-based memory/knowledge storage with migration tests.
- A typed planner/tool/observation/verification API.
- Lightweight RL policy interface and isolated training harness.
- Independent Device Security Supervisor.
- Stress, restart, offline and error-recovery reports.

**Exit criteria (proposed, not a performance claim):**
- Core question-answering and memory retrieval work with networking disabled.
- Ordinary offline interactions aim for **under 20 seconds** end-to-end on the selected phone with quality and prompt-length constraints stated in the benchmark report. Longer research tasks are measured separately.
- No repeated infinite thinking/action loops in the acceptance suite; every task has a known termination condition.
- A specialist learned policy improves held-out performance over a frozen baseline without unsafe side effects.
- Memory survives restart and is inspectable, correctable and deletable.
- Security tests demonstrate that dialogue or RL output cannot grant device permissions.

**No broad self-modification:** do not constantly fine-tune Qwen on-device or permit automatically generated code to change production components. Fine-tuning/LoRA is optional separate research requiring validated data and stronger hardware.

---

### Phase 3: True NET.Navi
**Integrate the intelligence engine into a personal AI assistant with conversation, voice, personality, autonomous task execution, device integration, and controlled self-improvement.**

**Codebase:** NET.Navi application, drawing on stable Phase 2 APIs.

**Purpose:** Deliver a persistent, personalized and genuinely useful operator/Navi partnership inspired by Mega Man Battle Network, without pretending software has fictional capabilities.

**Workstreams:**
1. **PET interface:** original 2D avatar, dialogue screen, tasks, current state, memory inspector, status, permissions, Stop/Jack Out, and skill management. Keep the interface legible and energy-efficient.
2. **Navi identity:** configurable name, original art, personality presentation and voice. Personality may style responses but must never determine permissions.
3. **Voice:** push-to-talk first; optional on-device speech recognition and TTS; later research wake phrase, locked-screen behavior and Android background restrictions.
4. **Skill Chips:** modular, inspectable tools for notes, files, knowledge, code assistance, scheduling and other authorized functions. Include scopes, dependencies, errors and undo where possible.
5. **Navi Customizer:** enable/disable skills and model profiles with clear RAM, latency and privilege costs; invalid/conflicting combinations must be blocked.
6. **Jack In / Jack Out:** operator grants a **revocable session** to a chosen local app/service, the Navi acts with a bounded plan, verifies results and reports the trace.
7. **Real autonomy:** autonomous planning/execution for approved low-risk tasks; approval gates for elevated-risk actions, sensitive data access and irreversible effects.
8. **Navi growth:** user-visible, *verified* skill improvement based on evaluations, corrections and safe policy updates. Style profiles may adapt with user override.
9. **Resilience:** graceful offline mode, crash recovery, backup/export, skill rollback, privacy protections and transparent failures.
10. **Optional future work:** desktop PET, multi-Navi collaboration, remote compute using the same explicitly selected model where feasible, optional AR/robotics. These are not MVP requirements.

**Phase 3 deliverables:**
- Installable Android NET.Navi application with offline chat.
- Original PET-like UI/animated Navi character.
- Configurable voice with clear microphone controls.
- User-editable memory and skill library.
- Independently governed tool execution with audit receipts.
- Demonstrated autonomous workflows with live Stop button.
- Documented security and performance audit, release process and rollback path.

**Exit criteria (minimum viable release):**
- A user can install the app, select a local model, converse offline, and retain/revise memory across restarts.
- The user can authorize a limited workflow, observe each important action and stop execution promptly.
- The Navi reports actual outcomes rather than fabricating success.
- Voice/avatar remain optional; the core works without them.
- The app does not silently transmit private data or obtain new privileges via learned policies.
- Representative workflows pass regression tests on the target Samsung phone and older PC baseline (where the desktop build is applicable).

---

## Shared milestones and dependencies

| Milestone | Depends on | Evidence required | Phase |
|---|---|---|---|
| M1: Baseline Pokémon agent | Existing Nora.EXE emulator integration | Fresh-save run and action logs | 1 |
| M2: Reliable perception | M1 | Labelled screen-state accuracy + unknown recovery | 1 |
| M3: Planner + story-aware RL | M2 | Held-out episodes, baseline comparison | 1 |
| M4: Portable agent contracts | M3 | Documented interfaces + replay test | 1 → 2 |
| M5: Benchmark local LLMs | Target hardware | Speed/accuracy/memory reports | 2 |
| M6: Memory + tool supervisor | M5 | Offline, restart and denial tests | 2 |
| M7: Learning policy + verification | M4, M6 | Held-out general task improvements | 2 |
| M8: PET vertical slice | M6 | Installable chat + memory + one tool | 3 |
| M9: Voice, avatar, skill customizer | M8 | UX and battery/permission tests | 3 |
| M10: Controlled autonomous release | M7, M9 | Full end-to-end tests + security review | 3 |

## Metrics collected from day one

- **Intelligence:** verified factual accuracy, task completion, hallucination rate, calibration and invalid-action rate.
- **Performance:** cold start, time to first token, full-response p50/p95, tokens/sec, memory peak, CPU/GPU load, thermal throttling and battery impact.
- **Autonomy:** loop rate, retries per task, verified completion without operator intervention, average time to recovery and cancellation response.
- **Learning:** holdout success rate before/after each policy version, reward hacking incidents, rollback events and improvement persistence across restarts.
- **Trust:** permission denial tests, unauthorized tool call count (must be zero), receipt coverage, data export/delete test results.

## Engineering rules for all phases

1. Preserve strict separation of **LLM reasoning**, **memory**, **RL policy**, **tool executor** and **security supervisor**.
2. Observe → act → independently verify before attributing success or granting reward.
3. No self-granted permissions or model-controlled supervisor edits; trained policies are untrusted inputs.
4. Keep Nora.EXE's game-specific content outside general NET.Navi modules. Port interfaces and principles, not the Pokémon rules.
5. Optimize for affordable, low-end devices; no heavyweight 3D or always-running inference by default.
6. Build incrementally; every milestone needs tests, measured evidence, and a reversible commit.
7. Record decisions, blockers, benchmarks and specification changes in repository documentation.
8. Prioritize **correctness and consistency** alongside speed.
9. Ensure all user data is inspectable, portable and deletable.
10. No phase is marked complete without acceptance evidence.

## First implementation order

- [ ] Audit Nora.EXE's current perception, planning, story progression and reinforcement-learning state without assuming any particular feature is already correct.
- [ ] Publish Phase 1 measurement suite and a reproducible fresh-save benchmark.
- [ ] Extract reusable observation/action/outcome contracts.
- [ ] Benchmark Qwen candidates on actual devices and choose a conservative baseline.
- [ ] Implement offline inference + memory + supervised tool execution as the NET.Navi vertical slice.
- [ ] Build PET interface only after an end-to-end core workflow functions.
- [ ] Expand to voice, skill chips, bounded autonomy, and verified self-improvement.

## Research links

- [NET.Navi canon-to-software research](NETNAVI_REFERENCE.md).
- [Capcom official Style Change](https://game.capcom.com/manual/REXEAC/vol1/en/steam/page/3/3): behavior-driven adaptation inspiration.
- [Capcom official Navi Customizer](https://game.capcom.com/manual/REXEAC/vol2/en/steam/page/1/4): modular program inspiration.
- [Capcom official Double Soul](https://game.capcom.com/manual/REXEAC/vol2/en/steam/page/1/3): temporary specialized capability inspiration.
- [Qwen3.5-0.8B model card](https://huggingface.co/Qwen/Qwen3.5-0.8B): actual model capabilities and limitations.
- [llama.cpp build and Android notes](https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md): inference portability and CPU target support.

**Current status:** These phases are approved *planning structure*, not statements of completed work. The exit gates are proposed until benchmarking is performed.
