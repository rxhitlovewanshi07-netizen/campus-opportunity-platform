#!/bin/bash
set -u

# Run this script from any directory. It expects the project's venv folder.
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_PYTHON="$PROJECT_DIR/venv/bin/python"
LOG_FILE="$PROJECT_DIR/reminders.log"

if [[ ! -x "$VENV_PYTHON" ]]; then
    echo "Virtual environment Python not found: $VENV_PYTHON" >&2
    echo "Create the project's venv or update VENV_PYTHON in run_reminders.sh." >&2
    exit 1
fi

cd "$PROJECT_DIR" || exit 1
{
    echo "===== $(date) ====="
    "$VENV_PYTHON" manage.py send_reminders
    echo "Exit code: $?"
} >> "$LOG_FILE" 2>&1
