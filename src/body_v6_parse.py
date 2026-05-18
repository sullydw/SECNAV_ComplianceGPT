#!/usr/bin/env python
"""
v6 Body Parser Prototype
Parse normalized payload body into structured paragraph records.
"""

import json
import os
import re
import sys


# Import the loader module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from letter_model_v6 import normalize_payload


def detect_marker_level(line):
    """Detect marker level and extract marker + text."""
    
    # Level 4: (a), (b), (c) - lowercase letters in parentheses
    match = re.match(r'^\(([a-z])\)\s*(.*)$', line)
    if match:
        return 4, f"({match.group(1)})", match.group(2)
    
    # Level 3: (1), (2), (3) - numbers in parentheses
    match = re.match(r'^\((\d+)\)\s*(.*)$', line)
    if match:
        return 3, f"({match.group(1)})", match.group(2)
    
    # Level 2: a., b., c. - lowercase letters with period
    match = re.match(r'^([a-z])\.\s*(.*)$', line)
    if match:
        return 2, f"{match.group(1)}.", match.group(2)
    
    # Level 1: 1., 2., 3. - numbers with period
    match = re.match(r'^(\d+)\.\s*(.*)$', line)
    if match:
        return 1, f"{match.group(1)}.", match.group(2)
    
    # No marker detected
    return None, "", line


def main():
    # Paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    
    # Accept optional file path argument
    if len(sys.argv) > 1:
        sample_path = os.path.join(base_dir, sys.argv[1])
    else:
        sample_path = os.path.join(base_dir, "examples", "v6_sample_letter.json")
    
    if not os.path.exists(sample_path):
        print(f"Missing: {sample_path}")
        return
    
    # Load sample payload
    with open(sample_path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    
    # Normalize
    normalized = normalize_payload(payload)
    
    # Parse body lines
    body_records = []
    for idx, line in enumerate(normalized.get("body", [])):
        level, marker, text = detect_marker_level(line)
        body_records.append({
            "raw": line,
            "level": level,
            "marker": marker,
            "text": text,
            "index": idx
        })
    
    # Print results
    print("=== BODY PARSE ===")
    print(json.dumps(body_records, indent=2))


if __name__ == "__main__":
    main()
