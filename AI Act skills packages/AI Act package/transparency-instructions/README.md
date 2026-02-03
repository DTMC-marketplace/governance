# Transparency Instructions Generator (Article 13)

This plugin automates the creation of **Instructions for Use** as required by **Article 13 of the EU AI Act**. It scans a local codebase/repository for technical details (accuracy metrics, logging configs, security protocols) and generates a fully compliant, rich-text Excel report.

## Features

- **Automated Context Scanning**: Recursively scans code (Python, YAML, JSON, etc.) to extract "ground truth" system settings.
- **AI-Powered Analysis**: Uses structured prompting (Gemini) to draft Description, Validation Reference, Mitigations, and Maintenance triggers.
- **Strict Excel Formatting**: Produces professional `.xlsx` files with solid white backgrounds, borders, and structured tables.
- **100% Fill Rate**: Ensures every cell in the Excel grid is populated, using "N/A" fallbacks for missing secondary data.

## Directory Structure

```text
transparency-instructions/
├── scripts/
│   ├── generate_instructions.py  # MAIN ENTRY POINT
│   ├── excel_injector.py         # Formatting & Generation Engine
│   └── scanner.py                # Codebase Analysis
├── templates/
│   └── Transparency_Instructions_Art13.xlsx # Master Template
├── examples/
│   └── fake_repo/                # Test Data
└── tests/                        # Integration Tests
```

## Integration Guide

### 1. Backend Integration (Python / FastAPI / Flask)

To integrate this plugin into your backend system, you should call the main generation script or import the logic directly.

**Option A: Subprocess Call (Recommended for Isolation)**
Run the script as a separate process to avoid dependency conflicts.

```python
import subprocess
import os

def run_generation_job(repo_path: str, output_dir: str):
    script_path = "ai_act_package/transparency-instructions/scripts/generate_instructions.py"
    template_path = "ai_act_package/transparency-instructions/templates/Transparency_Instructions_Art13.xlsx"
    
    cmd = [
        "python", script_path,
        "--repo", repo_path,
        "--template", template_path,
        "--output", output_dir
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Generation failed: {result.stderr}")
        
    return "Generation successful"
```

**Option B: Direct Import**
If your environment shares the same dependencies (see `requirements.txt`).

```python
from ai_act_package.transparency_instructions.scripts import generate_instructions

def run_job(repo_path, output_dir):
    # Ensure environment variables (GEMINI_API_KEY) are set
    generate_instructions.run_main_logic(
        repo_path=repo_path, 
        template_path="...", 
        output_dir=output_dir
    )
```

### 2. Frontend Integration (React / Vue / Streamlit)

The Frontend should provide a UI to select the target repository and trigger the generation.

**Workflow:**

1. **User Input**: User provides a path to the AI System's Codebase (or uploads a zip).
2. **API Call**: Frontend sends `POST /api/generate-transparency-instructions`.
3. **Payload**:

    ```json
    {
      "repo_id": "project-alpha-v2",
      "override_provider_name": "My Company Ltd."
    }
    ```

4. **Response**: Backend returns a download URL or the file stream.
5. **Download**: Browser prompts user to save `Transparency_Instructions_[Date].xlsx`.

**Example Fetch (JS):**

```javascript
async function generateReport(repoId) {
  const response = await fetch('/api/generate-transparency-instructions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repo_id: repoId })
  });
  
  if (response.ok) {
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = "Instructions_Art13.xlsx";
    a.click();
  }
}
```

## Configuration

Ensure the following Environment Variables are set in the backend environment:

- `GEMINI_API_KEY`: Required for the AI generation step.
