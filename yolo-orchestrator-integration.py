#!/usr/bin/env python3
"""
YOLO Mode Integration with Claude Orchestrator

This module bridges the YOLO executor with the existing orchestrator system,
creating proper HandoffEnvelope tasks for autonomous execution.
"""

import json
import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

from orchestrator import (
    YOLOMode, YOLO_CONFIG, assess_task_risk, should_auto_approve,
    HandoffEnvelope, AgentType, orchestrate_parallel, build_envelope,
    get_yolo_max_parallel_agents, get_yolo_enhanced_timeout
)
# Import YOLO executor from current directory
import importlib.util
spec = importlib.util.spec_from_file_location("yolo_executor", "yolo-executor.py")
yolo_executor_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(yolo_executor_module)
YOLOExecutor = yolo_executor_module.YOLOExecutor


class YOLOOrchestrator:
    """
    Integrates YOLO mode with the existing Claude orchestrator system
    """

    def __init__(self, repo_path: str, yolo_mode: YOLOMode = YOLOMode.AGGRESSIVE):
        self.repo_path = Path(repo_path)
        self.yolo_mode = yolo_mode
        self.executor = YOLOExecutor(str(repo_path))

    def create_yolo_envelopes(self, tasks_file: str) -> List[HandoffEnvelope]:
        """
        Convert YOLO tasks to proper HandoffEnvelope format for orchestrator

        Args:
            tasks_file: Path to tasks JSON file

        Returns:
            List of HandoffEnvelope objects ready for orchestration
        """
        with open(tasks_file, 'r') as f:
            tasks_data = json.load(f)

        envelopes = []

        for idx, task in enumerate(tasks_data.get("tasks", [])):
            task_name = task.get("name", f"task_{idx}")
            task_desc = task.get("description", "")
            task_prompt = task.get("prompt", "")

            # Assess risk for YOLO mode
            risk_score = assess_task_risk(task_desc, yolo_mode=self.yolo_mode)
            auto_approve = should_auto_approve(self.yolo_mode, task_desc)

            # Determine timeout based on YOLO mode
            base_timeout = 300  # 5 minutes base
            timeout = get_yolo_enhanced_timeout(base_timeout, self.yolo_mode)

            # Create specialized YOLO agent type
            if "documentation" in task_name.lower():
                agent_type = AgentType.DOCUMENTER
            elif "package" in task_name.lower():
                agent_type = AgentType.CUSTOM  # Package management
            elif "error" in task_name.lower():
                agent_type = AgentType.DEBUGGER
            elif "format" in task_name.lower():
                agent_type = AgentType.CUSTOM  # Code formatting
            else:
                agent_type = AgentType.REFACTORER

            envelope = build_envelope(
                agent_name=f"yolo_{task_name}_{idx}",
                task_name=task_name,
                inputs={
                    "task_description": task_desc,
                    "task_prompt": task_prompt,
                    "repo_path": str(self.repo_path),
                    "yolo_mode": self.yolo_mode.value,
                    "risk_score": risk_score,
                    "auto_approve": auto_approve,
                    "allowed_tools": task.get("allowed_tools", ["Read", "Write", "Edit"]),
                    "priority": task.get("priority", "medium"),
                    "task_complexity": self._assess_task_complexity(task_desc)
                },
                agent_type=agent_type,
                expected_outputs=["modified_files", "execution_log", "task_results", "model_used"],
                timeout_seconds=timeout,
                constraints={
                    "yolo_mode": self.yolo_mode.value,
                    "auto_approve": auto_approve,
                    "risk_threshold": YOLO_CONFIG[self.yolo_mode]["risk_threshold"],
                    "use_best_model": True,
                    "model_selection_strategy": "intelligent"
                }
            )

            envelopes.append(envelope)

            print(f"🎯 YOLO Task {idx+1}: {task_name}")
            print(f"   Risk Score: {risk_score:.2f}")
            print(f"   Auto-Approve: {'✅ YES' if auto_approve else '❌ NO'}")
            print(f"   Agent Type: {agent_type.value}")
            print(f"   Timeout: {timeout}s")
            print()

        return envelopes

    async def execute_with_orchestrator(self, tasks_file: str) -> Dict[str, Any]:
        """
        Execute YOLO tasks using the proper orchestrator system

        Args:
            tasks_file: Path to tasks JSON file

        Returns:
            Execution results with orchestrator integration
        """
        print("🚀 YOLO MODE WITH CLAUDE ORCHESTRATOR")
        print("=" * 60)
        print(f"Repository: {self.repo_path}")
        print(f"YOLO Mode: {self.yolo_mode.value.upper()}")
        print(f"Max Parallel Agents: {get_yolo_max_parallel_agents(self.yolo_mode)}")
        print()

        # Create orchestrator envelopes
        envelopes = self.create_yolo_envelopes(tasks_file)

        print(f"📋 Created {len(envelopes)} task envelopes for orchestration")
        print()

        # Determine requirements based on tasks
        requirements = []
        if any("format" in str(e.inputs.get("task_description", "")).lower() for e in envelopes):
            requirements.append("prettier")
        if any("package" in str(e.inputs.get("task_description", "")).lower() for e in envelopes):
            requirements.append("npm")

        # Execute with orchestrator
        try:
            print("🔄 Starting parallel orchestration...")
            results = await orchestrate_parallel(envelopes, requirements)

            # Process results
            successful_tasks = []
            failed_tasks = []

            for i, result in enumerate(results):
                task_name = envelopes[i].task_description  # Fix: HandoffEnvelope uses task_description, not task_name
                if result.status.value == "completed":
                    successful_tasks.append(task_name)
                else:
                    failed_tasks.append({
                        "task": task_name,
                        "error": result.error_message,
                        "status": result.status.value
                    })

            execution_summary = {
                "total_tasks": len(envelopes),
                "successful": len(successful_tasks),
                "failed": len(failed_tasks),
                "success_rate": (len(successful_tasks) / len(envelopes)) * 100,
                "yolo_mode": self.yolo_mode.value,
                "orchestrator_used": True,
                "successful_tasks": successful_tasks,
                "failed_tasks": failed_tasks,
                "execution_details": {
                    "max_parallel_agents": get_yolo_max_parallel_agents(self.yolo_mode),
                    "timeout_multiplier": YOLO_CONFIG[self.yolo_mode]["timeout_multiplier"],
                    "risk_threshold": YOLO_CONFIG[self.yolo_mode]["risk_threshold"]
                }
            }

            return execution_summary

        except Exception as e:
            return {
                "error": f"Orchestration failed: {str(e)}",
                "yolo_mode": self.yolo_mode.value,
                "total_tasks": len(envelopes),
                "successful": 0,
                "failed": len(envelopes),
                "orchestrator_used": True
            }

    def execute_fallback(self, tasks_file: str) -> Dict[str, Any]:
        """
        Fallback execution using direct YOLO executor if orchestrator fails

        Args:
            tasks_file: Path to tasks JSON file

        Returns:
            Direct execution results
        """
        print("⚠️  Using fallback direct execution...")

        with open(tasks_file, 'r') as f:
            tasks_data = json.load(f)

        results = self.executor.execute_all_tasks(tasks_data.get("tasks", []))

        return {
            **results,
            "yolo_mode": self.yolo_mode.value,
            "orchestrator_used": False,
            "execution_method": "direct_fallback"
        }

    def _assess_task_complexity(self, task_description: str) -> str:
        """
        Assess task complexity for model selection

        Args:
            task_description: Description of the task

        Returns:
            Complexity level: simple, moderate, or complex
        """
        from orchestrator import analyze_task_complexity
        return analyze_task_complexity(task_description)


async def main():
    """Main execution function with orchestrator integration"""
    import argparse

    parser = argparse.ArgumentParser(description="YOLO Orchestrator Integration")
    parser.add_argument("--repo", required=True, help="Repository path")
    parser.add_argument("--tasks", required=True, help="Tasks JSON file")
    parser.add_argument("--yolo", choices=["conservative", "standard", "aggressive", "autonomous"],
                       default="aggressive", help="YOLO mode")
    parser.add_argument("--output", help="Output file for results")
    parser.add_argument("--fallback", action="store_true", help="Use direct execution if orchestrator fails")

    args = parser.parse_args()

    # Convert string to YOLOMode enum
    yolo_mode = YOLOMode(args.yolo)

    # Create YOLO orchestrator
    yolo_orchestrator = YOLOOrchestrator(args.repo, yolo_mode)

    print("🎯 YOLO ORCHESTRATOR INTEGRATION")
    print("=" * 60)

    try:
        # Try orchestrator first
        results = await yolo_orchestrator.execute_with_orchestrator(args.tasks)

        # Fallback to direct execution if orchestrator fails and fallback is enabled
        if not results.get("orchestrator_used", True) and args.fallback:
            print("🔄 Orchestrator failed, trying direct execution...")
            results = yolo_orchestrator.execute_fallback(args.tasks)

    except Exception as e:
        print(f"❌ Execution failed: {e}")
        if args.fallback:
            print("🔄 Trying direct execution fallback...")
            results = yolo_orchestrator.execute_fallback(args.tasks)
        else:
            results = {
                "error": str(e),
                "yolo_mode": args.yolo,
                "total_tasks": 0,
                "successful": 0,
                "failed": 0,
                "orchestrator_used": False
            }

    # Save results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n📁 Results saved to: {args.output}")

    # Print summary
    print(f"\n{'='*60}")
    print("YOLO ORCHESTRATOR EXECUTION SUMMARY")
    print(f"{'='*60}")
    print(f"YOLO Mode: {results.get('yolo_mode', 'unknown').upper()}")
    print(f"Total Tasks: {results.get('total_tasks', 0)}")
    print(f"Successful: {results.get('successful', 0)}")
    print(f"Failed: {results.get('failed', 0)}")
    print(f"Success Rate: {results.get('success_rate', 0):.1f}%")
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

    print(f"{'='*60}")

    return 0 if results.get('failed', 0) == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))