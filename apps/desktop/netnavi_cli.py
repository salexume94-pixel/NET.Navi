"""Minimal interactive NET.Navi chat shell with explicit backend selection."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

# Run as 'python apps/desktop/netnavi_cli.py' without installation.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from core.inference.runtime import (InferenceError, SYSTEM_INSTRUCTIONS,
                                    bounded_messages, generate, select_route)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="NET.Navi streaming chat prototype")
    parser.add_argument("--backend", choices=("local", "cloud", "hybrid"), default="local",
                        help="Cloud/hybrid explicitly enable sharing prompts with OpenAI")
    parser.add_argument("--profile", choices=("fast", "balanced", "deep"), default="balanced")
    parser.add_argument("--model", default=os.getenv("NETNAVI_LOCAL_MODEL", "netnavi-v2"))
    parser.add_argument("--cloud-model", default=os.getenv("NETNAVI_CLOUD_MODEL", ""))
    parser.add_argument("--once", help="Send exactly one prompt, for shell use")
    args = parser.parse_args(argv)
    history = [{"role": "system", "content": SYSTEM_INSTRUCTIONS}]
    print("NET.Navi prototype | /exit quits | /clear resets session", flush=True)
    print(f"Backend: {args.backend} | profile: {args.profile}", flush=True)
    if args.backend != "local":
        print("NETWORK ENABLED: cloud-routed chat messages go to OpenAI and incur API charges.", flush=True)
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
            history = history[:1]
            print("Session cleared.")
            if args.once is not None:
                return 0
            continue
        try:
            route = select_route(prompt, args.backend, args.profile, args.model, args.cloud_model)
            incoming = bounded_messages([*history, {"role": "user", "content": prompt}])
            print(f"NET.Navi [{route.backend}/{route.model}]> ", end="", flush=True)
            answer, metrics = generate(incoming, route, on_text=lambda chunk: print(chunk, end="", flush=True))
            print()
            first = "n/a" if metrics.first_token_seconds is None else f"{metrics.first_token_seconds:.2f}s"
            print(f"[First text {first} | total {metrics.total_seconds:.2f}s | {metrics.chars} chars]")
            history = [*incoming, {"role": "assistant", "content": answer}]
        except (InferenceError, ValueError) as exc:
            print(f"\n[Not completed: {exc}]", file=sys.stderr)
            if args.once is not None:
                return 1
        except KeyboardInterrupt:
            print("\n[Cancelled. No answer committed to session.]")
            if args.once is not None:
                return 130
        if args.once is not None:
            return 0


if __name__ == "__main__":
    raise SystemExit(main())
