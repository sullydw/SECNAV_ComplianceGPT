# Hermes User Quickstart

Normal use is chatting with Hermes. Hermes calls the SECNAV builder tool behind the scenes so you don't have to run anything separately.

## How to use it

Just talk to Hermes like you would to a person. For example:

```
I need a standard letter from Commanding Officer, Marine Corps Air Station New River
  to Commanding General, II Marine Expeditionary Force about correspondence procedures.
  Use the date 1 July 2026, signer A. B. SAMPLE, subject Correspondence Procedures,
  and make the body about implementing local correspondence review procedures.
```

Hermes extracts the fields, builds the draft, and walks you through review, approval, and rendering.

## What you can ask

- **Draft / change:**
  - `I need a letter to ...`
  - `Use signer ...`
  - `Change the subject to ...`
  - `Make the body more formal`
  - `Show me the draft`

- **Approve:**
  - `Looks good`
  - `Approved`

- **Render:**
  - `Make the PDF`

- **Check status:**
  - `What's the status?`

## Safety gates (what Hermes will not do)

- **No PDF until approved.** Hermes will not render unless you explicitly approve the current draft. If you say "Make the PDF" too early, Hermes will tell you what is still needed.
- **Approval clears on change.** If you revise the draft after approving, approval is reset and you must re-approve.
- **No render until validation is ready.** Hermes checks that the letter has all required fields before rendering.

## Developer / local testing

If you need to run the builder directly for local testing or debugging, you can use the interactive mode:

```
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\hermes_chat_builder.py interactive
```

This is a local test/debug harness. Normal users should not need it.

For UI integration or automation scripts, you can also call the builder in `--json-lines` mode:

```
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\hermes_chat_builder.py interactive --json-lines
```

And optionally specify an output PDF path:

```
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\hermes_chat_builder.py interactive --out tmp\my_letter.pdf
```

## What happens behind the scenes

Hermes uses callable functions inside `tools/hermes_chat_builder.py`:
- `start_secnav_chat()` — begins a session
- `send_secnav_chat_turn()` — sends your message
- `get_secnav_chat_status()` — checks current phase
- `reset_secnav_chat()` — starts fresh while keeping the same chat ID

These functions return plain dictionaries, which Hermes turns into the responses you see.
