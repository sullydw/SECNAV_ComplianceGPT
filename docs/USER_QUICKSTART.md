# Hermes User Quickstart

This guide shows the fastest way to draft and render a SECNAV-compliant letter using the interactive chat builder.

## Recommended command

Open a terminal and run:

```
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\hermes_chat_builder.py interactive
```

This starts a live chat session. Hermes will print a `chat_id` and wait for your first message.

## Optional: specify an output file

```
C:\Users\drryl\pinokio\bin\miniconda\python.exe tools\hermes_chat_builder.py interactive --out tmp\my_letter.pdf
```

If you omit `--out`, Hermes uses a default path in the `tmp/` folder.

## Sample conversation

```
Hermes: Welcome! Chat ID: chat-ab12...

You: I need a standard letter to II MEF about reviewing correspondence procedures.
Hermes: Got it. I still need a few fields... (e.g., from, date, signature)

You: Use A. B. SAMPLE and 1 July 2026.
Hermes: Fields updated. Current phase: build_status.

You: Show me the draft.
Hermes: (shows draft preview)

You: Make the body more formal.
Hermes: Body revised. Approval was cleared because the draft changed. Please review and re-approve.

You: Looks good.
Hermes: Approved. Ready to render when you say "Make the PDF."

You: Make the PDF.
Hermes: PDF rendered to tmp\... .pdf

You: exit
Hermes: Goodbye.
```

## Plain-English commands you can use

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

- **Exit:**
  - `exit` or `quit` (also `/exit` or `/quit`)

## Safety gates (what Hermes will not do)

- **No PDF until approved.** Hermes will not render unless you explicitly approve the current draft.
- **Approval clears on change.** If you revise the draft after approving, approval is reset and you must re-approve.
- **No render until validation is ready.** Hermes checks that the letter has all required fields before rendering.

## Developer commands (not required for normal use)

The chat builder is a thin layer over lower-level session commands. Users should stick to `interactive`. Developers who need direct control can still use `tools/hermes_session_manager.py` commands (`new`, `say`, `answer`, `preview`, `approve`, `ready`, `revise`, `render`, etc.), but those are not part of the normal user workflow.
