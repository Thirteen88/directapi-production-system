"""
Worktree Manager - Handles git worktree creation and management
"""
import subprocess
import os
from pathlib import Path
from typing import List, Dict, Optional
import shutil


class WorktreeManager:
    """Manages git worktrees for parallel Claude sessions"""

    def __init__(self, repo_path: str, base_dir: Optional[str] = None):
        """
        Initialize WorktreeManager

        Args:
            repo_path: Path to the git repository
            base_dir: Base directory for worktrees (default: repo_path/../worktrees)
        """
        self.repo_path = Path(repo_path).resolve()
        self.base_dir = Path(base_dir) if base_dir else self.repo_path.parent / "worktrees"
        self.worktrees: Dict[str, Path] = {}

        if not self._is_git_repo():
            raise ValueError(f"{self.repo_path} is not a git repository")

    def _is_git_repo(self) -> bool:
        """Check if the path is a git repository"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def create_worktree(self, name: str, branch: Optional[str] = None, base_branch: str = "main") -> Path:
        """
        Create a new worktree

        Args:
            name: Name for the worktree (used for directory and branch)
            branch: Branch name (default: use name)
            base_branch: Base branch to branch from (default: main)

        Returns:
            Path to the created worktree
        """
        if branch is None:
            branch = f"task/{name}"

        worktree_path = self.base_dir / name

        # Create base directory if it doesn't exist
        self.base_dir.mkdir(parents=True, exist_ok=True)

        # Remove existing worktree if it exists
        if worktree_path.exists():
            self.remove_worktree(name)

        # Create the worktree
        try:
            subprocess.run(
                ["git", "worktree", "add", "-b", branch, str(worktree_path), base_branch],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            # If branch already exists, try without -b flag
            try:
                subprocess.run(
                    ["git", "worktree", "add", str(worktree_path), branch],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    check=True
                )
            except subprocess.CalledProcessError as e2:
                raise RuntimeError(f"Failed to create worktree: {e2.stderr}")

        self.worktrees[name] = worktree_path
        return worktree_path

    def list_worktrees(self) -> List[Dict[str, str]]:
        """
        List all worktrees

        Returns:
            List of worktree info dictionaries
        """
        result = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=True
        )

        worktrees = []
        current = {}

        for line in result.stdout.strip().split("\n"):
            if line.startswith("worktree "):
                if current:
                    worktrees.append(current)
                current = {"path": line.split(" ", 1)[1]}
            elif line.startswith("branch "):
                current["branch"] = line.split(" ", 1)[1]
            elif line.startswith("HEAD "):
                current["head"] = line.split(" ", 1)[1]

        if current:
            worktrees.append(current)

        return worktrees

    def remove_worktree(self, name: str, force: bool = True) -> None:
        """
        Remove a worktree

        Args:
            name: Name of the worktree to remove
            force: Force removal even with uncommitted changes
        """
        worktree_path = self.worktrees.get(name) or self.base_dir / name

        if not worktree_path.exists():
            return

        cmd = ["git", "worktree", "remove"]
        if force:
            cmd.append("--force")
        cmd.append(str(worktree_path))

        try:
            subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            # If git worktree remove fails, try manual cleanup
            if worktree_path.exists():
                shutil.rmtree(worktree_path)

        if name in self.worktrees:
            del self.worktrees[name]

    def cleanup_all(self) -> None:
        """Remove all managed worktrees"""
        for name in list(self.worktrees.keys()):
            self.remove_worktree(name)

    def get_worktree_path(self, name: str) -> Optional[Path]:
        """Get the path to a worktree by name"""
        return self.worktrees.get(name)
