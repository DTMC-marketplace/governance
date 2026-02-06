"""
Form Analyzer - Structured Form Field Processing
Supports text, select, radio, checkbox, and formatted input fields
"""
import json
import logging
import re
from typing import Dict, List, Optional, Any, Union
from enum import Enum

logger = logging.getLogger(__name__)


class FieldType(str, Enum):
    """Form field types"""
    TEXT = "text"
    SELECT = "select"
    RADIO = "radio"
    CHECKBOX = "checkbox"
    EMAIL = "email"
    PHONE = "phone"
    NUMBER = "number"
    DATE = "date"


class FormField:
    """Represents a form field with metadata"""

    def __init__(
        self,
        name: str,
        field_type: FieldType,
        options: Optional[List[str]] = None,
        required: bool = False,
        description: Optional[str] = None,
    ):
        self.name = name
        self.field_type = field_type
        self.options = options or []
        self.required = required
        self.description = description

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "field_type": self.field_type.value,
            "options": self.options,
            "required": self.required,
            "description": self.description,
        }


class FormAnalyzer:
    """Analyzes and processes form fields with AI assistance"""

    @staticmethod
    def detect_field_type(field_name: str, field_context: Optional[str] = None) -> FieldType:
        """
        Detect field type from field name and context.
        """
        field_name_lower = field_name.lower()

        # Email detection
        if any(keyword in field_name_lower for keyword in ["email", "e-mail"]):
            return FieldType.EMAIL

        # Phone detection
        if any(keyword in field_name_lower for keyword in ["phone", "telephone", "mobile"]):
            return FieldType.PHONE

        # Number detection
        if any(keyword in field_name_lower for keyword in ["number", "count", "quantity", "amount"]):
            return FieldType.NUMBER

        # Date detection
        if any(keyword in field_name_lower for keyword in ["date", "year", "month", "day"]):
            return FieldType.DATE

        # Checkbox detection (multi-select keywords)
        if field_context:
            context_lower = field_context.lower()
            if "select all that apply" in context_lower or "multiple" in context_lower:
                return FieldType.CHECKBOX

        # Radio/Select detection (single choice keywords)
        if field_context:
            context_lower = field_context.lower()
            if any(keyword in context_lower for keyword in ["yes/no", "select an option", "choose one"]):
                # If only 2-3 options, likely radio
                if field_context.count("\n") <= 3:
                    return FieldType.RADIO
                return FieldType.SELECT

        # Default to text
        return FieldType.TEXT

    @staticmethod
    def extract_options(field_context: str) -> List[str]:
        """
        Extract options from field context.
        """
        if not field_context:
            return []

        # Try to parse as JSON array
        try:
            options = json.loads(field_context)
            if isinstance(options, list):
                return [str(opt) for opt in options]
        except:
            pass

        # Try line-separated options
        lines = [line.strip() for line in field_context.split("\n") if line.strip()]
        if len(lines) > 1:
            return lines

        # Try comma-separated
        if "," in field_context:
            return [opt.strip() for opt in field_context.split(",") if opt.strip()]

        return []

    @staticmethod
    def build_structured_prompt(
        field: FormField,
        document_context: str,
        original_question: Optional[str] = None,
    ) -> str:
        """
        Build a structured prompt for Gemini based on field type.
        """
        base_context = f"""You are a precise data extraction assistant. Your task is to extract EXACT information from the provided document.

Field to Extract: {field.name}
Field Type: {field.field_type.value}
Required: {field.required}
"""

        if original_question:
            base_context += f"Question: {original_question}\n"

        if field.description:
            base_context += f"Description: {field.description}\n"
        
        # Add field name mapping hints for better matching
        field_hints = {
            # Section 2: Organization Profile
            "entity_name": "Also look for: Company Name, Organization Name, Entity, Company",
            "registration_number": "Also look for: Company Number, Registration No, Reg Number",
            "headquarter_address": "Also look for: Address, HQ Address, Main Office, Headquarters",
            "country": "Also look for: Country, Nation, Location",
            "postal_code": "Also look for: Postal Code, ZIP Code, Post Code, ZIP",
            "legal_representative": "Also look for: Legal Rep, Representative, CEO, Director",
            "contact_email": "Also look for: Email, Contact Email, E-mail",
            "contact_phone": "Also look for: Phone, Telephone, Contact Number, Phone Number",
            "public_authority": "Also look for: Public Authority, Government Entity, Public Body",
            "compliance_owner_name": "Also look for: Compliance Owner, Owner Name, Responsible Person",
            "compliance_owner_email": "Also look for: Owner Email, Compliance Email, Responsible Email",
            "department": "Also look for: Department, Division, Unit, Team",
            
            # Section 3: Scope / Applicability Screening
            "scope_use_default_roles": "Also look for: Use default roles, Default roles, Use organization roles",
            "scope_typical_roles": "Also look for: Typical activities, Roles, Activities, Provider/Deployer/Importer",
            "scope_place_on_eu_market": "Also look for: Place on EU market, EU market, EEA market",
            "scope_deployed_in_eu": "Also look for: Deployed in EU, Used in EU, EU deployment",
            "scope_affects_eu_persons": "Also look for: Affects EU persons, EU persons, Affects people in EU",
            
            # Section 4: Governance Setup
            "governance_has_policies": "Also look for: AI governance policies, Policies, Written policies",
            "governance_policy_link": "Also look for: Policy link, Policy URL, Governance link",
            "governance_has_escalation_path": "Also look for: Escalation path, Escalation procedure",
            "governance_has_register": "Also look for: Register of AI systems, AI register, System register",
            "governance_register_link": "Also look for: Register link, Register URL",
            "governance_has_version_history": "Also look for: Version history, Versioning, Version control",
            "governance_has_vendor_assessment": "Also look for: Vendor assessment, Third party assessment, Supplier assessment",
            
            # Section 5: AI Literacy
            "literacy_teams_using_ai": "Also look for: Teams using AI, Internal teams, Users, Departments",
            "literacy_number_of_users": "Also look for: Number of users, User count, How many users",
            "literacy_has_training": "Also look for: AI literacy training, Training, AI training",
            "literacy_training_content": "Also look for: Training covers, Training content, Training topics",
            "literacy_has_evidence": "Also look for: Evidence of training, Training evidence, Attendance logs",
            "literacy_training_refreshed": "Also look for: Training refreshed, Training updates, Training updated",
            
            # AI System fields
            "ai_system_name": "Also look for: System Name, AI Name, Name, System",
            "internal_system_id": "Also look for: System ID, ID, Internal ID, Reference",
            "owner_name": "Also look for: Owner, System Owner, Responsible Person",
            "owner_email": "Also look for: Owner Email, Contact Email",
            "owner_department": "Also look for: Department, Owner Department, Team",
            "system_status": "Also look for: Status, Current Status, State",
            "go_live_date": "Also look for: Go Live, Launch Date, Deployment Date, Live Date",
            "vendor": "Also look for: Vendor, Supplier, Provider, Third Party",
            "business_unit": "Also look for: Business Unit, BU, Division, Department",
            "purpose": "Also look for: Purpose, Objective, Goal, Use Case",
        }
        
        if field.name in field_hints:
            base_context += f"\nHINT: {field_hints[field.name]}\n"

        base_context += f"\n=== DOCUMENT CONTENT ===\n{document_context}\n=== END DOCUMENT ===\n\n"

        # Type-specific instructions with improved extraction guidance
        if field.field_type == FieldType.TEXT:
            instructions = """TASK: Extract the exact value for this field from the document.

INSTRUCTIONS:
1. Look for the field name or related keywords in the document
2. Extract the EXACT text value as it appears
3. Do NOT add explanations, formatting, or extra text
4. If the information is not found, return ONLY: "Not specified in the documents"
5. Return ONLY the extracted value, nothing else

EXAMPLES:
- If field is "entity_name" and document says "Company: Acme Corp", return: Acme Corp
- If field is "address" and document says "Address: 123 Main St, London", return: 123 Main St, London
- If field is "email" and document says "Contact: john@example.com", return: john@example.com

CRITICAL: Return ONLY the value, no labels, no explanations."""

        elif field.field_type == FieldType.SELECT:
            options_str = "\n".join([f"- {opt}" for opt in field.options])
            instructions = f"""TASK: Select the MOST appropriate option from the list below.

AVAILABLE OPTIONS:
{options_str}

INSTRUCTIONS:
1. Read the document carefully
2. Find information related to "{field.name}"
3. Match it to ONE option from the list above
4. Return ONLY the exact option text (copy-paste from the list)
5. If no match found, return: "Not specified in the documents"

CRITICAL: 
- Return ONLY one option from the list above
- Do NOT create new options
- Do NOT add explanations"""

        elif field.field_type == FieldType.RADIO:
            options_str = "\n".join([f"- {opt}" for opt in field.options])
            instructions = f"""TASK: Select ONE option from the list below.

AVAILABLE OPTIONS:
{options_str}

INSTRUCTIONS:
1. Find information about "{field.name}" in the document
2. Choose the SINGLE best matching option
3. Return ONLY the exact option text
4. If unclear, return: "Not specified in the documents"

CRITICAL: Return ONLY one option from the list, nothing else."""

        elif field.field_type == FieldType.CHECKBOX:
            options_str = "\n".join([f"- {opt}" for opt in field.options])
            instructions = f"""TASK: Select ALL applicable options from the list below.

AVAILABLE OPTIONS:
{options_str}

INSTRUCTIONS:
1. Find all mentions related to "{field.name}" in the document
2. Select ALL options that apply
3. Return a JSON array of selected options
4. Use exact option text from the list above
5. If none apply, return: []

EXAMPLE OUTPUT:
["Option 1", "Option 3"]

CRITICAL: Return ONLY a JSON array, nothing else."""

        elif field.field_type == FieldType.EMAIL:
            instructions = """TASK: Extract the email address.

INSTRUCTIONS:
1. Look for email addresses in the document
2. Return ONLY the email in format: user@domain.com
3. If multiple emails, return the most relevant one for this field
4. If no email found, return: "Not specified in the documents"

CRITICAL: Return ONLY the email address, nothing else."""

        elif field.field_type == FieldType.PHONE:
            instructions = """TASK: Extract the phone number.

INSTRUCTIONS:
1. Look for phone numbers in the document
2. Return the number in a clean format (e.g., +44 20 1234 5678)
3. If multiple numbers, return the most relevant one
4. If no phone found, return: "Not specified in the documents"

CRITICAL: Return ONLY the phone number, nothing else."""

        elif field.field_type == FieldType.NUMBER:
            instructions = """TASK: Extract the numeric value.

INSTRUCTIONS:
1. Find the number related to "{field.name}"
2. Return ONLY the number (e.g., 42, 3.14, 1000)
3. Do NOT include units or currency symbols
4. If no number found, return: "Not specified in the documents"

CRITICAL: Return ONLY the number, nothing else."""

        elif field.field_type == FieldType.DATE:
            instructions = """TASK: Extract the date.

INSTRUCTIONS:
1. Find the date related to "{field.name}"
2. Return in format: YYYY-MM-DD (e.g., 2024-03-15)
3. If only year/month available, use: YYYY-MM-01 or YYYY-01-01
4. If no date found, return: "Not specified in the documents"

CRITICAL: Return ONLY the date in YYYY-MM-DD format, nothing else."""

        else:
            instructions = """TASK: Extract relevant information.

INSTRUCTIONS:
1. Find information about this field in the document
2. Return the exact value as it appears
3. If not found, return: "Not specified in the documents"

CRITICAL: Return ONLY the value, no explanations."""

        return base_context + instructions

    @staticmethod
    def parse_response(response: str, field_type: FieldType) -> Union[str, List[str]]:
        """
        Parse Gemini response based on field type.
        """
        response = response.strip()

        # Handle empty or "not found" responses
        if not response or "not specified" in response.lower():
            return "" if field_type != FieldType.CHECKBOX else []

        # For checkbox, try to parse JSON array
        if field_type == FieldType.CHECKBOX:
            try:
                # Remove markdown code blocks if present
                clean_response = re.sub(r"```json\s*|```", "", response).strip()
                parsed = json.loads(clean_response)
                if isinstance(parsed, list):
                    return [str(item) for item in parsed]
            except:
                # Try to extract from text
                matches = re.findall(r'"([^"]+)"', response)
                if matches:
                    return matches

                # Fallback: split by comma or newline
                if "," in response:
                    return [item.strip() for item in response.split(",") if item.strip()]
                elif "\n" in response:
                    return [item.strip("- •*") for item in response.split("\n") if item.strip()]

            return []

        # For other types, return as string (cleaned)
        return response.strip()

    @staticmethod
    def format_structured_response(
        field_name: str,
        field_type: FieldType,
        value: Union[str, List[str]],
        confidence: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Format the final structured response.
        """
        response = {
            "field_name": field_name,
            "field_type": field_type.value,
            "value": value,
            "has_value": bool(value) if not isinstance(value, list) else len(value) > 0,
        }

        if confidence is not None:
            response["confidence"] = confidence

        return response
