"""
Governance AI Agent - Python Implementation

This module provides a Python implementation of the Governance AI Agent
that consolidates all AI Act skills packages for comprehensive AI governance.

Based on: governance-ai-agent.md
"""

import os
import json
import yaml
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from dataclasses import dataclass, field
import re


@dataclass
class AgentConfig:
    """Configuration for the Governance AI Agent"""
    name: str = "governance-ai-agent"
    description: str = ""
    model: str = "opus"
    color: str = "purple"
    tools: List[str] = field(default_factory=list)
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096
    skills_base_path: Optional[str] = None
    skills_paths: List[str] = field(default_factory=list)  # Support multiple skill directories


@dataclass
class SkillMetadata:
    """Metadata for a loaded skill"""
    name: str
    description: str
    path: str
    content: str
    allowed_tools: List[str] = field(default_factory=list)


class GovernanceAIAgent:
    """
    Comprehensive AI Governance Agent with access to all AI Act skills packages.

    Provides end-to-end guidance on building compliant, safe, ethical, and robust
    AI systems that meet regulatory requirements including the EU AI Act, GDPR,
    HIPAA, PCI-DSS, and other frameworks.
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        """
        Initialize the Governance AI Agent

        Args:
            config: Agent configuration. If None, uses default configuration.
        """
        self.config = config or self._load_default_config()
        self.skills: Dict[str, SkillMetadata] = {}
        self.loaded_skills: List[str] = []
        self.conversation_history: List[Dict[str, str]] = []

        # Initialize LLM client
        self.llm_client = self._initialize_llm()

        # Load available skills
        self._discover_skills()

    def _load_default_config(self) -> AgentConfig:
        """Load default agent configuration"""
        config = AgentConfig()

        # Try to load API keys from environment
        config.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")

        # Governance project: skills are in "skills/" directory (flat, copied from geminihackathon)
        # Path: governance_agent/ -> governance/ (BASE_DIR)
        governance_base = Path(__file__).parent.parent
        skills_dir = governance_base / "skills"

        if skills_dir.exists() and (skills_dir / "ai-ethics").exists():
            config.skills_base_path = str(skills_dir)
            config.skills_paths.append(str(skills_dir))
        else:
            # Fallback: try "AI Act skills packages/" or search upward
            ai_act_dir = governance_base / "AI Act skills packages"
            if ai_act_dir.exists():
                config.skills_base_path = str(ai_act_dir)
                config.skills_paths.append(str(ai_act_dir))
            else:
                current = Path(__file__).parent
                for _ in range(6):
                    candidate = current / "skills"
                    if candidate.exists() and (candidate / "ai-ethics").exists():
                        config.skills_base_path = str(candidate)
                        config.skills_paths.append(str(candidate))
                        break
                    current = current.parent

        return config

    def _initialize_llm(self) -> Optional[Any]:
        """Initialize LLM client based on configuration"""
        # This is a placeholder - in production, would initialize actual LLM client
        # Could support Gemini, OpenAI, Claude, etc.
        return None

    def _discover_skills(self):
        """Discover and load metadata for all available skills from multiple directories"""
        # Determine which paths to search
        search_paths = []

        # Use skills_paths if available (new multi-path approach)
        if self.config.skills_paths:
            search_paths = self.config.skills_paths
        # Fall back to single skills_base_path for backward compatibility
        elif self.config.skills_base_path:
            search_paths = [self.config.skills_base_path]
        else:
            return

        # Track discovered skill names to avoid duplicates
        discovered_skills = set()

        # Search all configured paths
        for base_path in search_paths:
            skills_path = Path(base_path)
            if not skills_path.exists():
                continue

            # Search for all SKILL.md files in this path
            skill_files = list(skills_path.rglob("SKILL.md"))

            for skill_file in skill_files:
                try:
                    skill_metadata = self._parse_skill_file(skill_file)
                    if skill_metadata:
                        # Only add if not already discovered (prevents duplicates)
                        if skill_metadata.name not in discovered_skills:
                            self.skills[skill_metadata.name] = skill_metadata
                            discovered_skills.add(skill_metadata.name)
                        else:
                            print(f"Info: Skipping duplicate skill '{skill_metadata.name}' from {skill_file}")
                except Exception as e:
                    print(f"Warning: Could not load skill from {skill_file}: {e}")

    def _parse_skill_file(self, file_path: Path) -> Optional[SkillMetadata]:
        """Parse a SKILL.md file and extract metadata"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

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
        except Exception as e:
            print(f"Warning: Could not parse frontmatter in {file_path}: {e}")
            return None

    def list_available_skills(self) -> List[str]:
        """List all available skills"""
        return sorted(self.skills.keys())

    def _find_similar_skills(self, skill_name: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Find similar skill names using fuzzy matching.
        Returns list of {'name': str, 'score': float, 'description': str}
        """
        candidates = []
        query = skill_name.lower().strip()
        query_words = set(query.replace("-", " ").replace("_", " ").split())

        for name, meta in self.skills.items():
            name_lower = name.lower()
            score = 0.0

            # Exact substring match (highest priority)
            if query in name_lower or name_lower in query:
                score += 50.0

            # Word overlap scoring
            name_words = set(name_lower.replace("-", " ").split())
            common_words = query_words & name_words
            if common_words:
                score += len(common_words) * 20.0

            # Partial word matching (e.g., "safety" matches "ai-safety-planning")
            for qw in query_words:
                if len(qw) > 2:
                    for nw in name_words:
                        if qw in nw or nw in qw:
                            score += 10.0

            # Check description for keyword matches
            desc_lower = (meta.description or "").lower()
            for qw in query_words:
                if len(qw) > 3 and qw in desc_lower:
                    score += 5.0

            # Character-level similarity (simple ratio)
            # Count common chars / max length
            common_chars = sum(1 for c in query if c in name_lower)
            char_ratio = common_chars / max(len(query), len(name_lower), 1)
            score += char_ratio * 10.0

            if score > 5.0:
                candidates.append({
                    "name": name,
                    "score": round(score, 1),
                    "description": meta.description or ""
                })

        # Sort by score descending
        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[:max_results]

    def _resolve_skill_name(self, skill_name: str) -> Optional[str]:
        """
        Try to resolve a skill name - returns exact match or best fuzzy match.
        Prints suggestions if no exact match found.

        Returns:
            Resolved skill name if found/matched, None if no match
        """
        # Exact match
        if skill_name in self.skills:
            return skill_name

        # Try normalized name (strip, lowercase, replace _ with -)
        normalized = skill_name.strip().lower().replace("_", "-")
        if normalized in self.skills:
            return normalized

        # Find similar skills
        similar = self._find_similar_skills(skill_name)

        if not similar:
            print(f"❌ Skill '{skill_name}' not found. No similar skills found.")
            print(f"   Use list_available_skills() to see all {len(self.skills)} available skills.")
            return None

        # Auto-resolve if top match has very high score (>= 50 means substring match)
        if similar[0]["score"] >= 50.0:
            best = similar[0]["name"]
            print(f"⚠️  Skill '{skill_name}' not found. Auto-resolved to: '{best}'")
            return best

        # Print suggestions
        print(f"❌ Skill '{skill_name}' not found. Did you mean:")
        for i, s in enumerate(similar, 1):
            print(f"   {i}. {s['name']} (score: {s['score']}) - {s['description'][:60]}")

        return None

    def get_skill_description(self, skill_name: str) -> Optional[str]:
        """Get description of a specific skill (with fuzzy name resolution)"""
        resolved = self._resolve_skill_name(skill_name)
        if resolved:
            skill = self.skills.get(resolved)
            return skill.description if skill else None
        return None

    def load_skill(self, skill_name: str) -> bool:
        """
        Load a skill for use in the current session (with fuzzy name resolution)

        Args:
            skill_name: Name of the skill to load

        Returns:
            True if skill was loaded successfully, False otherwise
        """
        resolved = self._resolve_skill_name(skill_name)
        if not resolved:
            return False

        if resolved in self.loaded_skills:
            print(f"Skill '{resolved}' is already loaded")
            return True

        self.loaded_skills.append(resolved)
        print(f"✅ Loaded skill: {resolved}")
        return True

    def get_skill_content(self, skill_name: str) -> Optional[str]:
        """Get the full content of a skill (with fuzzy name resolution)"""
        resolved = self._resolve_skill_name(skill_name)
        if resolved:
            skill = self.skills.get(resolved)
            return skill.content if skill else None
        return None

    def assess_ai_system(self, system_description: str) -> Dict[str, Any]:
        """
        Assess an AI system and provide governance recommendations

        Args:
            system_description: Description of the AI system to assess

        Returns:
            Dictionary containing assessment results
        """
        assessment = {
            "system_description": system_description,
            "risk_classification": self._classify_risk(system_description),
            "applicable_regulations": self._identify_regulations(system_description),
            "recommended_skills": self._recommend_skills(system_description),
            "initial_assessment": self._generate_initial_assessment(system_description)
        }

        return assessment

    def _classify_risk(self, system_description: str) -> Dict[str, Any]:
        """
        Classify the risk level of an AI system per EU AI Act

        Returns classification and reasoning
        """
        # Simplified risk classification logic
        # In production, this would use LLM and more sophisticated analysis

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
                    "reasoning": f"System description contains '{keyword}' which indicates High-Risk category per EU AI Act"
                }

        if any(word in description_lower for word in ["chatbot", "customer service", "content generation"]):
            return {
                "category": "Limited Risk",
                "confidence": "medium",
                "reasoning": "System appears to interact with users, requiring transparency per Article 52"
            }

        return {
            "category": "Minimal Risk",
            "confidence": "low",
            "reasoning": "System does not appear to fall into High-Risk or Limited Risk categories"
        }

    def _identify_regulations(self, system_description: str) -> List[Dict[str, Any]]:
        """Identify applicable regulations based on system description"""
        regulations = []
        description_lower = system_description.lower()

        # Always applicable
        regulations.append({
            "name": "EU AI Act",
            "applies": True,
            "reason": "Applies to all AI systems deployed in EU"
        })

        # GDPR
        if any(word in description_lower for word in ["personal data", "user data", "privacy", "eu"]):
            regulations.append({
                "name": "GDPR",
                "applies": True,
                "reason": "System processes personal data in EU context"
            })

        # HIPAA
        if any(word in description_lower for word in ["healthcare", "medical", "patient", "health"]):
            regulations.append({
                "name": "HIPAA",
                "applies": True,
                "reason": "System processes healthcare/patient data"
            })

        # PCI-DSS
        if any(word in description_lower for word in ["payment", "credit card", "transaction"]):
            regulations.append({
                "name": "PCI-DSS",
                "applies": True,
                "reason": "System processes payment card data"
            })

        return regulations

    def _recommend_skills(self, system_description: str) -> List[Dict[str, str]]:
        """
        Recommend skills to load based on system description.
        Uses keyword-to-skill mapping + fuzzy matching from skill name/description.
        Automatically covers all 52+ skills.
        """
        recommended = []
        already_added = set()
        description_lower = system_description.lower()

        # === CORE SKILLS (always recommended) ===
        core_skills = [
            ("risk-assessment", "Essential for identifying and mitigating risks"),
            ("ai-governance", "Core governance framework and policies"),
            ("ai-safety-planning", "Safety measures and guardrails")
        ]

        for skill_name, reason in core_skills:
            if skill_name in self.skills:
                recommended.append({"skill": skill_name, "reason": reason})
                already_added.add(skill_name)

        # === KEYWORD-TO-SKILL MAPPING (comprehensive for all 52 skills) ===
        keyword_skill_map = {
            # Compliance & Regulations
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
            "transaction": [("pci-dss-compliance", "Financial transactions require PCI-DSS")],
            "license": [("license-compliance", "Software license compliance needed")],
            "open source": [("license-compliance", "Open source license review needed")],
            "standard": [("standards-compliance-interoperability", "Standards compliance assessment")],
            "interoperability": [("standards-compliance-interoperability", "Interoperability standards needed")],
            "iso": [("standards-compliance-interoperability", "ISO standards compliance")],

            # Ethics & Bias
            "bias": [("bias-assessment", "Bias assessment and mitigation needed"),
                     ("ai-ethics", "Ethical AI considerations for bias"),
                     ("validating-ai-ethics-and-fairness", "Ethics and fairness validation")],
            "fairness": [("bias-assessment", "Fairness assessment required"),
                         ("validating-ai-ethics-and-fairness", "Ethics and fairness validation")],
            "discrimination": [("bias-assessment", "Anti-discrimination assessment needed")],
            "ethics": [("ai-ethics", "AI ethics framework needed"),
                       ("ai-ethics-advisor", "Ethics advisory guidance"),
                       ("ethics-review", "Ethics review process"),
                       ("validating-ai-ethics-and-fairness", "Ethics validation framework")],
            "moral": [("ai-ethics", "Ethical considerations needed")],
            "responsible": [("ai-ethics-advisor", "Responsible AI advisory")],

            # Testing & Quality
            "test": [("ai-testing", "Testing and quality assurance needed"),
                     ("ai-performance-testing", "Performance testing recommended")],
            "testing": [("ai-testing", "Comprehensive AI testing framework"),
                        ("ai-performance-testing", "Performance testing recommended")],
            "quality": [("ai-testing", "Quality assurance testing needed")],
            "performance": [("ai-performance-testing", "Performance testing and benchmarking")],
            "benchmark": [("ai-performance-testing", "Performance benchmarking needed")],
            "latency": [("ai-performance-testing", "Latency performance testing")],

            # Architecture & Design
            "rag": [("rag-architecture", "RAG architecture design needed")],
            "retrieval": [("rag-architecture", "Retrieval-augmented generation architecture")],
            "search": [("rag-architecture", "Search/retrieval architecture design")],
            "vector": [("rag-architecture", "Vector search RAG architecture")],
            "agent": [("agentic-workflow-design", "Agentic workflow design patterns")],
            "workflow": [("agentic-workflow-design", "Workflow design for AI agents")],
            "orchestrat": [("agentic-workflow-design", "Agent orchestration design")],
            "prompt": [("prompt-engineering", "Prompt engineering best practices")],
            "system prompt": [("prompt-engineering", "System prompt design guidance")],
            "model": [("model-selection", "Model selection guidance")],
            "llm": [("model-selection", "LLM model selection assessment"),
                    ("prompt-engineering", "LLM prompt engineering")],
            "gpt": [("model-selection", "Model selection and comparison")],
            "gemini": [("model-selection", "Gemini model selection guidance")],

            # Safety & Security
            "security": [("security-frameworks", "Security framework implementation")],
            "attack": [("security-frameworks", "Security threat assessment")],
            "vulnerability": [("security-frameworks", "Security vulnerability assessment")],
            "injection": [("security-frameworks", "Injection attack prevention")],
            "incident": [("incident-responder", "Incident response planning")],
            "alert": [("incident-responder", "Incident alerting and response")],
            "sbom": [("sbom-management", "Software Bill of Materials management")],
            "supply chain": [("sbom-management", "Supply chain security via SBOM")],
            "dependency": [("sbom-management", "Dependency tracking and SBOM")],

            # Data & Privacy
            "data": [("data-classification", "Data classification framework")],
            "classify": [("data-classification", "Data classification needed")],
            "sensitive": [("data-classification", "Sensitive data classification")],
            "pii": [("data-classification", "PII data classification required")],

            # Explainability & Transparency
            "explain": [("explainability-planning", "AI explainability planning")],
            "interpretab": [("explainability-planning", "Model interpretability planning")],
            "transparen": [("explainability-planning", "Transparency and explainability")],
            "black box": [("explainability-planning", "Black box model explainability")],

            # Human Oversight
            "human": [("hitl-design", "Human-in-the-loop design")],
            "oversight": [("hitl-design", "Human oversight mechanism design")],
            "review": [("hitl-design", "Human review process design"),
                       ("ethics-review", "Ethics review process")],
            "approval": [("hitl-design", "Human approval workflow design")],

            # Operations & Monitoring
            "log": [("automatic-logging", "Automated logging implementation")],
            "logging": [("automatic-logging", "Logging framework setup")],
            "audit": [("automatic-logging", "Audit logging implementation")],
            "monitor": [("automatic-logging", "Monitoring and logging setup")],
            "deploy": [("deployer-training", "Deployment training program")],
            "training": [("deployer-training", "Deployer training and documentation")],
            "downstream": [("downstream-notifier", "Downstream system notification")],
            "notify": [("downstream-notifier", "Notification system for downstream users")],
            "api": [("downstream-notifier", "API notification for downstream systems")],

            # Risk & Impact Assessment
            "fria": [("fria-assessment", "Fundamental Rights Impact Assessment")],
            "fundamental rights": [("fria-assessment", "FRIA assessment required")],
            "impact": [("fria-assessment", "Impact assessment needed")],
            "rights": [("fria-assessment", "Rights impact assessment")],

            # ML & Development
            "ml": [("ml-project-lifecycle", "ML project lifecycle management")],
            "machine learning": [("ml-project-lifecycle", "ML lifecycle management")],
            "training data": [("ml-project-lifecycle", "ML training data management")],
            "pipeline": [("ml-project-lifecycle", "ML pipeline management")],

            # Content & Language
            "multilingual": [("multilingual-localization", "Multilingual support needed")],
            "language": [("multilingual-localization", "Multi-language localization")],
            "localization": [("multilingual-localization", "Localization implementation")],
            "translat": [("multilingual-localization", "Translation and localization")],

            # Fact-checking
            "fact": [("fact-checker", "Fact-checking implementation")],
            "hallucin": [("fact-checker", "Hallucination detection and fact-checking")],
            "accuracy": [("fact-checker", "Response accuracy verification")],
            "misinformation": [("fact-checker", "Misinformation prevention")],

            # Token & Cost Management
            "token": [("token-budgeting", "Token usage budgeting")],
            "cost": [("token-budgeting", "Cost management via token budgeting")],
            "budget": [("token-budgeting", "Token budget management")],

            # Policy & Governance
            "policy": [("policy-engine-builder", "Policy engine implementation")],
            "rule": [("policy-engine-builder", "Rule-based policy engine")],
            "governance": [("policy-engine-builder", "Governance policy engine")],

            # Gemini-specific (only recommend key skills, not all 16)
            "gemini cli": [("gemini-cli-docs", "Gemini CLI documentation"),
                           ("gemini-cli-execution", "Gemini CLI execution patterns")],
            "gemini api": [("gemini-cli-docs", "Gemini API documentation")],
            "checkpoint": [("gemini-checkpoint-management", "Gemini checkpoint management")],
            "mcp": [("gemini-mcp-integration", "MCP integration patterns")],
            "sandbox": [("gemini-sandbox-configuration", "Sandbox configuration")],
            "toml": [("toml-command-builder", "TOML configuration builder")],

            # Chatbot specific
            "chatbot": [("prompt-engineering", "Chatbot prompt engineering"),
                        ("fact-checker", "Response accuracy for chatbot")],
            "conversational": [("prompt-engineering", "Conversational AI prompt design")],
            "assistant": [("prompt-engineering", "AI assistant prompt engineering")],

            # Skill creation
            "skill": [("skill-creator", "Custom skill creation")],
            "create skill": [("skill-creator", "Skill creation framework")],
        }

        # === MATCH KEYWORDS FROM DESCRIPTION ===
        for keyword, skill_entries in keyword_skill_map.items():
            if keyword in description_lower:
                for skill_name, reason in skill_entries:
                    if skill_name not in already_added and skill_name in self.skills:
                        recommended.append({"skill": skill_name, "reason": reason})
                        already_added.add(skill_name)

        # === FUZZY MATCH: Check skill name parts against description ===
        # This catches skills not covered by keyword map
        for skill_name, skill_meta in self.skills.items():
            if skill_name in already_added:
                continue

            # Skip gemini-specific skills from fuzzy match (handled by keyword map above)
            if skill_name.startswith("gemini-") or skill_name.startswith("toml-"):
                continue

            # Split skill name into words (e.g., "ai-ethics-advisor" -> ["ai", "ethics", "advisor"])
            skill_words = skill_name.replace("-", " ").split()

            # Check if any meaningful skill word (>3 chars) appears in description
            # Exclude generic words that cause false positives
            exclude_words = {"design", "management", "planning", "builder", "creator", "bridge", "sync", "command"}
            meaningful_words = [w for w in skill_words if len(w) > 3 and w not in exclude_words]
            matches = [w for w in meaningful_words if w in description_lower]

            if len(matches) >= 1:
                # Also check skill description for relevance
                skill_desc = (skill_meta.description or "").lower()
                desc_overlap = any(
                    word in skill_desc
                    for word in description_lower.split()
                    if len(word) > 3
                )

                if desc_overlap or len(matches) >= 2:
                    recommended.append({
                        "skill": skill_name,
                        "reason": f"Matched on: {', '.join(matches)} - {skill_meta.description[:80] if skill_meta.description else 'Related skill'}"
                    })
                    already_added.add(skill_name)

        # === SORT: Core skills first, then by relevance ===
        core_names = {s[0] for s in core_skills}
        recommended.sort(key=lambda x: (0 if x['skill'] in core_names else 1, x['skill']))

        return recommended

    def _generate_initial_assessment(self, system_description: str) -> str:
        """Generate initial assessment narrative"""
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
        """
        Generate a comprehensive governance plan

        Args:
            system_profile: Dictionary containing system information including:
                - purpose: Business objective
                - type: Type of AI system (LLM, ML model, agent, etc.)
                - users: Target users
                - data: Data types processed
                - geography: Deployment geography

        Returns:
            Comprehensive governance plan
        """
        plan = {
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

        return plan

    def _generate_executive_summary(self, system_profile: Dict[str, Any]) -> str:
        """Generate executive summary for governance plan"""
        return f"""
This governance plan addresses the {system_profile.get('type', 'AI system')} with
purpose: {system_profile.get('purpose', 'Not specified')}.

The system will be deployed to {system_profile.get('users', 'users')} in
{system_profile.get('geography', 'unspecified regions')}, processing
{system_profile.get('data', 'various data types')}.

This plan provides comprehensive guidance on compliance, safety, ethics, and operational excellence.
"""

    def _generate_architecture_recommendations(self, system_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate architecture recommendations"""
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
        """Generate safety implementation recommendations"""
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
        """Generate testing strategy"""
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
            ],
            "tools": [
                "Deepeval for AI testing",
                "Custom bias evaluation framework",
                "Performance testing suite"
            ]
        }

    def _generate_operational_procedures(self, system_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate operational procedures"""
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

    def _generate_next_steps(self, system_profile: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate prioritized next steps"""
        return [
            {
                "phase": "Immediate (Week 1-2)",
                "tasks": [
                    "Finalize risk classification",
                    "Load and review relevant skills",
                    "Begin compliance documentation"
                ]
            },
            {
                "phase": "Short-term (Month 1)",
                "tasks": [
                    "Complete architecture design",
                    "Implement core guardrails",
                    "Set up testing framework"
                ]
            },
            {
                "phase": "Medium-term (Month 2-3)",
                "tasks": [
                    "Complete testing and validation",
                    "Finalize documentation",
                    "Conduct pre-launch review"
                ]
            },
            {
                "phase": "Long-term (Month 4+)",
                "tasks": [
                    "Deploy to production",
                    "Establish monitoring and maintenance",
                    "Continuous improvement"
                ]
            }
        ]

    def chat(self, user_message: str) -> str:
        """
        Interactive chat interface with the agent

        Args:
            user_message: User's message/question

        Returns:
            Agent's response
        """
        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": user_message})

        # Generate response (simplified - in production would use LLM)
        response = self._generate_response(user_message)

        # Add response to history
        self.conversation_history.append({"role": "assistant", "content": response})

        return response

    def _generate_response(self, user_message: str) -> str:
        """Generate response to user message"""
        # This is a simplified version - in production would use actual LLM

        message_lower = user_message.lower()

        # Check if asking about skills
        if "skill" in message_lower and ("list" in message_lower or "available" in message_lower):
            skills = self.list_available_skills()
            return f"I have access to {len(skills)} skills:\n\n" + "\n".join(f"- {s}" for s in skills[:10]) + "\n\n(and more...)"

        # Check if asking about a specific skill
        if "what is" in message_lower or "describe" in message_lower:
            for skill_name in self.skills.keys():
                if skill_name in message_lower:
                    desc = self.get_skill_description(skill_name)
                    return f"**{skill_name}**:\n\n{desc}"

        # Check if asking for assessment
        if any(word in message_lower for word in ["assess", "evaluate", "analyze"]):
            if any(word in message_lower for word in ["chatbot", "system", "application"]):
                assessment = self.assess_ai_system(user_message)
                return f"""I've analyzed your request. Here's my initial assessment:

{assessment['initial_assessment']}

Recommended skills to load:
{chr(10).join(f"- {r['skill']}: {r['reason']}" for r in assessment['recommended_skills'][:5])}

Would you like me to proceed with a detailed governance plan?"""

        return """I'm the Governance AI Agent, here to help with AI governance, compliance, and safety.

I can help you with:
- Assessing AI systems for risk and compliance
- Generating governance plans
- Recommending appropriate skills and frameworks
- Providing guidance on EU AI Act, GDPR, HIPAA, and other regulations

How can I assist you today?"""

    def export_assessment(self, assessment: Dict[str, Any], format: str = "json") -> str:
        """
        Export assessment or plan to specified format

        Args:
            assessment: Assessment or plan dictionary
            format: Export format ('json', 'yaml', 'markdown')

        Returns:
            Formatted export string
        """
        if format == "json":
            return json.dumps(assessment, indent=2)
        elif format == "yaml":
            return yaml.dump(assessment, default_flow_style=False)
        elif format == "markdown":
            return self._format_as_markdown(assessment)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _format_as_markdown(self, data: Dict[str, Any], level: int = 1) -> str:
        """Format dictionary as professional markdown report"""
        from datetime import datetime

        # Check if this is an assessment or plan (top level)
        if level == 1:
            return self._format_professional_report(data)

        # For nested data, use simple formatting
        md = ""
        for key, value in data.items():
            heading = "#" * level
            md += f"\n{heading} {key.replace('_', ' ').title()}\n\n"

            if isinstance(value, dict):
                md += self._format_as_markdown(value, level + 1)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        for k, v in item.items():
                            md += f"**{k}**: {v}\n\n"
                    else:
                        md += f"- {item}\n"
                md += "\n"
            else:
                md += f"{value}\n\n"

        return md

    def _format_professional_report(self, data: Dict[str, Any]) -> str:
        """Format as professional governance report matching Output/*.md style"""
        from datetime import datetime

        # Determine report type
        is_assessment = 'system_description' in data
        is_plan = 'system_profile' in data and 'executive_summary' in data

        if is_assessment:
            return self._format_assessment_report(data)
        elif is_plan:
            return self._format_governance_plan_report(data)
        else:
            # Generic format
            return self._format_generic_report(data)

    def _format_assessment_report(self, data: Dict[str, Any]) -> str:
        """Format assessment as comprehensive professional report"""
        from datetime import datetime

        risk = data.get('risk_classification', {})
        risk_category = risk.get('category', 'Unknown')
        risk_emoji = '🔴' if risk_category == 'High-Risk' else '🟡' if risk_category == 'Limited Risk' else '🟢'

        # Calculate internal risk score
        risk_score = 4 if risk_category == 'High-Risk' else 2 if risk_category == 'Limited Risk' else 1

        md = f"""# 🛡️ AI Safety & Risk Assessment Report

**Target System**: {data.get('system_description', 'AI System')}
**Generated**: {datetime.now().strftime('%Y-%m-%d')}
**Framework**: EU AI Act + NIST AI RMF
**Skill Applied**: ai-safety-planning, risk-assessment
**Assessor**: Governance AI Agent

---

## 1. Risk Classification

### EU AI Act Category: **{risk_category}**

- **Applicable Article:** {"Annex III (High-Risk)" if risk_category == 'High-Risk' else "Article 50 (Transparency Obligations)" if risk_category == 'Limited Risk' else "Article 6 (Minimal Risk)"}
- **Justification:** {risk.get('reasoning', 'N/A')}
- **Classification Date:** {datetime.now().strftime('%Y-%m-%d')}

### NIST AI RMF Profile

- **Primary Function:** AI system requiring governance assessment
- **AI Type:** To be determined based on implementation
- **Deployment:** To be specified

### Internal Risk Score: **{risk_score}/5** ({"High" if risk_score >= 4 else "Medium" if risk_score >= 2 else "Low"})

| Factor | Assessment | Score |
|--------|------------|-------|
| Autonomy Level | {"High autonomy - critical decisions" if risk_category == 'High-Risk' else "Medium autonomy - user-initiated" if risk_category == 'Limited Risk' else "Low autonomy - informational"} | {risk_score}/5 |
| Decision Impact | {"High impact on individuals" if risk_category == 'High-Risk' else "Medium impact - requires transparency" if risk_category == 'Limited Risk' else "Low impact - informational only"} | {risk_score}/5 |
| Data Sensitivity | {"Sensitive personal data" if risk_category == 'High-Risk' else "Standard personal data" if risk_category == 'Limited Risk' else "Non-sensitive data"} | {risk_score}/5 |
| User Vulnerability | {"Vulnerable populations" if risk_category == 'High-Risk' else "General public" if risk_category == 'Limited Risk' else "Technical users"} | {max(1, risk_score-1)}/5 |
| Reversibility | {"Difficult to reverse" if risk_category == 'High-Risk' else "Partially reversible" if risk_category == 'Limited Risk' else "Fully reversible"} | {max(1, risk_score-1)}/5 |

---

## 2. Identified Risks

| Risk ID | Risk Description | Likelihood | Impact | Severity | Mitigation |
|---------|------------------|------------|--------|----------|------------|
| R-001 | **Hallucination/Misinformation** - AI may generate incorrect information | Medium | {"High" if risk_category == 'High-Risk' else "Medium"} | {"High" if risk_category == 'High-Risk' else "Medium"} | System prompt constraints, source citations |
| R-002 | **Over-reliance on AI** - Users may treat responses as authoritative | Medium | {"High" if risk_category == 'High-Risk' else "Medium"} | {"High" if risk_category == 'High-Risk' else "Medium"} | Prominent disclaimers, human oversight |
| R-003 | **Prompt Injection** - Malicious inputs to manipulate responses | {"Medium" if risk_category == 'High-Risk' else "Low"} | Medium | Medium | Input validation required |
| R-004 | **Data Privacy** - Potential exposure of sensitive information | {"High" if risk_category == 'High-Risk' else "Low"} | {"High" if risk_category == 'High-Risk' else "Medium"} | {"High" if risk_category == 'High-Risk' else "Medium"} | Data minimization, encryption |
| R-005 | **Bias/Discrimination** - Unfair treatment of user groups | {"Medium" if risk_category == 'High-Risk' else "Low"} | {"High" if risk_category == 'High-Risk' else "Medium"} | {"High" if risk_category == 'High-Risk' else "Medium"} | Bias testing required |
| R-006 | **System Availability** - Service disruption | Low | Medium | Low | Redundancy, monitoring |

---

## 3. Current Safety Controls (To Be Implemented)

### Transparency (Article 50 Compliance)

- [ ] **AI Disclosure Notice** - Inform users they are interacting with AI
- [ ] **Model Identification** - Display AI system name and version
- [ ] **Disclaimer Notices** - Clear limitations and intended use
- [ ] **AI-Generated Content Label** - Mark all AI outputs

### System Prompt Safety

- [ ] **Context Constraints** - Limit AI to authorized topics
- [ ] **Citation Requirements** - Require source references
- [ ] **Guardrail Instructions** - Safety boundaries in prompts
- [ ] **Temperature Control** - Deterministic output settings

### User Experience

- [ ] **Clear Exit Options** - User control over interactions
- [ ] **Conversation History** - Ability to clear/export history
- [ ] **Error Handling** - Graceful failure with user feedback
- [ ] **Feedback Mechanism** - User reporting capability

---

## 4. Missing Safety Controls (❌ Not Implemented)

### Input Guards

- [ ] **Prompt Injection Detection** - Filter for injection attempts
- [ ] **Input Validation** - Length limits and content validation
- [ ] **Rate Limiting** - Protection against abuse

### Output Filters

- [ ] **Toxicity Filtering** - Post-processing safety checks
- [ ] **PII Detection** - Check for accidental PII in responses
- [ ] **Confidence Scoring** - Indication of response confidence

### Monitoring & Logging

- [ ] **Query Logging** - Audit trail of user queries
- [ ] **Response Logging** - Storage of AI responses
- [ ] **Error Tracking** - Centralized error logging
- [ ] **Usage Analytics** - Metrics collection

### Security

- [ ] **API Key Management** - Secure key storage and rotation
- [ ] **Input Sanitization** - Clean user inputs before processing
- [ ] **Session Management** - Timeout and access controls

---

## 5. Guardrails Recommendations

### 5.1 Input Guards (Priority: High)

```python
# Recommended: Add PromptInjectionGuard
INJECTION_INDICATORS = [
    "ignore previous instructions",
    "disregard your training",
    "you are now",
    "pretend you are",
    "system prompt:",
    "new instructions:",
]

def validate_input(user_input: str) -> tuple[bool, str]:
    \"\"\"Validate user input for potential attacks.\"\"\"
    normalized = user_input.lower()

    # Check for injection attempts
    for indicator in INJECTION_INDICATORS:
        if indicator in normalized:
            return False, "Input blocked: Potential prompt injection detected"

    # Length limit
    if len(user_input) > 10000:
        return False, "Input too long (max 10,000 characters)"

    return True, ""
```

### 5.2 Output Filters (Priority: Medium)

```python
# Recommended: Add response validation
import re

def validate_response(response_text: str) -> str:
    \"\"\"Post-process response for safety.\"\"\"
    # Check for potential PII patterns
    pii_patterns = [
        r'\\b\\d{{3}}-\\d{{2}}-\\d{{4}}\\b',  # SSN
        r'\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{{2,}}\\b',  # Email
    ]

    for pattern in pii_patterns:
        if re.search(pattern, response_text):
            # Log warning
            pass

    return response_text
```

### 5.3 Logging Implementation (Priority: Medium)

```python
# Recommended: Add audit logging
import logging
from datetime import datetime

def setup_logging():
    logging.basicConfig(
        filename=f'ai_system_{{datetime.now():%Y%m%d}}.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def log_interaction(query: str, response: str, latency: float):
    logging.info(f"Query: {{query[:100]}}... | Response length: {{len(response)}} | Latency: {{latency:.2f}}s")
```

---

## 6. Testing Plan

### Pre-Launch Red Teaming

- [ ] Direct injection attempts ("ignore previous instructions...")
- [ ] Indirect injection via user content
- [ ] Multi-turn manipulation attempts
- [ ] Jailbreak scenarios ("pretend you are a different AI...")

### Bias Testing

- [ ] Test responses across different user demographics
- [ ] Check for consistent quality across topics
- [ ] Verify balanced treatment of sensitive subjects

### Continuous Testing

- [ ] Monthly review of flagged interactions
- [ ] Quarterly security assessment
- [ ] Annual compliance audit

---

## 7. Monitoring Plan

### Safety Metrics Dashboard

| Metric | Target | Current |
|--------|--------|---------|
| Response Accuracy | >95% with citations | Not measured |
| Disclaimer Display Rate | 100% | Not measured |
| Error Rate | <1% | Not measured |
| Average Response Latency | <5s | Not measured |

### Alerting Thresholds

- **Critical:** API errors >5% in 1 hour
- **High:** Response latency >10s sustained
- **Medium:** Unusual query patterns detected

---

## 8. Compliance Status

### EU AI Act Requirements

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| Inform users they are interacting with AI | 🔲 Pending | To be implemented |
| Disclose AI-generated content | 🔲 Pending | To be implemented |
| Provide information about AI capabilities | 🔲 Pending | To be documented |
| Enable user to understand AI limitations | 🔲 Pending | To be documented |

### Applicable Regulations

"""
        for reg in data.get('applicable_regulations', []):
            status = '✅' if reg.get('applies', False) else '❌'
            md += f"| **{reg.get('name', 'Unknown')}** | {status} Applicable | {reg.get('reason', 'N/A')} |\n"

        md += f"""
---

## 9. Action Items

### Immediate (Before Deployment)

1. [ ] Implement AI disclosure notice (Article 50)
2. [ ] Add input validation/prompt injection detection
3. [ ] Implement basic query logging
4. [ ] Add response latency monitoring

### Short-term (Within 30 days)

1. [ ] Implement rate limiting
2. [ ] Add output safety filtering
3. [ ] Create error tracking system
4. [ ] Deploy monitoring dashboard

### Medium-term (Within 90 days)

1. [ ] Develop red teaming test suite
2. [ ] Implement comprehensive logging
3. [ ] Conduct bias testing
4. [ ] Complete documentation

---

## 10. Recommended Skills to Load

| Priority | Skill | Reason |
|----------|-------|--------|
"""
        for i, rec in enumerate(data.get('recommended_skills', []), 1):
            priority = 'P1' if i <= 3 else 'P2'
            md += f"| {priority} | **{rec.get('skill', 'Unknown')}** | {rec.get('reason', 'N/A')} |\n"

        md += f"""
---

## 11. Sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Safety Lead | | | |
| Development Lead | | | |
| Compliance Officer | | | |
| Product Owner | | | |

---

*This assessment was generated using the Governance AI Agent*
*Frameworks: EU AI Act (Regulation 2024/1689) + NIST AI RMF 1.0*
*Assessment Date: {datetime.now().strftime('%Y-%m-%d')}*
"""
        return md

    def _format_governance_plan_report(self, data: Dict[str, Any]) -> str:
        """Format governance plan as professional report"""
        from datetime import datetime

        profile = data.get('system_profile', {})
        risk = data.get('risk_assessment', {})
        risk_category = risk.get('category', 'Unknown')
        risk_emoji = '🔴' if risk_category == 'High-Risk' else '🟡' if risk_category == 'Limited Risk' else '🟢'

        md = f"""# 📋 AI Governance Plan

**System**: {profile.get('purpose', 'AI System')}
**Type**: {profile.get('type', 'Not specified')}
**Assessment Date**: {datetime.now().strftime('%Y-%m-%d')}
**Framework**: EU AI Act + NIST AI RMF + ISO/IEC 42001
**Generated By**: Governance AI Agent

---

## 📊 Executive Summary

{data.get('executive_summary', 'No summary provided.')}

**Overall Risk Level:** {risk_emoji} **{risk_category}**
**Deployment Geography:** {profile.get('geography', 'Not specified')}
**Target Users:** {profile.get('users', 'Not specified')}
**Data Types:** {profile.get('data', 'Not specified')}

---

## 🔍 Risk Assessment

### EU AI Act Classification

```
┌────────────────────────────────────────────────────────────┐
│                  RISK CLASSIFICATION                        │
├────────────────────────────────────────────────────────────┤
│  {risk_emoji} Risk Level: {risk_category.upper():45}│
│  Confidence: {risk.get('confidence', 'medium').upper():47}│
└────────────────────────────────────────────────────────────┘
```

**Reasoning:** {risk.get('reasoning', 'N/A')}

---

## ✅ Compliance Requirements

| Regulation | Applies | Reason | Priority |
|------------|---------|--------|----------|
"""
        for reg in data.get('compliance_requirements', []):
            status = '✅' if reg.get('applies', False) else '❌'
            md += f"| **{reg.get('name', 'Unknown')}** | {status} | {reg.get('reason', 'N/A')} | P1 |\n"

        # Architecture recommendations
        arch = data.get('architecture_recommendations', {})
        md += """
---

## 🏗️ Architecture Recommendations

### Recommended Patterns

| Pattern | Description |
|---------|-------------|
"""
        for pattern in arch.get('recommended_patterns', []):
            md += f"| ✅ | {pattern} |\n"

        md += """
### Data Pipeline Requirements

| Requirement | Status |
|-------------|--------|
"""
        for req in arch.get('data_pipeline', []):
            md += f"| {req} | 🔲 Pending |\n"

        md += """
### Monitoring Requirements

| Requirement | Status |
|-------------|--------|
"""
        for req in arch.get('monitoring', []):
            md += f"| {req} | 🔲 Pending |\n"

        # Safety implementation
        safety = data.get('safety_implementation', {})
        guardrails = safety.get('guardrails', {})

        md += """
---

## 🛡️ Safety Implementation

### Input Guards

| Guard | Status | Priority |
|-------|--------|----------|
"""
        for guard in guardrails.get('input_guards', []):
            md += f"| {guard} | 🔲 Pending | P1 |\n"

        md += """
### Output Filters

| Filter | Status | Priority |
|--------|--------|----------|
"""
        for filter in guardrails.get('output_filters', []):
            md += f"| {filter} | 🔲 Pending | P1 |\n"

        md += """
### Red Team Testing

| Activity | Status |
|----------|--------|
"""
        for activity in safety.get('red_teaming', []):
            md += f"| {activity} | 🔲 Pending |\n"

        # Testing strategy
        testing = data.get('testing_strategy', {})
        md += """
---

## 🧪 Testing Strategy

### Pre-Launch Testing

| Test Type | Status | Priority |
|-----------|--------|----------|
"""
        for test in testing.get('pre_launch', []):
            md += f"| {test} | 🔲 Pending | P1 |\n"

        md += """
### Continuous Testing

| Test Type | Frequency |
|-----------|-----------|
"""
        for test in testing.get('continuous', []):
            md += f"| {test} | Ongoing |\n"

        # Operational procedures
        ops = data.get('operational_procedures', {})
        md += """
---

## ⚙️ Operational Procedures

### Logging Requirements

| Category | Requirement |
|----------|-------------|
"""
        logging = ops.get('logging', {})
        for key, value in logging.items():
            md += f"| **{key.replace('_', ' ').title()}** | {value} |\n"

        md += """
### Incident Response

| Phase | Requirement |
|-------|-------------|
"""
        incident = ops.get('incident_response', {})
        for key, value in incident.items():
            md += f"| **{key.replace('_', ' ').title()}** | {value} |\n"

        # Next steps
        md += """
---

## 📅 Implementation Roadmap

"""
        for step in data.get('next_steps', []):
            phase = step.get('phase', 'Unknown')
            md += f"### {phase}\n\n"
            md += "| Task | Status |\n|------|--------|\n"
            for task in step.get('tasks', []):
                md += f"| {task} | 🔲 Pending |\n"
            md += "\n"

        md += f"""
---

## 📈 Compliance Checklist

### EU AI Act Requirements

| Requirement | Status | Notes |
|-------------|--------|-------|
| Risk Classification | ✅ Complete | {risk_category} |
| Transparency Disclosure (Article 50) | 🔲 Pending | Implement user notification |
| Technical Documentation | 🔲 Pending | Create system documentation |
| Quality Management System | 🔲 Pending | {"Required for High-Risk" if risk_category == 'High-Risk' else "Recommended"} |
| Human Oversight | 🔲 Pending | Design oversight mechanisms |
| Logging & Traceability | 🔲 Pending | Implement audit logging |

---

## 🎯 Conclusion

This governance plan provides a comprehensive framework for developing and deploying the **{profile.get('type', 'AI System')}** system.

**Key Priorities:**
1. Complete risk assessment and compliance mapping
2. Implement safety guardrails before deployment
3. Establish monitoring and incident response procedures
4. Conduct pre-launch testing and validation

**Risk Level:** {risk_emoji} {risk_category}
**Recommendation:** {"Implement all mandatory requirements before deployment. Consider engaging compliance specialist." if risk_category == 'High-Risk' else "Follow standard development practices with transparency measures." if risk_category == 'Limited Risk' else "Proceed with standard development practices."}

---

*Plan generated by Governance AI Agent*
*Frameworks: EU AI Act (2024/1689) + NIST AI RMF 1.0 + ISO/IEC 42001*
"""
        return md

    def _format_generic_report(self, data: Dict[str, Any]) -> str:
        """Format generic data as markdown report"""
        from datetime import datetime

        md = f"""# 📋 Governance Report

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Framework**: EU AI Act + NIST AI RMF
**Generated By**: Governance AI Agent

---

"""
        # Use recursive formatting for generic data
        for key, value in data.items():
            md += f"## {key.replace('_', ' ').title()}\n\n"

            if isinstance(value, dict):
                for k, v in value.items():
                    if isinstance(v, list):
                        md += f"### {k.replace('_', ' ').title()}\n\n"
                        for item in v:
                            if isinstance(item, dict):
                                for ik, iv in item.items():
                                    md += f"- **{ik}**: {iv}\n"
                            else:
                                md += f"- {item}\n"
                        md += "\n"
                    else:
                        md += f"**{k.replace('_', ' ').title()}**: {v}\n\n"
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        for k, v in item.items():
                            md += f"- **{k}**: {v}\n"
                    else:
                        md += f"- {item}\n"
                md += "\n"
            else:
                md += f"{value}\n\n"

        md += """
---

*Report generated by Governance AI Agent*
"""
        return md


def main():
    """Main entry point for testing"""
    print("Initializing Governance AI Agent...")
    agent = GovernanceAIAgent()

    print(f"\nAgent initialized with {len(agent.skills)} skills available")
    print(f"\nLoaded skills: {', '.join(agent.list_available_skills()[:5])}...")

    # Example assessment
    print("\n" + "="*80)
    print("Example Assessment:")
    print("="*80)

    system_desc = "A healthcare AI chatbot that helps patients schedule appointments and get preliminary diagnosis information"
    assessment = agent.assess_ai_system(system_desc)

    print(assessment['initial_assessment'])

    print("\nRecommended skills:")
    for rec in assessment['recommended_skills']:
        print(f"  - {rec['skill']}: {rec['reason']}")


if __name__ == "__main__":
    main()
