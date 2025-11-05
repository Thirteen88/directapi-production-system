#!/bin/bash
# Claude Orchestrator - Activation Script
# This script activates the orchestrator for the current shell session

echo "========================================"
echo "Claude Orchestrator - Activation"
echo "========================================"
echo ""

# Export the environment variable
export CLAUDE_ORCHESTRATOR_PATH="/home/gary/claude-orchestrator"

# Verify it's set
if [ -n "$CLAUDE_ORCHESTRATOR_PATH" ]; then
    echo "✓ CLAUDE_ORCHESTRATOR_PATH set to: $CLAUDE_ORCHESTRATOR_PATH"
else
    echo "✗ Failed to set CLAUDE_ORCHESTRATOR_PATH"
    exit 1
fi

echo ""
echo "========================================"
echo "Activation Complete!"
echo "========================================"
echo ""
echo "The orchestrator is now active in this session."
echo ""
echo "To make it permanent for new tabs/sessions:"
echo "  The environment variable is already in ~/.bashrc and ~/.zshrc"
echo "  All NEW terminal tabs will automatically have it active."
echo ""
echo "To verify:"
echo "  echo \$CLAUDE_ORCHESTRATOR_PATH"
echo ""
