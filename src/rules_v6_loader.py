#!/usr/bin/env python
"""
v6 Rules Loader
---------------
Load all v6 rule files and return a consolidated dictionary.
"""

import csv
import json
import os


def load_lookup_tables(lookup_path):
    with open(lookup_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_csv_rules(csv_path):
    rows = []
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Validate required fields
            missing = [field for field in ["id", "type", "status", "enabled"] if field not in row or not row[field]]
            if missing:
                raise ValueError(f"Missing required fields in {csv_path}: {missing}")
            rows.append(row)
    return rows


def main():
    base = os.path.join(os.path.dirname(__file__), "..")
    rules_dir = os.path.join(base, "rules_v6")
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
        return
    lookup = load_lookup_tables(lookup_path)

    # Load CSV files
    def safe_load(path, name):
        if not os.path.exists(path):
            print(f"Missing: {path}")
            return []
        return load_csv_rules(path)

    source_rules = safe_load(source_rules_path, "source_rules.csv")
    layout_rules = safe_load(layout_rules_path, "layout_rules.csv")
    behavior_rules = safe_load(behavior_rules_path, "behavior_rules.csv")
    marker_rules = safe_load(marker_rules_path, "marker_rules.csv")
    body_rules = safe_load(body_rules_path, "body_rules.csv")
    letterhead_rules = safe_load(letterhead_rules_path, "letterhead_rules.csv")

    result = {
        "lookup": lookup,
        "source_rules": source_rules,
        "layout_rules": layout_rules,
        "behavior_rules": behavior_rules,
        "marker_rules": marker_rules,
        "body_rules": body_rules,
        "letterhead_rules": letterhead_rules
    }

    # Print summary
    print(f"Loaded source_rules: {len(source_rules)}")
    print(f"Loaded layout_rules: {len(layout_rules)}")
    print(f"Loaded behavior_rules: {len(behavior_rules)}")
    print(f"Loaded marker_rules: {len(marker_rules)}")
    print(f"Loaded body_rules: {len(body_rules)}")
    print(f"Loaded letterhead_rules: {len(letterhead_rules)}")


if __name__ == "__main__":
    main()
