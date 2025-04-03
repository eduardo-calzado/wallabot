#!/bin/bash
# Run Wallabot periodically

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "$(date): Running Wallabot..." >> wallabot.log
python3 wallabot.py >> wallabot.log 2>&1
echo "$(date): Finished Wallabot run" >> wallabot.log
echo "-----------------------------------" >> wallabot.log 