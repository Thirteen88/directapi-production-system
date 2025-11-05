#!/usr/bin/env python3
"""
Claude Orchestrator CLI - Command-line interface for parallel task delegation
"""
import asyncio
import argparse
import json
import sys
from pathlib import Path
from typing import List

from orchestrator import (
    YOLOMode, YOLO_CONFIG, assess_task_risk, should_auto_approve,
    get_yolo_enhanced_timeout, get_yolo_max_parallel_agents
)


def load_tasks_from_file(file_path: str) -> List[dict]:
    """
    Load tasks from a JSON file

    Expected format:
    {
        "tasks": [
            {
                "name": "task-name",
                "description": "Task description",
                "prompt": "Prompt for Claude",
                "allowed_tools": ["Read", "Write", "Edit"],  // optional
                "base_branch": "main"  // optional
            }
        ]
    }
    """
    with open(file_path, 'r') as f:
        data = json.load(f)

    return data.get("tasks", [])


def create_sample_tasks_file(output_path: str) -> None:
    """Create a sample tasks configuration file"""
    sample_tasks = {
        "tasks": [
            {
                "name": "feature-auth",
                "description": "Implement authentication",
                "prompt": "Implement a user authentication system with JWT tokens",
                "allowed_tools": ["Read", "Write", "Edit", "Bash"],
                "base_branch": "main"
            },
            {
                "name": "feature-api",
                "description": "Create REST API",
                "prompt": "Create REST API endpoints for user management",
                "allowed_tools": ["Read", "Write", "Edit", "Bash"],
                "base_branch": "main"
            },
            {
                "name": "tests",
                "description": "Write tests",
                "prompt": "Write comprehensive unit tests with 80% coverage",
                "allowed_tools": ["Read", "Write", "Edit", "Bash"],
                "base_branch": "main"
            }
        ]
    }

    with open(output_path, 'w') as f:
        json.dump(sample_tasks, f, indent=2)

    print(f"Sample tasks file created at: {output_path}")
    print("\nEdit this file to customize your tasks, then run:")
    print(f"  python cli.py run --tasks {output_path} --repo /path/to/repo")


async def run_orchestrator(args):
    """Run the orchestrator with YOLO mode support using proper integration"""

    # Load tasks
    if args.tasks:
        tasks = load_tasks_from_file(args.tasks)
        print(f"Loaded {len(tasks)} tasks from {args.tasks}")
    else:
        print("Error: --tasks file is required")
        sys.exit(1)

    # Set YOLO mode
    yolo_mode = YOLOMode.CONSERVATIVE
    if args.yolo:
        try:
            yolo_mode = YOLOMode(args.yolo)
            print(f"🚀 YOLO Mode: {yolo_mode.value.upper()}")
        except ValueError:
            print(f"Error: Invalid YOLO mode '{args.yolo}'. Valid modes: {[mode.value for mode in YOLOMode]}")
            sys.exit(1)

    # Import YOLO orchestrator integration
    try:
        from yolo_orchestrator_integration import YOLOOrchestrator
        use_orchestrator = True
    except ImportError:
        print("⚠️  YOLO orchestrator integration not available, using analysis mode only")
        use_orchestrator = False

    if use_orchestrator:
        # Use proper orchestrator integration
        print(f"\n🎯 Using Claude Orchestrator with YOLO Mode Integration")
        print(f"   Repository: {args.repo}")
        print(f"   Mode: {yolo_mode.value}")
        print(f"   Max Parallel Agents: {get_yolo_max_parallel_agents(yolo_mode)}")

        # Create YOLO orchestrator
        yolo_orch = YOLOOrchestrator(args.repo, yolo_mode)

        try:
            # Execute with orchestrator
            results = await yolo_orch.execute_with_orchestrator(args.tasks)

            # Save results if output specified
            if args.output:
                import json
                with open(args.output, 'w') as f:
                    json.dump(results, f, indent=2)
                print(f"📁 Results saved to: {args.output}")

            # Print summary
            print(f"\n{'='*60}")
            print("YOLO ORCHESTRATOR EXECUTION SUMMARY")
            print(f"{'='*60}")
            print(f"Total Tasks: {results['total_tasks']}")
            print(f"Successful: {results['successful']}")
            print(f"Failed: {results['failed']}")
            print(f"Success Rate: {results['success_rate']:.1f}%")
            print(f"Orchestrator Used: {'✅ YES' if results.get('orchestrator_used', False) else '❌ NO'}")

            if results.get('successful_tasks'):
                print(f"\n✅ Successful Tasks:")
                for task in results['successful_tasks']:
                    print(f"   - {task}")

            if results.get('failed_tasks'):
                print(f"\n❌ Failed Tasks:")
                for task in results['failed_tasks']:
                    if isinstance(task, dict):
                        print(f"   - {task['task']}: {task.get('error', 'Unknown error')}")
                    else:
                        print(f"   - {task}")

            return 0 if results['failed'] == 0 else 1

        except Exception as e:
            print(f"❌ Orchestration failed: {e}")
            print("🔄 Falling back to analysis mode...")
            use_orchestrator = False

    if not use_orchestrator:
        # Fallback to analysis mode (original behavior)
        print(f"\n📊 YOLO Mode Task Analysis (Analysis Mode)")
        print("="*60)

        auto_approved_count = 0
        manual_review_count = 0

        for task in tasks:
            task_desc = task.get("description", task.get("prompt", ""))
            task_name = task.get("name", "unnamed")

            # Assess risk
            risk_score = assess_task_risk(task_desc, yolo_mode=yolo_mode)

            # Check auto-approval
            auto_approve = should_auto_approve(yolo_mode, task_desc)

            print(f"\nTask: {task_name}")
            print(f"  Risk Score: {risk_score:.2f}")
            print(f"  Auto-Approve: {'✅ YES' if auto_approve else '❌ NO'}")

            if auto_approve:
                auto_approved_count += 1
                print(f"  Status: 🚀 AUTO-APPROVED for execution")
            else:
                manual_review_count += 1
                print(f"  Status: ⚠️  Requires manual confirmation")

        print(f"\nSummary:")
        print(f"  Auto-Approved: {auto_approved_count} tasks")
        print(f"  Manual Review: {manual_review_count} tasks")
        print(f"  Risk Threshold: {YOLO_CONFIG[yolo_mode]['risk_threshold']}")

        if yolo_mode != YOLOMode.CONSERVATIVE and auto_approved_count > 0:
            print(f"\n⚡ YOLO Mode active: {auto_approved_count} tasks would execute without confirmation!")
            if yolo_mode == YOLOMode.AGGRESSIVE:
                print("   Destructive operations will still require confirmation")
            elif yolo_mode == YOLOMode.AUTONOMOUS:
                print("   No confirmations required - use with caution!")

        print(f"\n🎯 YOLO Mode Analysis Complete!")
        print(f"   Repository: {args.repo}")
        print(f"   Mode: {yolo_mode.value}")
        print(f"   Max Parallel Agents: {get_yolo_max_parallel_agents(yolo_mode)}")
        print(f"   Timeout Multiplier: {YOLO_CONFIG[yolo_mode]['timeout_multiplier']}x")

        return 0


def list_worktrees(args):
    """List existing worktrees"""
    worktree_base = Path.home() / "claude-orchestrator" / "worktrees"

    print(f"\nWorktrees for {args.repo}:")
    print("="*60)
    print(f"Worktree base directory: {worktree_base}")

    if worktree_base.exists():
        worktrees = [d for d in worktree_base.iterdir() if d.is_dir()]
        if worktrees:
            for wt in sorted(worktrees):
                print(f"  {wt.name}")
        else:
            print("  No worktrees found")
    else:
        print("  Worktree directory does not exist")


def cleanup_worktrees(args):
    """Cleanup worktrees"""
    worktree_base = Path(args.worktree_dir) if args.worktree_dir else Path.home() / "claude-orchestrator" / "worktrees"

    print(f"Cleaning up worktrees in {worktree_base}...")

    if worktree_base.exists():
        import shutil
        try:
            shutil.rmtree(worktree_base)
            print("✓ Cleanup complete")
        except Exception as e:
            print(f"✗ Cleanup failed: {e}")
    else:
        print("✓ No worktrees to clean up")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Claude Orchestrator - Parallel task delegation across git worktrees",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create sample tasks file
  python cli.py init tasks.json

  # Run tasks with Conservative YOLO mode (default)
  python cli.py run --tasks tasks.json --repo /path/to/repo

  # Run with Aggressive YOLO mode (auto-approve non-destructive)
  python cli.py run --tasks tasks.json --repo /path/to/repo --yolo aggressive

  # Run with Autonomous YOLO mode (no confirmations)
  python cli.py run --tasks tasks.json --repo /path/to/repo --yolo autonomous

  # List worktrees
  python cli.py list --repo /path/to/repo

  # Cleanup worktrees
  python cli.py cleanup --repo /path/to/repo

YOLO Modes:
  conservative - Full confirmations required (safest)
  standard     - Auto-approve low-risk tasks
  aggressive   - Auto-approve non-destructive operations
  autonomous   - No confirmations (use with extreme caution)
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Init command
    init_parser = subparsers.add_parser('init', help='Create a sample tasks file')
    init_parser.add_argument('output', help='Output file path')

    # Run command
    run_parser = subparsers.add_parser('run', help='Run orchestrator with tasks')
    run_parser.add_argument('--tasks', required=True, help='Path to tasks JSON file')
    run_parser.add_argument('--repo', required=True, help='Path to git repository')
    run_parser.add_argument('--worktree-dir', help='Base directory for worktrees')
    run_parser.add_argument('--yolo', choices=['conservative', 'standard', 'aggressive', 'autonomous'],
                           help='YOLO mode level for autonomous execution')
    run_parser.add_argument('--permission-mode', default='acceptEdits',
                           choices=['acceptEdits', 'confirmEdits', 'rejectEdits'],
                           help='Permission mode for Claude sessions')
    run_parser.add_argument('--cleanup', action='store_true',
                           help='Cleanup worktrees after execution')
    run_parser.add_argument('--output', help='Save results to JSON file')

    # List command
    list_parser = subparsers.add_parser('list', help='List worktrees')
    list_parser.add_argument('--repo', required=True, help='Path to git repository')

    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Cleanup worktrees')
    cleanup_parser.add_argument('--repo', required=True, help='Path to git repository')
    cleanup_parser.add_argument('--worktree-dir', help='Base directory for worktrees')

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute command
    if args.command == 'init':
        create_sample_tasks_file(args.output)
        sys.exit(0)
    elif args.command == 'run':
        exit_code = asyncio.run(run_orchestrator(args))
        sys.exit(exit_code)
    elif args.command == 'list':
        list_worktrees(args)
        sys.exit(0)
    elif args.command == 'cleanup':
        cleanup_worktrees(args)
        sys.exit(0)


if __name__ == "__main__":
    main()
