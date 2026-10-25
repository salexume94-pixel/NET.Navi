# NET.Navi — Canon Research and Real-World Design Reference

**Project:** NET.Navi  
**Repository:** https://github.com/salexume94-pixel/NET.Navi  
**Research compiled:** 2026-10-25  
**Status:** Reference and requirements discovery; NOT an implementation report  
**Primary source of inspiration:** Capcom's Mega Man Battle Network / Rockman EXE games, with selected anime ideas clearly marked as alternate-continuity inspiration.

> **Purpose:** Preserve the NET.Navi concept accurately, identify which traits matter to the operator experience, and translate those traits into capabilities that can be engineered on consumer Android and Windows hardware. Canonical facts, adaptations, proposed features, and technical limitations must remain distinct.

## 0. Reading guide and source-quality rules

- **[CANON / GAMES]** refers to game-universe concepts documented by Capcom or game manuals.
- **[ANIME]** refers to concepts from the animated adaptations; details can differ from the games.
- **[SECONDARY]** refers to fan wikis or reference databases, used to supplement primary sources rather than establish hard requirements.
- **[PRODUCT]** refers to design choices for our software, *not* claims about the fictional series.
- **[FUTURE / RESEARCH]** refers to work not yet demonstrated, or features dependent on platform permissions, licensing, or hardware.
- Use Capcom manuals before wiki descriptions whenever they differ. Do not treat powers from the anime as game-canon capabilities.
- Do not claim the eventual AI is conscious, sentient, alive, or a digital human. Fictional Navis are characterized that way; our product is an AI software system.
- No gameplay ROMs, Capcom logos, character sprites, ripped voices, or other copyrighted media are included by default. Build original designs inspired by interaction patterns, not replicas or misleading official branding.

## 1. What is a NET.Navi?

**[CANON / GAMES]** A **Network Navigator**, usually called a **NetNavi** or **Navi**, is an AI-like personalized computer program serving a human **Operator** within a networked society. Navis are represented as recognizable characters with personalities and roles. A portable device called a **PET** (Personal Terminal) is the operator's gateway to communicating with the Navi. The Navi can act in the network, while the person supplies direction, companionship, and often battle programs. Capcom describes PETs and personality-simulation programs as part of the franchise's everyday network society. Sources: [Capcom product description](https://store.captown.capcom.com/en/products/645734-jp), [Capcom Legacy Collection](https://www.capcom-games.com/megaman/exe/en-uk/), [NetNavi reference](https://megaman.fandom.com/wiki/NetNavi).

In game terms, **Operator + Navi + PET + network access** form a complete working system, not four independent gadgets. The series emphasizes partnership; the operator does not merely submit prompts to an anonymous tool.

**[PRODUCT] Definition for this repository:** A NET.Navi is an **offline-first, operator-controlled digital companion** with (1) continuous identity and configurable personality, (2) conversational interaction, (3) durable local memory, (4) a defined inventory of permissioned skills, (5) the ability to plan and execute limited, verifiable tasks, (6) visible embodiment in a PET-like interface, and (7) the capacity to improve measurable skills from feedback without being allowed to grant itself new privileges.

### 1.1 Essential relationship

- **Operator:** the human owner; sets goals, grants or revokes capabilities, approves impactful actions, corrects mistakes, inspects memory and logs.
- **Navi:** an AI interface and delegated worker; asks for clarification when needed, explains uncertain results, observes outcomes, learns verified preferences and strategies.
- **PET equivalent:** mobile/desktop client, avatar, messages, tools, status, permission prompts, activity feed, voice interface.
- **Network equivalent:** local apps, personal files, and authorized remote services, each behind a connector and security boundary.
- **Jack-in equivalent:** an explicit, limited session to an allowed app or service; not unauthorized network access.

The minimum recognizable experience is: **the same Navi talks to you tomorrow, remembers the relevant parts of today, has its own recognizable presentation, can do useful work through approved skills, and behaves transparently when a request fails.**

## 2. PETs: the operator's portable interface

**[CANON / GAMES]** PETs function as an interface to the Navi and everyday network life. Game interactions include communicating between Lan and MegaMan and using jack-in/jack-out controls to shift between ordinary and cyber-world contexts. The Navi Customizer is reached from the PET's MegaMan screen in later games. Sources: [MMBN5 field controls](https://game.capcom.com/manual/REXEAC/vol2/en/steam/page/2/1), [MMBN4 Navi Customizer](https://game.capcom.com/manual/REXEAC/vol2/en/steam/page/1/4).

**[PRODUCT] PET screen concept:**

| Fictional element | Implementation target | Priority |
|---|---|---|
| PET handset | Android app first, Windows desktop shell second | MVP |
| Navi character on screen | Original animated 2D avatar with speaking/listening/thinking/idle/action states | MVP |
| Navi dialogue | Local text chat with streaming answers and history | MVP |
| Operator commands | Text and optional push-to-talk; wake phrase later | MVP / later |
| Status window | model loaded, offline/online, battery/thermal use, microphone state, current skill, task state | MVP |
| Jack-in / Jack-out | explicit authorization-bound task session, revoke/cancel button | MVP |
| Program library | installed and enabled skills / tools with metadata | MVP |
| Navi Customizer | modular capabilities with capability checks and dependency validation | Phase 2 |
| Battle Chip metaphor | signed/validated limited-operation "skill cards," not arbitrary executable internet downloads | Phase 2 |
| Mail/contacts/calendar | connectors requiring user authorization | Phase 4 |
| Net world visualization | optional stylized graph of trusted applications, tasks and sessions | Phase 5 |
| Navi emblem and themed HUD | original art, theme editor, colors, effects | Phase 3 |

**UX rule:** A PET skin should *reveal* capabilities, never hide what the AI did, which permissions it used, or whether an output was verified.

## 3. Navi personalities and specialization

**[CANON / GAMES / SECONDARY]** Different Navis have distinct roles, personalities, and combat styles; they are not interchangeable anonymous instances. Examples across the franchise include MegaMan.EXE (Lan Hikari), ProtoMan.EXE (Chaud), Roll.EXE (Mayl), GutsMan.EXE (Dex), and Glyde/Glide.EXE (Yai). Names and pairings are supported by [MMHP MMBN1 character reference](https://www.mmhp.net/GameHints/MMBN1-Data.html) and [NetNavi index](https://megaman.fandom.com/wiki/List_of_NetNavis).

Examples are **design archetypes**, not blueprints for copying character images or dialogue:

| Canon example | High-level impression | Inspired Navi design feature |
|---|---|---|
| MegaMan.EXE + Lan | Cooperative all-rounder, close operator bond | Context-sensitive general assistant and clear two-way communication |
| ProtoMan.EXE + Chaud | Disciplined task focus | Efficient task-focused profile and terse reporting |
| Roll.EXE + Mayl | Support-oriented | Friendly organizational and accessibility skill set |
| GutsMan.EXE + Dex | Forceful, direct approach | Bold game-coach personality profile |
| Glyde.EXE + Yai | Formal helper | Butler-like planning and scheduling profile |
| Bass.EXE | Independent Navi archetype (secondary lore) | Research inspiration only; no permissionless execution or unbounded self-direction |

**[PRODUCT] Personality is separate from reasoning and permission.** Define personality as configurable style, voice and animation settings. No speech style, affection, persuasion, threat, or fictional roleplay can alter what permissions the security supervisor grants. The model should not imply personhood or pretend that a response was directly experienced outside its inputs.

## 4. Operator partnership, bonds and the autonomy spectrum

**[CANON / GAMES]** The operator frequently issues instructions and supplies Battle Chips. Some Navis are more independent or operate without human partners. Secondary lore distinguishes normal operated Navis and solo Navis; some game spin-offs reduce direct operator involvement during battle. Sources: [Operator reference](https://megaman.fandom.com/wiki/Operator_%28Mega_Man_Battle_Network%29), [NetNavi reference](https://megaman.fandom.com/wiki/NetNavi).

**[PRODUCT]** Provide clear modes, not a vague switch labeled "autonomous":

1. **Conversation:** No tools; may advise, remember only with memory controls.
2. **Assisted task:** The Navi proposes a plan; operator approves each sensitive step.
3. **Bounded autonomy:** The operator grants a time-limited task scope with specified tools, budgets and stop conditions. Routine low-risk actions may execute without each-step confirmation.
4. **Sandbox practice:** The Navi independently explores a synthetic/test environment using a disposable state and no real-world privileges.
5. **Remote collaboration:** Optional, consent-based contact with another trusted Navi/service under separate identity, encryption and audit controls.

Every mode has an immediate **Stop** control. Autonomy is scoped by operation, not earned merely through successful training. There is no automatic promotion from practice mode to elevated real-device permissions.

## 5. Battle Chips: a modular skill system

**[CANON / GAMES]** Battle Chips are data/programs used by an operator and Navi for combat, especially virus busting. In the game world, chips provide discrete specialized actions; rules and available chips vary by title. Source: [Capcom official manual, Battle Network 4](https://game.capcom.com/manual/REXEAC/vol2/en/steam/top), [NetNavi reference](https://megaman.fandom.com/wiki/NetNavi).

**[PRODUCT]** Treat "Skill Chips" as discoverable, typed modules:

- Name, version, owner/publisher, description, required privileges, data accessed, offline availability, side effects, cost/latency estimate, undo capability, and test status.
- Inputs and outputs validated against explicit schemas; the assistant proposes the operation, a **separate Device Security Supervisor** determines authorization, and a typed executor performs the call.
- Possible chips: search local notes; summarize a PDF; set a timer; create a draft; search a file; extract structured data; launch an approved app; query a configured local code index; run a game agent in a test emulator; voice transcription; accessibility-compatible navigation.
- Installation from the Internet is *not* automatic: permission, provenance, content validation, sandbox review and approval first.
- A Skill Chip never bypasses Android OS permissions, app sandboxing, passwords, hardware security, or approval for destructive changes.

**Non-goal:** importing fictional battle programs literally, remote exploitation tools, or treating arbitrary natural-language commands as executable code.

## 6. Navi Customizer: composition, capacity and trade-offs

**[CANON / GAMES]** The **Navi Customizer** lets players install programs to strengthen MegaMan; placement and compatibility rules matter. Invalid setups can produce bugs. [Capcom MMBN4 Navi Customizer manual](https://game.capcom.com/manual/REXEAC/vol2/en/steam/page/1/4) and [MMBN6 manual](https://game.capcom.com/manual/REXEAC/vol2/en/steam/page/3/5) describe placement constraints and incompatible configurations.

**[PRODUCT]** This is an excellent metaphor for plugin architecture:

- Every skill has dependencies and hardware costs (RAM, CPU, network, wakeups, model context).
- The "Customizer" checks incompatible capabilities, permission conflicts, minimum API requirements and battery impact **before** enabling them.
- A profile may include: Conversation Core + Memory + Voice + File Reader + Programmer + Game Agent.
- Enabling everything should not imply running everything continuously. Lazy load models and tools; unload idle components.
- Provide one-click rollback to a known-good configuration and maintain a signed/configured manifest.
- Show a diagnosis if a capability cannot run on the current device; do not silently degrade or pretend to have executed it.

## 7. Style Change, Double Soul and other progression concepts

**[CANON / GAMES]** In MMBN2 and MMBN3, **Style Change** adapts MegaMan based on battle tendencies. In MMBN4–5, **Double Soul** temporarily changes properties through connection to other Navis. Later games introduce additional mechanics including Cross Change and Beast Out. Source: [MMBN3 Style Change](https://game.capcom.com/manual/REXEAC/vol1/en/steam/page/3/3), [MMBN4 Double Soul](https://game.capcom.com/manual/REXEAC/vol2/en/steam/page/1/3), [MMBN6 feature manual](https://game.capcom.com/manual/REXEAC/vol2/en/steam/top).

**[PRODUCT] Suggested adaptations:**

- **Style Change:** a transparent preference/skill profile driven by *verified* use patterns; e.g. "Developer", "Researcher", "Game Strategist". User must be able to inspect and override it.
- **Double Soul:** temporary permission-checked use of a specialist assistant/tool pack. It is *not* merging models into a sentient being.
- **Navi evolution:** meaningful improvements measured in lower error rate, improved reliability, fewer corrections, improved tool completion, and faster execution.
- **Operator sync:** learning how the owner prefers workflows while preserving permission boundaries and clear "I don't know" behavior.
- **Custom program layout:** modular skill packs with resource budget visualization rather than literal block-puzzle placement.

**Important distinction:** A theme or "level-up" animation may celebrate a verified benchmark improvement; it must not claim the model's reasoning ability increased when only an avatar stat changed.

## 8. Jack-in / cyber-world: real-world translation

**[CANON / GAMES]** Navis enter and navigate a represented networked world to interact with systems, fight viruses and receive data from the operator. Source: [MMBN5 control manual](https://game.capcom.com/manual/REXEAC/vol2/en/steam/page/2/1), [Capcom series description](https://store.captown.capcom.com/en/products/645734-jp).

**[PRODUCT]** There is no universal visual "Internet world" a Navi can enter. Instead, a **Resource Gateway** provides explicit adapters for:

- Local: app-owned databases; files selected through the system picker; approved documents; sandbox tasks and games.
- Device: intents, notifications, user-selected documents, accessibility-supported workflows when justified and permitted, screen observation only with appropriate consent.
- Connected services: authenticated APIs, calendar, mail, repository issues and pull requests, personal cloud files, and home devices where compatible.
- Simulation: a fictional cyber-world interface representing real authorized connections, with **accurate** statuses and activity traces.

"Jack in" = obtain an authorized, short-lived session/credential + scope. "Jack out" = revoke/close it, cancel queued actions, purge volatile token material as appropriate and report what happened.

**No implicit network scan, credential discovery, secret harvesting, or intrusion.** Fictional virus-busting becomes legitimate diagnostics or controlled cybersecurity labs, never unauthorized access.

## 9. NetBattles, virus busting, and game simulation

**[CANON / GAMES]** NetBattles involve Navis competing; the operator/Navi relationship and specialized programs affect performance. Capcom's manuals document battle screens, offline combat systems and modern collection online battles. Sources: [Legacy Collection vol. 1 manual](https://game.capcom.com/manual/REXEAC/vol1/en/steam/top), [vol. 2 manual](https://game.capcom.com/manual/REXEAC/vol2/en/steam/top).

**[PRODUCT]** Treat NetBattles as **training challenges, skill benchmarking and opt-in games**:

- Local duels: two agents in a deterministic arena with identical rules, resource limits, time budgets and measured results.
- Threat simulations: safe mock phishing/email/document scenarios, defensive file classification, puzzle-solving and mock malware triage (never live destructive code).
- Pokémon Lab: reuse lessons from the separate Nora.EXE project, particularly observation→decision→action→outcome loops, OCR, keyboard/menu reasoning, combat and story progression rewards.
- Domain separation: Pokémon policy learned in an emulator must *not* gain real-world device permissions or become the general response model automatically.
- A training match should leave observable records: environment version, seed, state features, legal actions, attempted action, outcome, reward breakdown and rollback point.

**"Delete" and "virus busting" should not imply removing actual user files or using offensive tools.** Present these as simulated arena language or carefully scoped defensive maintenance.

## 10. How NET.Navi capabilities map to real software

| NET.Navi inspiration | Feasible real capability | Limits / engineering requirement |
|---|---|---|
| Persistent individual identity | Configured persona + avatar + long-lived account/profile ID | Identity does not imply consciousness |
| Knows the operator | Consent-based structured memory, retrieval and corrections | Memory must be editable and removable |
| Speaks and listens | Offline STT, optional wake-word detector, local TTS | Android background mic restrictions, power draw |
| Operates independently | Bounded planner + tool calls + verification | Permissions, rollback, action budgets |
| Learns from experiences | Event log + preference learning + lightweight task-specific RL | Requires reliable rewards and evaluation |
| Visits networks | Authenticated app connectors and service adapters | No magic cross-app access |
| Battles viruses | Sandbox game, trusted device hygiene checks | Not malware deletion based only on model output |
| Customizer | Plugin manager and dependency/permission matrix | No unrestricted code loading |
| Evolves styles | Transparent specialized profiles and success metrics | No artificial "intelligence level" promises |
| Visible in PET | Original 2D avatar, animation, dashboard, PiP if supported | Always keep UI and actions auditable |
| Communicates with other Navis | Opt-in secure multi-agent messaging | Explicit trust and permissions |
| Manifests in the real world (anime fantasy) | Voice, notifications, optional physical robot/IoT interface | Separate hardware and controls required |

## 11. Game canon vs anime: don't collapse them

**[ANIME / SECONDARY]** Cross Fusion is an anime-specific concept involving the human operator and Navi in a physical-world transformation setting; this is not a capability of a normal software Navi. See [Cross Fusion reference](https://megaman.fandom.com/wiki/Cross_Fusion). More broadly, individual plots, physical manifestations, and some character details vary between games, anime and manga.

**[PRODUCT]** We can adopt an *aesthetic* of the Navi "appearing" through AR, a phone overlay, desktop widget, voice, or a robot display. These are user-interface outputs, **not** literal transfer of a digital life-form into the physical world.

## 12. Existing technology that can make the project practical

These references are **engineering sources**, not Battle Network lore.

### 12.1 Small local language models

- [Qwen3-0.6B / Transformers documentation](https://github.com/huggingface/transformers/blob/main/docs/source/en/model_doc/qwen3.md): Qwen3 family can switch between thinking and non-thinking paths (exact control depends on engine/template).
- [Official Qwen3.5-0.8B card](https://huggingface.co/Qwen/Qwen3.5-0.8B): separate, newer model family; compare actual accuracy, memory and latency rather than assuming "0.8" is always superior.
- [llama.cpp Android](https://github.com/ggml-org/llama.cpp/blob/master/docs/android.md): reference for quantized, local inference and Android integration. Validate actual model-architecture/runtime compatibility before choosing build.

**[PRODUCT]** Do not fine-tune 0.6–0.8B weights for every interaction. Keep model, memory, tools, personality and task-specific learning separate. Prefer inexpensive deterministic operations and cached validated outcomes to unnecessary generations. Context length advertised on a model card is not a recommended context length for a low-RAM device.

### 12.2 Speech and avatar

- [whisper.cpp Android example](https://github.com/ggml-org/whisper.cpp/blob/master/examples/whisper.android/README.md) is an on-device STT candidate. Benchmark alternatives on actual target device.
- TTS (including optional Kokoro voice assets) requires independent packaging/license review, audio quality checks, and measured memory/latency.
- For voice triggers, separate a low-power wake-phrase detector from STT and from the LLM; do not run all three continuously if avoidable.

### 12.3 Reinforcement learning

- [Stable-Baselines3 algorithms](https://stable-baselines3.readthedocs.io/en/master/guide/algos.html) and [DQN](https://stable-baselines3.readthedocs.io/en/master/modules/dqn.html) are useful *training-environment* references.
- Begin with contextual rules, success memory or tabular Q-learning when states/actions are bounded. Only train a compact neural policy (e.g. small DQN) when the environment justifies it. RL is not inherently a neural network.
- Rewards need external evidence. "The LLM says it succeeded" is **not** proof.
- Include failure penalties for loops, ineffective actions, elapsed time and forbidden actions; high priority for reaching actual goal state and safe completion.
- Evaluate on held-out states/scenarios with a frozen baseline; preserve rollback and do not reward uncontrolled persistent activity.

### 12.4 Device and security reality

- [Android foreground-service/microphone rules](https://developer.android.com/develop/background-work/services/fgs/service-types) and [background start restrictions](https://developer.android.com/develop/background-work/services/fgs/restrictions-bg-start): true "always listening while locked" depends on supported OS conditions, consent and power budget, and cannot be promised outright.
- [Android MediaProjection](https://developer.android.com/media/grow/media-projection): screen capture requires per-session user consent; modern versions impose token and lifecycle constraints.
- [Android accessibility service guidance](https://developer.android.com/guide/topics/ui/accessibility/service): API is designed for assistive usage, not unrestricted universal automation.
- [OWASP Mobile Application Security Verification Standard](https://mas.owasp.org/MASVS/): use storage, auth, platform interaction, privacy and network categories as security audit anchors.

## 13. Experience principles we must preserve

1. **The Navi has a recognizable, continuous identity**, but remains truthful about being software.
2. **The operator is in control.** Long-term trust grows from verifiable competence, not escalating permission.
3. **Usefulness precedes spectacle.** A PET aesthetic cannot rescue slow or inaccurate answers.
4. **The Navi acts in the world through authorized connectors**, never imaginary omnipresence.
5. **Skills have explicit limits.** Each tool has capability, budget, effects, verification and undo metadata.
6. **Learning is observable.** Show what was learned, from what evidence, and how it affected decisions.
7. **Personality is an interface layer**, not the security policy or a replacement for competent reasoning.
8. **Graceful failure is a feature.** When perception is ambiguous, stop/reobserve/correct rather than loop forever.
9. **Offline is the default.** No hidden network dependencies for baseline dialogue, memory or configured local tasks.
10. **The owner can inspect, export, reset and stop the Navi** without breaking the application.

## 14. Representative user journeys

### A. Morning operator briefing (early product)
Operator taps the PET → the Navi greets by configured persona → checks authorized local reminders/notes → reports verified items with source and time → asks permission before sending messages or changing accounts.

### B. "Jack in" to an app (limited autonomy)
Operator selects an app/workflow → Navi displays exact permission scope → app/system prompt authorizes session → planner works in small steps → observes each result → retries within budget or reports an actionable failure → user can press Stop or Jack Out.

### C. Game-training arena (sandbox)
Operator launches a prepared game challenge → the skill agent sees state → chooses only legal in-game controls → records outcome and story progress → adjusts reward for meaningful success → offline model is called only for novel situations → trained policy exports to versioned, reversible artifact.

### D. Teaching a Navi
Operator corrects a mistaken fact → Navi distinguishes conversational preference from world truth → stores verified correction in an inspectable memory record → future retrieval uses correct source → a separate benchmark checks improvement. Do **not** blindly rewrite foundation-model weights.

### E. Navi Customizer
Operator enables a programming chip → system verifies local dependencies and permission scopes → summarizes expected RAM, time and network requirement → loads on demand → failing upgrade automatically rolls back.

## 15. Candidate art and UX references

- [Capcom Battle Network Legacy Collection landing page](https://www.capcom-games.com/megaman/exe/en-uk/): visual tone, illustrated character identity and franchise presentation; **do not copy assets**.
- [MMBN5 PET / field controls](https://game.capcom.com/manual/REXEAC/vol2/en/steam/page/2/1): direct operator↔Navi interaction.
- [MMBN4 Navi Customizer](https://game.capcom.com/manual/REXEAC/vol2/en/steam/page/1/4): visible program slots and constraint feedback.
- [MMBN3 Style Change](https://game.capcom.com/manual/REXEAC/vol1/en/steam/page/3/3): progression reflecting user tendencies.
- [MMBN4 Double Soul](https://game.capcom.com/manual/REXEAC/vol2/en/steam/page/1/3): temporary specialist capability metaphor.

Design original avatar art, icons, cyber-grid motifs, card-style skills and a distinctive PET dashboard. Avoid reproducing original UI screens pixel-for-pixel.

## 16. Open questions for later decisions

These must be tested or explicitly chosen, not silently assumed:

- Product name / Navi's default name, visual identity and voice. The repository name does not force a character name.
- Android-only first release vs parallel Windows build; default recommendation is **Android first + shared headless core**.
- Qwen3-0.6B vs Qwen3.5-0.8B: choose from latency, quality, thermal and memory measurements.
- On-device model GPU acceleration: benchmark CPU baseline before adopting backend-specific paths.
- Desktop/browser/device control mechanisms that are stable, ethical, permitted and testable.
- Which third-party connectors to ship, and which data must remain strictly local.
- Which learning memories deserve automatic insertion versus explicit confirmation.
- How to host optional compute without silently swapping the user's selected local model.
- Animation standard (vector, 2D sprite sheet, resolution) and performance envelope.
- How to provide a PET fantasy without implying unverified access, unsafe behavior or actual sentience.

## 17. Research bibliography

**Primary franchise material**
1. Capcom — [Mega Man Battle Network Legacy Collection](https://www.capcom-games.com/megaman/exe/en-uk/).
2. Capcom — [Legacy Collection Vol. 1 store description](https://store.captown.capcom.com/en/products/645734-jp).
3. Capcom — [Legacy Collection Volume 1 manual index (MMBN1–3)](https://game.capcom.com/manual/REXEAC/vol1/en/steam/top).
4. Capcom — [Legacy Collection Volume 2 manual index (MMBN4–6)](https://game.capcom.com/manual/REXEAC/vol2/en/steam/top).
5. Capcom — [MMBN3 Style Change](https://game.capcom.com/manual/REXEAC/vol1/en/steam/page/3/3).
6. Capcom — [MMBN4 Navi Customizer](https://game.capcom.com/manual/REXEAC/vol2/en/steam/page/1/4).
7. Capcom — [MMBN6 Navi Customizer](https://game.capcom.com/manual/REXEAC/vol2/en/steam/page/3/5).
8. Capcom — [MMBN4 Double Soul](https://game.capcom.com/manual/REXEAC/vol2/en/steam/page/1/3).
9. Capcom — [MMBN5 field controls](https://game.capcom.com/manual/REXEAC/vol2/en/steam/page/2/1).

**Secondary franchise indexes (cross-check)**
10. [MMHP Mega Man Battle Network character data](https://www.mmhp.net/GameHints/MMBN1-Data.html).
11. [MMKB NetNavi description](https://megaman.fandom.com/wiki/NetNavi).
12. [MMKB Operator description](https://megaman.fandom.com/wiki/Operator_%28Mega_Man_Battle_Network%29).
13. [MMKB Cross Fusion (anime-only)](https://megaman.fandom.com/wiki/Cross_Fusion).

**Implementation references**
14. [Qwen3 model documentation](https://github.com/huggingface/transformers/blob/main/docs/source/en/model_doc/qwen3.md).
15. [Qwen3.5-0.8B official model card](https://huggingface.co/Qwen/Qwen3.5-0.8B).
16. [llama.cpp Android](https://github.com/ggml-org/llama.cpp/blob/master/docs/android.md).
17. [whisper.cpp Android](https://github.com/ggml-org/whisper.cpp/blob/master/examples/whisper.android/README.md).
18. [Stable Baselines3](https://stable-baselines3.readthedocs.io/en/master/).
19. [Android foreground service types](https://developer.android.com/develop/background-work/services/fgs/service-types).
20. [Android background restrictions](https://developer.android.com/develop/background-work/services/fgs/restrictions-bg-start).
21. [Android MediaProjection](https://developer.android.com/media/grow/media-projection).
22. [Android AccessibilityService](https://developer.android.com/guide/topics/ui/accessibility/service).
23. [OWASP MASVS](https://mas.owasp.org/MASVS/).

---

**Engineering plan:** [ARCHITECTURE_AND_ROADMAP.md](ARCHITECTURE_AND_ROADMAP.md). When implementation work starts, update the plan's evidence matrix and replace speculative components with measured and versioned implementations.