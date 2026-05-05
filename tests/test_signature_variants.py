#!/usr/bin/env python
"""
Test script for signature variant rendering.
Builds PDFs for all signature forms to verify correct rendering.
"""

import json
import os
import sys
import shutil

# Add src to path
script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(script_dir)
sys.path.insert(0, os.path.join(base_dir, "src"))

from pdf_v6_render import main as render_pdf

# Test cases for each signature variant
TEST_CASES = [
    {
        "name": "legacy_string",
        "signature": "DARRYL SULLIVAN",
        "description": "Legacy string signature (backward compatibility)"
    },
    {
        "name": "standard_structured",
        "signature": {
            "name": "DARRYL SULLIVAN",
            "title": None,
            "authority": None
        },
        "description": "Standard structured signature (name only)"
    },
    {
        "name": "by_direction",
        "signature": {
            "name": "DARRYL SULLIVAN",
            "title": None,
            "authority": "By direction"
        },
        "description": "By direction authority"
    },
    {
        "name": "acting",
        "signature": {
            "name": "DARRYL SULLIVAN",
            "title": None,
            "authority": "Acting"
        },
        "description": "Acting authority"
    },
    {
        "name": "title_based",
        "signature": {
            "name": "DARRYL SULLIVAN",
            "title": "Deputy",
            "authority": None
        },
        "description": "Title-based signature"
    },
    {
        "name": "title_plus_authority",
        "signature": {
            "name": "DARRYL SULLIVAN",
            "title": "Executive Officer",
            "authority": "By direction"
        },
        "description": "Title plus authority"
    }
]

def load_base_payload():
    """Load the base sample letter JSON."""
    sample_path = os.path.join(base_dir, "examples", "v6_sample_letter.json")
    with open(sample_path, "r", encoding="utf-8") as f:
        return json.load(f)

def run_test(test_case):
    """Run a single signature variant test."""
    print(f"\n{'='*60}")
    print(f"TEST: {test_case['name']}")
    print(f"Description: {test_case['description']}")
    print(f"Signature: {test_case['signature']}")
    print(f"{'='*60}")
    
    # Load base payload
    payload = load_base_payload()
    
    # Override signature
    payload["signature"] = test_case["signature"]
    
    # Create output path
    output_dir = os.path.join(base_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    
    # Temporarily modify the sample file
    sample_path = os.path.join(base_dir, "examples", "v6_sample_letter.json")
    backup_path = sample_path + ".bak"
    
    # Backup original
    shutil.copy(sample_path, backup_path)
    
    try:
        # Write test payload
        with open(sample_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        
        # Run renderer
        render_pdf()
        
        # Check output exists
        source_pdf = os.path.join(output_dir, "v6_test_letter.pdf")
        test_output = os.path.join(output_dir, f"v6_test_{test_case['name']}.pdf")
        
        if os.path.exists(source_pdf):
            # Copy to test-specific name
            shutil.copy(source_pdf, test_output)
            print(f"[PASS] PDF created at {test_output}")
            return True
        else:
            print(f"[FAIL] PDF not created")
            return False
            
    except Exception as e:
        print(f"[FAIL] {e}")
        return False
    finally:
        # Restore original
        shutil.copy(backup_path, sample_path)
        os.remove(backup_path)

def main():
    """Run all signature variant tests."""
    print("Signature Variant Test Suite")
    print("="*60)
    
    results = {}
    for test_case in TEST_CASES:
        results[test_case["name"]] = run_test(test_case)
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    all_passed = True
    for name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status}: {name}")
        if not passed:
            all_passed = False
    
    print(f"\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
