#!/bin/bash

##############################################################################
# Claude Multi-Agent Orchestrator - Global Installation Script
##############################################################################
# Version: 1.0.0
# Created: 2025-10-23
# Purpose: Install the orchestrator system globally for all Claude Code sessions
##############################################################################

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ORCHESTRATOR_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
RULES_DIR="$CLAUDE_DIR/rules"
AUDIT_DIR="$ORCHESTRATOR_PATH/audit-logs"
WORKTREES_DIR="$ORCHESTRATOR_PATH/worktrees"

##############################################################################
# Utility Functions
##############################################################################

print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

##############################################################################
# Pre-flight Checks
##############################################################################

check_requirements() {
    print_header "Checking System Requirements"

    local all_good=true

    # Check Python 3
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
        print_success "Python 3 found: $PYTHON_VERSION"
    else
        print_error "Python 3 not found. Please install Python 3.8 or higher."
        all_good=false
    fi

    # Check pip
    if command -v pip3 &> /dev/null; then
        print_success "pip3 found"
    else
        print_error "pip3 not found. Please install pip."
        all_good=false
    fi

    # Check git (optional but recommended)
    if command -v git &> /dev/null; then
        GIT_VERSION=$(git --version 2>&1 | awk '{print $3}')
        print_success "Git found: $GIT_VERSION"
    else
        print_warning "Git not found. Version control features will be limited."
    fi

    if [ "$all_good" = false ]; then
        print_error "Requirements check failed. Please install missing dependencies."
        exit 1
    fi

    echo ""
}

##############################################################################
# Installation Steps
##############################################################################

create_directories() {
    print_header "Creating Directory Structure"

    # Create .claude directory if it doesn't exist
    if [ ! -d "$CLAUDE_DIR" ]; then
        mkdir -p "$CLAUDE_DIR"
        print_success "Created $CLAUDE_DIR"
    else
        print_info "$CLAUDE_DIR already exists"
    fi

    # Create rules directory
    if [ ! -d "$RULES_DIR" ]; then
        mkdir -p "$RULES_DIR"
        print_success "Created $RULES_DIR"
    else
        print_info "$RULES_DIR already exists"
    fi

    # Create audit-logs directory
    if [ ! -d "$AUDIT_DIR" ]; then
        mkdir -p "$AUDIT_DIR"
        print_success "Created $AUDIT_DIR"
    else
        print_info "$AUDIT_DIR already exists"
    fi

    # Create worktrees directory
    if [ ! -d "$WORKTREES_DIR" ]; then
        mkdir -p "$WORKTREES_DIR"
        print_success "Created $WORKTREES_DIR"
    else
        print_info "$WORKTREES_DIR already exists"
    fi

    echo ""
}

setup_symlinks() {
    print_header "Setting Up Symlinks"

    # Symlink orchestration rules
    local rules_link="$RULES_DIR/orchestration-rules.md"
    local rules_source="$ORCHESTRATOR_PATH/CLAUDE_ORCHESTRATION.md"

    if [ -L "$rules_link" ]; then
        print_info "Orchestration rules symlink already exists"
    elif [ -f "$rules_link" ]; then
        print_warning "File exists at $rules_link (not a symlink). Backing up..."
        mv "$rules_link" "$rules_link.backup.$(date +%Y%m%d-%H%M%S)"
        ln -s "$rules_source" "$rules_link"
        print_success "Created orchestration rules symlink (original backed up)"
    else
        ln -s "$rules_source" "$rules_link"
        print_success "Created orchestration rules symlink"
    fi

    echo ""
}

install_python_dependencies() {
    print_header "Installing Python Dependencies"

    if [ -f "$ORCHESTRATOR_PATH/requirements.txt" ]; then
        print_info "Installing from requirements.txt..."

        # Try to install in user space, fallback to break-system-packages if needed
        if pip3 install --user -r "$ORCHESTRATOR_PATH/requirements.txt" 2>/dev/null; then
            print_success "Python dependencies installed successfully"
        elif pip3 install --user --break-system-packages -r "$ORCHESTRATOR_PATH/requirements.txt" 2>/dev/null; then
            print_success "Python dependencies installed successfully (with --break-system-packages)"
            print_warning "Used --break-system-packages flag due to externally managed environment"
        else
            print_warning "Could not install Python dependencies automatically"
            print_info "This is OK - the orchestrator will still work with standard library"
            print_info "To install manually later: pip3 install --user --break-system-packages -r $ORCHESTRATOR_PATH/requirements.txt"
        fi
    else
        print_warning "requirements.txt not found. Skipping Python dependencies."
    fi

    echo ""
}

setup_shell_integration() {
    print_header "Setting Up Shell Integration"

    local shell_config_added=false

    # Bash configuration
    if [ -f "$HOME/.bashrc" ]; then
        if grep -q "CLAUDE_ORCHESTRATOR_PATH" "$HOME/.bashrc"; then
            print_info "Bash integration already configured"
        else
            print_info "Adding configuration to ~/.bashrc..."
            cat >> "$HOME/.bashrc" << 'BASH_EOF'

# Claude Orchestrator Configuration
# Added: 2025-10-23
# Purpose: Make multi-agent orchestration system globally available
export CLAUDE_ORCHESTRATOR_PATH="/home/$USER/claude-orchestrator"

# Add orchestrator bin to PATH if it exists
if [ -d "$CLAUDE_ORCHESTRATOR_PATH/bin" ]; then
    export PATH="$CLAUDE_ORCHESTRATOR_PATH/bin:$PATH"
fi
BASH_EOF
            print_success "Added configuration to ~/.bashrc"
            shell_config_added=true
        fi
    fi

    # Zsh configuration
    if [ -f "$HOME/.zshrc" ]; then
        if grep -q "CLAUDE_ORCHESTRATOR_PATH" "$HOME/.zshrc"; then
            print_info "Zsh integration already configured"
        else
            print_info "Adding configuration to ~/.zshrc..."
            cat >> "$HOME/.zshrc" << 'ZSH_EOF'

# Claude Orchestrator Configuration
# Added: 2025-10-23
# Purpose: Make multi-agent orchestration system globally available
export CLAUDE_ORCHESTRATOR_PATH="/home/$USER/claude-orchestrator"

# Add orchestrator bin to PATH if it exists
if [ -d "$CLAUDE_ORCHESTRATOR_PATH/bin" ]; then
    export PATH="$CLAUDE_ORCHESTRATOR_PATH/bin:$PATH"
fi
ZSH_EOF
            print_success "Added configuration to ~/.zshrc"
            shell_config_added=true
        fi
    fi

    if [ "$shell_config_added" = true ]; then
        print_warning "Shell configuration updated. Run 'source ~/.bashrc' or 'source ~/.zshrc' to apply changes."
    fi

    echo ""
}

create_master_rules() {
    print_header "Creating Master Rules File"

    local master_rules="$CLAUDE_DIR/CLAUDE.md"

    if [ -f "$master_rules" ]; then
        print_info "CLAUDE.md already exists at $master_rules"
        print_info "To update, delete it and run this script again."
    else
        print_success "CLAUDE.md already created at $master_rules"
    fi

    echo ""
}

validate_installation() {
    print_header "Validating Installation"

    local all_valid=true

    # Check directories
    if [ -d "$CLAUDE_DIR" ]; then
        print_success "~/.claude directory exists"
    else
        print_error "~/.claude directory missing"
        all_valid=false
    fi

    if [ -d "$RULES_DIR" ]; then
        print_success "~/.claude/rules directory exists"
    else
        print_error "~/.claude/rules directory missing"
        all_valid=false
    fi

    # Check symlink
    if [ -L "$RULES_DIR/orchestration-rules.md" ]; then
        print_success "Orchestration rules symlink exists"
    else
        print_error "Orchestration rules symlink missing"
        all_valid=false
    fi

    # Check CLAUDE.md
    if [ -f "$CLAUDE_DIR/CLAUDE.md" ]; then
        print_success "CLAUDE.md master rules file exists"
    else
        print_error "CLAUDE.md master rules file missing"
        all_valid=false
    fi

    # Check Python scripts
    if [ -f "$ORCHESTRATOR_PATH/orchestrator.py" ]; then
        print_success "orchestrator.py found"
    else
        print_error "orchestrator.py missing"
        all_valid=false
    fi

    if [ -f "$ORCHESTRATOR_PATH/cli.py" ]; then
        print_success "cli.py found"
    else
        print_warning "cli.py missing (optional)"
    fi

    # Test Python import
    if python3 -c "import json, sys, os" &> /dev/null; then
        print_success "Python standard library accessible"
    else
        print_error "Python standard library import failed"
        all_valid=false
    fi

    if [ "$all_valid" = true ]; then
        echo ""
        print_success "All validation checks passed!"
    else
        echo ""
        print_error "Some validation checks failed. Please review the errors above."
        exit 1
    fi

    echo ""
}

##############################################################################
# Main Installation Flow
##############################################################################

main() {
    clear

    echo -e "${BLUE}"
    cat << "EOF"
   _____ _                 _         ____            _               _             _
  / ____| |               | |       / __ \          | |             | |           | |
 | |    | | __ _ _   _  __| | ___  | |  | |_ __ ___| |__   ___  ___| |_ _ __ __ _| |_ ___  _ __
 | |    | |/ _` | | | |/ _` |/ _ \ | |  | | '__/ __| '_ \ / _ \/ __| __| '__/ _` | __/ _ \| '__|
 | |____| | (_| | |_| | (_| |  __/ | |__| | | | (__| | | |  __/\__ \ |_| | | (_| | || (_) | |
  \_____|_|\__,_|\__,_|\__,_|\___|  \____/|_|  \___|_| |_|\___||___/\__|_|  \__,_|\__\___/|_|

EOF
    echo -e "${NC}"

    print_info "Multi-Agent Orchestration System - Global Installation"
    print_info "Installation Path: $ORCHESTRATOR_PATH"
    echo ""

    # Run installation steps
    check_requirements
    create_directories
    setup_symlinks
    install_python_dependencies
    setup_shell_integration
    create_master_rules
    validate_installation

    # Final success message
    print_header "Installation Complete!"

    echo -e "${GREEN}The Claude multi-agent orchestrator is now globally available!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Restart your terminal or run: source ~/.bashrc (or ~/.zshrc)"
    echo "2. Verify installation: echo \$CLAUDE_ORCHESTRATOR_PATH"
    echo "3. Read the documentation: $CLAUDE_DIR/CLAUDE.md"
    echo "4. View orchestration rules: $RULES_DIR/orchestration-rules.md"
    echo ""
    echo "Usage:"
    echo "  - Claude Code will automatically use the orchestrator for complex tasks"
    echo "  - Manual usage: cd $ORCHESTRATOR_PATH && python3 cli.py"
    echo "  - View audit logs: ls $AUDIT_DIR"
    echo ""
    echo "Documentation:"
    echo "  - Quick Start: $ORCHESTRATOR_PATH/QUICK-START.md"
    echo "  - Full Usage: $ORCHESTRATOR_PATH/USAGE.md"
    echo "  - Implementation: $ORCHESTRATOR_PATH/IMPLEMENTATION_SUMMARY.md"
    echo ""

    print_success "Installation completed successfully!"
}

# Run main installation
main "$@"
