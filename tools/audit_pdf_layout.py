#!/usr/bin/env python3
"""
PDF Layout Audit Tool for SECNAV Compliance Testing

This tool performs automated layout checks on generated PDFs against 
figure-based layout profiles, focusing on text positioning validation.
"""

import argparse
import json
import re
import sys
from typing import Dict, List, Tuple, Any

try:
    import fitz  # PyMuPDF
    PDF_LIB = "fitz"
except ImportError:
    try:
        import pdfplumber
        PDF_LIB = "pdfplumber"
    except ImportError:
        PDF_LIB = None


def extract_text_positions_fitz(pdf_path: str) -> List[Dict]:
    """
    Extract text positions using PyMuPDF (fitz).
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        List of dictionaries containing text and position information
    """
    text_spans = []
    
    with fitz.open(pdf_path) as doc:
        for page_num in range(len(doc)):
            page = doc[page_num]
            blocks = page.get_text("dict")
            
            for block in blocks["blocks"]:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text_spans.append({
                                "page": page_num + 1,
                                "text": span["text"],
                                "x0": span["bbox"][0],
                                "y0": span["bbox"][1],
                                "x1": span["bbox"][2],
                                "y1": span["bbox"][3]
                            })
    
    return text_spans


def extract_text_positions_pdfplumber(pdf_path: str) -> List[Dict]:
    """
    Extract text positions using pdfplumber.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        List of dictionaries containing text and position information
    """
    text_spans = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            texts = page.extract_words(extra_attrs=["bbox"])
            for text_obj in texts:
                text_spans.append({
                    "page": page_num + 1,
                    "text": text_obj["text"],
                    "x0": text_obj["x0"],
                    "y0": text_obj["top"],
                    "x1": text_obj["x1"],
                    "y1": text_obj["bottom"]
                })
    
    return text_spans


def extract_text_positions(pdf_path: str) -> List[Dict]:
    """
    Extract text positions using the available PDF library.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        List of dictionaries containing text and position information
        
    Raises:
        ImportError: If no suitable PDF library is available
        FileNotFoundError: If the PDF file doesn't exist
    """
    if PDF_LIB == "fitz":
        return extract_text_positions_fitz(pdf_path)
    elif PDF_LIB == "pdfplumber":
        return extract_text_positions_pdfplumber(pdf_path)
    else:
        raise ImportError(
            "No suitable PDF library found. Please install either PyMuPDF (fitz) "
            "or pdfplumber."
        )


def load_profile(profile_path: str) -> Dict:
    """
    Load layout profile from JSON file.
    
    Args:
        profile_path: Path to the profile JSON file
        
    Returns:
        Dictionary containing profile data
    """
    with open(profile_path, 'r') as f:
        return json.load(f)


def check_required_text(spans: List[Dict], required_texts: List[str]) -> Tuple[List[str], List[str]]:
    """
    Check if all required texts are present.
    
    Args:
        spans: List of text spans with positions
        required_texts: List of required text strings
        
    Returns:
        Tuple of (passed_checks, failed_checks)
    """
    found_texts = {span['text'].strip() for span in spans}
    passed = []
    failed = []
    
    for text in required_texts:
        if text in found_texts:
            passed.append(f"Required text '{text}' found")
        else:
            failed.append(f"Required text '{text}' missing")
            
    return passed, failed


def check_optional_text(spans: List[Dict], optional_texts: List[str]) -> List[str]:
    """
    Identify which optional texts are present.
    
    Args:
        spans: List of text spans with positions
        optional_texts: List of optional text strings
        
    Returns:
        List of found optional texts
    """
    found_texts = {span['text'].strip() for span in spans}
    found = []
    
    for text in optional_texts:
        if text in found_texts:
            found.append(f"Optional text '{text}' found")
            
    return found


def get_text_positions(spans: List[Dict], text: str) -> List[Dict]:
    """
    Get all positions for a specific text.
    
    Args:
        spans: List of text spans with positions
        text: Text to search for
        
    Returns:
        List of spans matching the text
    """
    return [span for span in spans if span['text'].strip() == text]


def check_vertical_order(spans: List[Dict], order_rules: List[List[str]], 
                        y_tolerance: float) -> Tuple[List[str], List[str]]:
    """
    Check if texts appear in correct vertical order.
    
    Args:
        spans: List of text spans with positions
        order_rules: List of [before, after] text pairs
        y_tolerance: Vertical tolerance in points
        
    Returns:
        Tuple of (passed_checks, failed_checks)
    """
    passed = []
    failed = []
    
    for before_text, after_text in order_rules:
        before_spans = get_text_positions(spans, before_text)
        after_spans = get_text_positions(spans, after_text)
        
        if not before_spans:
            failed.append(f"Cannot check order: '{before_text}' not found")
            continue
            
        if not after_spans:
            failed.append(f"Cannot check order: '{after_text}' not found")
            continue
            
        # Use the first occurrence of each text
        before_y = before_spans[0]['y0']
        after_y = after_spans[0]['y0']
        
        # In PDF coordinates, lower y values are higher on the page
        if before_y < after_y - y_tolerance:
            passed.append(f"Vertical order correct: '{before_text}' before '{after_text}'")
        else:
            failed.append(f"Vertical order incorrect: '{before_text}' should be before '{after_text}'")
            
    return passed, failed


def check_alignment_continuation_markers(spans: List[Dict], rules: List[Dict], 
                                       x_tolerance: float) -> Tuple[List[str], List[str], List[str]]:
    """
    Check alignment of continuation markers.
    
    Args:
        spans: List of text spans with positions
        rules: Alignment rules from profile
        x_tolerance: Horizontal tolerance in points
        
    Returns:
        Tuple of (passed_checks, failed_checks, warnings)
    """
    passed = []
    failed = []
    warnings = []
    
    for rule in rules:
        name = rule['name']
        regex = rule['marker_regex']
        tolerance = rule['tolerance_pt']
        
        pattern = re.compile(regex)
        matching_spans = [span for span in spans if pattern.match(span['text'].strip())]
        
        if len(matching_spans) < 2:
            if len(matching_spans) == 1:
                warnings.append(f"Only one {name} marker found, cannot check alignment")
            continue
            
        # Check if all markers align within tolerance
        first_x = matching_spans[0]['x0']
        aligned = True
        
        for span in matching_spans[1:]:
            if abs(span['x0'] - first_x) > tolerance:
                aligned = False
                break
                
        if aligned:
            passed.append(f"All {name} markers aligned within {tolerance}pt tolerance")
        else:
            failed.append(f"{name} markers not properly aligned")
            
    return passed, failed, warnings


def check_unique_labels(spans: List[Dict], labels: List[str]) -> Tuple[List[str], List[str]]:
    """
    Check that labels appear only once.
    
    Args:
        spans: List of text spans with positions
        labels: List of labels to check
        
    Returns:
        Tuple of (passed_checks, failed_checks)
    """
    passed = []
    failed = []
    
    for label in labels:
        matching_spans = get_text_positions(spans, label)
        count = len(matching_spans)
        
        if count == 0:
            # Label not present, which is fine
            continue
        elif count == 1:
            passed.append(f"Label '{label}' appears exactly once")
        else:
            failed.append(f"Label '{label}' appears {count} times (should be unique)")
            
    return passed, failed


def audit_pdf_layout(profile_path: str, pdf_path: str) -> Dict:
    """
    Perform layout audit on PDF using the specified profile.
    
    Args:
        profile_path: Path to the layout profile JSON
        pdf_path: Path to the PDF file to audit
        
    Returns:
        Dictionary with audit results
    """
    # Load profile
    profile = load_profile(profile_path)
    
    # Extract text positions
    try:
        spans = extract_text_positions(pdf_path)
    except FileNotFoundError:
        return {
            "error": f"PDF file not found: {pdf_path}",
            "profile": profile_path,
            "pdf": pdf_path
        }
    except ImportError as e:
        return {
            "error": str(e),
            "profile": profile_path,
            "pdf": pdf_path
        }
    
    # Initialize results
    results = {
        "profile": profile_path,
        "pdf": pdf_path,
        "passed": [],
        "failed": [],
        "warnings": [],
        "key_positions": []
    }
    
    # Get tolerances
    x_tolerance = profile.get("spacing_tolerances", {}).get("x_tolerance_pt", 3)
    y_tolerance = profile.get("spacing_tolerances", {}).get("y_tolerance_pt", 4)
    
    # Check required text
    passed, failed = check_required_text(spans, profile["required_text"])
    results["passed"].extend(passed)
    results["failed"].extend(failed)
    
    # Check optional text
    optional_found = check_optional_text(spans, profile["optional_text"])
    results["warnings"].extend(optional_found)
    
    # Check vertical order
    passed, failed = check_vertical_order(spans, profile["order_rules"], y_tolerance)
    results["passed"].extend(passed)
    results["failed"].extend(failed)
    
    # Check unique labels for Ref and Encl if they exist
    ref_spans = get_text_positions(spans, "Ref:")
    encl_spans = get_text_positions(spans, "Encl:")
    
    if ref_spans:
        passed, failed = check_unique_labels(spans, ["Ref:"])
        results["passed"].extend(passed)
        results["failed"].extend(failed)
        
    if encl_spans:
        passed, failed = check_unique_labels(spans, ["Encl:"])
        results["passed"].extend(passed)
        results["failed"].extend(failed)
    
    # Check alignment of continuation markers
    passed, failed, warnings = check_alignment_continuation_markers(
        spans, profile.get("alignment_rules", []), x_tolerance)
    results["passed"].extend(passed)
    results["failed"].extend(failed)
    results["warnings"].extend(warnings)
    
    # Extract key positions for reporting
    key_texts = profile["required_text"] + profile["optional_text"]
    for text in key_texts:
        positions = get_text_positions(spans, text)
        for pos in positions:
            results["key_positions"].append({
                "text": text,
                "page": pos["page"],
                "x0": pos["x0"],
                "y0": pos["y0"],
                "x1": pos["x1"],
                "y1": pos["y1"]
            })
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Audit PDF layout against figure-based profile")
    parser.add_argument("--profile", required=True, help="Path to layout profile JSON")
    parser.add_argument("--pdf", required=True, help="Path to PDF to audit")
    
    args = parser.parse_args()
    
    results = audit_pdf_layout(args.profile, args.pdf)
    
    # Print results as JSON
    print(json.dumps(results, indent=2))
    
    # Return exit code based on results
    if "error" in results:
        return 1
    elif results["failed"]:
        return 2  # Failed checks
    else:
        return 0  # All passed


if __name__ == "__main__":
    sys.exit(main())