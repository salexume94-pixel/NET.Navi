# NET.Navi — Architecture and Engineering Roadmap

**Status:** Proposed architecture / design document. **No implementation is claimed.**  
**Project:** [NET.Navi](https://github.com/salexume94-pixel/NET.Navi)  
**Date:** 2026-10-25  
**Branch:** main  
**Companion documents:** [Canon and product reference](NETNAVI_REFERENCE.md) · [Phase Development](PHASE_DEVELOPMENT.md)

## 1. North star

Deliver an **offline-first personal AI companion** inspired by the Operator, Navi, PET, Navi Customizer and Jack-In interaction model in Mega Man Battle Network. It should be useful, understandable, personable, fast on modest hardware, and able to execute authorized tasks with observable results. Characterful behavior is a presentation feature, not an excuse for overclaiming intelligence or ignoring permissions.

**Primary acceptance scenario:** The owner launches the app in airplane mode, gets a useful answer within a measured response budget, teaches the Navi a fact or preference, restarts the app, retrieves and edits that memory, approves an innocuous local skill action, watches it run, and sees a verified completion receipt. It must not be possible to persuade the language model to override the supervisor.

The [Phase Development](PHASE_DEVELOPMENT.md) document defines progression and exit gates. The present file defines **architecture**, interfaces, implementation sequence and reliability requirements.

## 2. Explicit engineering assumptions

- **Primary target:** Android Samsung device with around 6 GB RAM previously specified. Exact processor, usable RAM, Android version and background activity policies require measurement. Use **Android/Kotlin/Jetpack Compose** for UI as the provisional approach; validate SDK compatibility.
- **Development / secondary target:** Older Windows laptop with Intel Core i3-8130U, 32 GB RAM, Intel UHD 620. Design no mandatory GPU dependency.
- **Inference:** Quantized local Qwen candidates (Qwen3-0.6B and Qwen3.5-0.8B), selected by measured response quality, tokens/s, thermal impact, native RAM and task results. Do not assume both work in the same backend without testing. Candidate engine: pinned llama.cpp build/Android integration.
- **Data:** SQLite with FTS5 where supported; optional compact vector retrieval only when quality tests justify its cost. Device-private storage, protected secrets, appropriate encryption and visible backup/export controls.
- **Graphics:** Small original 2D Navi sprite/avatar with efficient state-based animation; no heavyweight 3D requirement.
- **Network:** Optional only, authenticated and clearly displayed; local model remains the same chosen local model unless user explicitly changes or authorizes a different backend.
- **Security:** A separate policy module always decides action authorization independently of LLM output or RL policy.

Do not claim these decisions are permanently finalized until there are target-device benchmark and engineering records.

## 3. Component architecture

~~~text
Operator
  |
[PET Client: chat, avatar, voice, memory, permissions, Stop]
  |
[Conversation / Session Gateway]
  |------> [LLM Runtime] -> local generation and tool proposals
  |------> [Memory Retrieval] -> typed, provenance-aware context
  |------> [Task Planner] -> bounded state machine
                      |
               Action Proposal
                      |
           [SECURITY SUPERVISOR]
                  |          |
              Deny/Ask   Scoped permit
                             |
                       [Tool Executor]
                             |
                       [Verifier]
                             |
                [Task Receipt and Journal]
                             |
                       [Memory Manager]
                             |
               [Training / Eval Lab]
             (offline isolated policies,
             never a security authority)
~~~

### Critical trust boundaries
1. **LLM output is untrusted.** The assistant may suggest operations, but it cannot confer rights or directly edit platform permissions.
2. **Tool outputs are untrusted.** Files, pages, mail and tool responses may contain adversarial instructions; they remain data rather than commands to the supervisor.
3. **Skill packages are untrusted until checked.** Installation needs reviewed provenance, dependency checks, sandbox tests and user confirmation.
4. **Learning artifacts are untrusted.** An RL policy can rank allowed actions within a granted session; it cannot modify the set of allowed actions.
5. **The UI cannot assert success based solely on generated text.** Success requires a verifier receipt.

## 4. Required runtime interfaces

Use typed, versioned schemas. Canonical encoding can be Kotlin data classes with JSON/protobuf only where serialization is needed; avoid committing to a format before integration tests.

| Interface | Required fields | Invariant |
|---|---|---|
| \`ChatRequest\` | session ID, message, model profile, context/token budget, trace ID | Cannot assign tool permissions |
| \`ChatResult\` | text, completion status, model ID, tokens, elapsed times, uncertainty/provenance | No false completion status |
| \`ActionProposal\` | skill ID/version, validated arguments, app/domain/target, declared side effects, desired postconditions, trace ID | Requires independent approval |
| \`AuthorizationDecision\` | allow/ask/deny, principal, scope, expiry, policy version, audit ID | Never authored by model |
| \`ToolReceipt\` | action ID, start/end, executor, sanitized result, side effects, errors, verifier ID | Reflects observed reality |
| \`MemoryRecord\` | record ID/type, content, source, verification status, timestamps, privacy class, user controls | Traceable and deletable |
| \`ExperienceRecord\` | environment version, objective, observation, action mask, action, reward components, verified terminal result | Training/evaluation separation |
| \`PolicyArtifact\` | version, hash, training data origin, holdout metrics, rollback version | Has no privilege fields |

### Planner cycle
1. Identify objective and explicit permissions.
2. Check whether deterministic skill/rule solves task; call Qwen only when useful.
3. Propose an action with expected result.
4. Ask supervisor to authorize typed arguments and target.
5. Execute in isolation; stop if cancelled or expired.
6. Observe state through designated source.
7. Independently verify expected change.
8. Record structured receipt and optionally an experience example.
9. If insufficient progress, retry under policy limit or return a meaningful failure.

Set strict budgets: maximum action count, retries, tokens, time, data footprint and tool cost for each workflow. These are configured by capability and should be visible to the owner.

## 5. Subsystem design

### 5.1 Local language engine
- Inference adapter with \`load\`, \`generate\`, \`stream\`, \`cancel\`, \`unload\` and \`metrics\`.
- Record model name, quantization source/hash, runtime commit and prompt template.
- Implement fast/non-thinking and deliberate/thinking profiles where actually supported.
- Hard-stop generation on token/time budgets; show partial answers as partial.
- Log prompt evaluation time, first-token latency, decode speed, peak memory and device temperature where available.
- Avoid multiple heavyweight models loaded simultaneously by default.
- User-visible model selection; do not silently route to a remote model.

### 5.2 Memory and local knowledge
Stores: operator profile, episodic summaries, verified facts, procedural workflows, model-independent policy metadata, redacted audit log. Keys and secrets belong in a dedicated credential store, **never** conversation memory.

- Data provenance: operator-entered / tool-observed / derived / externally sourced.
- Confidence and staleness are represented, not implied.
- Controls: view, edit, delete, clear, export and selective import.
- Prevent retrieval from scopes no longer authorized.
- Corruption and migration recovery tests; restore from backup must preserve intended permissions.

### 5.3 Skills / Navi Customizer
Each Skill Chip has \`id\`, \`version\`, \`description\`, \`inputs_schema\`, \`outputs_schema\`, \`permissions\`, \`side_effects\`, \`timeout\`, \`rollback_supported\`, \`offline_compatible\`, \`memory_cost\`, \`dependencies\`, \`verified_build\`.

Start with four low-risk skills:
1. **Calculate:** deterministic arithmetic / conversion, no model math guessing.
2. **Notes:** create/read/update app-owned notes.
3. **Search local knowledge:** retrieve indexed documentation with provenance.
4. **Draft planner:** produce a non-sending plan or reminder draft requiring operator confirmation before persistence.

Then consider file/document picker, external APIs and specialized developer/game skills. Avoid accessibility control until OS policy and end-user consent workflows are designed.

### 5.4 Security Supervisor
- Centralized allow/ask/deny with human-review categories for destructive actions, account changes, data transfers, software installation, remote sending and broad filesystem access.
- Explicit per-skill grants with expiry, audience/target, data class and user identity.
- A conversational instruction is **never** a grant.
- Security decisions and denials are audited with redaction.
- All tasks offer "Stop" / "Jack Out"; cancellation closes sessions and revokes ephemeral grants.
- No autonomous installation of downloaded code or permission elevation.
- Sandbox all self-improvement experiments. Evaluation cannot use production credentials.

Security acceptance tests: prompt injection, tool output injection, fabricated approvals, expired grants, cancellation races, private memory leakage, malicious skill manifests and rollback.

### 5.5 Outcome verification
For every nontrivial tool:
- define postcondition at implementation time;
- verify against authoritative execution result or observed state;
- report \`verified\`, \`failed\`, \`unknown\`, or \`cancelled\`, with evidence;
- never equate fluent model explanation with successful execution;
- prevent retry storms when the underlying service/device remains unavailable.

### 5.6 Learning and reinforcement learning
**Use different update mechanisms for different problems.**

| Mechanism | Target | When appropriate |
|---|---|---|
| User-editable memory | Preferences and facts | Immediate, no gradient training |
| Procedural memory | Repeatable tool sequences | After externally verified success |
| Contextual bandit/tabular RL | Small discrete actions/states | Many repeatable outcomes |
| Tiny DQN/policy neural net | Structured specialist task state | Dataset/holdout comparison justifies |
| LoRA / model fine-tune | Language-generation behavior | Later controlled research with curated data and adequate compute |

For the Pokémon laboratory, include reward components for story progress, legal input, correct menu navigation and actual battle/goal completion. Penalize getting stuck, invalid actions and unproductive button spam. Preserve game-specific reward data in Nora.EXE; reuse the event-loop abstractions in NET.Navi.

**Training promotion:** a candidate policy is tested offline on unseen scenarios, compared to frozen baseline for reliability *and* safety, versioned, signed/hashed, allowed only in its former scope and reversible. No promotion from RL success to device privileges.

### 5.7 Speech and animated personality
- Text-only MVP before voice.
- Microphone permission and clear capture status. Push-to-talk baseline.
- On-device STT and bundled/licensed TTS evaluated separately for RAM, cold start, battery and voice quality.
- Wake phrase/locked-screen voice require OS-specific investigation and must not be promised on all devices.
- Original avatar states: idle, listening, thinking, speaking, acting, success, error.
- Personality options affect vocabulary and visuals, **not** factual honesty or security.

## 6. Suggested repository structure (proposal)

~~~text
NET.Navi/
  README.md
  docs/
    NETNAVI_REFERENCE.md
    PHASE_DEVELOPMENT.md
    ARCHITECTURE_AND_ROADMAP.md
    ADR/                        # design decisions, when created
    TESTING.md                   # future test plan/results
    BENCHMARKS.md                # measured hardware/runtime results
  apps/
    android/                     # Android PET frontend (future)
    desktop/                     # optional thin client (future)
  core/
    inference/
    dialogue/
    memory/
    planner/
    skills/
    security/
    verification/
    learning/
    telemetry/
  tests/
    unit/
    integration/
    adversarial/
    performance/
    simulated_env/
  assets/
    original_avatar/
  tools/
    benchmark/
    policy_evaluation/
~~~

Folders beyond \`docs\` are **proposed future structure**. Do not generate empty boilerplate directories simply to make the project look advanced.

## 7. Development sequence

### A. Prerequisites and baseline
- Read [NETNAVI_REFERENCE.md](NETNAVI_REFERENCE.md) and [PHASE_DEVELOPMENT.md](PHASE_DEVELOPMENT.md).
- Audit current Nora.EXE for transferable functionality; record what really works and what does not.
- Inventory actual device model/SoC/API, RAM and battery constraints; create reproducible benchmark scripts.
- Choose a single narrow end-to-end MVP story and a frozen acceptance suite.

### B. Implement minimum reliable engine
- Set up Android shell, native inference binding and one pinned model.
- Build text chat, streaming, cancel, recovery and truthful error states.
- Add SQLite memory, migration, data controls and source attribution.
- Add ActionProposal → Supervisor → Tool → Verifier pipeline for one local safe action.
- Add basic offline CI tests and benchmarking.

### C. Add tested learning
- Implement portable ExperienceRecord schema and deterministic replay harness.
- Import lessons from Pokémon Lab while retaining domain isolation.
- Measure procedural memory/tabular/bandit learning first, then specialist neural policy if justified.
- Version and compare policy updates on holdout tasks; fail closed on regressions.

### D. Build PET interaction and expand capabilities
- Implement 2D avatar + PET dashboard and readable status.
- Add skill library/Customizer, explicit authorization UI, Stop/Jack Out.
- Add push-to-talk STT/TTS and optional more integrated voice.
- Expand limited tool adapters one at a time, never by broad unscoped access.

### E. Release gate
- Run Android offline tests, restart/backup checks, bounded autonomy scenarios, prompt-injection tests, permission denial/revocation checks, crash tests and thermal benchmarks.
- Publish what passed and failed with test logs; ship only approved capabilities.
- Maintain changelog, benchmark diff and rollback procedures.

## 8. Benchmark plan: what counts as 'fast and accurate'

Proposed user goal: **most ordinary responses under 20 seconds**, measured on the real device. This is *not a current measurement* or a promise that all prompts will finish this quickly.

Define a benchmark corpus with:
- short factual prompts, including known knowledge and controlled unknowns;
- multi-step reasoning and explanation prompts;
- local-memory recall/correction;
- small coding and debugging tasks;
- tool-use tasks with structured postconditions;
- adversarial prompts to induce fabricated evidence or unsafe action;
- 20-minute sustained test for temperature and battery behavior.

For each candidate model, record:
- runtime version, model hash/quantization, system state;
- cold and warm load, first-token latency, decode tokens/sec;
- p50 and p95 full-answer elapsed time;
- correct/incorrect/uncertain responses scored using a documented rubric;
- native RAM peak, context setting, CPU/GPU use, thermal behavior;
- timeouts, cancelled tasks, no-progress loops, recovery and verified task success.

**Provisional pass threshold:** >=90% of ordinary-prompt suite meets the under-20-second target while preserving answer quality against baseline. The benchmark definition, number of prompts and device conditions must be locked before a final pass/fail verdict.

## 9. Reliability and failure policy

**Common faults and explicit responses:**
- **Hallucinated action result:** mark unverified, suppress success claim, show receipt failure.
- **Reasoning loop:** enforce generation cap and route to brief summary of blockage or safer fallback.
- **No visual progress:** release controls, inspect state once, try alternate approved strategy, stop after retry cap.
- **Memory conflict:** retain sources, prefer explicit newer operator correction subject to verification, show uncertainty.
- **Thermal slowdown:** degrade animations/concurrency/context; notify user of reduced performance.
- **Skill crash:** terminate isolated process/task if supported, journal partial effects, preserve app stability.
- **Permission revoked mid-task:** stop subsequent calls and close token/session.
- **Offline unavailable capability:** show offline limitation, never secretly send data or promise network results.

## 10. Roadmap / governance

- The **single source of truth for phase order and milestone gates** is [Phase Development](PHASE_DEVELOPMENT.md).
- This architecture file is the canonical component/interface reference; changes to security boundary or model policy require a documented ADR and regression tests.
- Research claims belong in [NETNAVI_REFERENCE.md](NETNAVI_REFERENCE.md) and must carry sources and fictional/product labels.
- Each delivered feature requires a linked specification, acceptance tests, measured result and a rollback/change note.
- Keep independent app-specific behavior in Nora.EXE unless explicitly designed as shared core.
- Periodically reassess feasibility against real hardware data; prioritize reliability and truthful answers over novelty.

## 11. Source references

**Franchise canon**
- Capcom: [Style Change (MMBN3)](https://game.capcom.com/manual/REXEAC/vol1/en/steam/page/3/3)
- Capcom: [Navi Customizer (MMBN4)](https://game.capcom.com/manual/REXEAC/vol2/en/steam/page/1/4)
- Capcom: [Double Soul](https://game.capcom.com/manual/REXEAC/vol2/en/steam/page/1/3)

**Engineering**
- [Qwen3.5-0.8B official model card](https://huggingface.co/Qwen/Qwen3.5-0.8B)
- [llama.cpp Android build instructions](https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md)
- [Stable Baselines3 RL algorithms](https://stable-baselines3.readthedocs.io/en/master/guide/algos.html)
- [Android MediaProjection](https://developer.android.com/media/grow/media-projection)
- [Android foreground service types](https://developer.android.com/develop/background-work/services/fgs/service-types)
- [OWASP MASVS](https://mas.owasp.org/MASVS/)
