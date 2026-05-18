#!/usr/bin/env python
"""
v6 Pre-Render Audit Report
Generate audit report before rendering.
"""

import json
import os
import sys


# Import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from rules_v6_loader import load_csv_rules
from letter_model_v6 import normalize_payload
from render_plan_v6 import main as get_render_plan
from layout_v6_resolve import main as get_layout_resolution
from body_v6_validate import validate_body


def main():
    # Paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    sample_path = os.path.join(base_dir, "examples", "v6_sample_letter.json")
    rules_dir = os.path.join(base_dir, "rules_v6")
    authoring_dir = os.path.join(rules_dir, "authoring")
    
    if not os.path.exists(sample_path):
        print(f"Missing: {sample_path}")
        return
    
    # Load sample payload
    with open(sample_path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    
    # Normalize
    normalized = normalize_payload(payload)
    
    # Load layout rules
    layout_rules_path = os.path.join(authoring_dir, "layout_rules.csv")
    layout_rules = load_csv_rules(layout_rules_path)
    
    # Build render plan
    fixed_order = ["SEC_LTRHEAD", "SEC_SSIC", "SEC_FROM", "SEC_TO", "SEC_VIA", "SEC_SUBJ", "SEC_REF", "SEC_ENCL", "SEC_BODY", "SEC_SIG", "SEC_COPY"]
    render_plan = []
    for section in fixed_order:
        if section == "SEC_VIA" and normalized.get("via_count", 0) == 0:
            continue
        elif section == "SEC_REF" and normalized.get("ref_count", 0) == 0:
            continue
        elif section == "SEC_ENCL" and normalized.get("encl_count", 0) == 0:
            continue
        else:
            render_plan.append(section)
    
    # Build layout dict
    layout_dict = {}
    for rule in layout_rules:
        target = rule.get("target", "")
        if target == "left_margin_in":
            layout_dict["left_margin_in"] = 1.0
            layout_dict["left_margin_pt"] = 72.0
        elif target == "right_margin_in":
            layout_dict["right_margin_in"] = 1.0
            layout_dict["right_margin_pt"] = 72.0
        elif target == "top_margin_in":
            layout_dict["top_margin_in"] = 0.625
            layout_dict["top_margin_pt"] = 45.0
        elif target == "bottom_margin_in":
            layout_dict["bottom_margin_in"] = 1.0
            layout_dict["bottom_margin_pt"] = 72.0
        elif target == "line_spacing_single":
            layout_dict["line_spacing"] = "single"
        elif target == "one_blank_line":
            layout_dict["header_gap"] = "one_blank_line"
    
    # Validate body structure
    body_errors = validate_body(payload)
    
    # Print report
    print("=== PRE-RENDER AUDIT ===")
    print(f"DOCUMENT TYPE: {payload.get('doc_type', 'UNKNOWN')}")
    print()
    print("SECTION COUNTS:")
    print(f"via_count: {normalized.get('via_count', 0)}")
    print(f"ref_count: {normalized.get('ref_count', 0)}")
    print(f"encl_count: {normalized.get('encl_count', 0)}")
    print(f"body_count: {normalized.get('body_count', 0)}")
    print()
    print("BODY VALIDATION:")
    if body_errors:
        print("FAIL")
        for err in body_errors:
            print(f"<error>{err}</error>")
    else:
        print("PASS")
    print()
    print("RENDER PLAN:")
    for i, section in enumerate(render_plan, 1):
        print(f"{i}. {section}")
    print()
    print("LAYOUT:")
    for key, value in sorted(layout_dict.items()):
        print(f"{key}: {value}")
    print()
    if body_errors:
        print("RENDER READY: NO")
    else:
        print("RENDER READY: YES")


if __name__ == "__main__":
    main()
