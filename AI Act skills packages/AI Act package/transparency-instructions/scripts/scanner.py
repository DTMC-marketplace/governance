"""
Scanner Module for Transparency Instructions
============================================
Isolated file scanning logic.
Adopts pattern from 'deployer-training' but is self-contained.
"""

import os
from pathlib import Path
from typing import List, Set

# File extensions to ingest
TEXT_EXTENSIONS = {
    # Programming Languages
    ".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".java", ".kt", ".scala",
    ".c", ".cpp", ".h", ".hpp", ".cs", ".swift", ".rb", ".php", ".pl", ".lua",
    ".sh", ".bash", ".zsh", ".ps1", ".bat", ".cmd", ".dart",
    # Web & Config
    ".html", ".htm", ".css", ".scss", ".sass", ".less",
    ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf",
    ".xml", ".xsl", ".xslt",
    # Documentation
    ".md", ".markdown", ".rst", ".txt", ".adoc",
}

# Files to always exclude (security)
EXCLUDED_FILES = {".env", ".env.local", ".env.production", ".env.development", "secrets.json"}

def load_gitignore_patterns(repo_root: Path) -> Set[str]:
    """Load patterns from .gitignore file."""
    patterns = set()
    gitignore_path = repo_root / ".gitignore"
    if gitignore_path.exists():
        try:
            for line in gitignore_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    patterns.add(line)
        except Exception:
            pass
    return patterns

def is_ignored(path: Path, repo_root: Path, gitignore_patterns: Set[str]) -> bool:
    """Check if a path should be ignored based on .gitignore and security rules."""
    try:
        relative_path = path.relative_to(repo_root)
    except ValueError:
        return True # Path not in repo root
        
    path_str = str(relative_path).replace("\\", "/")
    
    if path.name in EXCLUDED_FILES:
        return True
    
    for pattern in gitignore_patterns:
        pattern_clean = pattern.strip("/")
        if pattern_clean in path_str or path.name == pattern_clean:
            return True
        if pattern_clean.endswith("/") and path_str.startswith(pattern_clean):
            return True
    
    return False

def scan_codebase(repo_root: Path) -> List[dict]:
    """Scan the repo and collect file contents."""
    files_data = []
    repo_root = Path(repo_root).resolve()
    
    gitignore_patterns = load_gitignore_patterns(repo_root)
    # Add standard ignore dirs
    gitignore_patterns.update({"node_modules", ".git", "__pycache__", ".venv", "venv", "dist", "build", "site-packages", "Output"})
    
    if not repo_root.exists():
        print(f"Error: Repo path not found: {repo_root}")
        return []

    for root, dirs, files in os.walk(repo_root):
        root_path = Path(root)
        # Modify dirs in-place to skip ignored directories
        dirs[:] = [d for d in dirs if not is_ignored(root_path / d, repo_root, gitignore_patterns)]
        
        for file_name in files:
            file_path = root_path / file_name
            if is_ignored(file_path, repo_root, gitignore_patterns):
                continue
            
            # Simple binary check via extension
            if file_path.suffix.lower() not in TEXT_EXTENSIONS and file_path.name.lower() not in {"makefile", "dockerfile", "license"}:
                continue
                
            try:
                # Try UTF-8 reading
                content = file_path.read_text(encoding="utf-8", errors='replace')
                relative_path = file_path.relative_to(repo_root)
                files_data.append({
                    "path": str(relative_path).replace("\\", "/"),
                    "content": content
                })
            except Exception as e:
                # Skip unreadable files
                pass
    
    return files_data

def build_context_string(files_data: List[dict], max_chars: int = 500000) -> str:
    """Build a context string, potentially truncated if too large."""
    context_parts = []
    current_chars = 0
    
    for file_info in files_data:
        part = f"--- FILE: {file_info['path']} ---\n{file_info['content']}\n"
        if current_chars + len(part) > max_chars:
            context_parts.append(f"\n[...Truncated after {max_chars} chars...]")
            break
        context_parts.append(part)
        current_chars += len(part)
        
    return "\n".join(context_parts)
