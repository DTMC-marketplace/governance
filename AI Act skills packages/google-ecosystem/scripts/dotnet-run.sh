#!/bin/bash
# Cross-platform dotnet run wrapper that normalizes mixed path separators
# Usage: dotnet-run.sh <script.cs> [additional args...]
#
# Problem: When ${CLAUDE_PLUGIN_ROOT} expands with Windows backslashes and
# hooks.json paths use forward slashes, the resulting mixed path
# (e.g., C:\...\1.0.0/scripts/...) causes dotnet run to fail on Git Bash/MSYS.
#
# Solution: Normalize all backslashes to forward slashes before invoking dotnet.

SCRIPT="$1"
shift

# Normalize mixed path separators on Windows/Git Bash/MSYS
if [[ "$OSTYPE" == msys* || "$OSTYPE" == cygwin* || "$OSTYPE" == mingw* ]]; then
    # Convert backslashes to forward slashes using tr
    SCRIPT=$(echo "$SCRIPT" | tr '\\' '/')
fi

exec dotnet run "$SCRIPT" "$@"
