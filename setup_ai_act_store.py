#!/usr/bin/env python3
"""
EU AI Act - Gemini File Search Store Setup
==========================================
This script creates a Gemini File Search Store (managed RAG vector database)
and uploads the EU AI Act documents for semantic search capabilities.

Requirements:
    pip install google-genai

Usage:
    export GEMINI_API_KEY="your-api-key-here"
    python setup_ai_act_store.py

After setup, you can query the store using the query_ai_act.py script.
"""

from pathlib import Path
from google import genai
import os

print("=" * 80)
print("[setup_ai_act_store] MODULE LOADED")
print("=" * 80)

# Configuration
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
STORE_DISPLAY_NAME = "EU-AI-Act-GDPR-Knowledge-Base"
BASE_DIR = Path(__file__).resolve().parent
ARTICLES_DIR = BASE_DIR / "ai_act_articles"  # Updated to use ai_act_articles directory

print(f"[setup_ai_act_store] BASE_DIR: {BASE_DIR}")
print(f"[setup_ai_act_store] ARTICLES_DIR: {ARTICLES_DIR}")
print(f"[setup_ai_act_store] ARTICLES_DIR exists: {ARTICLES_DIR.exists()}")
print(f"[setup_ai_act_store] GEMINI_API_KEY found: {bool(GEMINI_API_KEY)}")
print("=" * 80)

def create_client():
    """Initialize the Gemini API client."""
    print("  [setup_ai_act_store] create_client() called")
    if not GEMINI_API_KEY:
        print("  [setup_ai_act_store] ERROR: GEMINI_API_KEY not found!")
        raise ValueError("Please set the GEMINI_API_KEY environment variable")
    print(f"  [setup_ai_act_store] GEMINI_API_KEY found (length: {len(GEMINI_API_KEY)})")
    client = genai.Client(api_key=GEMINI_API_KEY)
    print("  [setup_ai_act_store] Client created successfully")
    return client

def create_file_search_store(client, quiet=False):
    """Create a new File Search Store for the AI Act documents."""
    print("  [setup_ai_act_store] create_file_search_store() called")
    if not quiet:
        print(f"Creating File Search Store: {STORE_DISPLAY_NAME}")
    
    print("  [setup_ai_act_store] Checking for existing stores...")
    # Check if store already exists
    existing_stores = list(client.file_search_stores.list())
    print(f"  [setup_ai_act_store] Found {len(existing_stores)} existing store(s)")
    
    for store in existing_stores:
        if store.display_name == STORE_DISPLAY_NAME:
            if not quiet:
                print(f"Store already exists: {store.name}")
            print(f"  [setup_ai_act_store] Using existing store: {store.name}")
            return store
    
    # Create new store
    print("  [setup_ai_act_store] Creating new store...")
    store = client.file_search_stores.create(
        config={'display_name': STORE_DISPLAY_NAME}
    )
    if not quiet:
        print(f"Created store: {store.name}")
    print(f"  [setup_ai_act_store] New store created: {store.name}")
    return store

def iter_article_documents():
    """Yield every file under the ai_act_articles directory."""
    if not ARTICLES_DIR.exists():
        return []
    return sorted([p for p in ARTICLES_DIR.rglob('*') if p.is_file()])


def get_existing_files(client, store_name, quiet=False):
    """Return a set of display names for files already in the store."""
    if not quiet:
        print("Checking existing files in store...")
    existing_files = set()
    try:
        # Note: pagination might be needed for >100 files, checking if iterator handles it
        files = client.file_search_stores.documents.list(parent=store_name)
        for f in files:
            if f.display_name:
                existing_files.add(f.display_name)
    except Exception as e:
        if not quiet:
            print(f"  Warning: Could not list existing files: {e}")
    return existing_files

def upload_documents(client, store):
    """Upload every article document to the File Search Store."""
    article_files = iter_article_documents()

    if not article_files:
        print(f"\nNo article documents found under {ARTICLES_DIR}")
        return 0

    existing_files = get_existing_files(client, store.name)
    print(f"\nFound {len(existing_files)} existing files in store.")
    
    print(f"\nProcessing {len(article_files)} documents from {ARTICLES_DIR}...")

    uploaded_count = 0
    skipped_count = 0
    
    for idx, file_path in enumerate(article_files, start=1):
        rel_name = file_path.relative_to(ARTICLES_DIR)
        display_name = str(rel_name)
        
        if display_name in existing_files:
            skipped_count += 1
            print(f"  [{idx}/{len(article_files)}] Skipping {display_name} (already exists)")
            continue

        try:
            print(f"  [{idx}/{len(article_files)}] Uploading {display_name}")
            with open(file_path, 'rb') as f:
                client.file_search_stores.upload_to_file_search_store(
                    file_search_store_name=store.name,
                    file=f,
                    config={'display_name': display_name, 'mime_type': 'text/plain'}
                )
            uploaded_count += 1
        except Exception as e:
            print(f"    Error uploading {file_path}: {e}")

    print(f"\nUpload summary: {uploaded_count} uploaded, {skipped_count} skipped.")
    return uploaded_count

def list_store_contents(client, store):
    """List documents in the File Search Store."""
    print(f"\nDocuments in store '{store.display_name}':")
    try:
        docs = list(client.file_search_stores.documents.list(parent=store.name))
        for doc in docs[:10]:  # Show first 10
            print(f"  - {doc.display_name}")
        if len(docs) > 10:
            print(f"  ... and {len(docs) - 10} more documents")
        return len(docs)
    except Exception as e:
        print(f"  Error listing documents: {e}")
        return 0

def upload_single_file(client, store, file_path, display_name=None, quiet=False):
    """
    Upload a single file to the File Search Store.
    
    Args:
        client: Gemini API client
        store: File Search Store object
        file_path: Path to the file to upload
        display_name: Optional display name for the file in the store
        quiet: If True, suppress print statements (useful when called from API)
    
    Returns:
        True if file was uploaded, False if it already exists
    """
    print("  [setup_ai_act_store] upload_single_file() called")
    print(f"  [setup_ai_act_store] file_path: {file_path}")
    print(f"  [setup_ai_act_store] display_name: {display_name}")
    print(f"  [setup_ai_act_store] quiet: {quiet}")
    
    if not file_path.exists():
        print(f"  [setup_ai_act_store] ERROR: File not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")
    
    print(f"  [setup_ai_act_store] File exists: {file_path.exists()}")
    print(f"  [setup_ai_act_store] File size: {file_path.stat().st_size} bytes")
    
    if display_name is None:
        # Use relative path from ARTICLES_DIR (ai_act_articles) if possible, otherwise just filename
        try:
            display_name = str(file_path.relative_to(ARTICLES_DIR))
        except ValueError:
            # Fallback to just filename if not in ARTICLES_DIR
            display_name = file_path.name
    
    # Check if file already exists in store
    print("  [setup_ai_act_store] Checking if file already exists in store...")
    existing_files = get_existing_files(client, store.name, quiet=quiet)
    print(f"  [setup_ai_act_store] Found {len(existing_files)} existing files in store")
    
    if display_name in existing_files:
        print(f"  [setup_ai_act_store] File '{display_name}' already exists in store, skipping...")
        if not quiet:
            print(f"  File '{display_name}' already exists in store, skipping...")
        return False
    
    try:
        print(f"  [setup_ai_act_store] Starting upload of {display_name}...")
        if not quiet:
            print(f"  Uploading {display_name} to store...")
        
        print(f"  [setup_ai_act_store] Opening file: {file_path}")
        with open(file_path, 'rb') as f:
            print(f"  [setup_ai_act_store] Calling upload_to_file_search_store...")
            print(f"  [setup_ai_act_store] Store name: {store.name}")
            print(f"  [setup_ai_act_store] Display name: {display_name}")
            
            client.file_search_stores.upload_to_file_search_store(
                file_search_store_name=store.name,
                file=f,
                config={'display_name': display_name, 'mime_type': 'text/plain'}
            )
        
        print(f"  [setup_ai_act_store] ✓ Upload completed successfully!")
        if not quiet:
            print(f"  ✓ Successfully uploaded {display_name}")
        return True
    except Exception as e:
        print(f"  [setup_ai_act_store] ✗ ERROR during upload: {e}")
        import traceback
        traceback.print_exc()
        if not quiet:
            print(f"  ✗ Error uploading {file_path}: {e}")
        raise

def main(file_paths=None):
    """
    Main function to set up the AI Act File Search Store.
    
    Args:
        file_paths: Optional list of specific file paths to upload.
                    If None, uploads all files from ai_act_articles directory.
    """
    print("=" * 60)
    print("EU AI Act - Gemini File Search Store Setup")
    print("=" * 60)
    
    # Initialize client
    client = create_client()
    print("✓ Gemini API client initialized")
    
    # Create store
    store = create_file_search_store(client, quiet=False)
    
    # Upload documents
    if file_paths:
        # Upload specific files
        print(f"\nUploading {len(file_paths)} specific file(s)...")
        uploaded_count = 0
        for file_path in file_paths:
            file_path_obj = Path(file_path) if isinstance(file_path, str) else file_path
            if upload_single_file(client, store, file_path_obj):
                uploaded_count += 1
        print(f"\nUpload summary: {uploaded_count} uploaded.")
    else:
        # Upload all documents from ai_act_articles directory
        upload_documents(client, store)
    
    # List contents
    doc_count = list_store_contents(client, store)
    
    print("\n" + "=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    print(f"Store Name: {store.name}")
    print(f"Display Name: {store.display_name}")
    print(f"Documents indexed: {doc_count}")
    print("\nYou can now query this store using the Gemini API")
    print("with the FileSearch tool configuration.")
    
    # Save store name for later use
    store_info_path = BASE_DIR / "store_info.txt"
    with open(store_info_path, 'w') as f:
        f.write(f"store_name={store.name}\n")
        f.write(f"display_name={store.display_name}\n")
    print(f"\nStore info saved to: {store_info_path}")
    
    return store

if __name__ == "__main__":
    main()
