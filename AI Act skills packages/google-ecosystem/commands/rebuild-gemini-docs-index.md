---
description: Force rebuild of Gemini CLI documentation search index
argument-hint: [--force] (optional)
allowed-tools: Read, Write, Bash(python:*), Bash(ls:*), Bash(test:*), Glob
---

# Rebuild Gemini Docs Index Command

Clear and immediately rebuild the gemini-cli-docs search index. This is faster than `/clear-gemini-docs-cache` + waiting for next search because it triggers the rebuild immediately.

## When to Use

- After manually editing `index.yaml` or documentation files
- When search results seem stale or incorrect
- After a `git pull` with documentation changes
- When you need search working immediately

## Difference from /clear-gemini-docs-cache

| Command | Action | Search Availability |
| --- | --- | --- |
| `/clear-gemini-docs-cache` | Clears cache only | Rebuild on next search (lazy) |
| `/rebuild-gemini-docs-index` | Clears + rebuilds | Immediate (eager) |

## Arguments

- **No arguments**: Show plan and ask for confirmation
- **--force**: Skip confirmation and rebuild immediately

## Instructions

This command clears the Gemini CLI documentation search cache and immediately rebuilds the index.

### Check Current Status

First, check the current cache state. Report whether the cache exists, is valid, and when it was last built.

### Request Confirmation

Unless the user passed `--force`, show a rebuild plan with the current cache state and ask for confirmation before proceeding. Explain that rebuilding takes a few seconds and search will be unavailable during the rebuild.

### Clear and Rebuild

Once confirmed (or if `--force` was passed):

1. Clear the cache using the cache_manager.py --clear command
2. Rebuild the index using rebuild_index.py
3. Verify the rebuild succeeded using manage_index.py verify

### Report Results

Report the new index statistics including document count and build time. Confirm that search is now available.

```markdown
## Index Rebuilt

Successfully rebuilt Gemini CLI documentation search index.

**New index stats:**
- Documents: X
- Build time: Xms

**Search is now available.**
```

## Error Handling

- **Plugin not installed:** Report "google-ecosystem plugin not found."
- **Rebuild failed:** Report error from script
- **Permission denied:** Report with remediation steps
