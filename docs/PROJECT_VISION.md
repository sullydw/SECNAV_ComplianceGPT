# SECNAV ComplianceGPT - Project Vision

**Purpose:** Generate SECNAV M-5216.5 compliant military correspondence

---

## System Philosophy

The system is designed to automate the creation of official military correspondence while ensuring strict compliance with SECNAV M-5216.5 standards.

Key principles:

- **Compliance First:** All output must adhere to SECNAV M-5216.5 formatting rules
- **Automation:** Reduce manual effort in constructing formal correspondence
- **Accessibility:** Make military correspondence standards accessible to all users
- **Accuracy:** Eliminate formatting errors through automated rule enforcement

---

## Interaction Model

The system is chat-driven and interactive, not form-based.

Users are not required to provide fully structured or complete inputs. The system must:

- Interpret partial or informal user input
- Resolve known entities (e.g., units, commands, abbreviations)
- Expand shorthand into proper official correspondence format

Example:
If a user says "send a request to MALS-11," the system should:
- Recognize MALS-11 as a unit
- Resolve it to its full official designation
- Populate the correct "To:" line format

The system must reduce the need for the user to manually construct formal elements of correspondence.

---

## Context Awareness

The system must apply contextual understanding to correspondence generation.

This includes:

- Recognizing unit relationships and organizational structure
- Understanding chains of command (e.g., Squadron → MAG → Wing)
- Suggesting required routing elements such as "Via" when appropriate
- Prompting the user when standard correspondence elements may be missing

Example:
If a user specifies a recipient unit but omits routing, the system should ask:
"Do you need to route this via the MAG?"

The system should guide the user toward correct structure without requiring prior knowledge of the rules.

---

## Writing Style Standard

All generated correspondence must follow the United States Marine Corps Staff Writing Guide.

This includes:

- Clear, concise, and direct language
- Proper tone and professionalism
- Correct formatting of military correspondence language

The system should not generate generic or overly verbose text.
Writing style must reflect official military communication standards.

---

## Technical Goals

- Maintain a single authoritative PDF renderer (`src/pdf_v6_render.py`)
- Use font-size-aware spacing calculations for scalability
- Centralize layout control through `BOUNDARY_SPACINGS` dict
- Support role-based signature blocks per SECNAV standards
- Handle pagination with proper continuation headers

---

## Compliance Reference

**Primary Source:** SECNAV M-5216.5 (April 2023)

**Key Chapters:**
- Chapter 2: Format and Preparation
- Chapter 7: Signature Blocks

**Rule System:** All formatting rules stored in `rules_v6/` with provenance tracking

---

**Last Updated:** 2026-05-06  
**GitHub:** https://github.com/sullydw/SECNAV_ComplianceGPT
