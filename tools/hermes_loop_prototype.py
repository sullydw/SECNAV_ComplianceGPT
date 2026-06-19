#!/usr/bin/env python3
"""
Hermes Loop Prototype — Phase L.29O

Narrow deterministic prototype proving the real CLI can support the Hermes
question loop: start → ingest → detect-facts → select next question →
apply simulated answer → detect-facts again → render gate check.

Reuses existing code paths. No live lookup, no candidate creation, no render.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_TOOL_ROOT = Path(__file__).resolve().parent
_REPO_ROOT = _TOOL_ROOT.parent
_SRC_DIR = _REPO_ROOT / "src"

if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from conversational_builder import BuilderSession
from llm_builder_mediator import MediatorInput, create_mock_mediator
from unresolved_fact_detector import detect_unresolved_facts

# ---------------------------------------------------------------------------
# Scenario definitions
# ---------------------------------------------------------------------------

SCENARIOS: dict[str, dict[str, Any]] = {
    "standard_letter_minimal": {
        "doc_type": "standard_letter",
        "initial_text": (
            "I need a standard letter requesting to change the software release "
            "brief date to TBD. It is from MISSA to MCAS New River HQ BN."
        ),
        "simulated_answers": {
            "from": "from: Commanding Officer, Manpower Information Systems Support Agency (MISSA)",
            "to": "to: Commanding Officer, Headquarters Battalion, MCAS New River",
            "date": "date: 19 June 2026",
            "subj": "subj: REQUEST TO CHANGE SOFTWARE RELEASE BRIEF DATE",
            "body": "body: 1. This letter requests a change to the software release brief date. The new date is to be determined (TBD).",
            "signature": "signature.name: J. Q. Sample\nsignature.role: Commanding Officer\nsignature.title: Commanding Officer",
        },
    },
    "mfr_minimal": {
        "doc_type": "memorandum_for_record",
        "initial_text": (
            "I need a memorandum for record about a phone conversation "
            "yesterday concerning the training schedule."
        ),
        "simulated_answers": {
            "date": "date: 19 June 2026",
            "body": "body: 1. On 18 June 2026, a phone conversation was held with the Training Officer concerning the upcoming training schedule. 2. The schedule will be adjusted to accommodate the new requirements.",
        },
    },
    "endorsement_minimal": {
        "doc_type": "endorsement",
        "initial_text": (
            "I need an endorsement forwarding a request."
        ),
        "simulated_answers": {
            "subj": "subj: FORWARDING OF REQUEST",
            "basic_letter_id": "basic_letter_id: Ser HQBN 001/26",
            "endorsement_ordinal": "endorsement_ordinal: First Endorsement",
            "from": "from: Commanding Officer, Headquarters Battalion",
            "to": "to: Commanding Officer, Marine Corps Installations East",
            "body": "body: 1. Forwarded, recommending approval.",
            "signature": "signature.name: J. Q. Sample\nsignature.role: Commanding Officer\nsignature.title: Commanding Officer",
        },
    },
}

# ---------------------------------------------------------------------------
# Core loop
# ---------------------------------------------------------------------------


def _select_next_fact(facts: list[dict], exclude_fields: set[str] | None = None) -> dict | None:
    """Select the highest-priority unresolved fact.

    Priority order: blocking > recommended > optional.
    Within same priority, stable fact_id order.
    Excludes fields already attempted (in exclude_fields).
    """
    exclude = exclude_fields or set()

    blocking = [f for f in facts if f.get("priority") == "blocking" and f.get("field") not in exclude]
    recommended = [f for f in facts if f.get("priority") == "recommended" and f.get("field") not in exclude]
    optional = [f for f in facts if f.get("priority") == "optional" and f.get("field") not in exclude]

    candidates = blocking or recommended or optional
    if not candidates:
        return None

    # Sort by fact_id for stable ordering
    candidates.sort(key=lambda f: f.get("fact_id", ""))
    return candidates[0]


def _build_answer_kv(field: str, answer: str) -> str:
    """Build a key:value line for a simulated answer.

    For signature, the answer may already be multi-line KV.
    If the answer already starts with 'field:', pass it through directly.
    """
    if field == "signature" and "\n" in answer:
        return answer  # already formatted as signature.name: ... etc.
    # Check if answer already has the field prefix
    prefix = f"{field}:"
    if answer.strip().startswith(prefix):
        return answer.strip()
    return f"{field}: {answer}"


def _check_render_gate(
    unresolved: dict,
    validation_summary: dict,
) -> dict:
    """Check whether the render gate is open."""
    summary = unresolved.get("summary", {})
    blocking = summary.get("blocking", 0)
    recommended = summary.get("recommended", 0)
    optional = summary.get("optional", 0)

    errors = validation_summary.get("errors", 0)
    finalize_allowed = validation_summary.get("finalize_allowed", True)

    blocking_resolved = blocking == 0
    can_render = blocking_resolved and errors == 0 and finalize_allowed

    if not blocking_resolved:
        reason = f"{blocking} blocking fact(s) remain unresolved"
    elif errors > 0:
        reason = f"{errors} validation error(s) present"
    elif not finalize_allowed:
        reason = "finalize not allowed by validation gate"
    else:
        reason = "blocking facts resolved and validation has no blocking errors"

    return {
        "blocking_resolved": blocking_resolved,
        "recommended_remaining": recommended,
        "optional_remaining": optional,
        "validator_errors": errors,
        "can_render": can_render,
        "reason": reason,
    }


def run_loop(
    scenario_name: str,
    max_steps: int = 20,
    json_output: bool = False,
) -> dict[str, Any]:
    """Run the Hermes question loop for a given scenario.

    Returns a structured result dict.
    """
    scenario = SCENARIOS.get(scenario_name)
    if not scenario:
        return {"success": False, "error": f"Unknown scenario: {scenario_name}"}

    doc_type = scenario["doc_type"]
    initial_text = scenario["initial_text"]
    simulated_answers = scenario["simulated_answers"]

    steps: list[dict] = []
    applied_fields: set[str] = set()

    # --- Step 1: Start session ---
    builder = BuilderSession()
    builder.start()

    # --- Step 2: Ingest initial user text via mock mediator ---
    payload = builder.build_payload()
    inp = MediatorInput(
        session_id=builder._session_id,
        current_step="intake",
        payload_snapshot=payload,
        missing_required_fields=[],
        missing_recommended_fields=[],
        validation_summary={"errors": 0, "warnings": 0},
        warning_summary=[],
        error_summary=[],
        user_message=initial_text,
    )
    mediator = create_mock_mediator()
    out = mediator.mediate(inp)
    proposed_kv = out.get("proposed_key_value_lines", []) or []

    if proposed_kv:
        kv_text = "\n".join(proposed_kv)
        builder.ingest_user_message(kv_text)

    # --- Step 3: Run detect-facts ---
    payload = builder.build_payload()
    unresolved = detect_unresolved_facts(
        payload=payload,
        user_text=initial_text,
        doc_type=doc_type,
    )

    steps.append({
        "step": 0,
        "action": "ingest_initial",
        "doc_type": doc_type,
        "initial_text": initial_text,
        "proposed_kv": proposed_kv,
        "unresolved_summary": unresolved.get("summary", {}),
    })

    # --- Step 4+: Loop ---
    step_num = 0
    while step_num < max_steps:
        step_num += 1
        summary = unresolved.get("summary", {})
        blocking = summary.get("blocking", 0)

        if blocking == 0:
            break

        # Select highest-priority blocking fact
        facts = unresolved.get("facts", [])
        next_fact = _select_next_fact(facts, exclude_fields=applied_fields)

        if not next_fact:
            # No facts to resolve but blocking > 0 — shouldn't happen
            break

        field = next_fact.get("field", "")
        question = next_fact.get("question", "")
        fact_id = next_fact.get("fact_id", "")
        rule_id = next_fact.get("rule_id", "")
        source_file = next_fact.get("source_file", "")
        recommended_action = next_fact.get("recommended_action", "")
        priority = next_fact.get("priority", "")

        # Get simulated answer
        answer = simulated_answers.get(field)
        if not answer:
            # No simulated answer for this field — skip and mark
            steps.append({
                "step": step_num,
                "action": "skip_no_answer",
                "field": field,
                "fact_id": fact_id,
                "rule_id": rule_id,
                "source_file": source_file,
                "recommended_action": recommended_action,
                "priority": priority,
                "question": question,
                "reason": "no simulated answer available for this field",
            })
            # Remove this fact from consideration by marking field as "applied"
            # even though we didn't apply — prevents infinite loop
            applied_fields.add(field)
            # Re-run detect-facts to get updated summary
            payload = builder.build_payload()
            unresolved = detect_unresolved_facts(
                payload=payload,
                user_text=initial_text,
                doc_type=doc_type,
            )
            continue

        # Build KV line and apply
        kv_text = _build_answer_kv(field, answer)
        builder.ingest_user_message(kv_text)
        applied_fields.add(field)

        # Re-run detect-facts
        payload = builder.build_payload()
        unresolved = detect_unresolved_facts(
            payload=payload,
            user_text=initial_text,
            doc_type=doc_type,
        )

        new_summary = unresolved.get("summary", {})

        steps.append({
            "step": step_num,
            "action": "apply_simulated_answer",
            "field": field,
            "fact_id": fact_id,
            "rule_id": rule_id,
            "source_file": source_file,
            "recommended_action": recommended_action,
            "priority": priority,
            "question": question,
            "answer_kv": kv_text,
            "unresolved_summary_before": summary,
            "unresolved_summary_after": new_summary,
        })

    # --- Final: validation and render gate ---
    payload = builder.build_payload()
    validation_summary = builder.validation_summary()
    final_unresolved = detect_unresolved_facts(
        payload=payload,
        user_text=initial_text,
        doc_type=doc_type,
    )

    render_gate = _check_render_gate(final_unresolved, validation_summary)

    result = {
        "success": True,
        "scenario": scenario_name,
        "doc_type": doc_type,
        "session_id": builder._session_id,
        "total_steps": step_num,
        "max_steps": max_steps,
        "steps": steps,
        "final_payload": payload,
        "final_unresolved_summary": final_unresolved.get("summary", {}),
        "final_unresolved_facts": final_unresolved.get("facts", []),
        "validation_summary": validation_summary,
        "render_gate": render_gate,
        "applied_fields": sorted(applied_fields),
        "performed_live_lookup": False,
        "created_candidates": False,
    }

    if json_output:
        print(json.dumps(result, indent=2, default=str))

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Hermes Loop Prototype — Phase L.29O",
    )
    parser.add_argument(
        "--scenario",
        required=True,
        choices=list(SCENARIOS.keys()),
        help="Scenario to run",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=20,
        help="Maximum loop steps (default: 20)",
    )
    parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Output full result as JSON",
    )
    args = parser.parse_args()

    result = run_loop(
        scenario_name=args.scenario,
        max_steps=args.max_steps,
        json_output=args.json_output,
    )

    if not args.json_output:
        # Human-readable summary
        print(f"Scenario: {result['scenario']}")
        print(f"Doc type: {result['doc_type']}")
        print(f"Steps taken: {result['total_steps']}")
        print(f"Applied fields: {', '.join(result['applied_fields'])}")
        print()
        print("Render gate:")
        rg = result["render_gate"]
        print(f"  blocking_resolved: {rg['blocking_resolved']}")
        print(f"  recommended_remaining: {rg['recommended_remaining']}")
        print(f"  validator_errors: {rg['validator_errors']}")
        print(f"  can_render: {rg['can_render']}")
        print(f"  reason: {rg['reason']}")
        print()
        print("Step log:")
        for s in result["steps"]:
            if s["action"] == "ingest_initial":
                print(f"  Step {s['step']}: ingest initial text")
                print(f"    proposed_kv: {s.get('proposed_kv', [])}")
                print(f"    unresolved: blocking={s['unresolved_summary'].get('blocking', 0)}")
            elif s["action"] == "apply_simulated_answer":
                print(f"  Step {s['step']}: apply {s['field']} ({s['priority']})")
                print(f"    question: {s['question']}")
                print(f"    rule_id: {s['rule_id']}")
                print(f"    source_file: {s['source_file']}")
                print(f"    recommended_action: {s['recommended_action']}")
                print(f"    blocking: {s['unresolved_summary_before'].get('blocking', 0)} → {s['unresolved_summary_after'].get('blocking', 0)}")
            elif s["action"] == "skip_no_answer":
                print(f"  Step {s['step']}: SKIP {s['field']} — no simulated answer")
        print()
        if result["final_unresolved_facts"]:
            print("Remaining unresolved facts:")
            for f in result["final_unresolved_facts"]:
                print(f"  {f['fact_id']}: {f['field']} ({f['priority']}) — {f['question']}")
        else:
            print("No remaining unresolved facts.")
        print()
        print(f"Success: {result['success']}")


if __name__ == "__main__":
    main()
