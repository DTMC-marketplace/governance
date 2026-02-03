---
description: Map controls across multiple security frameworks (ISO 27001, SOC 2, NIST CSF, CIS).
argument-hint: <frameworks> [--scope <area>]
allowed-tools: Task, Skill
---

# Security Framework Mapping

Create a cross-framework control mapping for unified compliance.

## Workflow

### Step 1: Load Required Skills

Load the skill:

- `security-frameworks` - Framework requirements and mappings

### Step 2: Parse Frameworks

Parse the requested frameworks from: $ARGUMENTS

Supported frameworks:

- ISO 27001:2022
- SOC 2 (Trust Services Criteria)
- NIST CSF 2.0
- CIS Controls v8
- NIST 800-53
- COBIT

### Step 3: Spawn Security Auditor Agent

Spawn the `security-auditor` agent with the following prompt:

```text
Create a comprehensive control mapping across these frameworks: $ARGUMENTS

For each control area, provide:

1. Control Mapping Matrix
   - Map equivalent controls across frameworks
   - Identify gaps where frameworks differ
   - Note framework-specific requirements

2. Unified Control Set
   - Create consolidated control list
   - One control satisfying multiple frameworks
   - Highlight additional requirements per framework

3. Evidence Mapping
   - Common evidence types
   - Framework-specific evidence needs
   - Evidence collection strategy

4. Implementation Guidance
   - Priority order for implementation
   - Effort estimation per control
   - Dependencies between controls

5. Gap Analysis
   - Controls in one framework but not others
   - Varying requirements across frameworks
   - Reconciliation approach

Provide mappings for these control domains:
- Access Control
- Asset Management
- Cryptography/Data Protection
- Operations Security
- Logging and Monitoring
- Incident Response
- Business Continuity
- Vendor Management
- Security Awareness
- Change Management
```

### Step 4: Generate Mapping Report

Ensure the report includes:

- Executive summary of framework coverage
- Detailed control mapping matrix
- Unified control set with evidence requirements
- Implementation roadmap

## Example Usage

```bash
# Map ISO 27001 to SOC 2
/compliance-planning:map-frameworks "ISO 27001, SOC 2"

# Map multiple frameworks
/compliance-planning:map-frameworks "ISO 27001, SOC 2, NIST CSF, CIS Controls"

# Focus on specific area
/compliance-planning:map-frameworks "ISO 27001, SOC 2" --scope "Access Control"
```

## Output Format

```markdown
# Security Framework Mapping

## Frameworks Included
- [Framework 1]
- [Framework 2]
- [Framework 3]

---

## Executive Summary

| Framework | Total Controls | Mapped | Unique | Coverage |
|-----------|----------------|--------|--------|----------|
| [Framework] | [N] | [N] | [N] | [%] |

### Key Insights
- [Insight 1]
- [Insight 2]

---

## Control Mapping Matrix

### Access Control

| Control | ISO 27001 | SOC 2 | NIST CSF | CIS v8 |
|---------|-----------|-------|----------|--------|
| User Access Management | A.5.15 | CC6.1 | PR.AA-01 | 5.1 |
| Privileged Access | A.8.2 | CC6.1 | PR.AA-05 | 5.4 |
| Multi-Factor Auth | A.8.5 | CC6.1 | PR.AA-03 | 6.3 |

### Data Protection

| Control | ISO 27001 | SOC 2 | NIST CSF | CIS v8 |
|---------|-----------|-------|----------|--------|
| Encryption at Rest | A.8.24 | CC6.1 | PR.DS-01 | 3.6 |
| Encryption in Transit | A.8.24 | CC6.7 | PR.DS-02 | 3.10 |

[Continue for all domains]

---

## Unified Control Set

### UC-001: User Access Management

**Satisfies:**
- ISO 27001: A.5.15, A.5.16
- SOC 2: CC6.1, CC6.2
- NIST CSF: PR.AA-01, PR.AA-02
- CIS v8: 5.1, 5.2

**Requirements:**
| Framework | Specific Requirement |
|-----------|---------------------|
| ISO 27001 | [Requirement] |
| SOC 2 | [Requirement] |
| NIST CSF | [Requirement] |
| CIS v8 | [Requirement] |

**Evidence Required:**
- Access management policy
- Access request/approval records
- Periodic access reviews
- Termination procedures

[Continue for all unified controls]

---

## Gap Analysis

### Framework-Specific Requirements

| Control Area | Framework | Unique Requirement |
|--------------|-----------|-------------------|
| [Area] | [Framework] | [Requirement] |

### Reconciliation

| Gap | Impact | Recommendation |
|-----|--------|----------------|

---

## Implementation Roadmap

### Phase 1: Foundation (Common Controls)
| Control | Frameworks Covered | Effort | Priority |
|---------|-------------------|--------|----------|

### Phase 2: Framework-Specific
| Control | Framework | Effort | Priority |
|---------|-----------|--------|----------|

---

## Evidence Collection Strategy

| Evidence Type | Controls Covered | Collection Method | Frequency |
|---------------|------------------|-------------------|-----------|
| Access logs | UC-001, UC-005 | SIEM export | Continuous |
| Policy docs | UC-001, UC-010 | Document repository | Annual review |

---

## Audit Efficiency Gains

### Shared Evidence
- [Evidence type] satisfies [N] frameworks
- Estimated time savings: [X]%

### Consolidated Testing
- [Testing approach] covers [frameworks]
```
