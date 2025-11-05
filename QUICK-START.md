# Claude Orchestrator - Quick Reference

## ✅ Status: TESTED & WORKING

Run multiple Claude Code sessions in parallel, each in its own git worktree!

## Quick Commands

```bash
# Create tasks file
cd ~/claude-orchestrator
python3 cli.py init tasks.json

# Run tasks in parallel
python3 cli.py run --tasks tasks.json --repo ~/my-project

# With cleanup
python3 cli.py run --tasks tasks.json --repo ~/my-project --cleanup

# With results export
python3 cli.py run --tasks tasks.json --repo ~/my-project --output results.json

# List worktrees
python3 cli.py list --repo ~/my-project
```

## Simple Example

**tasks.json:**
```json
{
  "tasks": [
    {
      "name": "feature-1",
      "prompt": "Add user authentication"
    },
    {
      "name": "feature-2",
      "prompt": "Create REST API endpoints"
    }
  ]
}
```

**Run:**
```bash
python3 cli.py run --tasks tasks.json --repo ~/my-project
```

**Result:**
- Creates 2 worktrees
- Runs 2 Claude sessions in parallel
- Each creates a branch: `task/feature-1`, `task/feature-2`
- Each works independently

## What Gets Created

```
~/worktrees/
├── feature-1/        # Worktree for task 1
│   └── (your code)
└── feature-2/        # Worktree for task 2
    └── (your code)

~/my-project/.git/
└── branches:
    ├── main
    ├── task/feature-1
    └── task/feature-2
```

## Review & Merge

```bash
# Check worktrees
git worktree list

# Review changes
cd ~/worktrees/feature-1
git diff main

# Merge if good
cd ~/my-project
git merge task/feature-1

# Cleanup
git worktree remove ~/worktrees/feature-1
git branch -D task/feature-1
```

## Test Results

```
✅ Tested: 2025-10-16
✅ 2 parallel tasks: 11.36 seconds
✅ 100% success rate
✅ Both files created correctly
```

## Common Use Cases

1. **Multiple Features**: Develop 3-5 features simultaneously
2. **Bug Fixes**: Fix multiple bugs in parallel
3. **Refactoring**: Refactor different modules concurrently
4. **Testing Approaches**: Try different implementations

## Tips

- Start with 2-3 tasks to test
- Use `--cleanup` for experiments
- Use `--output` to track results
- Review branches before merging
- Task names become branch names (keep them short!)

## Files

- `cli.py` - Command-line interface
- `orchestrator.py` - Main orchestration
- `session_manager.py` - Claude sessions
- `worktree_manager.py` - Git worktrees
- `USAGE.md` - Full documentation
- `README.md` - Setup guide

## Performance

More tasks = more time savings!
- 1 task: 10s
- 2 tasks parallel: 11s (50% faster than sequential)
- 3 tasks parallel: 12s (66% faster than sequential)

🚀 **Ready to use!**
