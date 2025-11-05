#!/bin/bash
#
# Claude Orchestrator Test Runner
#
# This script runs the comprehensive test suite for the Claude Orchestrator
#

set -e  # Exit on error

echo "=================================="
echo "Claude Orchestrator Test Suite"
echo "=================================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

# Check if required dependencies are installed
echo ""
echo "Checking dependencies..."

if ! python3 -c "import asyncio" 2>/dev/null; then
    echo "ERROR: asyncio not available"
    exit 1
fi

if ! python3 -c "import psutil" 2>/dev/null; then
    echo "WARNING: psutil not installed. Installing..."
    pip3 install psutil
fi

# Check git configuration
echo ""
echo "Checking git configuration..."
if ! git config user.email > /dev/null 2>&1; then
    echo "Setting default git user.email..."
    git config --global user.email "test@orchestrator.local"
fi

if ! git config user.name > /dev/null 2>&1; then
    echo "Setting default git user.name..."
    git config --global user.name "Orchestrator Test"
fi

# Create test directories
echo ""
echo "Setting up test environment..."
mkdir -p ~/claude-orchestrator/test_results
mkdir -p ~/claude-orchestrator/worktrees

# Run tests
echo ""
echo "=================================="
echo "Running Test Suite..."
echo "=================================="
echo ""

cd ~/claude-orchestrator
python3 test_orchestrator.py

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "=================================="
    echo "✓ ALL TESTS PASSED"
    echo "=================================="
    echo ""
    echo "Test results saved to: ~/claude-orchestrator/test_results/"
    exit 0
else
    echo ""
    echo "=================================="
    echo "✗ SOME TESTS FAILED"
    echo "=================================="
    echo ""
    echo "Check logs at: ~/claude-orchestrator/test_results/"
    exit 1
fi
