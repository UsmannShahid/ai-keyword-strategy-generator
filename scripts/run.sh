#!/usr/bin/env bash
# run.sh - Simple script to activate venv and run the app

# For Windows (PowerShell)
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    ./venv/Scripts/Activate.ps1
    streamlit run app.py --server.port 8504
else
    # For Unix-like systems
    source venv/bin/activate
    streamlit run app.py --server.port 8504
fi
