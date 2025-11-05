#!/usr/bin/env python3
"""
Claude Orchestrator - Async Multi-Agent Task Delegation System

This orchestrator manages parallel execution of AI agents in isolated git worktrees
with independent virtual environments. Each agent receives tasks via HandoffEnvelope
format and operates in complete isolation for reproducibility and auditability.

Key Features:
- Async parallel execution with asyncio.gather
- Git worktree isolation per agent
- Independent virtualenv per worktree
- Retry logic with exponential backoff + jitter
- Timeout controls for all operations
- Complete provenance tracking (hashes, timestamps)
- Comprehensive audit logging
- Automatic cleanup on success/failure
"""

import asyncio
import hashlib
import json
import logging
import os
import random
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union


# ============================================================================
# Configuration and Constants
# ============================================================================

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('orchestrator_audit.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Retry configuration
DEFAULT_RETRIES = 3
DEFAULT_BASE_DELAY = 1.0
DEFAULT_MAX_DELAY = 60.0
DEFAULT_JITTER_RANGE = 0.1

# Timeout configuration (seconds)
DEFAULT_COMMAND_TIMEOUT = 300
DEFAULT_AGENT_TIMEOUT = 1800
DEFAULT_OPERATION_TIMEOUT = 60

# Paths
WORKTREE_BASE_DIR = Path.home() / "claude-orchestrator" / "worktrees"
MAIN_REPO_DIR = Path.home() / "claude-orchestrator" / "main-repo"

# YOLO Mode Configuration will be defined after YOLOMode enum below

# Risk assessment patterns
DESTRUCTIVE_PATTERNS = [
    "delete", "remove", "drop", "truncate", "format", "destroy", "wipe",
    "rm -rf", "del ", "clear", "reset", "clean", "purge", "erase"
]

PRODUCTION_PATTERNS = [
    "prod", "production", "main", "master", "release", "deploy"
]

HIGH_RISK_FILE_PATTERNS = [
    "database", "db", "config", "credentials", "secrets", "keys",
    "backup", "migration", "schema"
]


# ============================================================================
# Data Models
# ============================================================================

class TaskStatus(Enum):
    """Status of task execution"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    RETRYING = "retrying"


class AgentType(Enum):
    """Types of agents that can be orchestrated"""
    CODE_GENERATOR = "code_generator"
    CODE_REVIEWER = "code_reviewer"
    TESTER = "tester"
    DOCUMENTER = "documenter"
    DEBUGGER = "debugger"
    REFACTORER = "refactorer"
    CUSTOM = "custom"


class YOLOMode(Enum):
    """YOLO mode levels for autonomous execution"""
    CONSERVATIVE = "conservative"  # Current behavior - full confirmations
    STANDARD = "standard"         # Reduced confirmations for low-risk tasks
    AGGRESSIVE = "aggressive"     # Auto-approve non-destructive operations
    AUTONOMOUS = "autonomous"     # No confirmations (use with extreme caution)


# Claude Model Assignment Configuration - ALWAYS USE BEST MODELS
BEST_MODEL_CONFIG = {
    # Task Complexity Models
    "complexity": {
        "simple": {
            "model": "claude-3-5-sonnet-20241022",  # Fast, capable for routine tasks
            "description": "Fast and efficient for straightforward tasks"
        },
        "moderate": {
            "model": "claude-3-5-sonnet-20241022",  # Balanced performance
            "description": "Good balance of speed and capability"
        },
        "complex": {
            "model": "claude-3-5-sonnet-20241022",  # High capability
            "description": "Maximum capability for complex tasks"
        }
    },

    # Task Type Specialization
    "task_types": {
        "documentation": {
            "model": "claude-3-5-sonnet-20241022",
            "description": "Excellent for documentation and explanations"
        },
        "code_generation": {
            "model": "claude-3-5-sonnet-20241022",
            "description": "Superior code generation and architecture"
        },
        "debugging": {
            "model": "claude-3-5-sonnet-20241022",
            "description": "Exceptional analytical and debugging capabilities"
        },
        "refactoring": {
            "model": "claude-3-5-sonnet-20241022",
            "description": "Best for complex code transformations"
        },
        "testing": {
            "model": "claude-3-5-sonnet-20241022",
            "description": "Comprehensive test generation and analysis"
        },
        "security": {
            "model": "claude-3-5-sonnet-20241022",
            "description": "Maximum security analysis and vulnerability detection"
        },
        "performance": {
            "model": "claude-3-5-sonnet-20241022",
            "description": "Best for performance optimization and analysis"
        },
        "architecture": {
            "model": "claude-3-5-sonnet-20241022",
            "description": "Superior system design and architecture"
        },
        "integration": {
            "model": "claude-3-5-sonnet-20241022",
            "description": "Best for complex system integration"
        }
    },

    # Agent Type Specialization
    "agent_types": {
        AgentType.CODE_GENERATOR: {
            "model": "claude-3-5-sonnet-20241022",
            "description": "Optimal for code generation tasks"
        },
        AgentType.CODE_REVIEWER: {
            "model": "claude-3-5-sonnet-20241022",
            "description": "Best for detailed code analysis and review"
        },
        AgentType.TESTER: {
            "model": "claude-3-5-sonnet-20241022",
            "description": "Comprehensive testing and quality assurance"
        },
        AgentType.DOCUMENTER: {
            "model": "claude-3-5-sonnet-20241022",
            "description": "Excellent documentation generation"
        },
        AgentType.DEBUGGER: {
            "model": "claude-3-5-sonnet-20241022",
            "description": "Superior debugging and problem-solving"
        },
        AgentType.REFACTORER: {
            "model": "claude-3-5-sonnet-20241022",
            "description": "Best for complex refactoring operations"
        },
        AgentType.CUSTOM: {
            "model": "claude-3-5-sonnet-20241022",
            "description": "Default high-performance model"
        }
    },

    # Priority-Based Assignment
    "priority": {
        "high": {
            "model": "claude-3-5-sonnet-20241022",
            "description": "Maximum capability for high-priority tasks"
        },
        "medium": {
            "model": "claude-3-5-sonnet-20241022",
            "description": "High performance for important tasks"
        },
        "low": {
            "model": "claude-3-5-sonnet-20241022",
            "description": "Quality results even for lower priority tasks"
        }
    },

    # Domain-Specific Models
    "domains": {
        "security": "claude-3-5-sonnet-20241022",
        "performance": "claude-3-5-sonnet-20241022",
        "architecture": "claude-3-5-sonnet-20241022",
        "documentation": "claude-3-5-sonnet-20241022",
        "testing": "claude-3-5-sonnet-20241022",
        "integration": "claude-3-5-sonnet-20241022",
        "optimization": "claude-3-5-sonnet-20241022"
    }
}

# YOLO Mode Configuration (defined after YOLOMode enum)
YOLO_CONFIG = {
    YOLOMode.CONSERVATIVE: {
        "auto_approve": False,
        "risk_threshold": 0.0,
        "require_confirmation_for": ["all"],
        "max_parallel_agents": 8,
        "timeout_multiplier": 1.0,
        "retry_limit": 3
    },
    YOLOMode.STANDARD: {
        "auto_approve": True,
        "risk_threshold": 0.3,
        "require_confirmation_for": ["destructive", "production"],
        "max_parallel_agents": 10,
        "timeout_multiplier": 1.2,
        "retry_limit": 2
    },
    YOLOMode.AGGRESSIVE: {
        "auto_approve": True,
        "risk_threshold": 0.7,
        "require_confirmation_for": ["destructive"],
        "max_parallel_agents": 15,
        "timeout_multiplier": 1.5,
        "retry_limit": 1
    },
    YOLOMode.AUTONOMOUS: {
        "auto_approve": True,
        "risk_threshold": 1.0,
        "require_confirmation_for": [],
        "max_parallel_agents": 20,
        "timeout_multiplier": 2.0,
        "retry_limit": 1
    }
}


@dataclass
class ProvenanceInfo:
    """Provenance tracking information"""
    task_id: str
    agent_name: str
    branch_name: str
    started_at: str
    completed_at: Optional[str] = None
    input_hash: Optional[str] = None
    output_hash: Optional[str] = None
    command_history: List[str] = field(default_factory=list)
    retry_count: int = 0
    worktree_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)


@dataclass
class HandoffEnvelope:
    """
    Standard envelope format for agent handoff
    Ensures consistent task delegation and result collection
    """
    task_id: str
    agent_name: str
    agent_type: AgentType
    task_description: str
    inputs: Dict[str, Any]
    context: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    expected_outputs: List[str] = field(default_factory=list)
    timeout_seconds: int = DEFAULT_AGENT_TIMEOUT
    retry_config: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['agent_type'] = self.agent_type.value
        return data

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HandoffEnvelope':
        """Create envelope from dictionary"""
        data['agent_type'] = AgentType(data['agent_type'])
        return cls(**data)


@dataclass
class TaskResult:
    """Result from agent task execution"""
    task_id: str
    agent_name: str
    status: TaskStatus
    outputs: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    provenance: Optional[ProvenanceInfo] = None
    execution_time_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['status'] = self.status.value
        if self.provenance:
            data['provenance'] = self.provenance.to_dict()
        return data


# ============================================================================
# Core Utility Functions
# ============================================================================

def compute_hash(data: Union[str, bytes, Dict]) -> str:
    """
    Compute SHA-256 hash of data for provenance tracking

    Args:
        data: String, bytes, or dict to hash

    Returns:
        Hex digest of SHA-256 hash
    """
    if isinstance(data, dict):
        data = json.dumps(data, sort_keys=True)
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.sha256(data).hexdigest()


def get_timestamp() -> str:
    """Get current ISO 8601 timestamp"""
    return datetime.utcnow().isoformat() + 'Z'


async def run_command(
    cmd: List[str],
    cwd: Optional[Path] = None,
    timeout: int = DEFAULT_COMMAND_TIMEOUT,
    env: Optional[Dict[str, str]] = None,
    capture_output: bool = True
) -> subprocess.CompletedProcess:
    """
    Run shell command asynchronously with timeout

    Args:
        cmd: Command and arguments as list
        cwd: Working directory
        timeout: Timeout in seconds
        env: Environment variables
        capture_output: Whether to capture stdout/stderr

    Returns:
        CompletedProcess instance

    Raises:
        asyncio.TimeoutError: If command times out
        subprocess.CalledProcessError: If command fails
    """
    logger.debug(f"Running command: {' '.join(cmd)}")

    process = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=cwd,
        env=env,
        stdout=asyncio.subprocess.PIPE if capture_output else None,
        stderr=asyncio.subprocess.PIPE if capture_output else None
    )

    try:
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout
        )

        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            logger.error(f"Command failed: {' '.join(cmd)}\nError: {error_msg}")
            raise subprocess.CalledProcessError(
                process.returncode,
                cmd,
                stdout,
                stderr
            )

        return subprocess.CompletedProcess(
            cmd,
            process.returncode,
            stdout,
            stderr
        )

    except asyncio.TimeoutError:
        logger.error(f"Command timeout after {timeout}s: {' '.join(cmd)}")
        process.kill()
        await process.wait()
        raise


# ============================================================================
# Retry Logic
# ============================================================================

T = TypeVar('T')


async def retry_with_backoff(
    func: Callable[..., T],
    *args,
    retries: int = DEFAULT_RETRIES,
    base_delay: float = DEFAULT_BASE_DELAY,
    max_delay: float = DEFAULT_MAX_DELAY,
    jitter_range: float = DEFAULT_JITTER_RANGE,
    **kwargs
) -> T:
    """
    Retry async function with exponential backoff and jitter

    Args:
        func: Async function to retry
        *args: Positional arguments for func
        retries: Maximum number of retries
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        jitter_range: Random jitter factor (0.0 to 1.0)
        **kwargs: Keyword arguments for func

    Returns:
        Result from successful function call

    Raises:
        Last exception if all retries exhausted
    """
    last_exception = None

    for attempt in range(retries + 1):
        try:
            logger.debug(f"Attempt {attempt + 1}/{retries + 1} for {func.__name__}")
            return await func(*args, **kwargs)

        except Exception as e:
            last_exception = e

            if attempt == retries:
                logger.error(
                    f"All {retries + 1} attempts failed for {func.__name__}: {e}"
                )
                raise

            # Calculate delay with exponential backoff
            delay = min(base_delay * (2 ** attempt), max_delay)

            # Add jitter to prevent thundering herd
            jitter = delay * jitter_range * (2 * random.random() - 1)
            total_delay = delay + jitter

            logger.warning(
                f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                f"Retrying in {total_delay:.2f}s..."
            )

            await asyncio.sleep(total_delay)

    raise last_exception


async def run_with_timeout(
    coro,
    timeout_sec: int,
    operation_name: str = "operation"
) -> Any:
    """
    Execute coroutine with timeout control

    Args:
        coro: Coroutine to execute
        timeout_sec: Timeout in seconds
        operation_name: Name for logging

    Returns:
        Result from coroutine

    Raises:
        asyncio.TimeoutError: If operation times out
    """
    try:
        logger.debug(f"Starting {operation_name} with {timeout_sec}s timeout")
        result = await asyncio.wait_for(coro, timeout=timeout_sec)
        logger.debug(f"Completed {operation_name}")
        return result

    except asyncio.TimeoutError:
        logger.error(f"Timeout after {timeout_sec}s for {operation_name}")
        raise


# ============================================================================
# YOLO Mode Risk Assessment
# ============================================================================

def assess_task_risk(
    task_description: str,
    files_to_modify: Optional[List[str]] = None,
    yolo_mode: YOLOMode = YOLOMode.CONSERVATIVE
) -> float:
    """
    Calculate risk score 0.0-1.0 for YOLO mode decisions

    Args:
        task_description: Description of the task to be performed
        files_to_modify: List of files that will be modified
        yolo_mode: Current YOLO mode setting

    Returns:
        Risk score between 0.0 (low risk) and 1.0 (high risk)
    """
    risk = 0.0
    task_lower = task_description.lower()

    # 1. Destructive pattern analysis (30% weight)
    destructive_risk = 0.0
    for pattern in DESTRUCTIVE_PATTERNS:
        if pattern in task_lower:
            destructive_risk += 0.1

    # Check for file deletion commands
    if any(cmd in task_lower for cmd in ["rm -rf", "delete file", "remove file"]):
        destructive_risk += 0.2

    risk += min(destructive_risk * 0.3, 0.3)

    # 2. Production system risk (25% weight)
    production_risk = 0.0
    for pattern in PRODUCTION_PATTERNS:
        if pattern in task_lower:
            production_risk += 0.15
    risk += min(production_risk * 0.25, 0.25)

    # 3. File-based risk (20% weight)
    if files_to_modify:
        file_risk = 0.0

        # High number of files
        if len(files_to_modify) > 100:
            file_risk += 0.3
        elif len(files_to_modify) > 50:
            file_risk += 0.2
        elif len(files_to_modify) > 20:
            file_risk += 0.1

        # High-risk file patterns
        for file_path in files_to_modify:
            file_lower = str(file_path).lower()
            for pattern in HIGH_RISK_FILE_PATTERNS:
                if pattern in file_lower:
                    file_risk += 0.05
                    break

        risk += min(file_risk * 0.2, 0.2)

    # 4. Task complexity risk (15% weight)
    complexity_keywords = ["refactor", "rewrite", "migrate", "architecture", "schema"]
    complexity_count = sum(1 for keyword in complexity_keywords if keyword in task_lower)
    risk += min(complexity_count * 0.05 * 0.15, 0.15)

    # 5. Scope risk (10% weight)
    scope_indicators = ["all", "entire", "whole", "complete", "full"]
    scope_count = sum(1 for indicator in scope_indicators if indicator in task_lower)
    risk += min(scope_count * 0.03 * 0.1, 0.1)

    return min(risk, 1.0)


def analyze_task_complexity(task_description: str, files_to_modify: Optional[List[str]] = None) -> str:
    """
    Analyze task complexity to determine the best model assignment

    Args:
        task_description: Description of the task
        files_to_modify: List of files to be modified

    Returns:
        Complexity level: "simple", "moderate", or "complex"
    """
    task_lower = task_description.lower()
    complexity_score = 0

    # Analyze task description complexity
    complexity_indicators = {
        "simple": ["add", "update", "fix", "format", "document", "test"],
        "moderate": ["refactor", "optimize", "improve", "enhance", "modify"],
        "complex": ["rewrite", "migrate", "architecture", "integration", "system"]
    }

    # Score based on complexity indicators
    for level, indicators in complexity_indicators.items():
        for indicator in indicators:
            if indicator in task_lower:
                if level == "simple":
                    complexity_score += 1
                elif level == "moderate":
                    complexity_score += 2
                else:  # complex
                    complexity_score += 3

    # Analyze file count complexity
    if files_to_modify:
        if len(files_to_modify) > 50:
            complexity_score += 3
        elif len(files_to_modify) > 10:
            complexity_score += 2
        elif len(files_to_modify) > 3:
            complexity_score += 1

    # Determine complexity level
    if complexity_score >= 5:
        return "complex"
    elif complexity_score >= 2:
        return "moderate"
    else:
        return "simple"


def determine_task_type(task_description: str, agent_type: AgentType) -> str:
    """
    Determine the primary task type for specialized model assignment

    Args:
        task_description: Description of the task
        agent_type: Type of agent performing the task

    Returns:
        Task type for model selection
    """
    task_lower = task_description.lower()

    # Priority-based task type detection
    task_type_patterns = {
        "security": ["security", "vulnerability", "auth", "encrypt", "secure", "audit"],
        "performance": ["performance", "optimize", "speed", "memory", "cache", "efficiency"],
        "architecture": ["architecture", "design", "structure", "system", "framework"],
        "documentation": ["document", "readme", "guide", "manual", "wiki", "comment"],
        "testing": ["test", "spec", "coverage", "unit", "integration", "e2e"],
        "debugging": ["debug", "fix", "error", "issue", "problem", "troubleshoot"],
        "integration": ["integrate", "connect", "api", "interface", "bridge", "link"],
        "code_generation": ["generate", "create", "build", "implement", "develop"],
        "refactoring": ["refactor", "clean", "organize", "restructure", "improve"]
    }

    # Check for task type patterns
    for task_type, patterns in task_type_patterns.items():
        for pattern in patterns:
            if pattern in task_lower:
                return task_type

    # Fallback to agent type
    agent_type_mapping = {
        AgentType.CODE_GENERATOR: "code_generation",
        AgentType.CODE_REVIEWER: "debugging",
        AgentType.TESTER: "testing",
        AgentType.DOCUMENTER: "documentation",
        AgentType.DEBUGGER: "debugging",
        AgentType.REFACTORER: "refactoring",
        AgentType.CUSTOM: "code_generation"
    }

    return agent_type_mapping.get(agent_type, "code_generation")


def extract_priority(task_description: str, inputs: Dict[str, Any]) -> str:
    """
    Extract task priority from description and inputs

    Args:
        task_description: Description of the task
        inputs: Task inputs and metadata

    Returns:
        Priority level: "high", "medium", or "low"
    """
    task_lower = task_description.lower()

    # Check for explicit priority indicators
    high_priority_patterns = ["urgent", "critical", "important", "security", "production"]
    medium_priority_patterns = ["enhance", "improve", "optimize", "update"]

    if any(pattern in task_lower for pattern in high_priority_patterns):
        return "high"
    elif any(pattern in task_lower for pattern in medium_priority_patterns):
        return "medium"
    else:
        return "medium"  # Default to medium for better results


def select_best_model(
    task_description: str,
    agent_type: AgentType,
    inputs: Dict[str, Any],
    files_to_modify: Optional[List[str]] = None,
    yolo_mode: YOLOMode = YOLOMode.AGGRESSIVE
) -> Dict[str, Any]:
    """
    Select the BEST Claude model for the task using intelligent assignment

    Args:
        task_description: Description of the task
        agent_type: Type of agent performing the task
        inputs: Task inputs and metadata
        files_to_modify: List of files to be modified
        yolo_mode: Current YOLO mode

    Returns:
        Dictionary containing selected model and reasoning
    """
    # Analyze task characteristics
    complexity = analyze_task_complexity(task_description, files_to_modify)
    task_type = determine_task_type(task_description, agent_type)
    priority = extract_priority(task_description, inputs)

    # Model selection priority order:
    # 1. Task type specialization (most important)
    # 2. Agent type specialization
    # 3. Priority-based assignment
    # 4. Complexity-based assignment (fallback)

    selected_model = None
    selection_reason = []

    # 1. Try task type specialization first
    if task_type in BEST_MODEL_CONFIG["task_types"]:
        selected_model = BEST_MODEL_CONFIG["task_types"][task_type]["model"]
        selection_reason.append(f"Task type specialization: {task_type}")

    # 2. Try agent type specialization
    if not selected_model and agent_type in BEST_MODEL_CONFIG["agent_types"]:
        selected_model = BEST_MODEL_CONFIG["agent_types"][agent_type]["model"]
        selection_reason.append(f"Agent type specialization: {agent_type.value}")

    # 3. Try priority-based assignment
    if not selected_model:
        selected_model = BEST_MODEL_CONFIG["priority"][priority]["model"]
        selection_reason.append(f"Priority-based assignment: {priority}")

    # 4. Fallback to complexity-based assignment
    if not selected_model:
        selected_model = BEST_MODEL_CONFIG["complexity"][complexity]["model"]
        selection_reason.append(f"Complexity-based assignment: {complexity}")

    # YOLO mode enhancement - always use best models
    if yolo_mode in [YOLOMode.AGGRESSIVE, YOLOMode.AUTONOMOUS]:
        # In aggressive/autonomous modes, always prefer the most capable model
        # Use Sonnet 4.5 via Perplexity app automation (no API key needed)
        if "sonnet-4-5" not in selected_model:
            selected_model = "claude-sonnet-4-5-20250929"  # Sonnet 4.5 via Perplexity app automation
            selection_reason.append("YOLO mode enhancement: using Sonnet 4.5 via Perplexity app automation")
        elif "sonnet" not in selected_model:
            selected_model = "claude-3-5-sonnet-20241022"
            selection_reason.append("YOLO mode enhancement: using most capable model")

    return {
        "model": selected_model,
        "reasoning": selection_reason,
        "task_analysis": {
            "complexity": complexity,
            "task_type": task_type,
            "priority": priority,
            "agent_type": agent_type.value
        }
    }


def is_destructive_operation(task_description: str, files_to_modify: Optional[List[str]] = None) -> bool:
    """
    Determine if an operation is potentially destructive

    Args:
        task_description: Description of the task
        files_to_modify: List of files to be modified

    Returns:
        True if operation is potentially destructive
    """
    task_lower = task_description.lower()

    # Check for destructive patterns
    for pattern in DESTRUCTIVE_PATTERNS:
        if pattern in task_lower:
            return True

    # Check for file deletion patterns
    destructive_file_patterns = ["rm -rf", "delete file", "remove file", "clean all"]
    for pattern in destructive_file_patterns:
        if pattern in task_lower:
            return True

    # Check files for destructive operations
    if files_to_modify:
        for file_path in files_to_modify:
            file_lower = str(file_path).lower()
            if any(pattern in file_lower for pattern in ["delete", "remove", "drop"]):
                return True

    return False


def is_production_operation(task_description: str, files_to_modify: Optional[List[str]] = None) -> bool:
    """
    Determine if an operation affects production systems

    Args:
        task_description: Description of the task
        files_to_modify: List of files to be modified

    Returns:
        True if operation affects production
    """
    task_lower = task_description.lower()

    # Check for production patterns
    for pattern in PRODUCTION_PATTERNS:
        if pattern in task_lower:
            return True

    # Check files for production indicators
    if files_to_modify:
        for file_path in files_to_modify:
            file_lower = str(file_path).lower()
            if any(pattern in file_lower for pattern in PRODUCTION_PATTERNS):
                return True

    return False


def should_auto_approve(
    yolo_mode: YOLOMode,
    task_description: str,
    files_to_modify: Optional[List[str]] = None
) -> bool:
    """
    Determine if a task should be auto-approved based on YOLO mode and risk assessment

    Args:
        yolo_mode: Current YOLO mode
        task_description: Description of the task
        files_to_modify: List of files to be modified

    Returns:
        True if task should be auto-approved
    """
    config = YOLO_CONFIG[yolo_mode]

    # Conservative mode never auto-approves
    if not config["auto_approve"]:
        return False

    # Calculate risk score
    risk_score = assess_task_risk(task_description, files_to_modify, yolo_mode)

    # Check if risk is within threshold
    if risk_score > config["risk_threshold"]:
        return False

    # Check confirmation requirements
    confirmation_required = config["require_confirmation_for"]

    if "all" in confirmation_required:
        return False

    if "destructive" in confirmation_required and is_destructive_operation(task_description, files_to_modify):
        return False

    if "production" in confirmation_required and is_production_operation(task_description, files_to_modify):
        return False

    return True


def get_yolo_enhanced_timeout(base_timeout: int, yolo_mode: YOLOMode) -> int:
    """
    Get timeout adjusted for YOLO mode

    Args:
        base_timeout: Base timeout in seconds
        yolo_mode: Current YOLO mode

    Returns:
        Adjusted timeout in seconds
    """
    multiplier = YOLO_CONFIG[yolo_mode]["timeout_multiplier"]
    return int(base_timeout * multiplier)


def get_yolo_max_parallel_agents(yolo_mode: YOLOMode) -> int:
    """
    Get maximum parallel agents for YOLO mode

    Args:
        yolo_mode: Current YOLO mode

    Returns:
        Maximum number of parallel agents
    """
    return YOLO_CONFIG[yolo_mode]["max_parallel_agents"]


def get_yolo_retry_limit(yolo_mode: YOLOMode) -> int:
    """
    Get retry limit for YOLO mode

    Args:
        yolo_mode: Current YOLO mode

    Returns:
        Retry limit
    """
    return YOLO_CONFIG[yolo_mode]["retry_limit"]


# ============================================================================
# Git Worktree Management
# ============================================================================

async def create_worktree(
    branch_name: str,
    base_repo: Path = MAIN_REPO_DIR,
    worktree_base: Path = WORKTREE_BASE_DIR
) -> Path:
    """
    Create isolated git worktree for agent execution

    Args:
        branch_name: Name of branch to create
        base_repo: Path to main repository
        worktree_base: Base directory for worktrees

    Returns:
        Path to created worktree

    Raises:
        RuntimeError: If worktree creation fails
    """
    logger.info(f"Creating worktree for branch: {branch_name}")

    # Ensure base directories exist
    worktree_base.mkdir(parents=True, exist_ok=True)

    # Initialize main repo if it doesn't exist
    if not base_repo.exists():
        logger.info(f"Initializing main repository at {base_repo}")
        base_repo.mkdir(parents=True, exist_ok=True)
        await run_command(['git', 'init'], cwd=base_repo)
        await run_command(
            ['git', 'config', 'user.email', 'orchestrator@example.com'],
            cwd=base_repo
        )
        await run_command(
            ['git', 'config', 'user.name', 'Claude Orchestrator'],
            cwd=base_repo
        )

        # Create initial commit
        readme_path = base_repo / "README.md"
        readme_path.write_text("# Claude Orchestrator Repository\n")
        await run_command(['git', 'add', 'README.md'], cwd=base_repo)
        await run_command(
            ['git', 'commit', '-m', 'Initial commit'],
            cwd=base_repo
        )

    # Create worktree path
    worktree_path = worktree_base / branch_name

    # Remove existing worktree if present
    if worktree_path.exists():
        logger.warning(f"Removing existing worktree at {worktree_path}")
        await remove_worktree(branch_name, base_repo, worktree_base)

    try:
        # Create new branch and worktree
        await run_command(
            ['git', 'worktree', 'add', '-b', branch_name, str(worktree_path)],
            cwd=base_repo
        )
        logger.info(f"Created worktree at {worktree_path}")
        return worktree_path

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create worktree: {e}")
        raise RuntimeError(f"Worktree creation failed: {e}")


async def remove_worktree(
    branch_name: str,
    base_repo: Path = MAIN_REPO_DIR,
    worktree_base: Path = WORKTREE_BASE_DIR
) -> None:
    """
    Remove git worktree and associated branch

    Args:
        branch_name: Name of branch/worktree to remove
        base_repo: Path to main repository
        worktree_base: Base directory for worktrees
    """
    logger.info(f"Removing worktree for branch: {branch_name}")

    worktree_path = worktree_base / branch_name

    try:
        # Remove worktree
        if worktree_path.exists():
            await run_command(
                ['git', 'worktree', 'remove', '--force', str(worktree_path)],
                cwd=base_repo
            )
            logger.debug(f"Removed worktree at {worktree_path}")

        # Delete branch
        try:
            await run_command(
                ['git', 'branch', '-D', branch_name],
                cwd=base_repo
            )
            logger.debug(f"Deleted branch {branch_name}")
        except subprocess.CalledProcessError:
            logger.debug(f"Branch {branch_name} already deleted or doesn't exist")

    except subprocess.CalledProcessError as e:
        logger.warning(f"Error during worktree removal: {e}")
        # Force cleanup of directory
        if worktree_path.exists():
            shutil.rmtree(worktree_path, ignore_errors=True)


async def merge_worktree(
    branch_name: str,
    base_repo: Path = MAIN_REPO_DIR,
    target_branch: str = "main"
) -> bool:
    """
    Merge completed branch into target branch

    Args:
        branch_name: Branch to merge
        base_repo: Path to main repository
        target_branch: Target branch for merge (default: main)

    Returns:
        True if merge successful, False otherwise
    """
    logger.info(f"Merging branch {branch_name} into {target_branch}")

    try:
        # Checkout target branch
        await run_command(['git', 'checkout', target_branch], cwd=base_repo)

        # Merge branch
        await run_command(
            ['git', 'merge', '--no-ff', branch_name, '-m',
             f'Merge agent work from {branch_name}'],
            cwd=base_repo
        )

        logger.info(f"Successfully merged {branch_name} into {target_branch}")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Merge failed: {e}")
        # Abort merge on failure
        try:
            await run_command(['git', 'merge', '--abort'], cwd=base_repo)
        except:
            pass
        return False


# ============================================================================
# Virtual Environment Management
# ============================================================================

async def setup_virtualenv(
    wt_path: Path,
    requirements: Optional[List[str]] = None
) -> Path:
    """
    Setup virtual environment and install dependencies

    Args:
        wt_path: Path to worktree
        requirements: List of pip packages to install

    Returns:
        Path to virtualenv directory

    Raises:
        RuntimeError: If venv setup fails
    """
    logger.info(f"Setting up virtualenv in {wt_path}")

    venv_path = wt_path / ".venv"

    try:
        # Create virtualenv
        await run_command(
            [sys.executable, '-m', 'venv', str(venv_path)],
            cwd=wt_path
        )
        logger.debug(f"Created virtualenv at {venv_path}")

        # Upgrade pip
        pip_path = venv_path / "bin" / "pip"
        await run_command(
            [str(pip_path), 'install', '--upgrade', 'pip'],
            cwd=wt_path
        )

        # Install requirements
        if requirements:
            logger.info(f"Installing {len(requirements)} packages")
            await run_command(
                [str(pip_path), 'install'] + requirements,
                cwd=wt_path,
                timeout=600  # Allow more time for package installation
            )

        # Check for requirements.txt
        req_file = wt_path / "requirements.txt"
        if req_file.exists():
            logger.info("Installing from requirements.txt")
            await run_command(
                [str(pip_path), 'install', '-r', 'requirements.txt'],
                cwd=wt_path,
                timeout=600
            )

        logger.info("Virtualenv setup complete")
        return venv_path

    except subprocess.CalledProcessError as e:
        logger.error(f"Virtualenv setup failed: {e}")
        raise RuntimeError(f"Failed to setup virtualenv: {e}")


async def run_agent_in_venv(
    wt_path: Path,
    command: List[str],
    timeout: int = DEFAULT_AGENT_TIMEOUT
) -> subprocess.CompletedProcess:
    """
    Run command inside virtualenv

    Args:
        wt_path: Path to worktree containing .venv
        command: Command to execute (will be prefixed with venv python)
        timeout: Timeout in seconds

    Returns:
        CompletedProcess instance
    """
    venv_python = wt_path / ".venv" / "bin" / "python"

    if not venv_python.exists():
        raise RuntimeError(f"Virtualenv python not found at {venv_python}")

    # Prepend venv python to command
    full_command = [str(venv_python)] + command

    logger.info(f"Running in venv: {' '.join(command)}")
    return await run_command(full_command, cwd=wt_path, timeout=timeout)


# ============================================================================
# Envelope Building
# ============================================================================

def build_envelope(
    agent_name: str,
    task_name: str,
    inputs: Dict[str, Any],
    agent_type: AgentType = AgentType.CUSTOM,
    context: Optional[Dict[str, Any]] = None,
    constraints: Optional[Dict[str, Any]] = None,
    expected_outputs: Optional[List[str]] = None,
    timeout_seconds: int = DEFAULT_AGENT_TIMEOUT,
    retry_config: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> HandoffEnvelope:
    """
    Build HandoffEnvelope for agent task delegation

    Args:
        agent_name: Unique identifier for agent
        task_name: Human-readable task description
        inputs: Input data for agent
        agent_type: Type of agent
        context: Additional context information
        constraints: Execution constraints
        expected_outputs: List of expected output keys
        timeout_seconds: Task timeout
        retry_config: Retry configuration
        metadata: Additional metadata

    Returns:
        HandoffEnvelope instance
    """
    task_id = f"{agent_name}_{int(time.time() * 1000)}"

    envelope = HandoffEnvelope(
        task_id=task_id,
        agent_name=agent_name,
        agent_type=agent_type,
        task_description=task_name,
        inputs=inputs,
        context=context or {},
        constraints=constraints or {},
        expected_outputs=expected_outputs or [],
        timeout_seconds=timeout_seconds,
        retry_config=retry_config or {},
        metadata=metadata or {}
    )

    logger.info(f"Built envelope for task {task_id}: {task_name}")
    return envelope


# ============================================================================
# Agent Execution
# ============================================================================

async def run_subagent(
    branch_name: str,
    task_payload: HandoffEnvelope,
    requirements: Optional[List[str]] = None
) -> TaskResult:
    """
    Execute agent in isolated worktree with full lifecycle management

    Args:
        branch_name: Name for git branch/worktree
        task_payload: Task envelope with all parameters
        requirements: Python packages to install

    Returns:
        TaskResult with execution outcome and provenance
    """
    start_time = time.time()
    worktree_path = None

    # Initialize provenance
    provenance = ProvenanceInfo(
        task_id=task_payload.task_id,
        agent_name=task_payload.agent_name,
        branch_name=branch_name,
        started_at=get_timestamp(),
        input_hash=compute_hash(task_payload.to_dict())
    )

    logger.info(
        f"Starting subagent {task_payload.agent_name} "
        f"for task {task_payload.task_id}"
    )

    try:
        # Create worktree
        worktree_path = await retry_with_backoff(
            create_worktree,
            branch_name,
            retries=2
        )
        provenance.worktree_path = str(worktree_path)
        provenance.command_history.append(f"Created worktree at {worktree_path}")

        # Setup virtualenv
        await retry_with_backoff(
            setup_virtualenv,
            worktree_path,
            requirements,
            retries=2
        )
        provenance.command_history.append("Setup virtualenv")

        # Extract YOLO mode from constraints if available
        yolo_mode = YOLOMode.AGGRESSIVE  # Default
        if hasattr(task_payload, 'constraints') and task_payload.constraints:
            yolo_mode_str = task_payload.constraints.get('yolo_mode', 'aggressive')
            try:
                yolo_mode = YOLOMode(yolo_mode_str)
            except ValueError:
                yolo_mode = YOLOMode.AGGRESSIVE

        # Intelligent model selection for this task
        model_selection = select_best_model(
            task_description=task_payload.task_description,
            agent_type=task_payload.agent_type,
            inputs=task_payload.inputs,
            yolo_mode=yolo_mode
        )

        # Log model selection
        model_info = model_selection['model']
        reasoning = " → ".join(model_selection['reasoning'])
        logger.info(f"🧠 Task {task_payload.task_id}: Selected {model_info}")
        logger.info(f"   Reasoning: {reasoning}")
        logger.info(f"   Analysis: {model_selection['task_analysis']}")

        # Write task envelope to worktree
        envelope_path = worktree_path / "task_envelope.json"
        envelope_path.write_text(task_payload.to_json())
        provenance.command_history.append(f"Wrote task envelope with model: {model_info}")

        # Create a simple agent script (this is a placeholder)
        # In production, you'd have actual agent implementation
        agent_script = worktree_path / "agent.py"
        agent_script.write_text("""
import json
import sys
from pathlib import Path

# Load task envelope
envelope_path = Path(__file__).parent / "task_envelope.json"
with open(envelope_path) as f:
    task = json.load(f)

# Simulate agent work
print(f"Agent {task['agent_name']} executing task {task['task_id']}")
print(f"Task: {task['task_description']}")
print(f"Inputs: {task['inputs']}")

# Create output
output = {
    "task_id": task['task_id'],
    "status": "completed",
    "results": {
        "message": f"Task {task['task_description']} completed successfully",
        "processed_inputs": task['inputs']
    }
}

# Write results
output_path = Path(__file__).parent / "task_result.json"
with open(output_path, 'w') as f:
    json.dump(output, f, indent=2)

print("Task completed successfully")
""")

        # Execute agent in virtualenv with timeout
        try:
            result = await run_with_timeout(
                run_agent_in_venv(
                    worktree_path,
                    ['agent.py'],
                    timeout=task_payload.timeout_seconds
                ),
                timeout_sec=task_payload.timeout_seconds,
                operation_name=f"agent_{task_payload.agent_name}"
            )
            provenance.command_history.append("Executed agent script")

        except asyncio.TimeoutError:
            logger.error(f"Agent timeout after {task_payload.timeout_seconds}s")
            return TaskResult(
                task_id=task_payload.task_id,
                agent_name=task_payload.agent_name,
                status=TaskStatus.TIMEOUT,
                error_message=f"Agent execution timeout after {task_payload.timeout_seconds}s",
                provenance=provenance,
                execution_time_seconds=time.time() - start_time
            )

        # Read results
        result_path = worktree_path / "task_result.json"
        if result_path.exists():
            result_data = json.loads(result_path.read_text())
            outputs = result_data.get('results', {})
        else:
            outputs = {"warning": "No result file generated"}

        # Commit changes
        await run_command(['git', 'add', '.'], cwd=worktree_path)
        await run_command(
            ['git', 'commit', '-m', f'Agent {task_payload.agent_name} completed task'],
            cwd=worktree_path
        )
        provenance.command_history.append("Committed results")

        # Calculate output hash
        provenance.output_hash = compute_hash(outputs)
        provenance.completed_at = get_timestamp()

        logger.info(f"Agent {task_payload.agent_name} completed successfully")

        return TaskResult(
            task_id=task_payload.task_id,
            agent_name=task_payload.agent_name,
            status=TaskStatus.COMPLETED,
            outputs=outputs,
            provenance=provenance,
            execution_time_seconds=time.time() - start_time
        )

    except Exception as e:
        logger.error(f"Agent execution failed: {e}", exc_info=True)
        provenance.completed_at = get_timestamp()

        return TaskResult(
            task_id=task_payload.task_id,
            agent_name=task_payload.agent_name,
            status=TaskStatus.FAILED,
            error_message=str(e),
            provenance=provenance,
            execution_time_seconds=time.time() - start_time
        )

    finally:
        # Cleanup worktree (optional - comment out to preserve for debugging)
        if worktree_path:
            try:
                await remove_worktree(branch_name)
                logger.debug(f"Cleaned up worktree for {branch_name}")
            except Exception as e:
                logger.warning(f"Failed to cleanup worktree: {e}")


# ============================================================================
# Orchestration
# ============================================================================

async def orchestrate_parallel(
    plan: List[HandoffEnvelope],
    requirements: Optional[List[str]] = None
) -> List[TaskResult]:
    """
    Main orchestrator - Execute multiple agents in parallel

    Args:
        plan: List of task envelopes to execute
        requirements: Python packages for all agents

    Returns:
        List of TaskResult instances
    """
    logger.info(f"Starting parallel orchestration of {len(plan)} tasks")

    # Create tasks for parallel execution
    tasks = []
    for idx, envelope in enumerate(plan):
        branch_name = f"{envelope.agent_name}_{idx}_{int(time.time())}"
        task = run_subagent(branch_name, envelope, requirements)
        tasks.append(task)

    # Execute all tasks in parallel
    start_time = time.time()
    results = await asyncio.gather(*tasks, return_exceptions=True)
    total_time = time.time() - start_time

    # Convert exceptions to failed results
    final_results = []
    for idx, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Task {idx} raised exception: {result}")
            final_results.append(TaskResult(
                task_id=plan[idx].task_id,
                agent_name=plan[idx].agent_name,
                status=TaskStatus.FAILED,
                error_message=str(result),
                execution_time_seconds=total_time
            ))
        else:
            final_results.append(result)

    # Log summary
    success_count = sum(1 for r in final_results if r.status == TaskStatus.COMPLETED)
    logger.info(
        f"Orchestration complete: {success_count}/{len(plan)} succeeded "
        f"in {total_time:.2f}s"
    )

    return final_results


def aggregate_results(results: List[TaskResult]) -> Dict[str, Any]:
    """
    Aggregate and validate results from all sub-agents

    Args:
        results: List of TaskResult instances

    Returns:
        Aggregated results dictionary with statistics and outputs
    """
    logger.info(f"Aggregating {len(results)} results")

    aggregated = {
        "total_tasks": len(results),
        "successful": 0,
        "failed": 0,
        "timeout": 0,
        "total_execution_time": 0.0,
        "results_by_agent": {},
        "all_outputs": {},
        "provenance_records": [],
        "errors": []
    }

    for result in results:
        # Update statistics
        if result.status == TaskStatus.COMPLETED:
            aggregated["successful"] += 1
        elif result.status == TaskStatus.TIMEOUT:
            aggregated["timeout"] += 1
        else:
            aggregated["failed"] += 1

        aggregated["total_execution_time"] += result.execution_time_seconds

        # Store results by agent
        aggregated["results_by_agent"][result.agent_name] = {
            "status": result.status.value,
            "outputs": result.outputs,
            "execution_time": result.execution_time_seconds
        }

        # Collect all outputs
        aggregated["all_outputs"][result.task_id] = result.outputs

        # Collect provenance
        if result.provenance:
            aggregated["provenance_records"].append(result.provenance.to_dict())

        # Collect errors
        if result.error_message:
            aggregated["errors"].append({
                "agent": result.agent_name,
                "task_id": result.task_id,
                "error": result.error_message
            })

    # Calculate success rate
    aggregated["success_rate"] = (
        aggregated["successful"] / aggregated["total_tasks"] * 100
        if aggregated["total_tasks"] > 0 else 0
    )

    logger.info(
        f"Aggregation complete: {aggregated['successful']}/{aggregated['total_tasks']} "
        f"succeeded ({aggregated['success_rate']:.1f}%)"
    )

    return aggregated


# ============================================================================
# Main Entry Point
# ============================================================================

async def main():
    """
    Main entry point with example orchestration plan
    Demonstrates parallel execution of multiple agents
    """
    logger.info("=" * 80)
    logger.info("Claude Orchestrator Starting")
    logger.info("=" * 80)

    # Example requirements for all agents
    requirements = [
        'requests',
        'aiohttp',
    ]

    # Build execution plan with multiple agents
    plan = [
        build_envelope(
            agent_name="code_generator_1",
            task_name="Generate utility functions",
            inputs={
                "module": "utils",
                "functions": ["parse_json", "validate_email", "hash_password"]
            },
            agent_type=AgentType.CODE_GENERATOR,
            expected_outputs=["generated_code", "tests"],
            timeout_seconds=300
        ),

        build_envelope(
            agent_name="code_reviewer_1",
            task_name="Review API endpoints",
            inputs={
                "files": ["api/users.py", "api/auth.py"],
                "focus_areas": ["security", "performance", "error_handling"]
            },
            agent_type=AgentType.CODE_REVIEWER,
            expected_outputs=["review_comments", "severity_scores"],
            timeout_seconds=300
        ),

        build_envelope(
            agent_name="tester_1",
            task_name="Generate integration tests",
            inputs={
                "test_suite": "integration",
                "endpoints": ["/api/login", "/api/users"],
                "coverage_target": 80
            },
            agent_type=AgentType.TESTER,
            expected_outputs=["test_code", "coverage_report"],
            timeout_seconds=300
        ),

        build_envelope(
            agent_name="documenter_1",
            task_name="Generate API documentation",
            inputs={
                "api_version": "v1",
                "endpoints": ["users", "auth", "posts"],
                "format": "openapi"
            },
            agent_type=AgentType.DOCUMENTER,
            expected_outputs=["documentation", "examples"],
            timeout_seconds=300
        ),
    ]

    try:
        # Execute orchestration
        results = await orchestrate_parallel(plan, requirements)

        # Aggregate results
        aggregated = aggregate_results(results)

        # Write aggregated results to file
        output_file = Path.home() / "claude-orchestrator" / "orchestration_results.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(json.dumps(aggregated, indent=2))

        logger.info(f"Results written to {output_file}")

        # Print summary
        print("\n" + "=" * 80)
        print("ORCHESTRATION SUMMARY")
        print("=" * 80)
        print(f"Total Tasks: {aggregated['total_tasks']}")
        print(f"Successful: {aggregated['successful']}")
        print(f"Failed: {aggregated['failed']}")
        print(f"Timeout: {aggregated['timeout']}")
        print(f"Success Rate: {aggregated['success_rate']:.1f}%")
        print(f"Total Execution Time: {aggregated['total_execution_time']:.2f}s")
        print("=" * 80)

        # Print individual results
        for agent_name, agent_result in aggregated['results_by_agent'].items():
            print(f"\n{agent_name}:")
            print(f"  Status: {agent_result['status']}")
            print(f"  Time: {agent_result['execution_time']:.2f}s")
            if agent_result['outputs']:
                print(f"  Outputs: {json.dumps(agent_result['outputs'], indent=4)}")

        if aggregated['errors']:
            print("\nERRORS:")
            for error in aggregated['errors']:
                print(f"  [{error['agent']}] {error['error']}")

    except Exception as e:
        logger.error(f"Orchestration failed: {e}", exc_info=True)
        raise

    logger.info("Orchestrator finished")


if __name__ == "__main__":
    # Run the async orchestrator
    asyncio.run(main())
