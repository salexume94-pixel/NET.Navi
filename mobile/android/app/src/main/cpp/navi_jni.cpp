#include <jni.h>
#include <llama.h>
#include <android/log.h>
#include <algorithm>
#include <atomic>
#include <chrono>
#include <cstdio>
#include <string>
#include <vector>

namespace {
std::atomic<bool> stop_requested{false};
llama_model * model = nullptr;
llama_context * context = nullptr;
bool backend_started = false;

jstring status(JNIEnv * env, const std::string & s) {
    return env->NewStringUTF(s.c_str());
}

void release_engine() {
    if (context) {
        llama_free(context);
        context = nullptr;
    }
    if (model) {
        llama_model_free(model);
        model = nullptr;
    }
}

bool aborted(void *) {
    return stop_requested.load(std::memory_order_relaxed);
}

std::string jstring_value(JNIEnv * env, jstring value) {
    if (!value) return {};
    const char * chars = env->GetStringUTFChars(value, nullptr);
    if (!chars) return {};
    std::string s(chars);
    env->ReleaseStringUTFChars(value, chars);
    return s;
}

bool emit_text(JNIEnv * env, jobject callback, jmethodID method, const std::string & bytes) {
    jbyteArray raw = env->NewByteArray(static_cast<jsize>(bytes.size()));
    if (!raw) return false;
    if (!bytes.empty()) {
        env->SetByteArrayRegion(raw, 0, static_cast<jsize>(bytes.size()),
                                reinterpret_cast<const jbyte *>(bytes.data()));
    }
    env->CallVoidMethod(callback, method, raw);
    env->DeleteLocalRef(raw);
    return !env->ExceptionCheck();
}

bool process_tokens(llama_batch_ext * batch, const llama_token * tokens,
                    size_t count, llama_pos first_pos, bool want_logits) {
    llama_batch_ext_clear(batch);
    for (size_t i = 0; i < count; ++i) {
        const int32_t index = llama_batch_ext_add_token(batch, 0, tokens[i]);
        if (index < 0) return false;
        const llama_pos pos = first_pos + static_cast<llama_pos>(i);
        if (!llama_batch_ext_set_pos(batch, index, &pos)) return false;
        if (want_logits && i + 1 == count) {
            if (!llama_batch_ext_set_output_logits(batch, index, true)) return false;
        }
    }
    return llama_process(context, LLAMA_PROCESS_TYPE_DECODE, batch) == 0;
}
}

extern "C" JNIEXPORT void JNICALL
Java_com_netnavi_mobile_NativeEngine_requestStop(JNIEnv *, jobject) {
    stop_requested.store(true, std::memory_order_relaxed);
}

extern "C" JNIEXPORT void JNICALL
Java_com_netnavi_mobile_NativeEngine_unload(JNIEnv *, jobject) {
    stop_requested.store(true, std::memory_order_relaxed);
    // Calls are serialized by the Kotlin worker. requestStop is the only concurrent call.
    release_engine();
}

extern "C" JNIEXPORT jstring JNICALL
Java_com_netnavi_mobile_NativeEngine_loadModel(JNIEnv * env, jobject, jstring jpath,
                                               jint ctx_size, jint threads) {
    release_engine();
    stop_requested.store(false, std::memory_order_relaxed);
    if (!backend_started) {
        llama_backend_init();
        backend_started = true;
    }
    const std::string path = jstring_value(env, jpath);
    if (path.empty()) return status(env, "ERROR: Model path is empty");
    llama_model_params mp = llama_model_default_params();
    mp.n_gpu_layers = 0; // documented CPU baseline for modest Android hardware
    mp.use_mmap = true;
    model = llama_model_load_from_file(path.c_str(), mp);
    if (!model) return status(env, "ERROR: GGUF load failed or unsupported architecture");
    llama_context_params cp = llama_context_default_params();
    cp.n_ctx = static_cast<uint32_t>(std::clamp(static_cast<int>(ctx_size), 512, 4096));
    cp.n_batch = 256;
    cp.n_ubatch = 128;
    cp.abort_callback = aborted;
    cp.abort_callback_data = nullptr;
    context = llama_init_from_model(model, cp);
    if (!context) {
        release_engine();
        return status(env, "ERROR: Model context allocation failed (check free RAM)");
    }
    const int nthreads = std::clamp(static_cast<int>(threads), 1, 6);
    llama_set_n_threads(context, nthreads, nthreads);
    return status(env, "Model loaded · " + std::to_string(llama_n_ctx(context)) + " ctx");
}

extern "C" JNIEXPORT jstring JNICALL
Java_com_netnavi_mobile_NativeEngine_generate(JNIEnv * env, jobject,
                                               jobjectArray jroles, jobjectArray jcontents,
                                               jint jmax, jobject callback) {
    if (!model || !context) return status(env, "ERROR: No loaded model");
    if (!jroles || !jcontents || !callback) return status(env, "ERROR: Invalid chat request");
    const jsize n = env->GetArrayLength(jroles);
    if (n == 0 || n != env->GetArrayLength(jcontents) || n > 64) {
        return status(env, "ERROR: Invalid conversation");
    }
    jclass callback_class = env->GetObjectClass(callback);
    jmethodID on_text = env->GetMethodID(callback_class, "onText", "([B)V");
    env->DeleteLocalRef(callback_class);
    if (!on_text) return status(env, "ERROR: Missing streaming callback");

    stop_requested.store(false, std::memory_order_relaxed);
    std::vector<std::string> roles, contents;
    roles.reserve(n); contents.reserve(n);
    for (jsize i = 0; i < n; ++i) {
        auto * jr = static_cast<jstring>(env->GetObjectArrayElement(jroles, i));
        auto * jc = static_cast<jstring>(env->GetObjectArrayElement(jcontents, i));
        roles.emplace_back(jstring_value(env, jr));
        contents.emplace_back(jstring_value(env, jc));
        if (jr) env->DeleteLocalRef(jr);
        if (jc) env->DeleteLocalRef(jc);
    }
    std::vector<llama_chat_message> chat;
    chat.reserve(n);
    for (jsize i = 0; i < n; ++i) {
        chat.push_back({roles[i].c_str(), contents[i].c_str()});
    }

    std::string prompt;
    const char * tmpl = llama_model_chat_template(model, nullptr);
    if (tmpl) {
        const int required = llama_chat_apply_template(tmpl, chat.data(), chat.size(),
                                                       true, nullptr, 0);
        if (required > 0 && required < 500000) {
            prompt.resize(required);
            const int actual = llama_chat_apply_template(tmpl, chat.data(), chat.size(),
                                                         true, prompt.data(), required);
            if (actual < 0) prompt.clear();
            else prompt.resize(actual);
        }
    }
    if (prompt.empty()) {
        // ChatML fallback for Qwen-style models only.
        for (const auto & item : chat) {
            prompt += "<|im_start|>";
            prompt += item.role;
            prompt += "\n";
            prompt += item.content;
            prompt += "<|im_end|>\n";
        }
        prompt += "<|im_start|>assistant\n";
    }

    const llama_vocab * vocab = llama_model_get_vocab(model);
    const int needed = -llama_tokenize(vocab, prompt.c_str(), static_cast<int32_t>(prompt.size()),
                                       nullptr, 0, true, true);
    if (needed <= 0 || needed > 100000) return status(env, "ERROR: Could not tokenize prompt");
    std::vector<llama_token> tokens(needed);
    const int actual = llama_tokenize(vocab, prompt.c_str(), static_cast<int32_t>(prompt.size()),
                                      tokens.data(), static_cast<int32_t>(tokens.size()), true, true);
    if (actual <= 0) return status(env, "ERROR: Tokenizer failed");
    tokens.resize(actual);
    const int ctx = static_cast<int>(llama_n_ctx(context));
    const int max_reply = std::clamp(static_cast<int>(jmax), 1, 512);
    if (actual + 2 >= ctx) return status(env, "ERROR: Context full. Use NEW CHAT or a shorter message.");

    llama_memory_clear(llama_get_memory(context), false);
    auto * batch = llama_batch_ext_init(context);
    if (!batch) return status(env, "ERROR: Cannot allocate inference batch");

    bool ok = true;
    size_t offset = 0;
    while (offset < tokens.size() && !stop_requested.load(std::memory_order_relaxed)) {
        const size_t chunk = std::min(static_cast<size_t>(128), tokens.size() - offset);
        const bool final_chunk = offset + chunk == tokens.size();
        ok = process_tokens(batch, tokens.data() + offset, chunk,
                            static_cast<llama_pos>(offset), final_chunk);
        if (!ok) break;
        offset += chunk;
    }
    if (!ok) {
        llama_batch_ext_free(batch);
        return status(env, "ERROR: Prompt inference failed");
    }
    if (stop_requested.load(std::memory_order_relaxed)) {
        llama_batch_ext_free(batch);
        return status(env, "STOPPED");
    }

    auto * sampler = llama_sampler_chain_init(llama_sampler_chain_default_params());
    llama_sampler_chain_add(sampler, llama_sampler_init_min_p(0.05f, 1));
    llama_sampler_chain_add(sampler, llama_sampler_init_temp(0.7f));
    llama_sampler_chain_add(sampler, llama_sampler_init_dist(LLAMA_DEFAULT_SEED));

    std::string output;
    const auto start = std::chrono::steady_clock::now();
    int generated = 0;
    const int budget = std::min(max_reply, ctx - actual - 1);
    for (int i = 0; i < budget && !stop_requested.load(std::memory_order_relaxed); ++i) {
        const llama_token id = llama_sampler_sample(sampler, context, -1);
        llama_sampler_accept(sampler, id);
        if (llama_vocab_is_eog(vocab, id)) break;
        char buffer[512];
        int bytes = llama_token_to_piece(vocab, id, buffer, sizeof(buffer), 0, false);
        if (bytes < 0) {
            std::vector<char> large(static_cast<size_t>(-bytes) + 4);
            bytes = llama_token_to_piece(vocab, id, large.data(),
                                         static_cast<int32_t>(large.size()), 0, false);
            if (bytes > 0) output.append(large.data(), bytes);
        } else if (bytes > 0) {
            output.append(buffer, bytes);
        }
        generated++;
        if (!emit_text(env, callback, on_text, output)) break;
        if (i + 1 < budget) {
            if (!process_tokens(batch, &id, 1, static_cast<llama_pos>(actual + i), true)) {
                ok = false;
                break;
            }
        }
    }
    llama_sampler_free(sampler);
    llama_batch_ext_free(batch);
    const double seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - start).count();
    if (stop_requested.load(std::memory_order_relaxed)) return status(env, "STOPPED");
    if (!ok) return status(env, "ERROR: Decode failed");
    char summary[128];
    std::snprintf(summary, sizeof(summary), "%d tokens · %.1f tok/s",
                  generated, generated / std::max(0.001, seconds));
    return status(env, summary);
}
