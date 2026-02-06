"""
Governance AI Agent Service - Adapted from geminihackathon/governance_agent.py

This module provides a Django-integrated Governance AI Agent that consolidates
all AI Act skills packages for comprehensive AI governance scanning.

Original: geminihackathon/agents/agents/implementation/governance_agent.py
Adapted for: governance Django app - used by GeminiScannerService.run_scan()
"""

import os
import json
import re
import logging
import yaml
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, field

from django.conf import settings

logger = logging.getLogger(__name__)

# Singleton instance
_agent_instance: Optional['GovernanceAgentService'] = None


def get_governance_agent_service() -> 'GovernanceAgentService':
    """Get or create singleton instance of GovernanceAgentService."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = GovernanceAgentService()
    return _agent_instance


@dataclass
class AgentConfig:
    """Configuration for the Governance AI Agent"""
    name: str = "governance-ai-agent"
    description: str = "Comprehensive AI governance agent with access to all AI Act skills packages"
    model: str = "gemini-3-pro-preview"
    temperature: float = 0.3
    max_tokens: int = 4096
    skills_paths: List[str] = field(default_factory=list)


@dataclass
class SkillMetadata:
    """Metadata for a loaded skill"""
    name: str
    description: str
    path: str
    content: str
    allowed_tools: List[str] = field(default_factory=list)


class GovernanceAgentService:
    """
    Comprehensive AI Governance Agent with access to all AI Act skills packages.

    Provides end-to-end guidance on building compliant, safe, ethical, and robust
    AI systems that meet regulatory requirements including the EU AI Act, GDPR,
    HIPAA, PCI-DSS, and other frameworks.

    Adapted from geminihackathon/governance_agent.py for Django integration.
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or self._load_default_config()
        self.skills: Dict[str, SkillMetadata] = {}
        self.loaded_skills: List[str] = []

        # Discover available skills
        self._discover_skills()
        logger.info(f"GovernanceAgentService initialized with {len(self.skills)} skills")

    def _load_default_config(self) -> AgentConfig:
        """Load default agent configuration from Django settings."""
        config = AgentConfig()

        # Model from Django settings
        config.model = getattr(settings, 'AI_ACT_MODEL_NAME', 'gemini-3-pro-preview')

        # Skills directories - support multiple paths
        # Primary: governance/skills/ (flat structure, copied from geminihackathon)
        skills_dir = Path(settings.BASE_DIR) / "skills"
        if skills_dir.exists():
            config.skills_paths.append(str(skills_dir))

        # Fallback: governance/AI Act skills packages/ (nested structure)
        ai_act_skills = Path(settings.BASE_DIR) / "AI Act skills packages"
        if ai_act_skills.exists() and not skills_dir.exists():
            config.skills_paths.append(str(ai_act_skills))

        return config

    def _discover_skills(self):
        """Discover and load metadata for all available skills from multiple directories."""
        if not self.config.skills_paths:
            logger.warning("No skills paths configured")
            return

        discovered_skills = set()

        for base_path in self.config.skills_paths:
            skills_path = Path(base_path)
            if not skills_path.exists():
                continue

            # Search for all SKILL.md files
            skill_files = list(skills_path.rglob("SKILL.md"))

            for skill_file in skill_files:
                try:
                    skill_metadata = self._parse_skill_file(skill_file)
                    if skill_metadata:
                        if skill_metadata.name not in discovered_skills:
                            self.skills[skill_metadata.name] = skill_metadata
                            discovered_skills.add(skill_metadata.name)
                except Exception as e:
                    logger.debug(f"Could not load skill from {skill_file}: {e}")

        logger.info(f"Discovered {len(self.skills)} skills from {len(self.config.skills_paths)} paths")

    def _parse_skill_file(self, file_path: Path) -> Optional[SkillMetadata]:
        """Parse a SKILL.md file and extract metadata from YAML frontmatter."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            return None

        # Extract YAML frontmatter
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if not frontmatter_match:
            return None

        try:
            frontmatter = yaml.safe_load(frontmatter_match.group(1))
            return SkillMetadata(
                name=frontmatter.get('name', ''),
                description=frontmatter.get('description', ''),
                path=str(file_path),
                content=content,
                allowed_tools=frontmatter.get('allowed-tools', [])
            )
        except Exception:
            return None

    # ─── Skill Management ──────────────────────────────────────────────

    def list_available_skills(self) -> List[str]:
        """List all available skill names."""
        return sorted(self.skills.keys())

    def _find_similar_skills(self, skill_name: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Find similar skill names using fuzzy matching."""
        candidates = []
        query = skill_name.lower().strip()
        query_words = set(query.replace("-", " ").replace("_", " ").split())

        for name, meta in self.skills.items():
            name_lower = name.lower()
            score = 0.0

            # Exact substring match
            if query in name_lower or name_lower in query:
                score += 50.0

            # Word overlap scoring
            name_words = set(name_lower.replace("-", " ").split())
            common_words = query_words & name_words
            if common_words:
                score += len(common_words) * 20.0

            # Partial word matching
            for qw in query_words:
                if len(qw) > 2:
                    for nw in name_words:
                        if qw in nw or nw in qw:
                            score += 10.0

            # Check description
            desc_lower = (meta.description or "").lower()
            for qw in query_words:
                if len(qw) > 3 and qw in desc_lower:
                    score += 5.0

            # Char-level similarity
            common_chars = sum(1 for c in query if c in name_lower)
            char_ratio = common_chars / max(len(query), len(name_lower), 1)
            score += char_ratio * 10.0

            if score > 5.0:
                candidates.append({
                    "name": name,
                    "score": round(score, 1),
                    "description": meta.description or ""
                })

        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[:max_results]

    def _resolve_skill_name(self, skill_name: str) -> Optional[str]:
        """Try to resolve a skill name - exact match or best fuzzy match."""
        if skill_name in self.skills:
            return skill_name

        normalized = skill_name.strip().lower().replace("_", "-")
        if normalized in self.skills:
            return normalized

        similar = self._find_similar_skills(skill_name)
        if not similar:
            return None

        # Auto-resolve if top match has very high score
        if similar[0]["score"] >= 50.0:
            return similar[0]["name"]

        return None

    def get_skill_content(self, skill_name: str) -> Optional[str]:
        """Get the full content of a skill (with fuzzy name resolution)."""
        resolved = self._resolve_skill_name(skill_name)
        if resolved:
            skill = self.skills.get(resolved)
            return skill.content if skill else None
        return None

    def load_skill(self, skill_name: str) -> bool:
        """Load a skill for use in the current session."""
        resolved = self._resolve_skill_name(skill_name)
        if not resolved:
            return False
        if resolved not in self.loaded_skills:
            self.loaded_skills.append(resolved)
        return True

    # ─── Risk Classification ───────────────────────────────────────────

    def _classify_risk(self, system_description: str) -> Dict[str, Any]:
        """Classify the risk level of an AI system per EU AI Act."""
        high_risk_keywords = [
            "healthcare", "medical", "diagnosis", "credit", "scoring",
            "employment", "hiring", "recruitment", "biometric", "law enforcement"
        ]

        description_lower = system_description.lower()

        for keyword in high_risk_keywords:
            if keyword in description_lower:
                return {
                    "category": "High-Risk",
                    "confidence": "high",
                    "reasoning": f"System contains '{keyword}' indicating High-Risk category per EU AI Act"
                }

        if any(word in description_lower for word in ["chatbot", "customer service", "content generation"]):
            return {
                "category": "Limited Risk",
                "confidence": "medium",
                "reasoning": "System interacts with users, requiring transparency per Article 52"
            }

        return {
            "category": "Minimal Risk",
            "confidence": "low",
            "reasoning": "System does not appear to fall into High-Risk or Limited Risk categories"
        }

    # ─── Article Requirements & Compulsory Skills ──────────────────────

    ARTICLE_REQUIREMENTS = {
        'Art. 9': {
            'name': 'Risk Management System',
            'status': 'Mandatory for all high-risk systems per Article 9.',
            'compulsory_skills': ['risk-management', 'risk-assessment', 'ai-safety', 'red-team-testing', 'guardrails-implementation', 'toxicity-detection', 'hate-speech-detection', 'claim-verification', 'ai-ethics-fact-checking', 'content-toxicity-analysis', 'ai-ethics', 'ai-governance', 'ai-alignment-framework', 'incident-responder', 'ethics-review'],
        },
        'Art. 10': {
            'name': 'Data and Data Governance',
            'status': 'Requirements for training, validation and testing data sets.',
            'compulsory_skills': ['risk-assessment', 'data-classification', 'gdpr-compliance', 'bias-assessment', 'ai-testing', 'validating-ai-ethics-and-fairness', 'ai-governance', 'transparency-instructions'],
        },
        'Art. 11': {
            'name': 'Technical Documentation',
            'status': 'Technical documentation must be drawn up before system placement.',
            'compulsory_skills': ['technical-documentation', 'model-card-generation', 'ai-transparency-labels', 'automatic-logging', 'standards-compliance-interoperability', 'ai-governance'],
        },
        'Art. 12': {
            'name': 'Record-keeping (Logging)',
            'status': 'Automatic recording of events (logs) during system lifetime.',
            'compulsory_skills': ['automatic-logging', 'ai-logging-system', 'incident-responder', 'technical-documentation', 'ai-governance'],
        },
        'Art. 13': {
            'name': 'Transparency & Provision of Information',
            'status': 'Systems must be sufficiently transparent for deployers to interpret output.',
            'compulsory_skills': ['transparency-instructions', 'ai-transparency-labels', 'model-card-generation', 'explainability-planning', 'deployer-training', 'ai-governance'],
        },
        'Art. 14': {
            'name': 'Human Oversight',
            'status': 'High-risk AI systems must be designed for effective human oversight.',
            'compulsory_skills': ['hitl-design', 'human-oversight', 'ai-safety-planning', 'deployer-training', 'ai-governance', 'ethics-review'],
        },
        'Art. 15': {
            'name': 'Accuracy, Robustness and Cybersecurity',
            'status': 'Systems shall achieve appropriate levels of accuracy and robustness.',
            'compulsory_skills': ['ai-testing', 'ai-performance-testing', 'conformance-calibration', 'guardrails-implementation', 'security-frameworks', 'prompt-injection-detector', 'incident-responder'],
        },
        'Art. 16': {
            'name': 'Obligations of Providers',
            'status': 'General obligations including QMS and post-market monitoring.',
            'compulsory_skills': ['qms-tracker', 'ai-governance', 'risk-management', 'incident-responder', 'technical-documentation', 'automatic-logging'],
        },
        'Art. 27': {
            'name': 'Fundamental Rights Impact Assessment',
            'status': 'Assessment of impact on fundamental rights per Article 27.',
            'compulsory_skills': ['fria-assessment', 'bias-assessment', 'hitl-design', 'ai-fairness-360', 'ethics-review', 'validating-ai-ethics-and-fairness', 'ai-governance'],
        },
        'Art. 50': {
            'name': 'Transparency for Certain AI Systems',
            'status': 'Transparency obligations for systems interacting with humans.',
            'compulsory_skills': ['ai-transparency-labels', 'transparency-instructions', 'model-card-generation', 'explainability-planning', 'deployer-training'],
        },
        'Art. 52': {
            'name': 'Transparency Obligations',
            'status': 'Specific transparency requirements for chatbots and deepfakes.',
            'compulsory_skills': ['ai-transparency-labels', 'transparency-instructions', 'explainability-planning'],
        }
    }

    # Skill to Article reverse mapping
    SKILL_TO_ARTICLE = {}
    for art, data in ARTICLE_REQUIREMENTS.items():
        for skill in data['compulsory_skills']:
            if skill not in SKILL_TO_ARTICLE:
                SKILL_TO_ARTICLE[skill] = art

    def get_compulsory_skills_for_tool(self, tool_id: str) -> List[str]:
        """Get the list of compulsory skills for the article related to this tool."""
        # Normalize tool_id (remove -assessment if needed, or check exact)
        tool_id = tool_id.lower()
        article = self.SKILL_TO_ARTICLE.get(tool_id)
        
        # Try without -assessment suffix
        if not article and tool_id.endswith('-assessment'):
            article = self.SKILL_TO_ARTICLE.get(tool_id.replace('-assessment', ''))
        
        if article:
            return self.ARTICLE_REQUIREMENTS[article]['compulsory_skills']
        return []

    def get_article_for_tool(self, tool_id: str) -> Optional[str]:
        """Get the Article ID for a specific tool."""
        tool_id = tool_id.lower()
        article = self.SKILL_TO_ARTICLE.get(tool_id)
        if not article and tool_id.endswith('-assessment'):
            article = self.SKILL_TO_ARTICLE.get(tool_id.replace('-assessment', ''))
        return article

    def _identify_regulations(self, system_description: str) -> List[Dict[str, Any]]:
        """Identify applicable regulations based on system description."""
        regulations = []
        description_lower = system_description.lower()

        regulations.append({
            "name": "EU AI Act",
            "applies": True,
            "reason": "Applies to all AI systems deployed in EU"
        })

        if any(word in description_lower for word in ["personal data", "user data", "privacy", "eu"]):
            regulations.append({
                "name": "GDPR",
                "applies": True,
                "reason": "System processes personal data in EU context"
            })

        if any(word in description_lower for word in ["healthcare", "medical", "patient", "health"]):
            regulations.append({
                "name": "HIPAA",
                "applies": True,
                "reason": "System processes healthcare/patient data"
            })

        if any(word in description_lower for word in ["payment", "credit card", "transaction"]):
            regulations.append({
                "name": "PCI-DSS",
                "applies": True,
                "reason": "System processes payment card data"
            })

        return regulations

    # ─── Skill Recommendation (Core logic from hackathon) ──────────────

    def _recommend_skills(self, system_description: str) -> List[Dict[str, str]]:
        """Recommend skills based on system description. Covers all 52+ skills."""
        recommended = []
        already_added = set()
        description_lower = system_description.lower()

        # Core skills (always recommended)
        core_skills = [
            ("risk-assessment", "Essential for identifying and mitigating risks"),
            ("ai-governance", "Core governance framework and policies"),
            ("ai-safety-planning", "Safety measures and guardrails")
        ]

        for skill_name, reason in core_skills:
            if skill_name in self.skills:
                recommended.append({"skill": skill_name, "reason": reason})
                already_added.add(skill_name)

        # Keyword-to-skill mapping
        keyword_skill_map = {
            "gdpr": [("gdpr-compliance", "GDPR compliance required")],
            "privacy": [("gdpr-compliance", "Privacy regulations applicable")],
            "personal data": [("gdpr-compliance", "Personal data processing requires GDPR compliance")],
            "hipaa": [("hipaa-compliance", "HIPAA compliance for healthcare data")],
            "health": [("hipaa-compliance", "Healthcare context requires HIPAA assessment")],
            "patient": [("hipaa-compliance", "Patient data requires HIPAA compliance")],
            "medical": [("hipaa-compliance", "Medical system requires HIPAA compliance")],
            "pci": [("pci-dss-compliance", "PCI-DSS compliance for payment data")],
            "payment": [("pci-dss-compliance", "Payment processing requires PCI-DSS")],
            "credit card": [("pci-dss-compliance", "Credit card data requires PCI-DSS")],
            "license": [("license-compliance", "Software license compliance needed")],
            "open source": [("license-compliance", "Open source license review needed")],
            "standard": [("standards-compliance-interoperability", "Standards compliance assessment")],
            "bias": [("bias-assessment", "Bias assessment and mitigation needed"),
                     ("ai-ethics", "Ethical AI considerations for bias"),
                     ("validating-ai-ethics-and-fairness", "Ethics and fairness validation")],
            "fairness": [("bias-assessment", "Fairness assessment required"),
                         ("validating-ai-ethics-and-fairness", "Ethics and fairness validation")],
            "ethics": [("ai-ethics", "AI ethics framework needed"),
                       ("ai-ethics-advisor", "Ethics advisory guidance")],
            "test": [("ai-testing", "Testing and quality assurance needed"),
                     ("ai-performance-testing", "Performance testing recommended")],
            "testing": [("ai-testing", "Comprehensive AI testing framework")],
            "performance": [("ai-performance-testing", "Performance testing and benchmarking")],
            "rag": [("rag-architecture", "RAG architecture design needed")],
            "retrieval": [("rag-architecture", "Retrieval-augmented generation architecture")],
            "agent": [("agentic-workflow-design", "Agentic workflow design patterns")],
            "workflow": [("agentic-workflow-design", "Workflow design for AI agents")],
            "prompt": [("prompt-engineering", "Prompt engineering best practices")],
            "model": [("model-selection", "Model selection guidance")],
            "llm": [("model-selection", "LLM model selection assessment")],
            "security": [("security-frameworks", "Security framework implementation")],
            "attack": [("security-frameworks", "Security threat assessment")],
            "injection": [("security-frameworks", "Injection attack prevention")],
            "incident": [("incident-responder", "Incident response planning")],
            "sbom": [("sbom-management", "Software Bill of Materials management")],
            "supply chain": [("sbom-management", "Supply chain security via SBOM")],
            "data": [("data-classification", "Data classification framework")],
            "sensitive": [("data-classification", "Sensitive data classification")],
            "explain": [("explainability-planning", "AI explainability planning")],
            "transparen": [("explainability-planning", "Transparency and explainability")],
            "human": [("hitl-design", "Human-in-the-loop design")],
            "oversight": [("hitl-design", "Human oversight mechanism design")],
            "log": [("automatic-logging", "Automated logging implementation")],
            "audit": [("automatic-logging", "Audit logging implementation")],
            "monitor": [("automatic-logging", "Monitoring and logging setup")],
            "deploy": [("deployer-training", "Deployment training program")],
            "fria": [("fria-assessment", "Fundamental Rights Impact Assessment")],
            "fundamental rights": [("fria-assessment", "FRIA assessment required")],
            "impact": [("fria-assessment", "Impact assessment needed")],
            "ml": [("ml-project-lifecycle", "ML project lifecycle management")],
            "machine learning": [("ml-project-lifecycle", "ML lifecycle management")],
            "multilingual": [("multilingual-localization", "Multilingual support needed")],
            "language": [("multilingual-localization", "Multi-language localization")],
            "fact": [("fact-checker", "Fact-checking implementation")],
            "hallucin": [("fact-checker", "Hallucination detection and fact-checking")],
            "token": [("token-budgeting", "Token usage budgeting")],
            "cost": [("token-budgeting", "Cost management via token budgeting")],
            "policy": [("policy-engine-builder", "Policy engine implementation")],
            "governance": [("policy-engine-builder", "Governance policy engine")],
            "chatbot": [("prompt-engineering", "Chatbot prompt engineering"),
                        ("fact-checker", "Response accuracy for chatbot")],
            "skill": [("skill-creator", "Custom skill creation")],
        }

        for keyword, skill_entries in keyword_skill_map.items():
            if keyword in description_lower:
                for skill_name, reason in skill_entries:
                    if skill_name not in already_added and skill_name in self.skills:
                        recommended.append({"skill": skill_name, "reason": reason})
                        already_added.add(skill_name)

        # Fuzzy match: check skill name parts against description
        for skill_name, skill_meta in self.skills.items():
            if skill_name in already_added:
                continue
            if skill_name.startswith("gemini-") or skill_name.startswith("toml-"):
                continue

            skill_words = skill_name.replace("-", " ").split()
            exclude_words = {"design", "management", "planning", "builder", "creator", "bridge", "sync", "command"}
            meaningful_words = [w for w in skill_words if len(w) > 3 and w not in exclude_words]
            matches = [w for w in meaningful_words if w in description_lower]

            if len(matches) >= 1:
                skill_desc = (skill_meta.description or "").lower()
                desc_overlap = any(
                    word in skill_desc
                    for word in description_lower.split()
                    if len(word) > 3
                )
                if desc_overlap or len(matches) >= 2:
                    recommended.append({
                        "skill": skill_name,
                        "reason": f"Matched: {', '.join(matches)} - {skill_meta.description[:80] if skill_meta.description else 'Related skill'}"
                    })
                    already_added.add(skill_name)

        # Sort: core first, then by name
        core_names = {s[0] for s in core_skills}
        recommended.sort(key=lambda x: (0 if x['skill'] in core_names else 1, x['skill']))

        return recommended

    # ─── Assessment & Plan Generation ──────────────────────────────────

    def assess_ai_system(self, system_description: str) -> Dict[str, Any]:
        """Assess an AI system and provide governance recommendations."""
        return {
            "system_description": system_description,
            "risk_classification": self._classify_risk(system_description),
            "applicable_regulations": self._identify_regulations(system_description),
            "recommended_skills": self._recommend_skills(system_description),
            "initial_assessment": self._generate_initial_assessment(system_description)
        }

    def _generate_initial_assessment(self, system_description: str) -> str:
        """Generate initial assessment narrative."""
        risk_info = self._classify_risk(system_description)
        regulations = self._identify_regulations(system_description)

        assessment = f"""
Initial Assessment:

System Risk Level: {risk_info['category']}
Reasoning: {risk_info['reasoning']}

Applicable Regulations:
"""
        for reg in regulations:
            assessment += f"- {reg['name']}: {reg['reason']}\n"

        assessment += """
Next Steps:
1. Load recommended skills for detailed guidance
2. Conduct comprehensive risk assessment
3. Map compliance requirements
4. Design governance framework
5. Implement safety measures and testing
"""
        return assessment

    def generate_governance_plan(self, system_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a comprehensive governance plan."""
        return {
            "system_profile": system_profile,
            "executive_summary": self._generate_executive_summary(system_profile),
            "risk_assessment": self._classify_risk(system_profile.get("purpose", "")),
            "compliance_requirements": self._identify_regulations(system_profile.get("purpose", "")),
            "architecture_recommendations": self._generate_architecture_recommendations(system_profile),
            "safety_implementation": self._generate_safety_recommendations(system_profile),
            "testing_strategy": self._generate_testing_strategy(system_profile),
            "operational_procedures": self._generate_operational_procedures(system_profile),
            "next_steps": self._generate_next_steps(system_profile)
        }

    def _generate_executive_summary(self, system_profile: Dict[str, Any]) -> str:
        return (
            f"This governance plan addresses the {system_profile.get('type', 'AI system')} with "
            f"purpose: {system_profile.get('purpose', 'Not specified')}. "
            f"The system will be deployed to {system_profile.get('users', 'users')} in "
            f"{system_profile.get('geography', 'unspecified regions')}, processing "
            f"{system_profile.get('data', 'various data types')}."
        )

    def _generate_architecture_recommendations(self, system_profile: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "recommended_patterns": [
                "Microservices architecture for scalability",
                "API gateway for controlled access",
                "Model versioning and registry",
                "Feature store for data consistency"
            ],
            "data_pipeline": [
                "Implement data validation and quality checks",
                "Set up data lineage tracking",
                "Configure privacy-preserving techniques"
            ],
            "monitoring": [
                "Real-time performance monitoring",
                "Bias detection in production",
                "Audit logging per Article 12"
            ]
        }

    def _generate_safety_recommendations(self, system_profile: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "guardrails": {
                "input_guards": [
                    "Prompt injection detection",
                    "Content filtering",
                    "Rate limiting"
                ],
                "output_filters": [
                    "Toxicity filtering",
                    "PII detection and redaction",
                    "Topic restrictions"
                ]
            },
            "red_teaming": [
                "Pre-launch adversarial testing",
                "Ongoing red team exercises",
                "Vulnerability disclosure program"
            ],
            "monitoring": [
                "Safety metrics dashboard",
                "Automated alerting",
                "Incident detection"
            ]
        }

    def _generate_testing_strategy(self, system_profile: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "pre_launch": [
                "Unit tests for all components",
                "Integration testing",
                "Red team testing",
                "Bias evaluation",
                "Performance benchmarking",
                "Security testing"
            ],
            "continuous": [
                "Automated test suite",
                "Ongoing red teaming",
                "User feedback monitoring",
                "Performance monitoring",
                "Compliance auditing"
            ]
        }

    def _generate_operational_procedures(self, system_profile: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "logging": {
                "audit_logs": "Log all AI system interactions per Article 12",
                "metrics": "Track performance, safety, and compliance metrics",
                "retention": "Configure appropriate retention policies"
            },
            "incident_response": {
                "detection": "Automated monitoring and alerting",
                "response": "Documented response procedures",
                "escalation": "Clear escalation paths",
                "reporting": "15-day reporting for serious incidents (Article 73)"
            },
            "deployment": {
                "training": "Deployer training program",
                "rollout": "Phased deployment with monitoring",
                "validation": "Post-deployment validation checks"
            }
        }

    def _generate_next_steps(self, system_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {"phase": "Immediate (Week 1-2)", "tasks": [
                "Finalize risk classification",
                "Load and review relevant skills",
                "Begin compliance documentation"
            ]},
            {"phase": "Short-term (Month 1)", "tasks": [
                "Complete architecture design",
                "Implement core guardrails",
                "Set up testing framework"
            ]},
            {"phase": "Medium-term (Month 2-3)", "tasks": [
                "Complete testing and validation",
                "Finalize documentation",
                "Conduct pre-launch review"
            ]},
            {"phase": "Long-term (Month 4+)", "tasks": [
                "Deploy to production",
                "Establish monitoring and maintenance",
                "Continuous improvement"
            ]}
        ]

    # ─── Export ─────────────────────────────────────────────────────────

    def export_assessment(self, assessment: Dict[str, Any], fmt: str = "json") -> str:
        """Export assessment or plan to specified format."""
        if fmt == "json":
            return json.dumps(assessment, indent=2)
        elif fmt == "yaml":
            return yaml.dump(assessment, default_flow_style=False)
        elif fmt == "markdown":
            return self._format_as_markdown(assessment)
        else:
            raise ValueError(f"Unsupported format: {fmt}")

    def _format_as_markdown(self, data: Dict[str, Any]) -> str:
        """Format data as markdown report."""
        from datetime import datetime

        is_assessment = 'system_description' in data
        is_plan = 'system_profile' in data and 'executive_summary' in data

        if is_assessment:
            return self._format_assessment_report(data)
        elif is_plan:
            return self._format_governance_plan_report(data)
        else:
            return json.dumps(data, indent=2)

    def _format_assessment_report(self, data: Dict[str, Any]) -> str:
        """Format assessment as professional markdown report."""
        from datetime import datetime

        risk = data.get('risk_classification', {})
        if isinstance(risk, str):
            risk_category = risk
        else:
            risk_category = risk.get('category', 'Unknown')
        
        # Calculate internal risk score
        risk_score = 4 if risk_category == 'High-Risk' else 2 if risk_category == 'Limited Risk' else 1

        md = f"""# 🛡️ AI Safety & Risk Assessment Report

**Target System**: {data.get('system_description', 'AI System')}
**Generated**: {datetime.now().strftime('%Y-%m-%d')}
**Framework**: EU AI Act + NIST AI RMF
**Skill Applied**: {data.get('skill_applied', 'risk-assessment')}
**Assessor**: Governance AI Agent

---

## 1. Risk Classification

### EU AI Act Category: **{risk_category}**

- **Applicable Article:** {"Annex III (High-Risk)" if risk_category == 'High-Risk' else "Article 50 (Transparency Obligations)" if risk_category == 'Limited Risk' else "Article 6 (Minimal Risk)"}
- **Justification:** {risk.get('reasoning', 'N/A')}
- **Classification Date:** {datetime.now().strftime('%Y-%m-%d')}

### NIST AI RMF Profile

- **Primary Function:** {data.get('nist_profile', {}).get('function', 'AI system requiring governance assessment')}
- **AI Type:** {data.get('nist_profile', {}).get('type', 'To be determined based on implementation')}
- **Deployment:** {data.get('nist_profile', {}).get('deployment', 'To be specified')}

### Internal Risk Score: **{risk_score}/5** ({"High" if risk_score >= 4 else "Medium" if risk_score >= 2 else "Low"})

| Factor | Assessment | Score |
|--------|------------|-------|
| Autonomy Level | {data.get('factors', {}).get('autonomy', "High autonomy - critical decisions" if risk_category == 'High-Risk' else "Medium autonomy" if risk_category == 'Limited Risk' else "Low autonomy")} | {risk_score}/5 |
| Decision Impact | {data.get('factors', {}).get('impact', "High impact on individuals" if risk_category == 'High-Risk' else "Medium impact" if risk_category == 'Limited Risk' else "Low impact")} | {risk_score}/5 |
| Data Sensitivity | {data.get('factors', {}).get('sensitivity', "Sensitive personal data" if risk_category == 'High-Risk' else "Standard data" if risk_category == 'Limited Risk' else "Non-sensitive")} | {risk_score}/5 |
| User Vulnerability | {data.get('factors', {}).get('vulnerability', "Vulnerable populations" if risk_category == 'High-Risk' else "General public" if risk_category == 'Limited Risk' else "Technical users")} | {max(1, risk_score-1)}/5 |
| Reversibility | {data.get('factors', {}).get('reversibility', "Difficult to reverse" if risk_category == 'High-Risk' else "Partially reversible" if risk_category == 'Limited Risk' else "Fully reversible")} | {max(1, risk_score-1)}/5 |

---

## 2. Identified Risks

| Risk ID | Risk Description | Likelihood | Impact | Severity | Mitigation |
|---------|------------------|------------|--------|----------|------------|
"""
        # Add risks from data or defaults
        risks = data.get('identified_risks', [])
        if not risks:
            # Fallback defaults if no Gemini findings
            risks = [
                {"id": "R-001", "desc": "**Hallucination** - AI may generate incorrect information", "like": "Medium", "imp": "High", "sev": "High", "mit": "System prompt constraints"},
                {"id": "R-002", "desc": "**Over-reliance** - Users may treat AI as authoritative", "like": "Medium", "imp": "Medium", "sev": "Medium", "mit": "Disclaimer notices"}
            ]
        
        for r in risks:
            md += f"| {r.get('id', '-')} | {r.get('desc', '-')} | {r.get('like', '-')} | {r.get('imp', '-')} | {r.get('sev', '-')} | {r.get('mit', '-')} |\n"

        md += """
---

## 3. Current Safety Controls (✅ Implemented)

"""
        controls = data.get('safety_controls', {})
        for category, items in controls.items():
            md += f"### {category}\n"
            for item in items:
                status = "[x]" if item.get('implemented') else "[ ]"
                md += f"- {status} **{item.get('name')}** - {item.get('details')}\n"
            md += "\n"

        md += """
---

## 4. Missing Safety Controls (❌ Not Implemented)

"""
        missing = data.get('missing_controls', {})
        for category, items in missing.items():
            md += f"### {category}\n"
            for item in items:
                md += f"- [ ] **{item.get('name')}** - {item.get('reason')}\n"
            md += "\n"

        md += """
---

## 5. Guardrails Recommendations

"""
        recommendations = data.get('guardrails_recommendations', [])
        for rec in recommendations:
            md += f"### {rec.get('title')} (Priority: {rec.get('priority', 'Medium')})\n\n"
            md += f"```python\n{rec.get('code', '# Recommendation code here')}\n```\n\n"

        md += """
---

## 6. Testing Plan

### Pre-Launch Red Teaming
"""
        for test in data.get('testing_plan', {}).get('red_teaming', []):
            md += f"- [ ] {test}\n"
        
        md += "\n### Bias Testing\n"
        for test in data.get('testing_plan', {}).get('bias_testing', []):
            md += f"- [ ] {test}\n"

        md += """
---

## 7. Monitoring Plan

### Safety Metrics Dashboard
| Metric | Target | Current |
|--------|--------|---------|
"""
        for m in data.get('monitoring_plan', {}).get('metrics', []):
            md += f"| {m.get('name')} | {m.get('target')} | {m.get('current')} |\n"

        md += f"""
---

## 8. Compliance Status

### EU AI Act Requirements

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| Inform users they are interacting with AI | {data.get('compliance', {}).get('disclosure', 'Pending')} | {data.get('compliance', {}).get('disclosure_ref', '-')} |
| Disclose AI-generated content | {data.get('compliance', {}).get('labeling', 'Pending')} | {data.get('compliance', {}).get('labeling_ref', '-')} |
| Provide information about AI capabilities | {data.get('compliance', {}).get('capability', 'Pending')} | {data.get('compliance', {}).get('capability_ref', '-')} |

---

## 9. Action Items

### Immediate (Before next release)
"""
        for i, item in enumerate(data.get('action_items', {}).get('immediate', []), 1):
            md += f"{i}. [ ] {item}\n"

        md += """
---

## 10. Sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Safety Lead | | | |
| Development Lead | | | |
| Compliance Officer | | | |

---

*This safety plan was generated using the Governance AI Agent*
*Generated by: {data.get('skill_applied', 'governance-agent')}*
"""
        return md

    def _format_governance_plan_report(self, data: Dict[str, Any]) -> str:
        """Format governance plan as professional report (premium version)."""
        # For brevity, let's just make sure this is the same high-level professional style
        # since it's used for 'plan' mode.
        from datetime import datetime
        profile = data.get('system_profile', {})
        risk = data.get('risk_assessment', {})
        risk_category = risk.get('category', 'Unknown')

        md = f"""# 📋 Comprehensive AI Governance Plan

**System**: {profile.get('purpose', 'AI System')}
**Type**: {profile.get('type', 'Not specified')}
**Deployment**: {profile.get('geography', 'Global')} 
**Date**: {datetime.now().strftime('%Y-%m-%d')}

---

## 📊 Executive Summary
{data.get('executive_summary', 'No summary provided.')}

---

## 🔍 Risk & Regulation
- **EU AI Act Category**: {risk_category}
- **Internal Score**: {data.get('risk_score', '2/5')}
- **Compliance Baseline**: {', '.join(r['name'] for r in data.get('compliance_requirements', []))}

---

## 🏗️ Implementation Roadmap
"""
        for step in data.get('next_steps', []):
            md += f"### {step.get('phase', 'Phase')}\n"
            for task in step.get('tasks', []):
                md += f"- [ ] {task}\n"
        
        md += "\n---\n*Generated by Governance AI Agent*\n"
        return md
