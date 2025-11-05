#!/bin/bash

##############################################################################
# Claude Multi-Agent Orchestrator - Installation Verification
##############################################################################
# Version: 1.0.0
# Created: 2025-10-23
# Purpose: Verify the orchestrator global installation
##############################################################################

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_section() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

PASSED=0
FAILED=0

##############################################################################
# Verification Tests
##############################################################################

print_section "Claude Orchestrator - Installation Verification"

# Test 1: Check CLAUDE.md exists
if [ -f "$HOME/.claude/CLAUDE.md" ]; then
    print_success "CLAUDE.md master rules file exists"
    ((PASSED++))
else
    print_error "CLAUDE.md master rules file missing"
    ((FAILED++))
fi

# Test 2: Check rules directory exists
if [ -d "$HOME/.claude/rules" ]; then
    print_success "Rules directory exists"
    ((PASSED++))
else
    print_error "Rules directory missing"
    ((FAILED++))
fi

# Test 3: Check orchestration-rules.md symlink
if [ -L "$HOME/.claude/rules/orchestration-rules.md" ]; then
    TARGET=$(readlink "$HOME/.claude/rules/orchestration-rules.md")
    if [ -f "$TARGET" ]; then
        print_success "Orchestration rules symlink valid (→ $TARGET)"
        ((PASSED++))
    else
        print_error "Orchestration rules symlink broken (→ $TARGET)"
        ((FAILED++))
    fi
else
    print_error "Orchestration rules symlink missing"
    ((FAILED++))
fi

# Test 4: Check orchestrator directory
if [ -d "$HOME/claude-orchestrator" ]; then
    print_success "Orchestrator directory exists"
    ((PASSED++))
else
    print_error "Orchestrator directory missing"
    ((FAILED++))
fi

# Test 5: Check orchestrator.py
if [ -f "$HOME/claude-orchestrator/orchestrator.py" ]; then
    print_success "orchestrator.py found"
    ((PASSED++))
else
    print_error "orchestrator.py missing"
    ((FAILED++))
fi

# Test 6: Check CLAUDE_ORCHESTRATION.md
if [ -f "$HOME/claude-orchestrator/CLAUDE_ORCHESTRATION.md" ]; then
    print_success "CLAUDE_ORCHESTRATION.md found"
    ((PASSED++))
else
    print_error "CLAUDE_ORCHESTRATION.md missing"
    ((FAILED++))
fi

# Test 7: Check install.sh
if [ -x "$HOME/claude-orchestrator/install.sh" ]; then
    print_success "install.sh found and executable"
    ((PASSED++))
else
    print_error "install.sh missing or not executable"
    ((FAILED++))
fi

# Test 8: Check audit-logs directory
if [ -d "$HOME/claude-orchestrator/audit-logs" ]; then
    print_success "Audit logs directory exists"
    ((PASSED++))
else
    print_error "Audit logs directory missing"
    ((FAILED++))
fi

# Test 9: Check shell integration (.bashrc)
if [ -f "$HOME/.bashrc" ]; then
    if grep -q "CLAUDE_ORCHESTRATOR_PATH" "$HOME/.bashrc"; then
        print_success "Shell integration found in .bashrc"
        ((PASSED++))
    else
        print_error "Shell integration missing from .bashrc"
        ((FAILED++))
    fi
else
    print_info ".bashrc not found (skipping)"
fi

# Test 10: Check shell integration (.zshrc)
if [ -f "$HOME/.zshrc" ]; then
    if grep -q "CLAUDE_ORCHESTRATOR_PATH" "$HOME/.zshrc"; then
        print_success "Shell integration found in .zshrc"
        ((PASSED++))
    else
        print_error "Shell integration missing from .zshrc"
        ((FAILED++))
    fi
else
    print_info ".zshrc not found (skipping)"
fi

# Test 11: Check environment variable (current session)
if [ -n "$CLAUDE_ORCHESTRATOR_PATH" ]; then
    print_success "CLAUDE_ORCHESTRATOR_PATH is set: $CLAUDE_ORCHESTRATOR_PATH"
    ((PASSED++))
else
    print_error "CLAUDE_ORCHESTRATOR_PATH not set (run: source ~/.bashrc or ~/.zshrc)"
    ((FAILED++))
fi

# Test 12: Check Python availability
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    print_success "Python 3 available: $PYTHON_VERSION"
    ((PASSED++))
else
    print_error "Python 3 not found"
    ((FAILED++))
fi

# Test 13: Test Python import
if python3 -c "import json, sys, os, re, datetime" &> /dev/null; then
    print_success "Python standard library imports work"
    ((PASSED++))
else
    print_error "Python standard library import failed"
    ((FAILED++))
fi

# Test 14: Check Git availability
if command -v git &> /dev/null; then
    GIT_VERSION=$(git --version 2>&1 | awk '{print $3}')
    print_success "Git available: $GIT_VERSION"
    ((PASSED++))
else
    print_info "Git not found (optional, but recommended)"
fi

print_section "Verification Summary"

echo "Tests Passed: $PASSED"
echo "Tests Failed: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All verification tests passed!${NC}"
    echo ""
    echo "The orchestrator is properly installed and ready to use."
    echo ""
    echo "Next steps:"
    echo "1. If CLAUDE_ORCHESTRATOR_PATH is not set, run: source ~/.bashrc (or ~/.zshrc)"
    echo "2. Read the documentation: cat ~/.claude/CLAUDE.md"
    echo "3. Review orchestration rules: less ~/.claude/rules/orchestration-rules.md"
    echo ""
    exit 0
else
    echo -e "${RED}✗ Some verification tests failed.${NC}"
    echo ""
    echo "Please run the installation script to fix issues:"
    echo "  cd ~/claude-orchestrator && ./install.sh"
    echo ""
    exit 1
fi
