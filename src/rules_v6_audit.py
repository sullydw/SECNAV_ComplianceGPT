#!/usr/bin/env python
"""
v6 Rules Audit Script
--------------------
Audit all v6 rules against lookup_tables.json.
"""

import csv
import json
import os
import sys


def load_lookup_tables(lookup_path):
    with open(lookup_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def load_csv_rules(csv_path):
    rows = []
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def is_valid_enabled(val):
    return val in ["true", "false", "True", "False"]


def audit_rules(lookup, rules_list, csv_path):
    errors = []
    total = len(rules_list)
    
    rule_types = lookup.get("rule_types", {})
    sections = lookup.get("sections", {})
    actions = lookup.get("actions", {})
    status_codes = lookup.get("status", {})
    sources = lookup.get("sources", {})
    
    for row in rules_list:
        # Check 1: Non-empty id, type, status
        for field in ["id", "type", "status"]:
            val = row.get(field, "")
            if not val:
                errors.append(f"{csv_path}: Missing or empty {field} in row {row.get('id', '?')}")
                break
        else:
            # Check enabled (required)
            enabled = row.get("enabled", "")
            if not is_valid_enabled(enabled):
                errors.append(f"{csv_path}: Invalid enabled value '{enabled}' in row {row.get('id', '?')}")
        
        # Check 2: type code exists in rule_types (ignore 'SRC' for source_rules)
        if row.get("type") and row.get("type") != "SRC":
            type_val = row.get("type", "")
            if type_val not in rule_types:
                errors.append(f"{csv_path}: Invalid type code '{type_val}' in row {row.get('id', '?')}")
        
        # Check 3: section code exists (ignore blank)
        sec = row.get("sec", "")
        if sec and sec not in sections:
            errors.append(f"{csv_path}: Invalid section code '{sec}' in row {row.get('id', '?')}")
        
        # Check 4: action code exists (ignore blank)
        act = row.get("action", "")
        if act and act not in actions:
            errors.append(f"{csv_path}: Invalid action code '{act}' in row {row.get('id', '?')}")
        
        # Check 5: status code exists
        stat = row.get("status", "")
        if stat and stat not in status_codes:
            errors.append(f"{csv_path}: Invalid status code '{stat}' in row {row.get('id', '?')}")
        
        # Check 6: source code exists (ignore blank)
        src = row.get("source", "")
        if src and src not in sources:
            errors.append(f"{csv_path}: Invalid source code '{src}' in row {row.get('id', '?')}")
    
    return total, len(errors), errors


def main():
    # Paths relative to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    rules_dir = os.path.join(base_dir, "rules_v6")
    authoring_dir = os.path.join(rules_dir, "authoring")
    
    lookup_path = os.path.join(rules_dir, "lookup_tables.json")
    
    source_rules_path = os.path.join(authoring_dir, "source_rules.csv")
    layout_rules_path = os.path.join(authoring_dir, "layout_rules.csv")
    behavior_rules_path = os.path.join(authoring_dir, "behavior_rules.csv")
    marker_rules_path = os.path.join(authoring_dir, "marker_rules.csv")
    body_rules_path = os.path.join(authoring_dir, "body_rules.csv")
    letterhead_rules_path = os.path.join(authoring_dir, "letterhead_rules.csv")
    
    # Load lookup tables
    if not os.path.exists(lookup_path):
        print(f"Missing: {lookup_path}")
        sys.exit(1)
    lookup = load_lookup_tables(lookup_path)
    
    # Load and audit each CSV
    csv_files = [
        (source_rules_path, "source_rules"),
        (layout_rules_path, "layout_rules"),
        (behavior_rules_path, "behavior_rules"),
        (marker_rules_path, "marker_rules"),
        (body_rules_path, "body_rules"),
        (letterhead_rules_path, "letterhead_rules")
    ]
    
    all_rules = []
    all_errors = []
    all_warnings = []
    total_rules = 0
    error_count = 0
    
    for path, name in csv_files:
        if not os.path.exists(path):
            print(f"Missing: {path}")
            continue
        rules = load_csv_rules(path)
        all_rules.extend(rules)
        rules_total, err_count, errors = audit_rules(lookup, rules, path)
        total_rules += rules_total
        error_count += err_count
        all_errors.extend(errors)
    
    print("=== RULE AUDIT REPORT ===")
    print(f"Total rules checked: {total_rules}")
    print(f"Errors found: {error_count}")
    print(f"Warnings: 0")
    
    if error_count == 0:
        print("PASS")
    else:
        for err in all_errors:
            print(err)


if __name__ == "__main__":
    main()
