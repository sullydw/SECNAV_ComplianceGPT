#!/usr/bin/env python
"""
v6 Letter Model Normalizer
Normalize payloads to standard v6 letter model format.
"""

import json
import os


def normalize_payload(payload):
    """Normalize a letter payload to v6 model format."""
    
    # Ensure optional list fields exist
    for field in ["via", "ref", "encl", "copy_to"]:
        if field not in payload:
            payload[field] = []
        elif not isinstance(payload[field], list):
            payload[field] = [payload[field]]
    
    # Convert body to list if string
    if "body" in payload and isinstance(payload["body"], str):
        payload["body"] = [payload["body"]]
    
    # Add derived fields
    payload["has_via"] = bool(payload.get("via", []))
    payload["has_ref"] = bool(payload.get("ref", []))
    payload["has_encl"] = bool(payload.get("encl", []))
    payload["has_copy_to"] = bool(payload.get("copy_to", []))
    payload["via_count"] = len(payload.get("via", []))
    payload["ref_count"] = len(payload.get("ref", []))
    payload["encl_count"] = len(payload.get("encl", []))
    payload["body_count"] = len(payload.get("body", []))
    
    return payload


def main():
    # Paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    sample_path = os.path.join(base_dir, "examples", "v6_sample_letter.json")
    
    if not os.path.exists(sample_path):
        print(f"Missing: {sample_path}")
        return
    
    # Load sample payload
    with open(sample_path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    
    # Normalize
    normalized = normalize_payload(payload)
    
    # Print results
    print("=== NORMALIZED LETTER MODEL ===")
    print(json.dumps(normalized, indent=2))


if __name__ == "__main__":
    main()
