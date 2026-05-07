#!/usr/bin/env python
"""
Audit Case Runner
Run all audit JSON files in examples/ and generate PDFs for each.
Uses the production renderer from pdf_v6_render.py to ensure consistency.
"""

import json
import os
import glob
import shutil
import sys

# Add src to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(script_dir)


def run_audit_with_production_renderer(audit_json_path, output_pdf_path):
    """
    Run audit payload through the production renderer.
    
    Strategy:
    1. Backup original v6_sample_letter.json
    2. Copy audit JSON to v6_sample_letter.json
    3. Run pdf_v6_render.py (which reads v6_sample_letter.json)
    4. Move generated PDF to correct output location
    5. Restore original v6_sample_letter.json
    """
    
    sample_path = os.path.join(base_dir, "examples", "v6_sample_letter.json")
    temp_backup_path = os.path.join(base_dir, "examples", "v6_sample_letter.json.backup")
    output_dir = os.path.join(base_dir, "output")
    temp_pdf_path = os.path.join(output_dir, "v6_test_letter.pdf")
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Step 1: Backup original sample
        if os.path.exists(sample_path):
            shutil.copy2(sample_path, temp_backup_path)
        
        # Step 2: Copy audit JSON to sample location
        shutil.copy2(audit_json_path, sample_path)
        
        # Step 3: Run production renderer
        # Import and execute main() from pdf_v6_render.py
        import importlib.util
        spec = importlib.util.spec_from_file_location("pdf_v6_render", os.path.join(script_dir, "pdf_v6_render.py"))
        pdf_v6_render = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pdf_v6_render)
        
        # Call main() which reads v6_sample_letter.json and generates v6_test_letter.pdf
        pdf_v6_render.main()
        
        # Step 4: Move generated PDF to correct output location
        if os.path.exists(temp_pdf_path):
            shutil.move(temp_pdf_path, output_pdf_path)
            return True, f"Generated: {output_pdf_path}"
        else:
            return False, f"PDF not generated at {temp_pdf_path}"
    
    except Exception as e:
        return False, f"Error: {str(e)}"
    
    finally:
        # Step 5: Restore original sample (always runs, even on error)
        if os.path.exists(temp_backup_path):
            shutil.move(temp_backup_path, sample_path)
        # Clean up temp PDF if it exists
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)


def main():
    examples_dir = os.path.join(base_dir, "examples")
    output_dir = os.path.join(base_dir, "output")
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all audit JSON files
    audit_files = glob.glob(os.path.join(examples_dir, "audit_*.json"))
    
    if not audit_files:
        print("No audit files found matching examples/audit_*.json")
        return
    
    print(f"Found {len(audit_files)} audit file(s)")
    print("=" * 60)
    
    results = []
    for audit_file in sorted(audit_files):
        filename = os.path.basename(audit_file)
        filename_no_ext = os.path.splitext(filename)[0]
        output_pdf = os.path.join(output_dir, f"{filename_no_ext}.pdf")
        
        print(f"\nProcessing: {filename}")
        
        # Run through production renderer
        success, message = run_audit_with_production_renderer(audit_file, output_pdf)
        
        if success and os.path.exists(output_pdf):
            print(f"  PASS: {message}")
            results.append((f"{filename_no_ext}.pdf", "PASS", message))
        else:
            print(f"  FAIL: {message}")
            results.append((f"{filename_no_ext}.pdf", "FAIL", message))
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for pdf_filename, status, message in results:
        print(f"{pdf_filename}: {status}")
    
    passed = sum(1 for _, status, _ in results if status == "PASS")
    print(f"\nTotal: {passed}/{len(results)} passed")


if __name__ == "__main__":
    main()
