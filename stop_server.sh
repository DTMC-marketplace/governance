#!/bin/bash
# Stop Django server running on port 8000

echo "🛑 Stopping server on port 8000..."

PID=$(lsof -ti:8000)

if [ -z "$PID" ]; then
    echo "✅ No server running on port 8000"
else
    echo "🔍 Found process: $PID"
    kill -9 $PID
    echo "✅ Server stopped"
fi
