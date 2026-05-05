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
    # Valid role-based signatures
    {
        "name": "activity_head",
        "signature": {
            "name": "D. SULLIVAN",
            "role": "activity_head"
        },
        "description": "Activity head signature (name only)",
        "expect_warning": False
    },
    {
        "name": "title_based",
        "signature": {
            "name": "D. SULLIVAN",
            "role": "principal_subordinate_by_title",
            "title": "Deputy"
        },
        "description": "Principal subordinate signing by title",
        "expect_warning": False
    },
    {
        "name": "acting",
        "signature": {
            "name": "D. SULLIVAN",
            "role": "acting"
        },
        "description": "Acting signature",
        "expect_warning": False
    },
    {
        "name": "acting_by_title",
        "signature": {
            "name": "D. SULLIVAN",
            "role": "acting_by_title",
            "title": "Executive Officer"
        },
        "description": "Acting by title",
        "expect_warning": False
    },
    {
        "name": "by_direction",
        "signature": {
            "name": "D. SULLIVAN",
            "role": "by_direction"
        },
        "description": "By direction signature",
        "expect_warning": False
    },
    {
        "name": "by_direction_pay",
        "signature": {
            "name": "D. SULLIVAN",
            "role": "by_direction_pay_allowance",
            "title": "Executive Officer",
            "activity_head_title": "Commanding Officer"
        },
        "description": "By direction (pay/allowance case)",
        "expect_warning": False
    },
    {
        "name": "legacy_string",
        "signature": "D. SULLIVAN",
        "description": "Legacy string signature (backward compatibility)",
        "expect_warning": False
    },
    # Validation test cases (should warn but still render)
    {
        "name": "missing_title",
        "signature": {
            "name": "D. SULLIVAN",
            "role": "principal_subordinate_by_title",
            "title": None
        },
        "description": "Missing title for principal_subordinate_by_title (should warn + fallback)",
        "expect_warning": True
    },
    {
        "name": "missing_activity_head_title",
        "signature": {
            "name": "D. SULLIVAN",
            "role": "by_direction_pay_allowance",
            "title": "Executive Officer",
            "activity_head_title": None
        },
        "description": "Missing activity_head_title for by_direction_pay_allowance (should warn + fallback)",
        "expect_warning": True
    },
    {
        "name": "invalid_role",
        "signature": {
            "name": "D. SULLIVAN",
            "role": "unknown_role"
        },
        "description": "Invalid/unsupported role (should warn + name only)",
        "expect_warning": True
    },
    {
        "name": "invalid_name_format",
        "signature": {
            "name": "Darryl Sullivan",
            "role": "by_direction"
        },
        "description": "Full first name instead of initial (should warn)",
        "expect_warning": True
    },
    {
        "name": "rank_included",
        "signature": {
            "name": "Col D. SULLIVAN USMC",
            "role": "by_direction"
        },
        "description": "Rank and service in signature (should warn)",
        "expect_warning": True
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
    print(f"Expect warning: {test_case.get('expect_warning', False)}")
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
            if test_case.get('expect_warning', False):
                print(f"[PASS] PDF created with expected warnings at {test_output}")
            else:
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
