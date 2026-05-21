# PDF Layout Audit C7 Prototype

## Overview

This is a prototype automated PDF layout audit that extracts text positions from generated PDFs and compares them against figure-derived layout expectations. Currently focused on SECNAV M-5216.5 Figure 7-1 (Standard Letter, First Page) as a proof of concept.

## Purpose

The prototype serves to:
1. Validate that generated PDFs conform to required layout specifications
2. Automatically check positioning of key header elements
3. Verify proper vertical ordering of document components
4. Demonstrate feasibility of programmatic layout compliance checking

## Approach

This prototype uses rule/profile-based validation rather than pixel-image comparison:
- Text extraction libraries parse PDF content and positions
- Layout profiles define expected elements and relationships
- Tolerance-based comparisons account for rendering variations
- Structured output enables automation and integration

## Key Features

### Text Position Extraction
- Uses PyMuPDF (fitz) when available, falling back to pdfplumber
- Extracts text spans with precise bounding box coordinates
- Maintains page number association for multi-page documents

### Profile-Based Validation
- JSON profiles define required and optional text elements
- Configurable order relationships between elements
- Alignment rules for continuation markers
- Tolerance settings for flexible comparisons

### Coarse Layout Checks
Currently implements validation for:
- Presence of required text labels ("From:", "To:", "Subj:", "1.")
- Recognition of optional labels ("Via:", "Ref:", "Encl:") when present
- Proper vertical ordering (From → To → Subj → Body)
- Unique appearance of Ref and Encl labels when used
- Alignment of continuation markers within tolerance
- Proper spacing relationships using configurable tolerances

## Important Limitations

⚠️ **THIS IS A PROTOTYPE, NOT A REPLACEMENT FOR MANUAL VISUAL REVIEW**

### Scope Limitations
- Currently supports only Figure 7-1 Standard Letter first page
- Focuses on coarse layout rules, not detailed typography
- Does not validate font selections, sizes, or styling
- Does not check exact positioning against absolute coordinates

### Technical Limitations
- Rule-based comparison, not pixel-perfect visual verification
- Dependent on PDF text extraction quality
- May not handle complex layouts or rotated text well
- Tolerance settings may need adjustment for different renderers

## Design Philosophy

### Rule-Based Over Visual Comparison
Manual figures contain instructional dots, percent signs, captions, and artifacts, making raw screenshot comparison intentionally avoided. Instead:
- Profiles codify layout rules and relationships
- Focus on semantic content positioning
- Enable precise validation without visual reference images
- Support automation and regression testing

### Tolerance-Based Validation
Rather than exact pixel matching:
- X tolerance: 3 points
- Y tolerance: 4 points
- Accounts for rendering variations between systems
- Allows for minor positioning differences that don't affect compliance

## Future Expansion

Planned profile additions for:
- Figure 7-2 (Standard Letter, Continuation Page)
- Figure 8-1/8-2/8-3 (Memorandum)
- Figure 9-2 (Official Mail Request)
- Figure 10-1 (Naval Message Format)
- Figure 10-3 (Special Type Message Examples)

## Usage

```bash
python tools/audit_pdf_layout.py --profile docs/layout_profiles/figure_7_1_standard_letter.json --pdf output/audit_c7_phase1_standard_letter.pdf
```

## Integration Status

This prototype is not yet integrated with the regression testing framework. It operates as a standalone tool for experimentation and validation.

## Dependencies

Requires one of:
- PyMuPDF (fitz) - preferred
- pdfplumber - fallback option

Will report appropriate error messages if neither is available.