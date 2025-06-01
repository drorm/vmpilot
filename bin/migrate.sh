#!/bin/bash
# VMPilot Database Migration Script
# This script provides database migration utilities for VMPilot

set -e

# Get the directory where the script is located and move up one level to root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export VMPILOT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Change to the database directory
cd "$VMPILOT_ROOT/src/vmpilot/db"

# Function to show usage
show_usage() {
    echo "VMPilot Database Migration Utility"
    echo ""
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  current     Show current database revision"
    echo "  history     Show migration history"
    echo "  upgrade     Apply all pending migrations"
    echo "  downgrade   Downgrade database by one revision"
    echo "  create      Create a new migration (requires message)"
    echo ""
    echo "Examples:"
    echo "  $0 current"
    echo "  $0 upgrade"
    echo "  $0 create \"add new table\""
    echo "  $0 downgrade"
    echo ""
}

# Check if alembic is available (prefer python -m alembic)
if python -m alembic --version &> /dev/null; then
    ALEMBIC_CMD="python -m alembic"
elif command -v alembic &> /dev/null; then
    ALEMBIC_CMD="alembic"
else
    echo "Error: alembic not found. Please install alembic:"
    echo "  pip install alembic"
    exit 1
fi

# Parse command line arguments
COMMAND=${1:-""}

case "$COMMAND" in
    "current")
        echo "Current database revision:"
        $ALEMBIC_CMD current
        ;;
    "history")
        echo "Migration history:"
        $ALEMBIC_CMD history --verbose
        ;;
    "upgrade")
        echo "Applying database migrations..."
        $ALEMBIC_CMD upgrade head
        echo "Database migrations completed successfully"
        ;;
    "downgrade")
        echo "Downgrading database by one revision..."
        $ALEMBIC_CMD downgrade -1
        echo "Database downgrade completed"
        ;;
    "create")
        MESSAGE=${2:-""}
        if [ -z "$MESSAGE" ]; then
            echo "Error: Migration message is required for create command"
            echo "Usage: $0 create \"migration message\""
            exit 1
        fi
        echo "Creating new migration: $MESSAGE"
        $ALEMBIC_CMD revision -m "$MESSAGE"
        echo "Migration created successfully"
        ;;
    "help"|"-h"|"--help"|"")
        show_usage
        ;;
    *)
        echo "Error: Unknown command '$COMMAND'"
        echo ""
        show_usage
        exit 1
        ;;
esac
