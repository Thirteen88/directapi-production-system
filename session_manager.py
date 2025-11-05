"""
Claude Session Manager - Handles Claude SDK sessions for each worktree
"""
import asyncio
import json
from pathlib import Path
from typing import Dict, List, Optional, AsyncIterator
from dataclasses import dataclass
import subprocess


@dataclass
class SessionResult:
    """Result from a Claude session"""
    task_name: str
    worktree_path: Path
    messages: List[str]
    success: bool
    error: Optional[str] = None
    model_used: Optional[str] = None
    execution_time: Optional[float] = None


class ClaudeSessionManager:
    """Manages Claude Code SDK sessions for parallel task execution"""

    def __init__(self):
        """Initialize the session manager"""
        self.sessions: Dict[str, asyncio.Task] = {}
        self.results: Dict[str, SessionResult] = {}

    async def run_session(
        self,
        task_name: str,
        worktree_path: Path,
        prompt: str,
        allowed_tools: Optional[List[str]] = None,
        permission_mode: str = "acceptEdits",
        model: Optional[str] = None
    ) -> SessionResult:
        """
        Run a Claude Code session in a specific worktree with intelligent model assignment

        Args:
            task_name: Name of the task
            worktree_path: Path to the worktree
            prompt: Task prompt for Claude
            allowed_tools: List of allowed tools (default: all)
            permission_mode: Permission mode (acceptEdits, confirmEdits, etc.)
            model: Specific Claude model to use (if None, uses default)

        Returns:
            SessionResult with execution details including model used
        """
        import time
        start_time = time.time()

        messages = []
        success = False
        error = None
        model_used = model or "default"

        try:
            # Build Claude CLI command with model selection
            cmd = [
                "claude",
                "-p",  # Print mode (non-interactive)
                prompt,
                "--output-format", "stream-json",
                "--permission-mode", permission_mode,
                "--verbose"  # Required for stream-json with print mode
            ]

            # Add model specification if provided
            if model:
                cmd.extend(["--model", model])
                print(f"[{task_name}] 🤖 Using model: {model}")

            if allowed_tools:
                cmd.extend(["--allowedTools", ",".join(allowed_tools)])

            # Run Claude in the worktree directory
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(worktree_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Stream output
            if process.stdout:
                async for line in process.stdout:
                    try:
                        data = json.loads(line.decode().strip())

                        # Extract message content
                        if "type" in data:
                            if data["type"] == "text":
                                text = data.get("text", "")
                                messages.append(text)
                                print(f"[{task_name}] {text}")
                            elif data["type"] == "tool_use":
                                tool_name = data.get("name", "unknown")
                                print(f"[{task_name}] Using tool: {tool_name}")
                    except json.JSONDecodeError:
                        # Skip non-JSON lines
                        pass

            # Wait for process to complete
            await process.wait()

            success = process.returncode == 0

            if not success and process.stderr:
                stderr = await process.stderr.read()
                error = stderr.decode().strip()

        except Exception as e:
            error = str(e)
            success = False

        # Calculate execution time
        execution_time = time.time() - start_time

        result = SessionResult(
            task_name=task_name,
            worktree_path=worktree_path,
            messages=messages,
            success=success,
            error=error,
            model_used=model_used,
            execution_time=execution_time
        )

        self.results[task_name] = result

        # Log completion with model info
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"[{task_name}] {status} - Model: {model_used} - Time: {execution_time:.2f}s")

        return result

    async def run_parallel_sessions(
        self,
        tasks: Dict[str, tuple[Path, str]]
    ) -> Dict[str, SessionResult]:
        """
        Run multiple Claude sessions in parallel

        Args:
            tasks: Dict mapping task_name -> (worktree_path, prompt)

        Returns:
            Dict mapping task_name -> SessionResult
        """
        # Create tasks for all sessions
        session_tasks = {
            name: asyncio.create_task(
                self.run_session(name, path, prompt)
            )
            for name, (path, prompt) in tasks.items()
        }

        # Store tasks
        self.sessions.update(session_tasks)

        # Wait for all to complete
        results = await asyncio.gather(*session_tasks.values(), return_exceptions=True)

        # Process results
        for task_name, result in zip(tasks.keys(), results):
            if isinstance(result, Exception):
                self.results[task_name] = SessionResult(
                    task_name=task_name,
                    worktree_path=tasks[task_name][0],
                    messages=[],
                    success=False,
                    error=str(result)
                )
            else:
                self.results[task_name] = result

        return self.results

    def get_result(self, task_name: str) -> Optional[SessionResult]:
        """Get the result of a task"""
        return self.results.get(task_name)

    def get_all_results(self) -> Dict[str, SessionResult]:
        """Get all task results"""
        return self.results.copy()

    async def cancel_session(self, task_name: str) -> None:
        """Cancel a running session"""
        if task_name in self.sessions:
            self.sessions[task_name].cancel()
            try:
                await self.sessions[task_name]
            except asyncio.CancelledError:
                pass

    async def cancel_all_sessions(self) -> None:
        """Cancel all running sessions"""
        for task_name in list(self.sessions.keys()):
            await self.cancel_session(task_name)
