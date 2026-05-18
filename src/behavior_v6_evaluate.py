#!/usr/bin/env python
"""
v6 Behavior Rule Evaluator
Evaluate behavior rules against normalized letter model.
"""

import json
import os
import sys


# Import the loader module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from rules_v6_loader import load_lookup_tables, load_csv_rules
from letter_model_v6 import normalize_payload


def evaluate_condition(condition, field_name, value):
    """Evaluate a simple condition against a value."""
    if condition.endswith("==0"):
        return value == 0
    elif condition.endswith(">0"):
        return value > 0
    elif "==" in condition:
        parts = condition.rsplit("==", 1)
        if len(parts) == 2:
            field_name, val = parts[0].strip(), parts[1].strip()
            return value == int(val) if val.isdigit() else value == val
    elif ">" in condition:
        parts = condition.rsplit(">", 1)
        if len(parts) == 2:
            field_name, val = parts[0].strip(), parts[1].strip()
            return value > int(val) if val.isdigit() else value > val
    return False


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
    
    # Set page_number = 1 (as specified)
    normalized["page_number"] = 1
    
    # Evaluate each behavior rule
    print("=== BEHAVIOR RULE EVALUATION ===")
    
    for rule in behavior_rules:
        rule_id = rule.get("id", "")
        condition = rule.get("condition", "")
        action = rule.get("action", "")
        target = rule.get("target", "")
        
        # Determine field name from condition
        if condition == "via_count==0":
            field_name, matched = "via_count", normalized.get("via_count", 0) == 0
        elif condition == "ref_count>0":
            field_name, matched = "ref_count", normalized.get("ref_count", 0) > 0
        elif condition == "encl_count>0":
            field_name, matched = "encl_count", normalized.get("encl_count", 0) > 0
        elif condition == "page_number>1":
            field_name, matched = "page_number", normalized.get("page_number", 1) > 1
        elif "==" in condition:
            field_name = condition.split("==")[0].strip()
            parts = condition.rsplit("==", 1)
            val = parts[1].strip()
            matched = normalized.get(field_name, 0) == int(val) if val.isdigit() else normalized.get(field_name, "") == val
        elif ">" in condition:
            field_name = condition.split(">")[0].strip()
            parts = condition.rsplit(">", 1)
            val = parts[1].strip()
            matched = normalized.get(field_name, 0) > int(val) if val.isdigit() else normalized.get(field_name, "") > val
        else:
            matched = False
        
        status = "MATCH" if matched else "SKIP"
        print(f"{rule_id} {condition} -> {status} {action} {target}")


if __name__ == "__main__":
    main()
