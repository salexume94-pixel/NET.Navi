# NET.Navi: Streaming inference prototype

**Status: functional desktop text-chat prototype, NOT the finished NET.Navi.**

This implementation preserves the separate Nora.EXE Pokémon laboratory and NET.Navi roadmap. It introduces no skill execution, privileged tool calls, learned model weights, or claims of autonomous learning.

## Why this approach

The i3-8130U / Intel UHD 620 / 32 GB laptop cannot locally host a frontier-scale model at frontier quality or latency. Optimize **time to useful answer**, not a fabricated intelligence score. The local model offers privacy and offline availability. An explicitly selected cloud backend can provide stronger reasoning, with network availability, API access, and token cost. Streaming lowers *perceived* latency, not actual computation time.

Profiles are static budgets, not guaranteed latency caps:

| Profile | Ollama 'think' | Local output cap | Context tokens | Cloud reasoning effort | Cloud output cap |
| --- | --- | ---: | ---: | --- | ---: |
| 'fast' | off | 256 | 2,048 | low | 384 |
| 'balanced' | off | 768 | 4,096 | medium | 1,024 |
| 'deep' | on | 2,048 | 4,096 | high | 3,072 |

Local thinking-on results may be empty if a model spends its output budget thinking, as seen in the earlier benchmark. This runner treats empty/incomplete results as failures, never successful answers. Ollama thinking support varies by model; changing a model may require adjusting the profile.

## First run (Windows PowerShell)

Install Ollama, download a suitable small local model, then from the repo root:

```powershell
ollama pull qwen3:0.6b
python apps/desktop/netnavi_cli.py --backend local --model qwen3:0.6b --profile fast
```

A custom 'netnavi-v2' Ollama model can be selected with '--model netnavi-v2' after you create it locally. The CLI never downloads models itself.

For opt-in stronger reasoning through OpenAI's Responses API, set your API key **only in a local terminal/session** (not in GitHub, CLI arguments or source code):

```powershell
$env:OPENAI_API_KEY = Read-Host 'API key'
$env:NETNAVI_CLOUD_MODEL = 'gpt-6.1-sol'  # requires API model access; charges apply
python apps/desktop/netnavi_cli.py --backend cloud --profile balanced
```

'--backend hybrid' explicitly authorizes network routing for more demanding messages. It routes short messages locally, and certain longer/coding/analysis prompts to the cloud. The chosen backend is displayed **before** content is sent. Simple keyword routing can misclassify tasks. For sensitive messages, choose '--backend local', never hybrid. Neither cloud nor hybrid is enabled by default. Cloud responses are requested with 'store: false' (this is not a guarantee of zero provider-side retention; consult the provider's terms). No local files or memories are sent automatically.

One-shot commands:

```powershell
python apps/desktop/netnavi_cli.py --backend local --model qwen3:0.6b --profile fast --once 'Hello Navi'
```

Run offline unit tests:

```powershell
python -m unittest discover -s tests -p 'test_*.py' -v
```

## Performance and safety notes

- Streams visible text as it arrives and displays time to **first visible text** and total wall-clock latency. Deep thinking may delay first visible text while internal reasoning is generated. Neither number is a promise on the target device.
- 'keep_alive: 10m' avoids repeated Ollama model reloads for interactive use but keeps memory occupied for that duration. Context is trimmed to recent complete turns by character count (a rough approximation, not exact token accounting).
- 'num_predict' and 'max_output_tokens' prevent unlimited output, and requests have socket timeouts. Total wall-clock deadlines and per-device performance benchmarks still need engineering.
- The console uses an in-memory session: '/clear' resets it. It does not persist chat history, implement secure memories, access files or programs, or execute tool calls.
- HTTP failures, incomplete streams, and blank answers produce errors rather than fabricated success. Ctrl+C cancels a running request and does not commit an incomplete answer to the session.
- Local inference is restricted to the loopback Ollama API to avoid silently transferring private prompts elsewhere. Cloud credentials stay in environment variables. They must not be logged or committed.

## Measurement and next gates

1. Run the existing **frozen** 100-case benchmark with each candidate local model and thinking mode; do not train on the evaluation set.
2. Run representative one-shot and conversation tests; record time to first text, complete response, correctness, and memory consumption. Benchmark cold vs warm runs and compare different 'keep_alive' values.
3. Implement persistent *editable* SQLite memory with provenance and an independent security supervisor before any skills are allowed. Then build the Android PET UI and permission controls.
4. Do not treat cloud-model quality as proof that the local model has become more intelligent. Quantify costs and measure performance against agreed tasks.
