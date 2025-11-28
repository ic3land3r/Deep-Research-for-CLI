#!/bin/bash
# Navigate to the script's directory (project root)
cd "$(dirname "$0")"

# Set the API Key
export GOOGLE_API_KEY="api_key"

# Run the server using uv
# We assume uv is in the user's local bin or system path. 
# If not found, we try the common location.
UV_BIN=$(which uv)
if [ -z "$UV_BIN" ]; then
    UV_BIN="$HOME/.local/bin/uv"
fi

# Execute
"$UV_BIN" run server.py
