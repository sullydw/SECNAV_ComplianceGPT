#!/usr/bin/env python
"""
v6 Payload Validator
Validate sample letter payloads against v6 schema requirements.
"""

import json
import os


def main():
    # Paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    sample_path = os.path.join(base_dir, "examples", "v6_sample_letter.json")
    
    if not os.path.exists(sample_path):
        print(f"Missing: {sample_path}")
        return
    
    # Load payload
    with open(sample_path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    
    # Required fields
    required_fields = ["doc_type", "date", "from", "to", "subj", "body", "signature"]
    
    errors = []
    
    # Check required fields
    for field in required_fields:
        if field not in payload:
            errors.append(f"Missing required field: {field}")
    
    # Validate body is a list with at least 1 item
    if "body" in payload:
        body = payload["body"]
        if not isinstance(body, list):
            errors.append("body must be a list")
        elif len(body) < 1:
            errors.append("body must have at least 1 item")
    
    # via/ref/encl/copy_to if present must be lists
    optional_list_fields = ["via", "ref", "encl", "copy_to"]
    for field in optional_list_fields:
        if field in payload:
            if not isinstance(payload[field], list):
                errors.append(f"{field} must be a list if present")
    
    # Print results
    print("=== PAYLOAD VALIDATION ===")
    if errors:
        for err in errors:
            print(f"FAIL: {err}")
    else:
        print("PASS")


if __name__ == "__main__":
    main()
