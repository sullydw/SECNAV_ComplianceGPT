# Rule Catalog Plan - SECNAV M-5216.5

**Purpose:** Define how SECNAV M-5216.5 rules will be cataloged and implemented in SECNAV ComplianceGPT.

---

## 1. Catalog Order

Rules will be cataloged in the order they appear in the manual:

1. **Chapter 2** — Writing/procedure
2. **Chapter 7** — Standard letters
3. **Chapter 8** — Distribution
4. **Chapter 9** — Endorsements
5. **Chapter 10** — Memorandums
6. **Chapter 11** — Business letters

---

## 2. Rule Categories

| Category | Description |
|----------|-------------|
| `format` | Layout, spacing, font, positioning, visual structure |
| `content` | Required/forbidden text, phrasing, data fields |
| `cross_field` | Rules spanning multiple fields or sections |
| `procedural` | Process steps, sequencing, workflow requirements |
| `advisory` | Recommendations, best practices, non-mandatory guidance |

---

## 3. Rule Entry Schema

Each rule entry must contain:

| Field | Type | Description |
|-------|------|-------------|
| `rule_id` | string | Unique identifier (e.g., `C2-R001`, `C7-R015`) |
| `manual_section` | string | Source section (e.g., `2.1.3`, `7.4.2`) |
| `source_text` | string | Exact quote from the manual (required) |
| `plain_language_rule` | string | Normalized, unambiguous rule statement |
| `category` | enum | One of: `format`, `content`, `cross_field`, `procedural`, `advisory` |
| `enforceable` | boolean | `true` if rule can be validated programmatically |
| `severity` | enum | `error`, `warning`, or `advisory` |
| `target_fields` | array | Document fields this rule applies to |
| `validator_type` | string | Validator implementation type (if applicable) |
| `status` | enum | `candidate`, `reviewed`, or `active` |

---

## 4. Workflow

```
1. Extract rule from manual
   ↓
2. Normalize into plain language
   ↓
3. Assign category and fields
   ↓
4. Review for accuracy
   ↓
5. Mark as candidate
   ↓
6. Create audit test
   ↓
7. Implement validator
   ↓
8. Promote to active
```

---

## 5. Governing Rules

1. **No rule is implemented until reviewed.** All rules must pass review before promotion to `active` status.

2. **Manual source must always be preserved.** The `source_text` field (exact quote from SECNAV M-5216.5) is mandatory for every rule entry and must never be modified or paraphrased.

---

## 6. File Locations

- **Rule definitions:** `rules_v6/` (organized by chapter: `C2-*.json`, `C7-*.json`, etc.)
- **Audit tests:** `examples/audit_*.json`
- **Validators:** `src/` (named by rule series: `validator_c2_*.py`, etc.)
- **Documentation:** `docs/RULE_CATALOG_PLAN.md` (this file)

---

**Version:** 1.0  
**Created:** 2026-05-07
