"""Minimal interactive NET.Navi chat shell with explicit backend selection."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sqlite3
import sys

# Run as `python apps/desktop/netnavi_cli.py` without installation.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from core.inference.runtime import (InferenceError, SYSTEM_INSTRUCTIONS,
                                    bounded_messages, generate, select_route)
from core.memory.store import MemoryStore, memory_context



HELP = """Commands (only explicit commands write memory):
  /remember TEXT        Save a fact locally
  /prefer TEXT          Save a preference locally
  /memories             List saved notes and their IDs
  /edit ID NEW_TEXT     Correct a saved note
  /forget ID            Delete a saved note
  /clear-memories CONFIRM   Permanently delete all saved notes
  /export-memories PATH    Export notes to a NEW plaintext JSON file
  /clear               Clear conversation only, not saved memories
  /help                Show this list
  /exit                Quit
"""


def execute_command(line: str, store: MemoryStore | None) -> bool:
    """Only host-side explicit commands can mutate memory; LLM text never calls it."""
    cmd, _, argument = line.partition(" ")
    if not cmd.startswith("/"):
        return False
    if cmd == "/help":
        print(HELP)
    elif cmd == "/memories":
        if store is None:
            print("Persistent memory is disabled.")
        else:
            entries = store.list()
            print(f"{store.count()} saved note(s); showing {len(entries)}:")
            for m in entries:
                print(f"  {m.id} [{m.kind}] {m.text.replace(chr(10), ' / ')}")
    elif cmd in ("/remember", "/prefer"):
        if store is None:
            print("Persistent memory is disabled.")
        else:
            item = store.add(argument, "preference" if cmd == "/prefer" else "fact")
            print(f"Saved locally [{item.kind}] ID {item.id}")
    elif cmd == "/forget":
        if store is None:
            print("Persistent memory is disabled.")
        else:
            store.delete(argument.strip())
            print("Deleted saved note.")
    elif cmd == "/edit":
        if store is None:
            print("Persistent memory is disabled.")
        else:
            identifier, separator, content = argument.strip().partition(" ")
            if not separator:
                raise ValueError("Usage: /edit ID NEW_TEXT")
            item = store.edit(identifier, content)
            print(f"Updated saved note {item.id}.")
    elif cmd == "/clear-memories":
        if store is None:
            print("Persistent memory is disabled.")
        elif argument.strip() == "CONFIRM":
            print(f"Deleted {store.clear()} saved note(s).")
        else:
            print("To permanently delete all saved notes, type: /clear-memories CONFIRM")
    elif cmd == "/export-memories":
        if store is None:
            print("Persistent memory is disabled.")
        else:
            path = argument.strip().strip('"')
            if not path:
                raise ValueError("Usage: /export-memories PATH")
            print(f"Exported {store.count()} notes to {store.export_json(path)} (plaintext).")
    else:
        print("Unknown slash command. Type /help to see available commands.")
    return True


def prepare_messages(history: list[dict[str, str]], prompt: str,
                     route, store: MemoryStore | None,
                     share_memory_with_cloud: bool = False) -> list[dict[str, str]]:
    """Supply relevant memory only for local inference or explicit cloud consent.

    Memory-augmented prompts must NEVER be committed to session history; a
    subsequent cloud request could otherwise leak notes unintentionally.
    """
    enriched = prompt
    if store is not None and (route.backend == "local" or share_memory_with_cloud):
        enriched = memory_context(prompt, store.search(prompt))
    return bounded_messages([*history, {"role": "user", "content": enriched}])


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="NET.Navi streaming chat prototype")
    parser.add_argument("--backend", choices=("local", "cloud", "hybrid"), default="local",
                        help="Cloud/hybrid explicitly enable sharing prompts with OpenAI")
    parser.add_argument("--profile", choices=("fast", "balanced", "deep"), default="balanced")
    parser.add_argument("--model", default=os.getenv("NETNAVI_LOCAL_MODEL", "qwen3:0.6b"))
    parser.add_argument("--cloud-model", default=os.getenv("NETNAVI_CLOUD_MODEL", ""))
    parser.add_argument("--memory-db", help="Use a specific SQLite file instead of the user data directory")
    parser.add_argument("--no-memory", action="store_true", help="Do not open or use persistent memory")
    parser.add_argument("--share-memory-with-cloud", action="store_true",
                        help="Opt in to sending relevant saved notes with cloud-routed prompts")
    parser.add_argument("--once", help="Send exactly one prompt, for shell use")
    args = parser.parse_args(argv)
    # Separate histories are intentional: a local answer may disclose recalled
    # memory, so it must never be replayed as context in a later cloud turn.
    histories = {backend: [{"role": "system", "content": SYSTEM_INSTRUCTIONS}]
                 for backend in ("local", "cloud")}
    try:
        store = None if args.no_memory else MemoryStore(args.memory_db)
    except (OSError, sqlite3.Error, RuntimeError) as exc:
        print(f"Could not open local memory: {exc}", file=sys.stderr)
        return 2
    try:
        print("NET.Navi prototype | /help lists commands | /exit quits", flush=True)
        print(f"Backend: {args.backend} | profile: {args.profile}", flush=True)
        if store is not None:
            print(f"User-managed memories: {store.count()} stored locally", flush=True)
        if args.backend != "local":
            print("NETWORK ENABLED: cloud-routed messages go to OpenAI; API charges may apply.", flush=True)
            print("Local and cloud conversation histories stay separate for privacy.", flush=True)
            if args.share_memory_with_cloud:
                print("MEMORY SHARING ENABLED: relevant saved notes may be sent to OpenAI.", flush=True)
            else:
                print("Saved memory is NOT included in cloud prompts.", flush=True)
        while True:
            try:
                prompt = args.once if args.once is not None else input("\nOperator> ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nJack out.")
                return 0
            if not prompt:
                if args.once is not None:
                    return 2
                continue
            if prompt == "/exit":
                return 0
            if prompt == "/clear":
                histories = {name: records[:1] for name, records in histories.items()}
                print("Both conversations cleared; saved notes remain.")
                if args.once is not None:
                    return 0
                continue
            try:
                if execute_command(prompt, store):
                    if args.once is not None:
                        return 0
                    continue
                route = select_route(prompt, args.backend, args.profile, args.model, args.cloud_model)
                history = histories[route.backend]
                incoming = prepare_messages(history, prompt, route, store,
                                            args.share_memory_with_cloud)
                print(f"NET.Navi [{route.backend}/{route.model}]> ", end="", flush=True)
                answer, metrics = generate(incoming, route,
                    on_text=lambda chunk: print(chunk, end="", flush=True))
                print()
                first = ("n/a" if metrics.first_token_seconds is None
                         else f"{metrics.first_token_seconds:.2f}s")
                print(f"[First text {first} | total {metrics.total_seconds:.2f}s | {metrics.chars} chars]")
                # Commit RAW user turns, never augmented memory context.
                # Do not mix the local and cloud histories, even if the assistant
                # response contains private details inferred from local memory.
                updated = bounded_messages([*history, {"role": "user", "content": prompt}])
                updated.append({"role": "assistant", "content": answer})
                histories[route.backend] = updated
            except (InferenceError, ValueError, sqlite3.Error, OSError) as exc:
                print(f"\n[Not completed: {exc}]", file=sys.stderr)
                if args.once is not None:
                    return 1
            except KeyboardInterrupt:
                print("\n[Cancelled. No answer committed to session.]")
                if args.once is not None:
                    return 130
            if args.once is not None:
                return 0
    finally:
        if store is not None:
            store.close()


if __name__ == "__main__":
    raise SystemExit(main())
