---
description: Clear Gemini CLI documentation search cache (inverted index)
argument-hint: [--force] (optional)
allowed-tools: Read, Bash(python:*), Bash(ls:*), Bash(du:*), Bash(test:*), Glob
---

# Clear Gemini Docs Cache Command

Clear the gemini-cli-docs search cache (inverted index). This forces the index to rebuild on the next documentation search.

## When to Use

- After manually editing `index.yaml` or documentation files
- When search results seem stale or incorrect
- After a `git pull` with documentation changes
- To free up disk space

## Arguments

- **No arguments**: Show what will be cleared and ask for confirmation
- **--force**: Skip confirmation and clear immediately

## Step 1: Parse Arguments

Check if `--force` flag is present in `$ARGUMENTS`.

```text
force_mode = "--force" in arguments (case-insensitive)
```

## Step 2: Locate Cache Directory

The gemini-cli-docs cache is located at:

```text
${CLAUDE_PLUGIN_ROOT}/skills/gemini-cli-docs/.cache/
```

Or via installed path:

```text
~/.claude/plugins/cache/<marketplace>/google-ecosystem/<version>/skills/gemini-cli-docs/.cache/
```

## Step 3: Check Cache Status

List the cache files:

| File | Purpose |
| --- | --- |
| `inverted_index.json` | Search index |
| `cache_version.json` | Hash-based validity tracking |

If cache directory doesn't exist or is empty, report: "Cache already clear. Nothing to do."

## Step 4: Confirmation (unless --force)

If NOT force_mode, present the cache clear plan:

```markdown
## Cache Clear Plan

**Target:** Gemini CLI documentation search index

| File | Size |
| --- | --- |
| inverted_index.json | X.X MB |
| cache_version.json | 512 bytes |

**Total:** X.X MB

> **Note:** The search index will rebuild automatically on the next documentation search.
> For immediate rebuild, run `/rebuild-gemini-docs-index` after clearing.

**Proceed?** Reply "yes" to continue, or use `--force` to skip this confirmation.
```

## Step 5: Clear Cache

Use the cache_manager.py script to clear:

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/gemini-cli-docs/scripts/utils/cache_manager.py" --clear
```

Or manually delete the cache files:

```bash
rm -f "${CLAUDE_PLUGIN_ROOT}/skills/gemini-cli-docs/.cache/inverted_index.json"
rm -f "${CLAUDE_PLUGIN_ROOT}/skills/gemini-cli-docs/.cache/cache_version.json"
```

## Step 6: Report Success

```markdown
## Cache Cleared

Successfully cleared Gemini CLI documentation search cache.

**Cleared:**
- inverted_index.json
- cache_version.json

**Next steps:**
- Search index will rebuild automatically on next search
- Or run `/rebuild-gemini-docs-index` to rebuild immediately
```

## Error Handling

- **Cache not found:** Report "Cache already clear or plugin not installed."
- **Permission denied:** Report "Permission denied. Try running with elevated privileges."
- **Plugin not installed:** Report "google-ecosystem plugin not found."
