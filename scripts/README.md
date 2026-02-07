# Scripts Directory

This directory contains utility scripts for the Governance platform.

Currently, no setup scripts are required. The AI Act chat service uses Gemini's Long Context approach, injecting the full regulation text directly into the system instruction without needing external vector databases or file search stores.

## Requirements

- `google-genai` package installed
- `GEMINI_API_KEY` environment variable set
- `ai_act_articles/` directory with the full EU AI Act text
