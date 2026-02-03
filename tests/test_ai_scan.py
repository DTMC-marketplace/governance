import os
import sys
import json
import django
from pathlib import Path

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from governance.infrastructure.services.gemini_scanner_service import GeminiScannerService
from governance.mock_data import get_compliance_detail

def test_skill_discovery():
    print("\n--- Testing Skill Discovery ---")
    scanner = GeminiScannerService()
    skills = scanner._discover_skills()
    
    if not skills:
        print("❌ No skills discovered. Check 'AI Act skills packages' directory.")
    else:
        print(f"✅ Discovered {len(skills)} skills:")
        for sid, path in skills.items():
            print(f"  - {sid}: {path}")

def test_load_checklist():
    print("\n--- Testing Checklist Loading ---")
    scanner = GeminiScannerService()
    checklist = scanner._load_checklist()
    
    if not checklist:
        print("❌ Checklist not found.")
    else:
        print(f"✅ Checklist loaded (length: {len(checklist)} chars)")
        if "Article 9" in checklist:
            print("  - Verified: Article 9 found in checklist.")

def test_scan_logic_mock():
    print("\n--- Testing Scan Logic (Mock) ---")
    scanner = GeminiScannerService()
    # Force mock generation by using an empty tool_id or simulating no client
    project = get_compliance_detail("1")
    if not project:
        print("❌ Mock project '1' not found.")
        return

    report = scanner._generate_mock_scan(project, "ai-governance")
    print("✅ Mock Report Generated:")
    print(json.dumps(report, indent=2))
    
    assert "compliance_status" in report
    assert "score" in report

def test_api_endpoints():
    print("\n--- Testing API Endpoints (via Django Test Client) ---")
    from django.test import Client
    client = Client()
    
    # 1. Test Skills Discovery API
    print("GET /api/compliance/skills/ ...")
    response = client.get('/api/compliance/skills/')
    if response.status_code == 200:
        data = json.loads(response.content)
        if data.get('success'):
            print(f"✅ API Success: Found {len(data.get('skills', []))} skills.")
        else:
            print(f"❌ API logical failure: {data.get('error')}")
    else:
        print(f"❌ API HTTP failure: {response.status_code}")

    # 2. Test AI Scan API (POST)
    print("POST /api/compliance/ai-scan/ (this may take a moment) ...")
    payload = {
        "project_id": "1",
        "tool_id": "ai-governance"
    }
    try:
        response = client.post('/api/compliance/ai-scan/', 
                               data=json.dumps(payload), 
                               content_type='application/json')
        
        if response.status_code == 200:
            data = json.loads(response.content)
            if data.get('success'):
                print("✅ API Success: Scan report received.")
                report = data.get('report', {})
                print(f"  - Status: {report.get('compliance_status')}")
                print(f"  - Score: {report.get('score')}")
                print(f"  - Findings: {len(report.get('detailed_output', []))}")
            else:
                print(f"❌ API logical failure: {data.get('error')}")
        else:
            print(f"❌ API HTTP failure: {response.status_code}")
            print(f"   Response: {response.content[:200]}")
    except Exception as e:
        print(f"❌ Exception during API call: {e}")

if __name__ == "__main__":
    print("Starting AI Agent Scan Integration Tests...")
    test_skill_discovery()
    test_load_checklist()
    test_scan_logic_mock()
    test_api_endpoints() # Added this
    # test_real_scan_integration() # Keep it separated or at the end
    print("\nDone.")
