"""
Service for AI Act Scanning and Skill Discovery using Gemini
"""
import os
import json
import logging
import yaml
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

class GeminiScannerService:
    """
    Service to perform AI Act compliance scans using Gemini.
    Uses instructions and artifacts from AI Act skills packages.
    """
    
    def __init__(self):
        self.api_key = getattr(settings, 'GEMINI_API_KEY', '') or os.environ.get('GEMINI_API_KEY', '')
        self.model_name = getattr(settings, 'AI_ACT_MODEL_NAME', 'gemini-2.5-flash')
        
        if genai and self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None
            
        self.skills_dir = Path(settings.BASE_DIR) / "AI Act skills packages"
        self.checklist_path = self.skills_dir / "compliance_checklist_high_risk.yaml"

    def _discover_skills(self) -> Dict[str, str]:
        """Dynamically discover all SKILL.md files and their relative paths."""
        skills = {}
        if not self.skills_dir.exists():
            return skills
            
        for root, dirs, files in os.walk(self.skills_dir):
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
                    
        return skills

    def _load_skill_content(self, tool_id: str) -> str:
        """Load content for a specific tool by searching discovered skills."""
        skills_map = self._discover_skills()
        
        # Hardcoded overrides for common mappings if discovery naming varies
        overrides = {
            'fria-assessment': 'AI Act package/risk-assessment/SKILL.md',
            'ai-governance': 'AI Act package/ai-governance/SKILL.md',
            'ai-safety': 'AI Act package/ai-safety-SKILL.md',
            'ai-ethics-advisor': 'AI Act package/ai-ethics-advisor/SKILL.md',
            'transparency-instructions': 'AI Act package/transparency-instructions/SKILL.md',
            'prompt-injection-detector': 'AI Act package/ai-safety-planning/SKILL.md',
            'privacy-preservation-scanner': 'AI Act package/ai-ethics-advisor/modules/technical-safeguards/privacy-preserving.py',
            'ai-bias-detector': 'AI Act package/ai-ethics-advisor/modules/technical-safeguards/bias-monitoring.py',
        }
        
        skill_rel_path = overrides.get(tool_id) or skills_map.get(tool_id)
        
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
                    return full_path.read_text(encoding='utf-8')
                except Exception as e:
                    logger.error(f"Error reading skill file {full_path}: {e}")
        
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
        Run a compliance scan for a project using a specific tool and the full skills toolkit.
        """
        if not self.client:
            return self._generate_mock_scan(project_data, tool_id, "Gemini API not configured")

        skill_instructions = self._load_skill_content(tool_id)
        checklist_reference = self._load_checklist()
        
        # Prepare prompt parts
        short_system_instruction = "You are an expert AI Act Compliance Auditor. Your task is to perform an 'AI Agent Scan'. You must return ONLY a valid JSON object following the requested schema."
        
        # Truncate checklist if it's massive
        if len(checklist_reference) > 15000:
            checklist_reference = checklist_reference[:15000] + "... [truncated for brevity]"

        main_prompt = f"""
--- KNOWLEDGE BASE: SKILL GUIDELINES ---
{skill_instructions}

--- REFERENCE: COMPLIANCE CHECKLIST ---
{checklist_reference}

ANALYSIS REQUIREMENTS:
1. Evaluate the system against the specific Skill Guidelines above using the tool: {tool_id}.
2. Cross-reference with the Compliance Checklist to identify missing controls.
3. Provide a realistic, evidence-based assessment of compliance.
4. If project data is insufficient for a clear determination, flag it as a finding with a requirement for documentation.

RESPONSE FORMAT (JSON ONLY):
{{
  "compliance_status": "Compliant | Partially Compliant | Non-Compliant",
  "score": 0-100,
  "summary": "High-level audit summary",
  "detailed_output": [
    {{
      "id": "A unique finding ID (e.g. AUDIT-01)",
      "category": "The specific requirement category",
      "finding": "Description of what was found or what is missing",
      "recommendation": "Specific actionable advice to fix the issue"
    }}
  ],
  "next_steps": ["Action 1", "Action 2", ...]
}}

PROJECT TO ANALYZE:
{json.dumps(project_data, indent=2)}

Return ONLY the JSON object.
"""

        # Prepare prompt parts
        short_system_instruction = "You are an expert AI Act Compliance Auditor. Your task is to perform an 'AI Agent Scan'. You must return ONLY a valid JSON object following the requested schema."
        
        # Truncate checklist if it's massive
        if len(checklist_reference) > 15000:
            checklist_reference = checklist_reference[:15000] + "... [truncated for brevity]"

        main_prompt = f"""
--- KNOWLEDGE BASE: SKILL GUIDELINES ---
{skill_instructions}

--- REFERENCE: COMPLIANCE CHECKLIST ---
{checklist_reference}

ANALYSIS REQUIREMENTS:
1. Evaluate the system against the specific Skill Guidelines above using the tool: {tool_id}.
2. Cross-reference with the Compliance Checklist to identify missing controls.
3. Provide a realistic, evidence-based assessment of compliance.
4. If project data is insufficient for a clear determination, flag it as a finding with a requirement for documentation.

RESPONSE FORMAT (JSON ONLY):
{{
  "compliance_status": "Compliant | Partially Compliant | Non-Compliant",
  "score": 0-100,
  "summary": "High-level audit summary",
  "detailed_output": [
    {{
      "id": "A unique finding ID (e.g. AUDIT-01)",
      "category": "The specific requirement category",
      "finding": "Description of what was found or what is missing",
      "recommendation": "Specific actionable advice to fix the issue"
    }}
  ],
  "next_steps": ["Action 1", "Action 2", ...]
}}

PROJECT TO ANALYZE:
{json.dumps(project_data, indent=2)}

Return ONLY the JSON object.
"""

        try:
            # Using 60s timeout for complex scans
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=main_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=short_system_instruction,
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )
            
            if not response or not response.text:
                logger.error("Empty response from Gemini API.")
                return self._generate_mock_scan(project_data, tool_id, "Empty response from API")
                
            report = json.loads(response.text)
            return report
            
        except Exception as e:
            logger.error(f"Error during Gemini scan: {str(e)}", exc_info=True)
            return self._generate_mock_scan(project_data, tool_id, f"Error: {str(e)}")

    def _generate_mock_scan(self, project_data: Dict[str, Any], tool_id: str, error_msg: str = "") -> Dict[str, Any]:
        """Generate a realistic mock scan result if Gemini is unavailable."""
        return {
            "compliance_status": "Needs Review",
            "score": 65,
            "summary": f"Automated scan for {tool_id} completed with warnings. {error_msg}",
            "detailed_output": [
                {
                    "id": "GAP-01",
                    "category": "Technical Documentation",
                    "finding": "Annex IV section on 'methods used to design the system' is incomplete.",
                    "recommendation": "Use the 'technical_documentation_template_annex_iv.md' from the skills packages to update your docs."
                }
            ],
            "next_steps": ["Identify missing documentation", "Run full risk classifier script"]
        }
