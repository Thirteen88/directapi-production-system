# Claude Multi-Agent Orchestrator - Global Installation

This document describes how the orchestrator system has been configured for global availability across all Claude Code sessions.

## Installation Status

The orchestrator has been configured to be automatically available in every Claude Code session through:

1. **Global Rules**: Master rules file at `~/.claude/CLAUDE.md`
2. **Orchestration Rules**: Symlinked to `~/.claude/rules/orchestration-rules.md`
3. **Shell Integration**: Environment variables in `~/.bashrc` and `~/.zshrc`
4. **Automated Installation**: Installation script at `~/claude-orchestrator/install.sh`

## Files Created

### 1. ~/.claude/CLAUDE.md
**Purpose**: Master rules file that Claude Code reads on every session

**Content**:
- Auto-import of orchestration rules
- Delegation triggers (when to use orchestrator)
- Token budget management guidelines
- Delegation decision matrix
- Sub-agent prompt protocol reference
- Audit trail requirements
- Quick reference for decomposition strategies

**Location**: `/home/gary/.claude/CLAUDE.md`

### 2. ~/.claude/rules/orchestration-rules.md
**Purpose**: Symlink to the complete orchestration protocol

**Content**: Points to `/home/gary/claude-orchestrator/CLAUDE_ORCHESTRATION.md`

**Includes**:
- Complete orchestration protocol (39KB, 1274 lines)
- Task decomposition strategies
- Sub-agent prompt templates
- Context management rules
- Conflict resolution strategies
- Reproducibility requirements
- Safety and compliance guidelines
- Detailed examples and best practices

### 3. Shell Configuration
**Purpose**: Make orchestrator globally available via environment variables

**Files Modified**:
- `~/.bashrc` (for Bash users)
- `~/.zshrc` (for Zsh users)

**Environment Variables Added**:
```bash
export CLAUDE_ORCHESTRATOR_PATH="/home/gary/claude-orchestrator"
export PATH="$CLAUDE_ORCHESTRATOR_PATH/bin:$PATH"  # if bin/ exists
```

### 4. Installation Script
**Purpose**: Automated installation and validation

**Location**: `/home/gary/claude-orchestrator/install.sh`

**Features**:
- Pre-flight requirements check (Python 3, pip3, git)
- Directory structure creation
- Symlink management
- Python dependency installation
- Shell integration setup
- Installation validation
- User-friendly output with color coding

## How It Works

### Automatic Integration

1. **Claude Code Startup**: When Claude Code starts, it reads `~/.claude/CLAUDE.md`
2. **Rules Loading**: The master rules file imports orchestration-rules.md via symlink
3. **Delegation Triggers**: Claude Code automatically detects when to use the orchestrator:
   - File count > 10
   - Multiple modules/packages
   - 3+ parallelizable sub-tasks
   - Token forecast > 80,000
   - Time estimate > 15 minutes

### Manual Usage

You can also invoke the orchestrator manually:

```bash
# CLI interface
cd /home/gary/claude-orchestrator
python3 cli.py --task "your task description"

# Python API
cd /home/gary/claude-orchestrator
python3 orchestrator.py

# From anywhere (after shell integration)
cd $CLAUDE_ORCHESTRATOR_PATH
python3 cli.py
```

## Installation Instructions

### First-Time Installation

Run the installation script:

```bash
cd /home/gary/claude-orchestrator
./install.sh
```

The script will:
1. Check system requirements (Python 3, pip3)
2. Create necessary directories (~/.claude, ~/.claude/rules, audit-logs)
3. Set up symlinks to orchestration rules
4. Install Python dependencies from requirements.txt
5. Add environment variables to shell configuration
6. Validate the installation

### After Installation

1. **Restart your terminal** or reload shell configuration:
   ```bash
   source ~/.bashrc  # for Bash
   # or
   source ~/.zshrc   # for Zsh
   ```

2. **Verify installation**:
   ```bash
   echo $CLAUDE_ORCHESTRATOR_PATH
   # Should output: /home/gary/claude-orchestrator
   ```

3. **Test the orchestrator**:
   ```bash
   cd $CLAUDE_ORCHESTRATOR_PATH
   python3 cli.py --help
   ```

## Directory Structure

```
/home/gary/
├── .claude/
│   ├── CLAUDE.md                           # Master rules file
│   └── rules/
│       └── orchestration-rules.md          # Symlink to CLAUDE_ORCHESTRATION.md
│
└── claude-orchestrator/
    ├── CLAUDE_ORCHESTRATION.md             # Complete orchestration protocol
    ├── orchestrator.py                     # Main orchestrator logic
    ├── cli.py                              # Command-line interface
    ├── requirements.txt                    # Python dependencies
    ├── install.sh                          # Installation script
    ├── INSTALL_GLOBAL.md                   # This file
    ├── README.md                           # Project README
    ├── QUICK-START.md                      # Quick start guide
    ├── USAGE.md                            # Usage documentation
    ├── IMPLEMENTATION_SUMMARY.md           # Implementation details
    ├── audit-logs/                         # Orchestration audit trails
    ├── worktrees/                          # Git worktrees for sub-agents
    ├── sub_agent_prompts/                  # Prompt templates
    └── schemas/                            # JSON schemas
```

## Environment Variables

After installation, these variables are available in every shell session:

```bash
CLAUDE_ORCHESTRATOR_PATH=/home/gary/claude-orchestrator
```

The orchestrator path is added to PATH if `bin/` directory exists.

## Orchestration Workflow

When Claude Code detects a complex task:

1. **Analyze Complexity**: Check if delegation triggers apply
2. **Present Plan**: Show decomposition strategy to user
3. **Get Approval**: Wait for user confirmation
4. **Spawn Sub-Agents**: Execute sub-agents with structured prompts
5. **Aggregate Results**: Collect and merge outputs
6. **Resolve Conflicts**: Handle overlapping changes
7. **Deliver Output**: Provide comprehensive report with audit trail

## Delegation Decision Matrix

| Task Complexity | File Count | Module Count | Decision |
|-----------------|------------|--------------|----------|
| Low | 1-3 | 1 | Direct execution (no delegation) |
| Medium | 4-10 | 1-2 | Optional delegation (efficiency gain) |
| High | 11-30 | 3-5 | **Recommended delegation** |
| Very High | 31+ | 6+ | **Required delegation** |

## Token Budget

**Total Available**: 200,000 tokens (Claude Sonnet 4.5)

**Allocation**:
- Orchestrator overhead: 20,000 tokens (10%)
- Sub-agent pool: 160,000 tokens (80%)
- Safety buffer: 20,000 tokens (10%)

**Limits**:
- Maximum 12 concurrent sub-agents
- Minimum 10,000 tokens per sub-agent
- Context pruning when orchestrator exceeds 15,000 tokens

## Decomposition Strategies

### 1. File-Based Decomposition
- **When**: Independent operations on multiple files
- **Method**: One sub-agent per file or small file group (3-5 files)
- **Example**: "Update imports across 20 components" → 4 sub-agents (5 files each)

### 2. Module-Based Decomposition
- **When**: Task spans architectural boundaries
- **Method**: One sub-agent per module/package
- **Example**: "Add error handling to backend, frontend, shared utils" → 3 sub-agents

### 3. Phase-Based Decomposition
- **When**: Sequential dependencies but parallelizable phases
- **Method**: One sub-agent per phase, orchestrator chains outputs
- **Example**: "Analyze → Generate plan → Implement" → 3 sequential sub-agents

### 4. Pattern-Based Decomposition
- **When**: Same operation to multiple patterns
- **Method**: One sub-agent per pattern type
- **Example**: "Migrate all class components to hooks" → 1 sub-agent per component pattern

## Audit Trails

Every orchestration creates an audit log:

**Location**: `~/claude-orchestrator/audit-logs/{orchestration_id}.json`

**Contents**:
- Orchestration ID (UUID)
- Start and end timestamps
- User request (verbatim)
- Codebase state (git commit or checksums)
- Delegation plan and strategy
- All sub-agent prompts and outputs
- Conflicts and errors
- Total tokens consumed
- Total execution time

**Retention**: Permanent (user manages cleanup)

## Troubleshooting

### Environment Variables Not Set

If `$CLAUDE_ORCHESTRATOR_PATH` is not set after installation:

```bash
# Reload shell configuration
source ~/.bashrc  # or ~/.zshrc

# Or manually export
export CLAUDE_ORCHESTRATOR_PATH="/home/gary/claude-orchestrator"
```

### Symlink Issues

If orchestration rules are not found:

```bash
# Recreate symlink
ln -sf /home/gary/claude-orchestrator/CLAUDE_ORCHESTRATION.md \
       /home/gary/.claude/rules/orchestration-rules.md
```

### Python Dependencies Missing

If Python imports fail:

```bash
# Reinstall dependencies
cd /home/gary/claude-orchestrator
pip3 install --user -r requirements.txt
```

### Permission Issues

If installation fails due to permissions:

```bash
# Make install script executable
chmod +x /home/gary/claude-orchestrator/install.sh

# Ensure directories are writable
chmod -R u+w /home/gary/.claude
chmod -R u+w /home/gary/claude-orchestrator
```

## Uninstallation

To remove the global installation:

```bash
# Remove master rules
rm /home/gary/.claude/CLAUDE.md

# Remove symlink
rm /home/gary/.claude/rules/orchestration-rules.md

# Remove shell configuration
# Edit ~/.bashrc and ~/.zshrc, remove the "Claude Orchestrator Configuration" section

# Optional: Remove orchestrator directory
# rm -rf /home/gary/claude-orchestrator
```

## Additional Resources

- **Full Orchestration Protocol**: `/home/gary/.claude/rules/orchestration-rules.md`
- **Quick Start Guide**: `/home/gary/claude-orchestrator/QUICK-START.md`
- **Usage Documentation**: `/home/gary/claude-orchestrator/USAGE.md`
- **Implementation Summary**: `/home/gary/claude-orchestrator/IMPLEMENTATION_SUMMARY.md`
- **Quick Reference**: `/home/gary/claude-orchestrator/QUICK_REFERENCE.md`

## Support

For issues or questions:
1. Check the documentation in `/home/gary/claude-orchestrator/`
2. Review audit logs in `/home/gary/claude-orchestrator/audit-logs/`
3. Verify installation with `./install.sh` (safe to re-run)

## Version

- **Installation Version**: 1.0.0
- **Created**: 2025-10-23
- **Orchestration Rules Version**: 1.0.0 (see CLAUDE_ORCHESTRATION.md)

## Changelog

### 1.0.0 (2025-10-23)
- Initial global installation setup
- Created master rules file (~/.claude/CLAUDE.md)
- Set up orchestration rules symlink
- Added shell integration (.bashrc, .zshrc)
- Created automated installation script
- Configured environment variables
- Documented installation process
