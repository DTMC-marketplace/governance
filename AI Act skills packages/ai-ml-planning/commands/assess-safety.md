---
description: Conduct an AI safety assessment using EU AI Act classification, NIST AI RMF, and bias/fairness evaluation.
argument-hint: <system-description>
allowed-tools: Task, Skill
---

# AI Safety Assessment

Conduct a comprehensive safety assessment of an AI system.

## Workflow

### Step 1: Load Required Skills

Load these skills for comprehensive assessment:

- `ai-safety-planning` - Safety frameworks
- `bias-assessment` - Fairness evaluation
- `explainability-planning` - XAI requirements
- `hitl-design` - Human oversight

### Step 2: Spawn AI Safety Reviewer Agent

Spawn the `ai-safety-reviewer` agent with the following prompt:

```text
Conduct a comprehensive AI safety review for: $ARGUMENTS

Perform the following assessments:

1. EU AI Act Risk Classification
   - Determine risk category (Unacceptable/High/Limited/Minimal)
   - Identify applicable compliance requirements
   - Note any prohibited use concerns

2. NIST AI RMF Evaluation
   - Govern: Policies, accountability, oversight
   - Map: Stakeholders, impacts, constraints
   - Measure: Metrics, testing, monitoring
   - Manage: Mitigations, responses

3. Fairness Assessment
   - Identify protected attributes
   - Evaluate for demographic parity
   - Check for equalized odds
   - Detect proxy variables

4. Safety Testing Plan
   - Prompt injection resistance
   - Jailbreak attempts
   - Harmful content generation
   - Privacy leakage risks

5. Guardrail Recommendations
   - Input filtering needs
   - Output moderation
   - Rate limiting
   - Human oversight

6. Explainability Requirements
   - Regulatory mandates
   - Stakeholder needs
   - Technical approach

Provide a complete safety assessment with:
- Risk classification
- Identified vulnerabilities
- Specific recommendations
- Compliance checklist
- Priority remediation actions
```

### Step 3: Generate Assessment Report

Ensure the assessment includes:

- Executive summary with overall risk rating
- Detailed findings by category
- Prioritized recommendations
- Compliance checklist
- Sign-off requirements

### Step 4: Create Action Plan

If issues are found:

1. Categorize by severity (Critical/High/Medium/Low)
2. Assign remediation priorities
3. Define success criteria
4. Establish review timeline

## Example Usage

```bash
# Assess a hiring assistant
/ai-ml-planning:assess-safety "AI-powered resume screening and candidate ranking system"

# Assess a chatbot
/ai-ml-planning:assess-safety "customer service chatbot for financial services"

# Assess a medical assistant
/ai-ml-planning:assess-safety "symptom checker and health recommendations app"
```

## Output Format

```markdown
# AI Safety Assessment: [System Name]

## Executive Summary

### Overall Risk Rating
**[HIGH RISK / MEDIUM RISK / LOW RISK]**

### Key Findings
- [Critical finding 1]
- [Critical finding 2]

### Recommendation
[PROCEED / PROCEED WITH CONDITIONS / DO NOT PROCEED]

---

## EU AI Act Classification

### Risk Category: [Category]

**Justification:**
[Why this classification]

**Compliance Requirements:**
- [ ] Requirement 1
- [ ] Requirement 2

---

## NIST AI RMF Assessment

| Dimension | Score (1-5) | Key Findings |
|-----------|-------------|--------------|
| Govern | [X] | [Findings] |
| Map | [X] | [Findings] |
| Measure | [X] | [Findings] |
| Manage | [X] | [Findings] |

---

## Fairness Assessment

### Protected Attributes Evaluated
- [Attribute 1]
- [Attribute 2]

### Metrics
| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|

### Bias Findings
| Finding | Severity | Recommendation |
|---------|----------|----------------|

---

## Safety Vulnerabilities

### Identified Risks
| Risk | Severity | Likelihood | Impact |
|------|----------|------------|--------|

### Testing Recommendations
| Test Type | Priority | Approach |
|-----------|----------|----------|

---

## Guardrail Requirements

### Required Guardrails
| Guardrail | Purpose | Implementation |
|-----------|---------|----------------|

---

## Explainability Requirements

### Regulatory Requirements
[List applicable requirements]

### Recommended Approach
[XAI technique and implementation]

---

## Remediation Plan

### Critical (Fix Before Launch)
1. [Issue and remediation]

### High Priority (Fix Within 30 Days)
1. [Issue and remediation]

### Medium Priority (Fix Within 90 Days)
1. [Issue and remediation]

---

## Compliance Checklist

### Pre-Launch
- [ ] Item 1
- [ ] Item 2

### Ongoing
- [ ] Item 1
- [ ] Item 2

---

## Sign-Off

| Role | Name | Approval | Date |
|------|------|----------|------|
| Safety Reviewer | | [ ] | |
| Tech Lead | | [ ] | |
| Legal/Compliance | | [ ] | |
```
