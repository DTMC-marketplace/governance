"""
Article 13 Transparency Instructions Generator
==============================================
Main entry point for generating EU AI Act compliant instructions.

Workflow:
1. Scan Repo (via scanner.py)
2. Generate Compliance JSON (via Gemini)
3. Gap Analysis (Check for missing fields)
4. Inject into Excel Template (via excel_injector.py)
"""

import argparse
import sys
import json
import os
from pathlib import Path
from datetime import datetime

# Import local modules
import scanner
import excel_injector

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not found. Environment variables might not be loaded.")

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("Error: google-genai package not found. Run: pip install google-genai")
    sys.exit(1)

# Models
PRIMARY_MODEL = "gemini-3-pro-preview"
FALLBACK_MODEL = "gemini-2.0-flash-exp"

def get_api_key():
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        print("Error: GEMINI_API_KEY not found in environment.")
        sys.exit(1)
    return key

def generate_compliance_json(client, context, provider_name, model_name=None):
    """
    Prompts Gemini to generate the compliance data structure.
    """
    
    prompt = f"""
    You are an expert AI Compliance Officer for the EU AI Act.
    Your task is to generate the content for the "Instructions for use" (Article 13) of a High-Risk AI System.
    
    SYSTEM CONTEXT (Codebase Scan):
    ===============================
    {context[:100000]} 
    ===============================
    
    INSTRUCTIONS:
    1. Analyze the codebase to understand the system's purpose, inputs, outputs, and limitations.
    2. Generate a JSON object where KEYS correspond to the requirements below, and VALUES are the specific text for the "Instructions".
    3. BE SPECIFIC. Do not use placeholders. If information is missing, infer a reasonable default based on the code type (e.g. if Python, assume standard Python library limitations).
    
    REQUIRED JSON KEYS (Must match Excel Labels or AI Act Codes):
    # 1. Provider Identity
    - "provider_name": Official legal name
    - "trading_name": Trading name if different
    - "registered_address": Full address
    - "contact_details": Email, Phone, Website
    - "auth_rep_name": Authorised Representative Name (if outside Union)
    - "auth_rep_address": Authorised Representative Address
    - "auth_rep_contact": Authorised Representative Contact

    # 2. Characteristics
    - "intended_purpose": Intended Purpose
    - "intended_purpose_ref": Validation Reference (e.g. Clinical Evaluation Report)
    - "target_audience": Person/Group Intended
    - "accuracy_metrics": Accuracy Level (Metrics)
    - "accuracy_ref": Validation Reference for Accuracy
    - "robustness_level": Robustness Level description
    - "robustness_ref": Validation Reference for Robustness
    - "cybersecurity_level": Cybersecurity Level description
    - "cybersecurity_ref": Technical Reference/Standard (e.g. ISO 27001)
    - "circumstances_performance": Known Foreseeable Circumstances affecting Performance

    # 3. Risks & Limitations
    - "foreseeable_misuse": Known Foreseeable Misuse
    - "misuse_mitigation": Mitigation for Deployer (Misuse)
    - "risks_health_safety": Risks to Health/Safety/Fundamental Rights
    - "risks_mitigation": Mitigation for Deployer (Health/Safety)
    - "input_specifications": Input Data Specifications (Format, Quality)
    - "limitations_explainability": Limitations in Explainability
    - "explainability_mitigation": Mitigation for Deployer (Explainability)

    # 4. Oversight & Maintenance
    - "human_oversight": Human Oversight Measures
    - "oversight_freq": Frequency/Trigger for Oversight
    - "lifecycle_changes": Pre-determined Changes (Lifecycle)
    - "expected_lifetime": Expected Lifetime of System
    - "lifetime_trigger": Trigger for End of Life
    - "maintenance_measures": Maintenance Measures (Frequency)
    - "maintenance_freq": Frequency (e.g. "Monthly")
    - "software_updates": Software Update Procedures
    - "update_freq": Frequency of Updates
    - "computational_resources": Computational Resources Needed
    - "hardware_resources": Hardware Resources Needed

    # 5. Logging
    - "logging_collection": Mechanism to Collect Logs
    - "logging_collection_ref": Technical Reference (Log file path)
    - "logging_storage": Mechanism to Store Logs
    - "logging_interpretation": Interpretation of Logs
    
    RETURN JSON ONLY.
    """
    
    models_to_try = [model_name] if model_name else [PRIMARY_MODEL, FALLBACK_MODEL]
    
    for model in models_to_try:
        try:
            print(f"Prompting {model}...")
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config={'response_mime_type': 'application/json'}
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"Warning: {model} failed: {e}")
            continue
            
    return None

def main():
    parser = argparse.ArgumentParser(description="Generate Article 13 Instructions")
    parser.add_argument("--repo", required=True, help="Path to the repository to scan")
    parser.add_argument("--template", required=True, help="Path to the Excel template")
    parser.add_argument("--output", default="Output", help="Directory to save output")
    parser.add_argument("--provider", default="MyAIProvider", help="Name of the AI Provider")
    parser.add_argument("--model", help="Force specific Gemini model")
    
    args = parser.parse_args()
    
    repo_path = Path(args.repo)
    template_path = Path(args.template)
    output_dir = Path(args.output)
    
    if not repo_path.exists():
        print(f"Repo not found: {repo_path}")
        sys.exit(1)
        
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Scan
    print(f"Step 1: Scanning {repo_path}...")
    files = scanner.scan_codebase(repo_path)
    if not files:
        print("No files found to scan.")
        sys.exit(1)
    
    context = scanner.build_context_string(files)
    print(f"Scanned {len(files)} files. Context size: {len(context)} chars.")
    
    # 2. Analyze
    print(f"Step 2: Analyzing with Gemini...")
    api_key = get_api_key()
    client = genai.Client(api_key=api_key)
    
    compliance_data = generate_compliance_json(client, context, args.provider, args.model)
    
    if not compliance_data:
        print("Failed to generate compliance data.")
        sys.exit(1)
        
    # 3. Gap Analysis
    print(f"\n[Step 3] Gap Identification & Validation")
    print("="*40)
    
    # Full list of expected fields mapped to their readable names
    all_fields = {
        "provider_name": "Provider Name",
        "intended_purpose": "Intended Purpose",
        "expected_lifetime": "Expected Lifetime",
        "maintenance_measures": "Maintenance Measures",
        "software_updates": "Software Updates",
        "human_oversight": "Human Oversight",
        "cybersecurity_level": "Cybersecurity Level",
        "logging_collection": "Logging Mechanism",
        "accuracy_metrics": "Accuracy Metrics"
    }
    
    gap_count = 0
    for key, label in all_fields.items():
        val = compliance_data.get(key)
        if not val or str(val).lower() in ["none", "unknown", "n/a"]:
           print(f"[!] GAP DETECTED: Field '{label}' ({key}) is empty/unknown. Manual Input Required.")
           gap_count += 1
    
    if gap_count == 0:
        print(">> No Gaps Detected. All critical fields populated.")
    else:
        print(f">> WARNING: {gap_count} Gaps Detected.")
    print("="*40 + "\n")

            
    # Save raw JSON for debugging
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    json_path = output_dir / f"compliance_data_{ts}.json"
    json_path.write_text(json.dumps(compliance_data, indent=2))
    
    # 4. Inject
    print(f"Step 4: Generating Excel...")
    output_xlsx = output_dir / f"Transparency_Instructions_{ts}.xlsx"
    
    # Map API keys to Template Labels (Normalization layer)
    # Now supports mapping to DICTIONARY for multiple columns
    final_map = {}
    c = compliance_data
    
    def get_val(key, default="N/A"):
        """Helper to ensure no empty cells. Returns "N/A" if key missing or None."""
        val = c.get(key)
        if not val or str(val).lower() in ["none", "unknown", ""]:
            return default
        return val

    # 1. Provider
    final_map["Provider Name"] = get_val("provider_name")
    final_map["Trading Name (if different)"] = get_val("trading_name")
    final_map["Registered Address"] = get_val("registered_address")
    final_map["Contact Details"] = get_val("contact_details")
    final_map["Authorised Representative Name (if applicable)"] = get_val("auth_rep_name", "N/A (EU Provider)")
    final_map["Authorised Representative Address"] = get_val("auth_rep_address", "N/A")
    final_map["Authorised Representative Contact"] = get_val("auth_rep_contact", "N/A")

    # 2. Characteristics
    # Col 1: Description/Metric, Col 2: Validation Reference
    final_map["Intended Purpose"] = {"Description/Metric": get_val("intended_purpose"), "Validation Reference": get_val("intended_purpose_ref", "N/A")}
    final_map["Person/Group Intended (Target Audience)"] = {"Description/Metric": get_val("target_audience"), "Validation Reference": "N/A"}
    final_map["Accuracy Level (Metrics)"] = {"Description/Metric": get_val("accuracy_metrics"), "Validation Reference": get_val("accuracy_ref", "Internal Validation Report")}
    final_map["Robustness Level"] = {"Description/Metric": get_val("robustness_level"), "Validation Reference": get_val("robustness_ref", "Technical Documentation")}
    final_map["Cybersecurity Level"] = {"Description/Metric": get_val("cybersecurity_level"), "Validation Reference": get_val("cybersecurity_ref", "Security Config")}
    final_map["Known Foreseeable Circumstances affecting Performance"] = {"Description/Metric": get_val("circumstances_performance"), "Validation Reference": "N/A"}

    # 3. Risks
    # Col 1: Warning/Instruction, Col 2: Mitigation for Deployer
    final_map["Known Foreseeable Misuse"] = {"Warning/Instruction": get_val("foreseeable_misuse"), "Mitigation for Deployer": get_val("misuse_mitigation", "Ensure user training")}
    final_map["risks to Health/Safety/Fundamental Rights"] = {"Warning/Instruction": get_val("risks_health_safety"), "Mitigation for Deployer": get_val("risks_mitigation", "Human Oversight")}
    final_map["Input Data Specifications (Format, Quality)"] = {"Warning/Instruction": get_val("input_specifications"), "Mitigation for Deployer": "N/A"}
    final_map["Limitations in Explainability"] = {"Warning/Instruction": get_val("limitations_explainability"), "Mitigation for Deployer": get_val("explainability_mitigation", "Review logs if uncertain")}

    # 4. Oversight
    # Col 1: Instruction to Deployer, Col 2: Frequency/Trigger
    final_map["Human Oversight Measures (Art 14)"] = {"Instruction to Deployer": get_val("human_oversight"), "Frequency/Trigger": get_val("oversight_freq", "Continuous")}
    final_map["Pre-determined Changes (Lifecycle)"] = {"Instruction to Deployer": get_val("lifecycle_changes", "None pre-determined"), "Frequency/Trigger": "N/A"}
    final_map["Expected Lifetime of System"] = {"Instruction to Deployer": get_val("expected_lifetime"), "Frequency/Trigger": get_val("lifetime_trigger", "Performance degradation")}
    final_map["Maintenance Measures (Frequency)"] = {"Instruction to Deployer": get_val("maintenance_measures"), "Frequency/Trigger": get_val("maintenance_freq", "Monthly")}
    final_map["Software Update Procedures"] = {"Instruction to Deployer": get_val("software_updates"), "Frequency/Trigger": get_val("update_freq", "As needed")}
    final_map["Computational Resources Needed"] = {"Instruction to Deployer": get_val("computational_resources"), "Frequency/Trigger": "N/A (Hardware Requirement)"}
    final_map["Hardware Resources Needed"] = {"Instruction to Deployer": get_val("hardware_resources"), "Frequency/Trigger": "N/A (Hardware Requirement)"}

    # 5. Logging
    # Col 1: Instruction, Col 2: Technical Reference
    final_map["Mechanism to Collect Logs"] = {"Instruction": get_val("logging_collection"), "Technical Reference": get_val("logging_collection_ref", "System Documentation")}
    final_map["Mechanism to Store Logs"] = {"Instruction": get_val("logging_storage"), "Technical Reference": "N/A"}
    final_map["Interpretation of Logs"] = {"Instruction": get_val("logging_interpretation"), "Technical Reference": "N/A"}
    
    success = excel_injector.generate_excel_from_csvs(str(template_path.parent), str(output_xlsx), final_map)
    
    if success:
        print(f"\nSUCCESS: Instructions generated at {output_xlsx}")
    else:
        print("\nFAILED: Could not generate Excel.")

if __name__ == "__main__":
    main()
