#!/bin/bash
# Navigate to the script's directory (project root)
cd "$(dirname "$0")"

# Load API Key from .env if it exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Fallback or manual set (if .env is missing)
if [ -z "$GOOGLE_API_KEY" ]; then
    export GOOGLE_API_KEY="YOUR_API_KEY_HERE"
fi

# Run the server using uv
# We assume uv is in the user's local bin or system path. 
# If not found, we try the common location.
UV_BIN=$(which uv)
if [ -z "$UV_BIN" ]; then
    UV_BIN="$HOME/.local/bin/uv"
fi

# Execute
"$UV_BIN" run server.py
