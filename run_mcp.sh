#!/bin/bash

# --- 1. PREPARE LOGGING ---
# Redirect all System Logs (Stderr) to a file. 
# This prevents the "FastMCP" banner from breaking the connection
# and lets you see errors if it crashes.
LOG_FILE="/tmp/adk-deep-research.log"
exec 2>>"$LOG_FILE"

echo "=== Starting MCP Server at $(date) ===" >&2

# --- 2. SETUP ENVIRONMENT ---
# Navigate to the script's directory
cd "$(dirname "$0")"

# Load .env file if it exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# --- 3. CHECK API KEY ---
# CRITICAL: Ensure the key is actually set. 
# If .env is missing/empty, this block alerts the log file.
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "ERROR: GOOGLE_API_KEY is missing! Please add it to .env" >&2
    # You can temporarily hardcode it here for testing, but .env is better:
    # export GOOGLE_API_KEY="AIzaSy..." 
fi

# --- 4. LOCATE UV ---
# Hardcode path to ensure it works even if HOME/PATH are missing in the IDE environment
UV_BIN="/home/lander/.local/bin/uv"

if [ ! -f "$UV_BIN" ]; then
    echo "CRITICAL ERROR: 'uv' not found at $UV_BIN" >&2
    exit 1
fi

echo "Using uv path: $UV_BIN" >&2

# --- 5. EXECUTE SERVER ---
# Use unbuffered output to prevent MCP communication issues
export PYTHONUNBUFFERED=1

# Always use 'uv run' to ensure dependencies (fastmcp) are available.
# The previous attempt to use .venv/bin/python directly failed because dependencies weren't installed/sync'd.
exec "$UV_BIN" run --quiet server.py
