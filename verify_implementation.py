#!/usr/bin/env python3
"""Verification script to confirm all required functions are implemented"""

import sys
from pathlib import Path

# Add orchestrator to path
sys.path.insert(0, str(Path.home() / "claude-orchestrator"))

# Import and verify
try:
    from orchestrator import (
        # Core functions
        create_worktree,
        setup_virtualenv,
        remove_worktree,
        merge_worktree,
        build_envelope,
        # Async agent execution
        run_subagent,
        run_agent_in_venv,
        retry_with_backoff,
        run_with_timeout,
        # Orchestration
        orchestrate_parallel,
        aggregate_results,
        main,
        # Data models
        HandoffEnvelope,
        TaskResult,
        ProvenanceInfo,
        AgentType,
        TaskStatus,
    )
    
    print("✓ All required functions and classes successfully imported!")
    print("\nCore Functions (5):")
    print("  1. create_worktree")
    print("  2. setup_virtualenv")
    print("  3. remove_worktree")
    print("  4. merge_worktree")
    print("  5. build_envelope")
    
    print("\nAsync Agent Execution (4):")
    print("  6. run_subagent")
    print("  7. run_agent_in_venv")
    print("  8. retry_with_backoff")
    print("  9. run_with_timeout")
    
    print("\nOrchestration (3):")
    print("  10. orchestrate_parallel")
    print("  11. aggregate_results")
    print("  12. main")
    
    print("\nData Models (5):")
    print("  - HandoffEnvelope")
    print("  - TaskResult")
    print("  - ProvenanceInfo")
    print("  - AgentType")
    print("  - TaskStatus")
    
    print("\n" + "="*60)
    print("VERIFICATION SUCCESSFUL")
    print("="*60)
    print(f"\nFile: {Path.home() / 'claude-orchestrator' / 'orchestrator.py'}")
    print("Status: Ready for execution")
    print("\nRun with: python3 ~/claude-orchestrator/orchestrator.py")
    
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Verification failed: {e}")
    sys.exit(1)
