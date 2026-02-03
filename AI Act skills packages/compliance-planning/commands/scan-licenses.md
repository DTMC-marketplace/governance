---
description: Analyze open source license compliance for a project's dependencies.
argument-hint: [project-path]
allowed-tools: Task, Skill, Read, Glob, Grep
---

# Open Source License Compliance Scan

Analyze project dependencies for license compliance.

## Workflow

### Step 1: Load Required Skills

Load these skills:

- `license-compliance` - License requirements and compatibility
- `sbom-management` - Dependency tracking

### Step 2: Identify Project Type

Detect the project type and package manager:

- **.NET**: Look for `*.csproj`, `*.sln`, `packages.config`
- **Node.js**: Look for `package.json`, `package-lock.json`
- **Python**: Look for `requirements.txt`, `pyproject.toml`, `setup.py`
- **Java**: Look for `pom.xml`, `build.gradle`

### Step 3: Extract Dependencies

For .NET projects:

```bash
dotnet list package --include-transitive
```

For Node.js:

```bash
npm ls --all --json
```

### Step 4: Analyze Licenses

For each dependency:

1. Identify the license (SPDX identifier)
2. Categorize (Permissive, Weak Copyleft, Strong Copyleft)
3. Check against policy (Approved, Requires Review, Prohibited)
4. Identify obligations

### Step 5: Check Compatibility

Verify license compatibility:

- Check inbound vs outbound license compatibility
- Identify conflicting licenses
- Flag copyleft contamination risks

### Step 6: Generate Report

Create a comprehensive license compliance report.

## Example Usage

```bash
# Scan current directory
/compliance-planning:scan-licenses

# Scan specific project
/compliance-planning:scan-licenses "./src/MyApp"

# Scan solution
/compliance-planning:scan-licenses "./MySolution.sln"
```

## Output Format

````markdown
# License Compliance Report: [Project Name]

## Summary

| Metric | Count |
|--------|-------|
| Total Dependencies | [N] |
| Direct Dependencies | [N] |
| Transitive Dependencies | [N] |
| Approved Licenses | [N] |
| Requires Review | [N] |
| Prohibited | [N] |
| Unknown | [N] |

### Compliance Status: [COMPLIANT / REVIEW REQUIRED / NON-COMPLIANT]

---

## License Distribution

| License | Category | Count | Status |
|---------|----------|-------|--------|
| MIT | Permissive | [N] | Approved |
| Apache-2.0 | Permissive | [N] | Approved |
| GPL-3.0 | Strong Copyleft | [N] | Prohibited |

---

## Dependencies by Status

### Approved

| Package | Version | License | Category |
|---------|---------|---------|----------|
| [Package] | [Version] | [License] | Permissive |

### Requires Review

| Package | Version | License | Concern |
|---------|---------|---------|---------|
| [Package] | [Version] | [License] | [Why review needed] |

### Prohibited

| Package | Version | License | Issue | Alternative |
|---------|---------|---------|-------|-------------|
| [Package] | [Version] | [License] | [Issue] | [Suggested alternative] |

### Unknown

| Package | Version | License Info | Action |
|---------|---------|--------------|--------|
| [Package] | [Version] | [Info] | [Required action] |

---

## Compatibility Analysis

### License Conflicts
| Package 1 | License 1 | Package 2 | License 2 | Conflict |
|-----------|-----------|-----------|-----------|----------|

### Copyleft Assessment

**Copyleft Packages Found:** [Y/N]

| Package | License | Impact | Mitigation |
|---------|---------|--------|------------|

---

## Obligations Summary

### Attribution Required
| Package | License | Attribution Text |
|---------|---------|-----------------|

### Source Disclosure Required
| Package | License | Requirement |
|---------|---------|-------------|

### Notice Files Required
| Package | NOTICE File | Status |
|---------|-------------|--------|

---

## Recommended Actions

### Immediate Actions
1. **Replace prohibited packages**
   - [Package] -> [Alternative]

2. **Review flagged packages**
   - [Package] - [Review reason]

### Documentation Actions
1. **Update NOTICE file**
   - Add attributions for: [Packages]

2. **Add license files**
   - Include: [License files needed]

---

## NOTICE File Content

```text

THIRD-PARTY SOFTWARE NOTICES AND INFORMATION

This software includes the following third-party components:

[Package Name] ([Version])
License: [License]
[Copyright notice]

---
[Continue for all dependencies]

```

---

## Policy Compliance

| Policy Rule | Status | Details |
|-------------|--------|---------|
| No GPL in proprietary | [Status] | [Details] |
| No AGPL | [Status] | [Details] |
| All licenses identified | [Status] | [Details] |
| Attributions complete | [Status] | [Details] |
````

## .NET-Specific Commands

For .NET projects, the following commands are useful:

```bash
# Install license checker
dotnet tool install --global dotnet-project-licenses

# Generate license report
dotnet-project-licenses -i ./MySolution.sln

# Generate SBOM
dotnet CycloneDX ./MySolution.sln -o sbom.json -j
```
