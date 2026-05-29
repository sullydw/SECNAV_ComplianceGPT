# Correspondence Intelligence Layer Plan

## Purpose

The current v0.1.0-c7-c10-baseline proves that the renderer, layout profiles, regression scripts, README, requirements file, and GitHub Actions workflow are stable for the implemented Chapter 7 through Chapter 10 scope.

The next phase should not primarily change layout. It should add a context-aware correspondence intelligence layer that helps transform user intent into compliant SECNAV M-5216.5 correspondence before the renderer receives final JSON.

This layer must account for:

- universal correspondence standards from Chapters 2 through 5;
- format-specific rules from Chapters 7 through 10;
- rules embedded inside figure text, captions, example body paragraphs, labels, notes, and callouts;
- Navy, Marine Corps, joint, and other Department of the Navy context differences;
- deterministic validation where rules are objective;
- AI-assisted drafting and human-review warnings where the manual requires judgment.

## Core Architecture Principle

The AI should help draft, ask questions, normalize input, and propose correspondence structure. The rule layer should decide what is allowed. Deterministic validators should prove hard rules before rendering. The renderer should remain focused on producing compliant PDF layout from already-compliant structured data.

Recommended flow:

```text
User intent
  -> intake and missing-information questions
  -> context classification
  -> AI content plan
  -> structured draft JSON
  -> deterministic content/header validators
  -> AI revision if validator findings are fixable
  -> human-review warnings for judgment calls
  -> PDF renderer
  -> layout audit/regression
```

## Source Scope for the Inventory

### Universal correspondence rules

Primary source area: Chapters 2 through 5.

These rules apply before choosing a specific correspondence format. They govern whether correspondence should be written, how it should be written, what identifying information is required, and what warnings must be raised.

Important areas include:

- correspondence quality, grammar, technical correctness, and proofreading;
- use of clear, concise, plain English;
- gender-neutral language and avoidance of stereotyping;
- whether correspondence is necessary or whether conversation, telephone, e-mail, or memorandum would be more appropriate;
- point of contact, return telephone number, and e-mail address when a reply or inquiry may result;
- correspondence through channels;
- chain-of-command use and exceptions;
- signature authority and delegated signature authority;
- electronic signature handling;
- outgoing and incoming correspondence controls;
- congressional, FOIA, and Privacy Act response considerations;
- Social Security Number and PII limitations;
- identification of Navy and Marine Corps personnel;
- letterhead stationery restrictions;
- enclosure handling, marking, and separate cover handling;
- copy distribution and need-to-know limitations;
- military time formatting;
- date formatting;
- abbreviation and acronym handling;
- typeface rules;
- e-mail formal correspondence rules;
- e-mail security, privacy, encryption, and recordkeeping warnings;
- fax/security/privacy/PII warnings.

### Format-specific correspondence rules

Primary source area: Chapters 7 through 10.

These rules apply after correspondence type is known.

Important areas include:

- standard letters;
- window-envelope letters;
- joint letters;
- classified correspondence markings;
- FOUO/CUI-related markings;
- multiple-address letters;
- endorsements;
- memorandums for the record;
- From-To memorandums;
- plain-paper memorandums;
- letterhead memorandums;
- decision memorandums;
- memoranda of agreement and understanding.

### Figure-embedded rules

The inventory must inspect figure text as a first-class source. In SECNAV M-5216.5, figures are not merely illustrations. They often include operational rules inside example text, labels, captions, callouts, and notes.

The rule miner and planning process must examine:

- Figure 7-1 through Figure 7-10;
- Figure 8-1 through Figure 8-4;
- Figure 9-1 through Figure 9-3;
- Figure 10-1 through Figure 10-7;
- later chapter figures if the project scope expands.

Figure-derived rules should be tagged distinctly so future validators can explain whether a rule came from narrative text or figure text.

Suggested metadata:

```json
{
  "source_type": "figure_text",
  "source_chapter": "7",
  "source_figure": "Figure 7-4",
  "rule_kind": "joint_letter_signature_order",
  "enforcement": "deterministic_or_review_flag"
}
```

## Context Model

The intelligence layer should classify each correspondence request using a context object before drafting or validating content.

Recommended fields:

```json
{
  "component": "navy | marine_corps | joint | don_secretariat | unknown",
  "origin_activity_type": "ship | squadron | shore_activity | headquarters | marine_unit | joint_activity | unknown",
  "correspondence_type": "standard_letter | multiple_address_letter | endorsement | memorandum_for_record | from_to_memo | joint_letter | other",
  "classification_context": "unclassified | fouo_cui | classified | unknown",
  "routing_context": {
    "requires_chain_of_command": null,
    "via_required": null,
    "dirlauth_or_direct_liaison": null,
    "tv5_tasker": null
  },
  "audience_context": "internal_command | dod | navy | marine_corps | congress | civilian_agency | business | individual | nato | unknown",
  "response_context": {
    "reply_expected": null,
    "deadline_required": null,
    "controlled_correspondence": null
  },
  "records_privacy_context": {
    "contains_pii": null,
    "contains_ssn": null,
    "foia_privacy_act": null,
    "classified_or_sensitive": null
  }
}
```

Unknown fields should trigger questions or review flags rather than silent assumptions.

## Navy, Marine Corps, and Joint Context

The layer must treat Navy and Marine Corps differences as first-class rule inputs.

### Navy-specific areas

- SNDL-based activity names and addresses.
- SNDL short titles for From, To, Copy to, and reference construction.
- Navy personnel identification format, including abbreviated rank/rate, warfare designator where applicable, branch of service, DoD ID or justified SSN substitute, and officer designator when applicable.
- Navy unit/activity address source handling.
- Navy forms, instructions, messages, notices, and publication reference formats.

### Marine Corps-specific areas

- Marine Corps directives and letterhead/addressing rules where the manual points to Marine Corps directives.
- Marine Corps personnel identification format using unabbreviated grade, name, DoD ID or justified SSN substitute, MOS, and branch of service.
- Marine Corps unit hierarchy and routing logic.
- NAVMC 10274 / Administrative Action form issue for individuals writing to higher authority on personal command-related matters.
- MCO-specific reference handling when applicable.

### Joint-letter areas

- Multiple originating commands.
- Senior command ordering in letterhead.
- Joint sender-symbol blocks.
- Multiple From entries.
- Signature placement with senior official on the right.
- Third cosigner placement in the middle.
- Last signer sends copies to all cosigners.

## Header Intelligence

Header intelligence is broader than physical header layout. It decides what the header should contain and whether the content is compliant.

### Letterhead

Needs to determine:

- whether letterhead is authorized;
- whether command letterhead is appropriate for the matter;
- whether a command/activity is represented in the required activity source;
- whether Navy or Marine Corps addressing rules apply;
- whether the activity name/address should come from SNDL, Marine Corps source, DoDAAD, or other local data.

Hard validators:

- command letterhead should not include an individual name;
- command letterhead should be used only for official command matters;
- letterhead address should avoid prohibited punctuation/abbreviation patterns where applicable.

Review flags:

- source of authoritative activity address is uncertain;
- user-provided command title or address may not match authoritative source;
- board/committee use of letterhead requires confirmation.

### SSIC and sender symbols

Needs to determine:

- best SSIC based on subject/body;
- whether originator code is required or locally determined;
- whether serial number is required due to classification or local practice;
- date format for sender symbol block;
- whether classification/FOUO marking affects sender symbol or serial handling.

Hard validators:

- SSIC exists and is numeric with appropriate length;
- classified correspondence must have a serial number;
- date in sender symbol area uses abbreviated military date format;
- no unauthorized writer/typist identification symbols in final outgoing correspondence.

Review flags:

- SSIC selection is low confidence;
- local serial/originator-code practice is unknown;
- classification context is unknown.

### From line

Needs to determine:

- activity head title;
- activity name;
- whether location is needed to distinguish activity;
- joint-letter multiple From entries;
- board/committee title handling.

Hard validators:

- command letterhead From line should contain activity head title and command/activity name;
- From line should not contain an individual name when using command letterhead;
- avoid multiple titles unless the selected title matches the letter content.

Review flags:

- selected title may not match subject matter;
- location may be needed to distinguish similar activities;
- user supplied an individual name in From line.

### To line

Needs to determine:

- action addressee;
- activity head title;
- office code or person title in parentheses when known;
- whether Code prefix is needed before numeric office code;
- whether individual name should be avoided;
- whether full mailing address is needed for record/window-envelope purposes.

Hard validators:

- To line should address the activity head rather than an individual when possible;
- numeric office codes should use Code before the number;
- office codes beginning with letters should not be prefixed with Code.

Review flags:

- action addressee may not be the correct official;
- individual name used despite turnover/misrouting concern;
- full mailing address included without clear need.

### Via line

Needs to determine:

- whether chain of command or cognizant office routing is required;
- whether routine direct correspondence is authorized;
- whether intermediate commands should be Via or Copy to;
- whether multiple Via addressees are in routing order;
- whether TV-5 Taskers or equivalent routing means suppresses Via.

Hard validators:

- two or more Via addressees must be numbered;
- Via numbering should start at (1) and be consecutive;
- if only one remaining Via addressee in an endorsement, do not number it;
- if multiple remaining Via addressees in an endorsement, number from (1).

Review flags:

- chain-of-command path uncertain;
- user wants to bypass intermediate commands;
- DIRLAUTH/direct liaison or urgent deadline exception needs confirmation;
- TV-5/Taskers context needs confirmation.

### Subject line

Needs to determine:

- clear sentence fragment;
- normal word order;
- all letters capitalized after the colon in standard letter subject line;
- no acronyms in correspondence subject lines unless later project rules permit a narrow exception;
- whether reply repeats the incoming subject unless clarity requires change.

Hard validators:

- subject present when required;
- subject is all caps where required;
- subject has no terminal punctuation unless required by special context;
- prohibited acronyms detected in subject;
- duplicate Subj label removed if user included it inside the field.

Review flags:

- subject is vague;
- subject may not match body purpose;
- reply subject changed without stated reason.

### References

Needs to determine:

- whether references are necessary;
- whether listed references bear directly on the subject;
- order references by first body mention;
- cite references in the body;
- choose correct reference format by type;
- avoid NOTAL where possible;
- handle reference copies to Via or Copy to addressees.

Hard validators:

- references listed with lowercase markers in sequence;
- single reference still uses marker (a);
- body cites every listed reference;
- no duplicate reference markers;
- endorsement added references continue sequence and do not repeat earlier references;
- no item appears both as reference and enclosure in same letter.

Review flags:

- reference appears unnecessary;
- reference may not bear directly on subject;
- NOTAL reference used;
- user lacks complete reference metadata.

### Enclosures

Needs to determine:

- whether enclosure is appropriate rather than reference;
- list enclosures in order of body appearance;
- whether external document should be reference rather than enclosure;
- whether sep cover is required;
- distribution variations for Copy to or Via addressees.

Hard validators:

- enclosures listed with numeric markers in sequence;
- single enclosure still uses marker (1);
- body mentions every listed enclosure;
- no duplicate enclosure markers;
- endorsement added enclosures continue sequence and do not repeat earlier enclosures;
- same item not listed as reference and enclosure.

Review flags:

- enclosure may be too bulky;
- enclosure source may be external to the DON organization;
- sep cover likely but not specified;
- enclosure distribution variation affects only some addressees and needs explicit notation.

### Copy to and Distribution

Needs to determine:

- need-to-know for Copy to;
- whether multiple action addressees require To-only, Distribution-only, or To-plus-Distribution format;
- whether more than four action addressees require Distribution;
- whether copy counts vary;
- whether copy/enclosure variations are required;
- endorsement significant/routine copy-to propagation.

Hard validators:

- four or fewer action addressees may use To-only;
- more than four action addressees should use Distribution;
- Distribution-only omits To line;
- To-plus-Distribution uses group title in To and individual members in Distribution;
- significant endorsement copy-to list includes originator and prior endorsers as required by current C9 rules.

Review flags:

- Copy to list seems broad or just-in-case;
- need-to-know is not stated;
- action addressee vs information addressee role unclear.

## Body and Content Intelligence

### Plain language and tone

The AI should draft in clear, concise, respectful official-military language. It should avoid slang, jargon, unnecessary adjectives, and unnecessarily complicated wording.

Hard validators:

- none for tone beyond simple pattern checks.

Review flags:

- possible slang/jargon;
- excessively long sentence;
- vague action request;
- unsupported assertion;
- overly casual tone.

### Acronyms and abbreviations

Hard validators:

- acronym used in body before being spelled out with parenthetical acronym;
- acronym introduced once but not used consistently afterward;
- acronym appears in prohibited field such as subject where rules prohibit it;
- known allowed abbreviations list honored.

Review flags:

- acronym appears common but was not defined;
- directive or highly formal writing may require every abbreviation/acronym to be identified.

### Dates and time

Hard validators:

- military time is four digits from 0000 through 2359 with no colon;
- standard text date for military correspondence uses day month year, no leading zero for single-digit day;
- sender symbol date uses abbreviated format;
- civilian correspondence date uses month day, year;
- congressional response opening line uses civilian-style date reference.

Review flags:

- audience context unclear, so correct date format is uncertain;
- deadline date may be unrealistic.

### Personnel identification

Hard validators:

- Navy personnel identification uses Navy-specific order when the user provides enough fields;
- Marine Corps personnel identification uses Marine Corps-specific order when the user provides enough fields;
- Sailor, Marine, and Service Member are capitalized when referring to U.S. Navy or U.S. Marine Corps members;
- last names are not all caps except subject and signature lines.

Review flags:

- missing EDIPI/DoD ID, designator, MOS, or branch;
- SSN or last-four usage requires justification and privacy review;
- user appears to mix Navy and Marine Corps identification conventions.

### Paragraph structure

Hard validators:

- main paragraphs start with Arabic numerals;
- subparagraph sequence is valid;
- if a subdivision exists, at least two entries exist at that level;
- continuation lines return to left margin;
- no subdivision exceeds allowed level from Figure 7-8;
- paragraph citations use compact form without periods or spaces, such as 2b(4)(a).

Review flags:

- document subdivides too deeply when simpler structure is possible;
- paragraph headings are inconsistent across peer paragraphs;
- long correspondence may benefit from headings.

### Point of contact

Hard validators:

- if correspondence indicates reply, action, or inquiry expected and no POC block/paragraph is present, flag or fail depending on policy.

Review flags:

- correspondence might prompt reply but user did not provide phone/e-mail;
- POC included but missing return telephone number or e-mail.

### Records, privacy, classification, and transmission warnings

Hard validators:

- if user explicitly marks material as classified, FOUO/CUI, PII, SSN, e-mail, or fax, required warning checks must run;
- SSN pattern detected should trigger privacy review warning;
- e-mail formal correspondence should include SSIC, serial/date where required, letterhead identification, and signature authority;
- PII by e-mail/fax requires need-to-know and security/privacy warning.

Review flags:

- possible PII detected;
- classified/sensitive handling uncertain;
- FOIA/Privacy Act context present;
- recordkeeping disposition is relevant.

## Deterministic Validator Categories

Recommended new validator groups:

1. `content_subject_validate.py`
   - subject capitalization;
   - acronym prohibition;
   - punctuation;
   - duplicate label cleanup;
   - reply-subject consistency warning.

2. `content_ref_encl_validate.py`
   - reference order;
   - body citation presence;
   - enclosure order;
   - body mention presence;
   - duplicate ref/encl item detection;
   - sep cover notation.

3. `content_acronym_validate.py`
   - first-use expansion;
   - prohibited fields;
   - approved abbreviations;
   - formal-writing strictness mode.

4. `content_date_time_validate.py`
   - military time;
   - standard date;
   - abbreviated sender-symbol date;
   - civilian date;
   - audience-specific date validation.

5. `content_personnel_validate.py`
   - Navy personnel identification pattern;
   - Marine Corps personnel identification pattern;
   - capitalization of Sailor/Marine/Service Member;
   - last-name capitalization warning;
   - SSN/EDIPI warning.

6. `content_routing_validate.py`
   - Via requirement review flags;
   - Via numbering;
   - chain-of-command path consistency;
   - Copy to versus Via role distinction;
   - DIRLAUTH/direct-liaison exceptions.

7. `content_privacy_security_validate.py`
   - SSN/PII detection;
   - classified/FOUO/CUI review flags;
   - e-mail/fax transmission warnings;
   - congressional/FOIA/Privacy Act response warnings.

8. `correspondence_context.py`
   - normalize component, audience, type, routing, security, and records context;
   - provide one context object to validators and AI prompt layer.

## Rule Catalog Recommendations

Add a new rule namespace separate from the layout-only rule files.

Recommended path:

```text
rules_v6/CCI/
```

CCI means Correspondence Content Intelligence.

Suggested files:

```text
rules_v6/CCI/cci_ch2_standards.json
rules_v6/CCI/cci_ch3_records.json
rules_v6/CCI/cci_ch4_email.json
rules_v6/CCI/cci_ch5_fax.json
rules_v6/CCI/cci_ch7_standard_letter_content.json
rules_v6/CCI/cci_ch8_multiple_address_content.json
rules_v6/CCI/cci_ch9_endorsement_content.json
rules_v6/CCI/cci_ch10_memorandum_content.json
rules_v6/CCI/cci_figure_embedded_rules.json
rules_v6/CCI/cci_context_schema.json
```

Each rule should classify enforcement level:

```json
{
  "rule_id": "CCI-CH7-SUBJ-001",
  "source": "SECNAV M-5216.5",
  "source_location": "Chapter 7, paragraph 7-2.9 and Figure 7-1",
  "source_type": "narrative_and_figure_text",
  "applies_to": ["standard_letter", "multiple_address_letter", "endorsement", "memorandum_when_subject_used"],
  "component_scope": ["navy", "marine_corps", "joint", "don_secretariat"],
  "rule_text_summary": "Subject line uses normal word order, all letters capitalized after the colon, and no acronyms in correspondence subject lines.",
  "enforcement": "deterministic",
  "validator": "content_subject_validate.py",
  "severity": "error"
}
```

Recommended enforcement levels:

- `deterministic`: can be checked reliably by code;
- `heuristic_warning`: can be detected but may need user confirmation;
- `ai_review`: requires AI judgment and explanation;
- `human_review`: must be confirmed by the user or command/admin staff;
- `out_of_scope`: known but intentionally not implemented yet.

## AI Prompt and Orchestration Role

The AI should not directly bypass validators. It should operate in a constrained role.

AI responsibilities:

- ask for missing From/To/Via/context information;
- identify likely correspondence type;
- identify Navy, Marine Corps, joint, civilian, congressional, NATO, or other audience context;
- propose subject line;
- propose SSIC when uncertain, with confidence and rationale;
- draft plain-English body content;
- propose references and enclosures;
- explain which references/enclosures must be mentioned in body;
- propose Copy to/Distribution logic;
- respond to deterministic validator findings by revising content;
- escalate uncertainty to the user instead of guessing.

AI must not silently decide:

- classified/FOUO/CUI status;
- SSN/PII acceptability;
- whether a Via addressee has official cognizance;
- whether a Copy to addressee has a genuine need to know;
- whether a reference truly bears directly on the subject;
- whether local command serial/originator-code practice applies;
- whether a user has delegated signature authority.

## Existing Repo Support to Reuse

Current useful foundations:

- stable PDF renderer and layout validators;
- existing C7 through C10 validators;
- existing regression scripts;
- `context_resolver.py` for routing/unit lookup concepts;
- `ssic_resolver.py` concept for SSIC inference;
- `rules_v6` catalog structure;
- GitHub Actions workflow for regression protection;
- checkpoint docs for layout confidence.

The new layer should extend, not replace, these foundations.

## Smallest Safe First Implementation Task

The first implementation task should be narrow and deterministic.

Recommended first task:

```text
Create CCI subject-line rule catalog and validator.
```

Scope:

- add `rules_v6/CCI/cci_ch7_subject_rules.json`;
- add `src/content_subject_validate.py`;
- validate subject is present when required;
- validate standard-letter subject is all caps after the label;
- warn or fail on unapproved acronyms in subject;
- strip or detect duplicated `Subj:` label inside user input;
- add fixtures for pass/fail cases;
- add a dedicated regression script such as `tools/run_cci_subject_regression.py`;
- do not touch renderer layout.

Why first:

- the rule is clear;
- it is visible to users;
- it is easy to test;
- it exercises the new architecture without destabilizing the layout baseline.

## Later Implementation Sequence

1. Subject-line compliance.
2. Reference/enclosure body mention and duplicate detection.
3. Acronym first-use validation in body text.
4. Date/time validation with audience context.
5. Navy vs Marine personnel identification validation.
6. Context schema and intake-question generation.
7. Via/Copy to/Distribution role warnings.
8. Privacy/security/classification warning layer.
9. AI drafting prompt contract and validator-revision loop.
10. Figure-embedded rule miner or manual figure-rule catalog expansion.

## Guardrails for Hermes or Other Local Agents

When implementing this phase:

- start from `v0.1.0-c7-c10-baseline` or current `origin/main` after verifying clean state;
- do not edit renderer layout unless a new task explicitly requires it;
- add one validator group at a time;
- add regression tests before expanding scope;
- keep rule catalogs source-cited and explainable;
- tag figure-derived rules separately;
- run existing C7, C8, C9, and C10 regressions after every implementation;
- verify GitHub Actions remains green before moving to the next rule group.

## Open Questions

- Should CCI validators block generation on errors, or allow generation with a prominent audit report?
- Should the AI ask all missing context questions up front, or use progressive prompts?
- How strict should acronym detection be for common military terms?
- Which external sources should be integrated first: SNDL, Marine Corps command/address source, DoDAAD, SSIC manual, or local lookup tables?
- Should the first CCI implementation use JSON-only fixtures, or also render PDFs after content validation passes?
- Should privacy/security checks block generation or require explicit user acknowledgment?
