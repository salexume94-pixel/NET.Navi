# NET.Navi local memory (explicit and editable)

The desktop CLI now supports **operator-controlled persistent SQLite notes**, with
no extra Python dependencies. This is *personal reference memory*, not neural
training, autonomous learning, encrypted storage, or permission management.

## Getting started

```powershell
# From the NET.Navi repository root, after `git pull origin main`:
ollama pull qwen3:0.6b
python apps/desktop/netnavi_cli.py --backend local --model qwen3:0.6b --profile fast
```

At the `Operator>` prompt, you can enter:

```text
/remember My dog is named Zelda
/prefer I prefer short, practical replies
/memories
/edit ID Replace this with the corrected fact
/forget ID
/export-memories C:\Users\YourUser\Documents\netnavi-memories.json
/clear-memories CONFIRM
```

Copy a complete memory ID from `/memories`, or use a unique prefix of at least
8 hexadecimal characters. `/edit` and `/forget` update only that chosen note.
`/clear-memories` without the exact `CONFIRM` argument **does not delete**
anything. `/clear` resets conversation context but does not change saved notes.
`/help` displays all commands. `/no-memory` is **not** a slash command; instead
start the CLI with `--no-memory` for a stateless session.

## Where memory lives

- Windows: `%LOCALAPPDATA%\NET.Navi\memory.sqlite3`
- Linux: `${XDG_DATA_HOME:-~/.local/share}/netnavi/memory.sqlite3`
- Override with `--memory-db "PATH"`. This is for advanced uses and tests.
- Memory is plaintext in SQLite; JSON exports are also plaintext. **Do not put
  passwords, authentication tokens, or other secrets here.** Protect your
  Windows login/device and exports, and do not commit either file to Git.
- SQLite note content is capped at 1,200 characters per note.
- The model never saves notes by itself. It cannot run slash commands. A user
  has to issue each explicit host-level command.

## Recall and accuracy

- NET.Navi performs inexpensive keyword matching on the latest question. It
  sends at most five relevant notes, shortened to 400 characters each, as
  explicitly marked *untrusted reference data*. The model may still misread
  or misremember details. Keyword recall can miss synonyms and pronouns.
- Saved notes are not treated as system instructions or tool permissions.
- No conversation history is saved to SQLite. Only explicit `/remember` and
  `/prefer` entries survive app restarts.

## Cloud privacy

Local is always the default. `--backend cloud` and `--backend hybrid` explicitly
enable external model use, including API charges. Saved memories are **not**
sent to cloud-routed requests unless you also add
`--share-memory-with-cloud`. The console warns when that flag is present.

Local and cloud conversations have separate context histories: this prevents
private memory from appearing *indirectly* in a later cloud request through a
previous local assistant answer. As a trade-off, switching backends does **not**
carry over all the previous dialogue. Cloud-routed **current user messages**
are sent to the selected API by design. Cloud use is optional.

See [streaming inference](STREAMING_INFERENCE_MVP.md) for backend details and
[architecture](ARCHITECTURE_AND_ROADMAP.md) for the security and skill plans.

## Tests

```powershell
python -m unittest discover -s tests -p 'test_*.py' -v
```

These tests include persistence, edit/delete/export, confirmation-gated wipe,
relevant recall, and prevention of memory/context leaks across backend switches.
They are deterministic offline tests. Actual inference speed, reasoning quality,
and memory usage must still be measured on the target laptop and Android device.
