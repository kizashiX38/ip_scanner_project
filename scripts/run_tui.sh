#!/bin/bash
# run_tui.sh — Launch the IP Scanner TUI with sudo elevation
BASE_DIR=$(dirname "$(dirname "$(readlink -f "$0")")")
VENV_PATH="$BASE_DIR/venv"

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo "Error: Virtual environment not found at $VENV_PATH"
    exit 1
fi

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "===================================================="
    echo "  Network Scanner requires root privileges"
    echo "  Re-launching with sudo..."
    echo "===================================================="
    exec sudo -E "$0" "$@"
fi

# Activate virtual environment and run
source "$VENV_PATH/bin/activate"
python3 "$BASE_DIR/scripts/tui_scanner.py"
