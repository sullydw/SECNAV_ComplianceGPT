#!/usr/bin/env python
"""
v6 Rules Runtime Exporter
Export authoring CSV rules to JSONL in runtime folder.
"""

import csv
import json
import os
import sys


# Import the loader module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from rules_v6_loader import load_lookup_tables, load_csv_rules


def main():
    # Paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    rules_dir = os.path.join(base_dir, "rules_v6")
    authoring_dir = os.path.join(rules_dir, "authoring")
    runtime_dir = os.path.join(rules_dir, "runtime")
    
    # Create runtime folder if missing
    if not os.path.exists(runtime_dir):
        os.makedirs(runtime_dir)
    
    # Define CSV files
    csv_files = [
        (os.path.join(authoring_dir, "source_rules.csv"), "source_rules.jsonl"),
        (os.path.join(authoring_dir, "layout_rules.csv"), "layout_rules.jsonl"),
        (os.path.join(authoring_dir, "behavior_rules.csv"), "behavior_rules.jsonl"),
        (os.path.join(authoring_dir, "marker_rules.csv"), "marker_rules.jsonl"),
        (os.path.join(authoring_dir, "body_rules.csv"), "body_rules.jsonl"),
        (os.path.join(authoring_dir, "letterhead_rules.csv"), "letterhead_rules.jsonl")
    ]
    
    for csv_path, jsonl_path in csv_files:
        if not os.path.exists(csv_path):
            print(f"Missing: {csv_path}")
            continue
        
        # Load CSV rules
        rules = load_csv_rules(csv_path)
        
        # Write to JSONL
        jsonl_path_full = os.path.join(runtime_dir, jsonl_path)
        with open(jsonl_path_full, "w", encoding="utf-8") as f:
            for rule in rules:
                f.write(json.dumps(rule, ensure_ascii=False) + "\n")
        
        count = len(rules)
        if csv_path.endswith('source_rules.csv'):
            print(f"Exported source_rules: {count}")
        elif csv_path.endswith('layout_rules.csv'):
            print(f"Exported layout_rules: {count}")
        elif csv_path.endswith('behavior_rules.csv'):
            print(f"Exported behavior_rules: {count}")
        elif csv_path.endswith('marker_rules.csv'):
            print(f"Exported marker_rules: {count}")
        elif csv_path.endswith('body_rules.csv'):
            print(f"Exported body_rules: {count}")
        elif csv_path.endswith('letterhead_rules.csv'):
            print(f"Exported letterhead_rules: {count}")


if __name__ == "__main__":
    main()
