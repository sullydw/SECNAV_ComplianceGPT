#!/usr/bin/env python
"""
v6 Render Plan Builder (Text Version)
Build ordered render plan for letter pages based on behavior rules.
"""

import json
import os
import sys


# Import the loader module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from rules_v6_loader import load_lookup_tables, load_csv_rules
from letter_model_v6 import normalize_payload


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
    
    # Load behavior rules
    behavior_rules_path = os.path.join(authoring_dir, "behavior_rules.csv")
    behavior_rules = load_csv_rules(behavior_rules_path)
    
    # Set page_number = 1 (first page, no continuation)
    normalized["page_number"] = 1
    
    # Build render plan following exact base order
    # Behavior rules only remove sections, never reorder
    
    render_plan = []
    
    # Always include these sections in fixed order
    fixed_order = ["SEC_LTRHEAD", "SEC_SSIC", "SEC_FROM", "SEC_TO", "SEC_VIA", "SEC_SUBJ", "SEC_REF", "SEC_ENCL", "SEC_BODY", "SEC_SIG", "SEC_COPY"]
    
    # Check each section in order and add if should be included
    for section in fixed_order:
        if section == "SEC_VIA" and normalized.get("via_count", 0) == 0:
            continue
        elif section == "SEC_REF" and normalized.get("ref_count", 0) == 0:
            continue
        elif section == "SEC_ENCL" and normalized.get("encl_count", 0) == 0:
            continue
        else:
            render_plan.append(section)
    
    # Print render plan
    print("=== RENDER PLAN ===")
    for i, section in enumerate(render_plan, 1):
        print(f"{i}. {section}")


if __name__ == "__main__":
    main()
