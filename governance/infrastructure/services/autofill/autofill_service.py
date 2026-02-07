"""
Autofill Service - AI-powered form completion from documents.
Adapted from geminihackathon/autofill logic for the Governance platform.
"""
import logging
import asyncio
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from django.conf import settings
try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None

from .form_analyzer import FormAnalyzer, FieldType, FormField

logger = logging.getLogger(__name__)

class AutofillService:
    """
    Independent tool for autofilling form data using Gemini and document analysis.
    """
    
    def __init__(self, model_name: str = "gemini-3-pro-preview"):
        self.model_name = model_name
        self.client = None
        if genai and hasattr(settings, 'GEMINI_API_KEY'):
            try:
                self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client in AutofillService: {e}")

    def run_bulk_autofill(self, file_paths: List[str], fields_metadata: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract multiple fields from a set of documents.
        
        Args:
            file_paths: List of absolute or relative paths to documents.
            fields_metadata: List of field definitions, e.g.:
                [
                    {"name": "entity_name", "type": "text"},
                    {"name": "industry", "type": "select", "options": ["Tech", "Finance"]}
                ]
        """
        if not self.client:
            return {"success": False, "error": "Gemini client not initialized"}

        # 1. Extract context
        context_text = self._extract_text(file_paths)
        if not context_text.strip():
            logger.warning("No text content found in documents")
            return {"success": False, "error": "No text content found in documents"}
        
        logger.info(f"Extracted text from {len(file_paths)} files, total length: {len(context_text)} characters")
        logger.debug(f"First 500 chars of extracted text: {context_text[:500]}")

        # 2. Process each field in chunks of 10 to avoid rate limits
        results = {}
        chunk_size = 10
        
        for i in range(0, len(fields_metadata), chunk_size):
            chunk = fields_metadata[i:i + chunk_size]
            for field_data in chunk:
                field_name = field_data.get('name')
                field_type_str = field_data.get('type', 'text')
                options = field_data.get('options', [])
                
                try:
                    ft = FieldType(field_type_str)
                    field = FormField(field_name, ft, options=options)
                    
                    # Build prompt using FormAnalyzer logic
                    prompt = FormAnalyzer.build_structured_prompt(field, context_text)
                    
                    logger.info(f"Processing field: {field_name} (type: {field_type_str})")
                    
                    # Call Gemini
                    response = self.client.models.generate_content(
                        model=self.model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            temperature=0.1,
                            max_output_tokens=2048,
                            thinking_config=types.ThinkingConfig(
                                thinking_level=types.ThinkingLevel.HIGH
                            ),
                        )
                    )
                    
                    if response and response.text:
                        parsed_value = FormAnalyzer.parse_response(response.text, ft)
                        results[field_name] = parsed_value
                        logger.info(f"Field {field_name}: extracted value = '{parsed_value}'")
                    else:
                        results[field_name] = ""
                        logger.warning(f"Field {field_name}: no response from Gemini")
                        
                except Exception as e:
                    logger.error(f"Error extracting field {field_name}: {e}")
                    results[field_name] = ""
            
            # Rate limit mitigation: wait 2 seconds between chunks
            if i + chunk_size < len(fields_metadata):
                logger.info(f"Rate limiting: waiting 2 seconds before next chunk of {chunk_size} fields...")
                time.sleep(2)

        return {"success": True, "data": results}

    def _extract_text(self, file_paths: List[str]) -> str:
        """Helper to extract text from files (local paths)."""
        all_text = []
        
        # We can reuse extraction logic from GeminiScannerService or implement a clean version here
        # For simplicity and independence, implementing a clean version
        try:
            import pypdf
        except ImportError:
            pypdf = None
            logger.warning("pypdf not installed — PDF extraction disabled. Run: pip install pypdf")
        try:
            import docx
        except ImportError:
            docx = None

        for path_str in file_paths:
            path = Path(path_str)
            
            # Try multiple path resolution strategies
            if not path.is_absolute():
                # Strategy 1: Relative to BASE_DIR
                candidate1 = Path(settings.BASE_DIR) / path_str
                # Strategy 2: Relative to static folder
                static_dir = settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else Path(settings.BASE_DIR) / 'static'
                candidate2 = static_dir / path_str
                
                # Use whichever exists
                if candidate1.exists():
                    path = candidate1
                elif candidate2.exists():
                    path = candidate2
                else:
                    path = candidate1  # Default to BASE_DIR for error message

            if not path.exists():
                logger.warning(f"File not found: {path} (original: {path_str})")
                continue

            try:
                if path.suffix.lower() == '.pdf' and pypdf:
                    with open(path, 'rb') as f:
                        reader = pypdf.PdfReader(f)
                        text = "\n".join([page.extract_text() or "" for page in reader.pages])
                        all_text.append(f"--- DOCUMENT: {path.name} ---\n{text}")
                elif path.suffix.lower() == '.pdf' and not pypdf:
                    logger.warning(f"Skipping PDF {path.name}: pypdf not installed")
                elif path.suffix.lower() in ['.docx', '.doc'] and docx:
                    doc = docx.Document(path)
                    text = "\n".join([p.text for p in doc.paragraphs])
                    all_text.append(f"--- DOCUMENT: {path.name} ---\n{text}")
                elif path.suffix.lower() in ['.txt', '.md', '.csv', '.json']:
                    text = path.read_text(encoding='utf-8', errors='ignore')
                    all_text.append(f"--- DOCUMENT: {path.name} ---\n{text}")
            except Exception as e:
                logger.error(f"Failed to extract text from {path}: {e}")
                
        return "\n\n".join(all_text)
