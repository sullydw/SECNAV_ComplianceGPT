#!/usr/bin/env python
"""
v6 Layout Resolver
Resolve layout rules into a dictionary of layout values.
"""

import os
import sys


# Import the loader module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from rules_v6_loader import load_csv_rules


def main():
    # Paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    rules_dir = os.path.join(base_dir, "rules_v6")
    authoring_dir = os.path.join(rules_dir, "authoring")
    
    # Load layout rules
    layout_rules_path = os.path.join(authoring_dir, "layout_rules.csv")
    layout_rules = load_csv_rules(layout_rules_path)
    
    # Resolve layout values
    layout_dict = {}
    
    for rule in layout_rules:
        target = rule.get("target", "")
        notes = rule.get("notes", "")
        
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
    
    # Print resolution
    print("=== LAYOUT RESOLUTION ===")
    for key, value in sorted(layout_dict.items()):
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
