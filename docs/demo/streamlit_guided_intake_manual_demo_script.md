# SECNAV Compliant Letter Builder — Streamlit Guided Intake Manual Demo Script

**Version:** Phase L.25  
**Date:** 2026-06-14  
**App file:** `app_streamlit_llm_guided_intake.py`  
**Baseline commit:** `d84d4d7`

---

## Prerequisites

- Python 3.10+
- Repo cloned to `C:\Users\drryl\SECNAV_ComplianceGPT`
- Optional: `pip install streamlit`
- No API key required
- No network connection required
- Default provider is safe, offline mock

---

## Launch Command

```powershell
cd C:\Users\drryl\SECNAV_ComplianceGPT
streamlit run app_streamlit_llm_guided_intake.py
```

Browser opens automatically at:
```
http://localhost:8501
```

If the browser does not open, visit the URL manually.

---

## Demo Scenario: Standard Letter — Training Plan

We will create a standard Navy letter with the following fields:

| Field | Value |
|-------|-------|
| Document type | standard_letter |
| From | Commanding Officer, Example Command |
| To | Commander, Example Group |
| Subject | Training Plan |
| SSIC | 5216 |
| Body | This letter provides the proposed training plan. |
| Signature | J. Q. Sample, Commanding Officer |
| Window envelope | false |

---

## Step-by-Step Walkthrough

### Step 1 — Start the app

- Open the browser at `http://localhost:8501`
- Verify the title: **📄 SECNAV Compliant Letter Builder**
- Expand the **ℹ️ How to use** section at the top
- Note the example prompts listed inside
- Look at the **Provider Status** sidebar:
  - Should read **mock (default — no network)** — this confirms safe/offline mode
  - No API key is shown anywhere on the page

### Step 2 — Enter the document type

In the chat box at the bottom of the left column, type:

```
I need to write a standard letter.
```

**Expected observation:**
- Conversation history records your message
- Intent detected as `start_letter` or `provide_field`
- Draft summary on the right shows **Document Type:** `standard_letter`
- No errors shown

### Step 3 — Enter sender

Type:

```
It is from Commanding Officer, Example Command.
```

**Expected observation:**
- **From:** field populated
- Missing fields panel still lists other required fields (To, Subject, SSIC, etc.)
- Validation counts remain low

### Step 4 — Enter recipient

Type:

```
Send it to Commander, Example Group.
```

**Expected observation:**
- **To:** field populated
- Missing fields count decreases
- Validation panel unchanged or improves

### Step 5 — Enter subject

Type:

```
The subject is Training Plan.
```

**Expected observation:**
- **Subject:** `Training Plan`
- Validation panel may show an advisory or warning related to subject formatting — this is expected
- The mock mediator intentionally surfaces formatting hints as advisories
- If warnings appear, note them; they must be accepted before finalize

### Step 6 — Enter SSIC

Type:

```
Use SSIC 5216.
```

**Expected observation:**
- **SSIC:** `5216`
- All critical routing fields now present
- Validation may improve; missing required fields should drop further

### Step 7 — Enter body

Type:

```
The body should say this letter provides the proposed training plan.
```

**Expected observation:**
- **Body:** captured (may show truncated preview in draft summary)
- Missing fields should now be minimal

### Step 8 — Enter signature

Type:

```
Signed by J. Q. Sample, Commanding Officer.
```

**Expected observation:**
- **Signature Name:** `J. Q. Sample`
- **Signature Role:** may be inferred or set based on mediator output
- Missing required fields should now show "All required fields present"

### Step 9 — Set window envelope

Type:

```
No window envelope.
```

**Expected observation:**
- **Window Envelope:** `False` or `(not set)` depending on mediator extraction
- This is an optional field; draft may still be viable without it

---

## Review Stage

### Check the Draft Summary (right column)

Verify all fields:
- Document Type: `standard_letter`
- From: `Commanding Officer, Example Command`
- To: `Commander, Example Group`
- Subject: `Training Plan`
- SSIC: `5216`
- Body: present (may be truncated)
- Signature Name: `J. Q. Sample`
- Window Envelope: set or not set

### Check Missing Fields

If all required fields are present, you should see:
- **All required fields present** (green)
- Recommended fields may still be listed if applicable

### Check Validation Panel

Look at the three metric cards:
- **Errors:** should be 0 (or low)
- **Warnings:** may be non-zero (formatting advisories)
- **Advisories:** may be non-zero

If **Warnings** are pending:
- The message "Warnings are pending — accept them before finalizing" appears
- The **⚠️ Accept Warnings** button is enabled
- Click it before finalizing

---

## Finalize

Once all required fields are present and warnings are accepted (if any):

1. Check that **Finalize allowed** shows **Yes**
2. Click **✅ Finalize**
3. Expected result:
   - Message: "Finalized successfully!"
   - **Finalized** status in payload becomes `True`
   - **🖨️ Render PDF** button becomes enabled

If finalize is blocked:
- Read the error message in the validation panel
- Address the stated reason (missing fields, unresolved errors, etc.)
- Re-check after providing the missing data

---

## Render PDF

1. Click **🖨️ Render PDF**
2. Expected result:
   - PDF is generated via `src/pdf_v6_render.py`
   - Info message shows PDF size (e.g., "PDF rendered (1665 bytes)")
   - A **⬇️ Download PDF** button appears
3. Click **Download PDF** to save the file locally
4. The PDF is a real SECNAV-compliant standard letter

**Important:** Generated PDFs are saved to the `output/` folder temporarily. They are **not** committed to git and should be cleaned up after review.

---

## Reset / New Letter

To start a completely new letter without restarting the app:

1. Click **🔄 New Letter** in the sidebar
2. Expected result:
   - Session state resets
   - Draft summary clears
   - Conversation history clears
   - All fields revert to initial values (doc_type, component.service)
3. You may begin a new intake from Step 2

---

## Provider Behavior

### Default (Mock)
- Label: `mock (default — no network)`
- No API key needed
- No network calls
- Fully deterministic, safe for demonstrations

### Optional Live (Manual Only)
- OpenAI: requires `OPENAI_API_KEY` and `SECNAV_LLM_PROVIDER=openai`
- Ollama: requires local server and `SECNAV_LLM_PROVIDER=ollama`
- Both are strictly opt-in; the app will show **unavailable** if misconfigured
- **Never** displays API key values in the UI

---

## Troubleshooting

### "Streamlit is not installed"
```powershell
pip install streamlit
```
Re-run the launch command.

### Port already in use
```powershell
streamlit run app_streamlit_llm_guided_intake.py --server.port 8502
```
Visit `http://localhost:8502` instead.

### PDF render unavailable
- Check that `src/pdf_v6_render.py` exists
- Ensure Python environment has required PDF dependencies (reportlab, etc.)
- The app will show a warning instead of crashing
- Render failure does not affect intake or validation

### Validation prevents finalize
- Read the validation panel carefully
- Fill all **required** fields shown in red
- Accept any **warnings** using the **⚠️ Accept Warnings** button
- Retry finalize

### Provider unavailable / fail-closed
- If you set an unsupported provider, the app shows "unavailable"
- Switch back to mock by unsetting provider env vars:
  ```powershell
  $env:SECNAV_LLM_PROVIDER=$null
  ```
- Restart the app

---

## Expected Full Demo Duration

- Steps 1–9 (intake): 2–3 minutes
- Review + warnings acceptance: 30 seconds
- Finalize: instant
- Render + download: 5–10 seconds
- Total: ~5 minutes

---

## Verification Checklist

After completing the demo, verify:

- [ ] App opened without errors
- [ ] Provider showed mock/default — no API key visible
- [ ] All 8 demo fields were captured in draft summary
- [ ] Missing required fields reached zero
- [ ] Validation panel was visible and accurate
- [ ] Warnings (if any) were accepted before finalize
- [ ] Finalize succeeded
- [ ] Render PDF produced a downloadable file
- [ ] New Letter reset worked cleanly
- [ ] No generated PDFs or logs were accidentally committed

---

## Cleanup Reminder

Any PDFs downloaded during the demo are saved to the `output/` directory. They are not tracked by git. Delete them after review if desired:

```powershell
Remove-Item output/*.pdf, output/*.log, output/*.json
```

Do not commit generated PDFs or logs.
