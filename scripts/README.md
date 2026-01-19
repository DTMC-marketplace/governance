# Scripts Directory

This directory contains utility scripts for the Governance platform.

## setup_ai_act_store.py

Sets up the Gemini File Search Store for AI Act and GDPR articles.

### Usage

```bash
export GEMINI_API_KEY="your-api-key"
python scripts/setup_ai_act_store.py
```

### What it does

1. Creates a Gemini File Search Store (if it doesn't exist)
2. Uploads all articles from `ai_act_articles/` directory
3. Saves store information to `ai_act_store_info.txt`

### Requirements

- `google-genai` package installed
- `GEMINI_API_KEY` environment variable set
- `ai_act_articles/` directory with article files

### Output

The script will:
- Create or reuse an existing store named "EU-AI-Act-GDPR-Knowledge-Base"
- Upload all `.txt` files from `ai_act_articles/`
- Save the store name to `ai_act_store_info.txt` (this file is gitignored)
