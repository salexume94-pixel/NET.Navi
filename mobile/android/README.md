# NET.Navi Android local GGUF launcher

**Status:** source implementation. Not yet compiled on the target Samsung phone. This module adds a separate Android application without modifying Nora.EXE or the NET.Navi benchmark.

## Features
- Import a local .gguf from Android's document picker into app-private storage.
- Load quantized Qwen GGUFs through llama.cpp on **arm64 CPU**; no account, server, network permission, or remote model fallback.
- Offline conversation with token streaming, a 2048-token context, and a 256-token response budget.
- Stop / Jack Out generation, reload, new chat, and device-private chat persistence.
- Minimal original PET-inspired UI.
- No autonomous device operations. The launcher is a text-chat inference milestone, not a full agent.

## Build

Requirements: Android Studio / JDK 17, Android SDK 35, NDK 27.0.12077973, CMake 3.22.1, Git.

From a shell in `mobile/android`:

```bash
bash scripts/bootstrap-llama.sh
```

Open `mobile/android` as a project in Android Studio, let it sync, then choose **Build APK(s)**. Alternatively run `gradle :app:assembleDebug` with Gradle 8.11.1 installed. APK will be at `app/build/outputs/apk/debug/app-debug.apk`.

The workflow `.github/workflows/android-launcher.yml` can build an APK artifact when GitHub Actions minutes are available. GitHub Actions spending/usage restrictions may prevent that job from starting.

## Get your trained model onto the phone

1. Train or merge your Qwen model on the computer or Colab.
2. Export it as **one compatible GGUF** (Q4_K_M is a sensible first CPU test); a .safetensors file, LoRA adapter, or Ollama tag is not a GGUF.
3. Transfer that GGUF to Downloads on the phone.
4. Open NET.Navi, choose **IMPORT GGUF**, select the file, and let the launcher copy and automatically load the model. On future launches tap **LOAD MODEL**.
5. Chat with airplane mode enabled to verify local-only operation.

This application **does not download model weights** and no weights are committed to GitHub. A trained Qwen3-0.6B export must actually be Qwen3: the earlier sample script used `unsloth/Qwen2.5-0.5B-bnb-4bit`, a different base model.

## Notes and limitations

- 2048 context tokens and 256 generated tokens per response, bounded deliberately for low RAM / thermals; maximum retained chat context also trims old turns.
- The model is copied to `files/models/active-model.gguf`, not loaded from a transient `content://` URI. The original picked file remains untouched.
- CPU-only. This avoids unverified GPU drivers and backend fallbacks; compare optimized GPU backend only after baseline tests.
- Imported model persists across app restarts; model memory is unloaded when the process exits. The app does not update model weights or perform on-device training.
- Stop is checked between decoding steps and via a llama.cpp compute abort callback. In-progress model loading may not stop immediately.
- The package ID is stable: `com.netnavi.mobile`. Future builds signed with **the same signing key** update in place. Switching from a debug-signed APK to a differently signed release APK normally requires uninstalling the earlier version.
- Chat history remains in private SharedPreferences and can be cleared with **NEW CHAT**. This is not the future structured memory system.
- Importing huge GGUFs can fail if device storage is low; the UI reports errors instead of pretending loading succeeded.

## Security

No INTERNET permission. No background service, accessibility control, arbitrary command execution, or account credentials. Model text never acts as authorization to run device tools.
