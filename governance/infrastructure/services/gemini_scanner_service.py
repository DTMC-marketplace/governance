"""
Service for AI Act Scanning and Skill Discovery using Gemini.
Integrates GovernanceAgentService for comprehensive risk assessment and skill recommendation.
"""
import os
import json
import logging
import yaml
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

from django.conf import settings

logger = logging.getLogger(__name__)

# Document extraction imports
try:
    import pypdf
except ImportError:
    pypdf = None

try:
    import docx
except ImportError:
    docx = None


class GeminiScannerService:
    """
    Service to perform AI Act compliance scans using Gemini.
    Uses GovernanceAgentService for risk classification, skill recommendation,
    and governance plan generation.
    """

    # Class-level cache for discovered skills (shared across instances)
    _skills_cache = None
    _cache_timestamp = None
    _cache_ttl = 300  # Cache for 5 minutes

    def __init__(self):
        self.api_key = getattr(settings, 'GEMINI_API_KEY', '') or os.environ.get('GEMINI_API_KEY', '')
        self.model_name = getattr(settings, 'AI_ACT_MODEL_NAME', 'gemini-3-pro-preview')

        self.client = None
        if genai and self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client in ScannerService: {e}")
        elif not self.api_key:
            logger.warning("GEMINI_API_KEY not configured — ScannerService will use mock mode")

        self.skills_dir = Path(settings.BASE_DIR) / "skills"
        # Fallback to "AI Act skills packages" if "skills/" doesn't exist
        if not self.skills_dir.exists():
            self.skills_dir = Path(settings.BASE_DIR) / "AI Act skills packages"
        self.checklist_path = Path(settings.BASE_DIR) / "skills" / "compliance_checklist_high_risk.yaml"
        if not self.checklist_path.exists():
            self.checklist_path = Path(settings.BASE_DIR) / "AI Act skills packages" / "compliance_checklist_high_risk.yaml"

        # Initialize GovernanceAgentService (lazy - created on first use)
        self._governance_agent = None

    def _get_governance_agent(self):
        """Get or create GovernanceAgentService singleton."""
        if self._governance_agent is None:
            try:
                from .governance_agent_service import get_governance_agent_service
                self._governance_agent = get_governance_agent_service()
                logger.info(f"GovernanceAgentService loaded with {len(self._governance_agent.skills)} skills")
            except Exception as e:
                logger.warning(f"Could not initialize GovernanceAgentService: {e}")
        return self._governance_agent

    def _discover_skills(self) -> Dict[str, str]:
        """Dynamically discover all SKILL.md files and their relative paths (with caching)."""
        import time
        
        # Check if cache is valid
        current_time = time.time()
        if (self._skills_cache is not None and 
            self._cache_timestamp is not None and 
            (current_time - self._cache_timestamp) < self._cache_ttl):
            logger.debug("Returning cached skills")
            return self._skills_cache
        
        logger.info("Discovering skills (cache miss or expired)")
        skills = {}
        if not self.skills_dir.exists():
            return skills
        
        # Limit depth to avoid scanning too deep (max 3 levels)
        max_depth = 3
        base_depth = str(self.skills_dir).count(os.sep)
        
        for root, dirs, files in os.walk(self.skills_dir):
            current_depth = str(root).count(os.sep) - base_depth
            
            # Limit depth
            if current_depth >= max_depth:
                dirs[:] = []  # Don't recurse deeper
                continue
            
            for file in files:
                if file.endswith("SKILL.md"):
                    full_path = Path(root) / file
                    rel_path = full_path.relative_to(self.skills_dir)
                    # Use the parent directory name or the filename as the key
                    parent_name = rel_path.parent.name
                    if not parent_name or parent_name == ".":
                        skill_id = rel_path.stem.replace("-SKILL", "").replace("SKILL", "").strip("-")
                    else:
                        skill_id = parent_name
                    skills[skill_id] = str(rel_path)
        
        # Update cache
        GeminiScannerService._skills_cache = skills
        GeminiScannerService._cache_timestamp = current_time
        logger.info(f"Discovered {len(skills)} skills")
        
        return skills

    def _load_skill_content(self, tool_id: str) -> str:
        """Load content for a specific tool by searching discovered skills."""
        skills_map = self._discover_skills()

        skill_rel_path = skills_map.get(tool_id)
        
        if not skill_rel_path:
            # Fallback fuzzy matching
            for sid, path in skills_map.items():
                if tool_id in sid or sid in tool_id:
                    skill_rel_path = path
                    break
                    
        if skill_rel_path:
            full_path = self.skills_dir / skill_rel_path
            if full_path.exists():
                try:
                    content = full_path.read_text(encoding='utf-8')
                    logger.info(f"Loaded Skill Content from: {full_path} (Length: {len(content)} chars)")
                    return content
                except Exception as e:
                    logger.error(f"Error reading skill file {full_path}: {e}")
        
        logger.warning(f"No skill content found for tool_id: {tool_id}")
        return ""

    def _load_checklist(self) -> str:
        """Load the high-risk compliance checklist as reference."""
        if self.checklist_path.exists():
            try:
                # We return it as text to feed into LLM context
                return self.checklist_path.read_text(encoding='utf-8')
            except Exception as e:
                logger.error(f"Error reading checklist: {e}")
        return ""

    def run_scan(self, project_data: Dict[str, Any], tool_id: str) -> Dict[str, Any]:
        """
        Run a compliance scan for a project using a specific tool.

        Flow:
        1. Use GovernanceAgentService to assess the project and get risk/skill recommendations
        2. Load skill content for the specific tool_id
        3. Load compliance checklist as reference
        4. Send enriched prompt to Gemini for detailed scan
        5. Return structured JSON report
        """
        # Step 1: Get governance agent assessment (enriches context)
        governance_context = ""
        agent = self._get_governance_agent()
        if agent:
            try:
                # Build description from project data
                system_desc = project_data.get('description', '') or project_data.get('name', '')
                if not system_desc:
                    system_desc = json.dumps(project_data, indent=2)[:500]

                assessment = agent.assess_ai_system(system_desc)
                risk_info = assessment.get('risk_classification', {})
                regulations = assessment.get('applicable_regulations', [])
                recommended = assessment.get('recommended_skills', [])
                
                # Get compulsory skills for the current tool
                compulsory = agent.get_compulsory_skills_for_tool(tool_id)
                article_id = agent.get_article_for_tool(tool_id)

                governance_context = f"""
--- GOVERNANCE AGENT ASSESSMENT ---
Risk Classification: {risk_info.get('category', 'Unknown')} (confidence: {risk_info.get('confidence', 'N/A')})
Reasoning: {risk_info.get('reasoning', 'N/A')}

Applicable Regulations:
{chr(10).join(f"- {r['name']}: {r['reason']}" for r in regulations)}

Recommended Skills ({len(recommended)} total):
{chr(10).join(f"- {r['skill']}: {r['reason']}" for r in recommended[:10])}

"""
                if article_id and compulsory:
                    governance_context += f"""
Compulsory Skills for {article_id}:
{chr(10).join(f"- {s}" for s in compulsory)}
"""
                
                logger.info(f"Governance assessment: {risk_info.get('category')} risk, "
                           f"{len(regulations)} regulations, {len(recommended)} skills recommended")

                # Also try to load additional skill content from governance agent
                agent_skill_content = agent.get_skill_content(tool_id)
                if agent_skill_content:
                    governance_context += f"\n--- SKILL CONTENT (via Governance Agent) ---\n{agent_skill_content[:5000]}\n"

            except Exception as e:
                logger.warning(f"GovernanceAgentService assessment failed: {e}")

        # Step 2: Load skill content (from scanner's own discovery)
        skill_instructions = self._load_skill_content(tool_id)

        # Step 3: Load compliance checklist
        checklist_reference = self._load_checklist()

        if not self.client:
            # No Gemini API — use governance agent to generate mock with real assessment
            return self._generate_mock_scan(project_data, tool_id, "Gemini API not configured",
                                            governance_context=governance_context)

        # Step 4: Build enriched prompt matching premium cli.py / governance_agent.py structure
        short_system_instruction = (
            "You are an expert AI Act Compliance Auditor. "
            "Your task is to perform a deep-dive 'AI Agent Scan' and generate a professional Safety Plan. "
            "You must return ONLY a valid JSON object matching the requested schema."
        )

        main_prompt = f"""
{governance_context}

--- KNOWLEDGE BASE: SKILL GUIDELINES ---
{skill_instructions}

--- REFERENCE: COMPLIANCE CHECKLIST ---
{checklist_reference}

ANALYSIS REQUIREMENTS:
1. Perform a deep assessment of the project using the Skill Guidelines for tool: {tool_id}.
2. Use the GOVERNANCE AGENT ASSESSMENT for risk context.
3. Generate a comprehensive Safety Plan encompassing NIST AI RMF profiles, risk factors, controls, and guardrails.
4. For "safety_controls", identify specific line numbers or mechanisms in the project if possible.
5. Provide actionable code snippets for recommended guardrails.

RESPONSE FORMAT (JSON ONLY):
{{
  "compliance_status": "Compliant | Partially Compliant | Non-Compliant",
  "score": 0-100,
  "skill_applied": "{tool_id}",
  "nist_profile": {{
    "function": "Primary business function",
    "type": "AI architecture type",
    "deployment": "Deployment model used"
  }},
  "factors": {{
    "autonomy": "Level of system autonomy description",
    "impact": "Impact on human stakeholders description",
    "sensitivity": "Data sensitivity assessment",
    "vulnerability": "Target user vulnerability assessment",
    "reversibility": "Decision reversibility description"
  }},
  "identified_risks": [
    {{
      "id": "R-001",
      "desc": "**Title** - Concise description",
      "like": "High|Medium|Low",
      "imp": "High|Medium|Low",
      "sev": "High|Medium|Low",
      "mit": "Specific mitigation step"
    }}
  ],
  "safety_controls": {{
    "Transparency (Art. 50)": [
      {{ "implemented": true, "name": "AI Notice", "details": "Found in [ref]" }}
    ],
    "System Prompt Safety": [
       {{ "implemented": true, "name": "Context Constraints", "details": "Ref: [ref]" }}
    ]
  }},
  "missing_controls": {{
    "Input Guards": [
      {{ "name": "Injection Detection", "reason": "Not found in analysis" }}
    ]
  }},
  "guardrails_recommendations": [
    {{
      "title": "Input Guardrail",
      "priority": "High|Medium|Low",
      "code": "python code snippet"
    }}
  ],
  "testing_plan": {{
    "red_teaming": ["Scenario 1", "Scenario 2"],
    "bias_testing": ["Testing strategy 1"]
  }},
  "monitoring_plan": {{
    "metrics": [
      {{ "name": "Accuracy", "target": ">95%", "current": "unknown" }}
    ]
  }},
  "compliance": {{
    "disclosure": "Compliant|Pending",
    "disclosure_ref": "Implementation details",
    "labeling": "Compliant|Pending",
    "labeling_ref": "Implementation details"
  }},
  "action_items": {{
    "immediate": ["Fix 1", "Fix 2"]
  }},
  "summary": "Executive summary of safety plan"
}}

PROJECT TO ANALYZE:
{json.dumps(project_data, indent=2)}

Return ONLY the JSON object.
"""

        # Step 5: Call Gemini API
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=main_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=short_system_instruction,
                    response_mime_type="application/json",
                    temperature=0.1,
                    thinking_config=types.ThinkingConfig(
                        thinking_level=types.ThinkingLevel.HIGH
                    ),
                )
            )

            if not response or not response.text:
                logger.error("Empty response from Gemini API.")
                return self._generate_mock_scan(project_data, tool_id, "Empty response from API",
                                                governance_context=governance_context)

            try:
                report = json.loads(response.text)
            except json.JSONDecodeError as json_err:
                logger.error(f"Failed to parse Gemini response as JSON: {json_err}")
                logger.debug(f"Raw response text (first 500 chars): {response.text[:500]}")
                return self._generate_mock_scan(
                    project_data, tool_id,
                    f"Invalid JSON response from Gemini: {json_err}",
                    governance_context=governance_context
                )

            # Step 6: Generate professional report using GovernanceAgentService formatter
            if agent:
                # Merge data for the professional template
                report['system_description'] = system_desc
                assessment = agent.assess_ai_system(system_desc)
                report['risk_classification'] = assessment.get('risk_classification', {}).get('category', 'Unclassified')
                report['applicable_regulations'] = assessment.get('applicable_regulations', [])
                
                # Use GovernanceAgentService's premium formatting logic (same as cli.py)
                md_report = agent.export_assessment(report, fmt='markdown')
            else:
                # Basic fallback if no agent
                md_report = f"# AI Scan Report: {tool_id}\n\n{report.get('summary', '')}"

            # Step 7: Save report to file
            now = datetime.now()
            reports_dir = Path(settings.BASE_DIR) / "scan_reports"
            reports_dir.mkdir(exist_ok=True)
            filename = f"scan_{tool_id}_{now.strftime('%Y%m%d_%H%M%S')}.md"
            file_path = reports_dir / filename
            file_path.write_text(md_report, encoding='utf-8')

            report['report_md'] = md_report
            report['report_file'] = f"/scan-reports/{filename}"
            report['report_filename'] = filename

            # Step 8: Compatibility mapping for legacy frontend summary view
            report['detailed_output'] = [
                {
                    "id": r.get("id", "R"), 
                    "category": "Risk", 
                    "finding": r.get("desc", ""), 
                    "recommendation": r.get("mit", "")
                } for r in report.get("identified_risks", [])
            ]
            report['next_steps'] = report.get('action_items', {}).get('immediate', [])
            
            return report

        except Exception as e:
            logger.error(f"Error during Gemini scan: {str(e)}", exc_info=True)
            return self._generate_mock_scan(project_data, tool_id, f"Error: {str(e)}",
                                            governance_context=governance_context)

    def _generate_mock_scan(self, project_data: Dict[str, Any], tool_id: str,
                            error_msg: str = "", governance_context: str = "") -> Dict[str, Any]:
        """Generate a mock scan result, enriched with governance agent assessment."""
        agent = self._get_governance_agent()
        system_desc = project_data.get('description', '') or project_data.get('name', '')
        
        # Base mock structure that matches the premium template
        mock_report = {
            "compliance_status": "Needs Review",
            "score": 50,
            "skill_applied": tool_id,
            "system_description": system_desc,
            "summary": f"Initial automated scan for {tool_id} (Mock). {error_msg}",
            "nist_profile": {"function": "Inquiry handling", "type": "Mock AI", "deployment": "Testing"},
            "identified_risks": [
                {"id": "MOCK-01", "desc": "**Incomplete Analysis** - Scan ran in mock mode", "like": "Low", "imp": "Medium", "sev": "Low", "mit": "Configure API and rerun"}
            ],
            "action_items": {"immediate": ["Configure Gemini API Key", "Review system documentation"]},
            "recommended_skills": ["risk-assessment", "ai-governance"]
        }

        # Add agent assessment if available
        if agent:
            try:
                assessment = agent.assess_ai_system(system_desc)
                mock_report['risk_classification'] = assessment.get('risk_classification', {})
                mock_report['applicable_regulations'] = assessment.get('applicable_regulations', [])
            except Exception:
                pass

        # Generate and save MD report using centralized logic
        md_result = self._generate_and_save_md_report(mock_report, tool_id)
        mock_report['report_md'] = md_result.get('content', '')
        mock_report['report_file'] = md_result.get('file_path', '')
        mock_report['report_filename'] = md_result.get('filename', '')

        return mock_report

    def _generate_and_save_md_report(self, report: Dict[str, Any], tool_id: str) -> Dict[str, Any]:
        """
        Centrally generate and save a Markdown report using GovernanceAgentService formatter.
        """
        agent = self._get_governance_agent()
        
        if agent:
            # Use GovernanceAgentService's premium formatting logic (same as cli.py)
            md_report = agent.export_assessment(report, fmt='markdown')
        else:
            # Basic fallback if no agent
            md_report = f"# AI Scan Report: {tool_id}\n\n{report.get('summary', '')}"

        # Save to file
        now = datetime.now()
        reports_dir = Path(settings.BASE_DIR) / "scan_reports"
        reports_dir.mkdir(exist_ok=True)
        
        filename = f"scan_{tool_id}_{now.strftime('%Y%m%d_%H%M%S')}.md"
        file_path = reports_dir / filename
        file_path.write_text(md_report, encoding='utf-8')

        return {
            "content": md_report,
            "file_path": f"/scan-reports/{filename}",
            "filename": filename
        }
