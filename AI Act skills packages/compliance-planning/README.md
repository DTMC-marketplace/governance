# Compliance Planning Plugin

Regulatory compliance and governance planning methodologies for addressing compliance requirements **before development begins**. This plugin provides structured approaches for data privacy, AI governance, industry compliance, security frameworks, and open source licensing.

## Installation

```bash
/plugin install compliance-planning@claude-code-plugins
```

## Skills

| Skill | Description |
|-------|-------------|
| `gdpr-compliance` | GDPR requirements, lawful bases, data subject rights, DPIA |
| `hipaa-compliance` | PHI handling, safeguards, BAAs, risk assessments |
| `pci-dss-compliance` | Payment card security, SAQ selection, scope reduction |
| `ai-governance` | EU AI Act, NIST AI RMF, responsible AI practices |
| `security-frameworks` | ISO 27001, SOC 2, NIST CSF 2.0, CIS Controls mapping |
| `license-compliance` | Open source licensing, compatibility, obligations |
| `sbom-management` | Software bill of materials, dependency tracking |
| `data-classification` | Sensitivity levels, handling requirements, labeling |
| `ethics-review` | AI ethics assessment, ethical impact evaluation |

## Commands

| Command | Description |
|---------|-------------|
| `/compliance-planning:assess-gdpr` | Conduct GDPR compliance assessment |
| `/compliance-planning:assess-hipaa` | Conduct HIPAA compliance assessment |
| `/compliance-planning:assess-pci` | Conduct PCI-DSS scope and compliance assessment |
| `/compliance-planning:assess-ai` | Conduct AI governance assessment |
| `/compliance-planning:map-frameworks` | Map controls across security frameworks |
| `/compliance-planning:scan-licenses` | Analyze open source license compliance |

## Agents

| Agent | Description |
|-------|-------------|
| `compliance-analyst` | Assesses compliance requirements and gaps |
| `privacy-officer` | Evaluates data privacy requirements |
| `security-auditor` | Reviews security framework alignment |

## Use Cases

### Data Privacy Assessment

```bash
# GDPR compliance for EU customers
/compliance-planning:assess-gdpr customer data processing application

# HIPAA for healthcare data
/compliance-planning:assess-hipaa patient portal with PHI access
```

### Security Framework Alignment

```bash
# Map to multiple frameworks
/compliance-planning:map-frameworks ISO 27001, SOC 2 Type II, NIST CSF

# PCI-DSS scoping
/compliance-planning:assess-pci e-commerce checkout integration
```

### AI Governance

```bash
# EU AI Act classification
/compliance-planning:assess-ai hiring recommendation system
```

## Framework Coverage

### Data Privacy

- GDPR (General Data Protection Regulation)
- CCPA/CPRA (California Consumer Privacy Act)
- HIPAA (Health Insurance Portability and Accountability Act)
- LGPD (Brazil General Data Protection Law)

### AI Governance

- EU AI Act risk classification
- NIST AI RMF framework
- Responsible AI principles
- AI ethics review processes

### Industry Standards

- PCI-DSS (Payment Card Industry)
- SOX (Sarbanes-Oxley)
- FDA 21 CFR Part 11 (Life Sciences)

### Security Frameworks

- ISO 27001:2022
- SOC 2 Type I/II
- NIST Cybersecurity Framework 2.0
- CIS Controls v8

### Open Source

- License compatibility matrix
- SBOM requirements
- Dependency vulnerability management
- Export control considerations

## Integration with Other Plugins

- **security**: Security controls implementation
- **ai-ml-planning**: AI safety and governance
- **enterprise-architecture**: Governance integration
- **data-architecture**: Data handling requirements

## .NET/C# Examples

This plugin provides examples using:

- Data annotation attributes for classification
- Policy-based authorization patterns
- Audit logging implementations
- GDPR-compliant consent management

## License

MIT - see [LICENSE](../../LICENSE)
