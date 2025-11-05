# Quick Reference - Claude Orchestrator

## File Location
```
/home/gary/claude-orchestrator/orchestrator.py
```

## Core Functions

### 1. create_worktree(branch_name)
Create isolated git worktree + auto-init repo if needed
```python
worktree_path = await create_worktree("agent-1-branch")
```

### 2. setup_virtualenv(wt_path, requirements=None)
Setup venv + install dependencies
```python
venv_path = await setup_virtualenv(worktree_path, ['requests', 'numpy'])
```

### 3. remove_worktree(branch_name)
Cleanup worktree + branch
```python
await remove_worktree("agent-1-branch")
```

### 4. merge_worktree(branch_name, target_branch="main")
Merge completed branch
```python
success = await merge_worktree("agent-1-branch")
```

### 5. build_envelope(agent_name, task_name, inputs, ...)
Create HandoffEnvelope
```python
envelope = build_envelope(
    agent_name="my_agent",
    task_name="Process data",
    inputs={"data": "value"},
    agent_type=AgentType.CUSTOM,
    timeout_seconds=300
)
```

### 6. run_subagent(branch_name, task_payload, requirements=None)
Execute agent in isolated worktree
```python
result = await run_subagent("my-branch", envelope, ['requests'])
# Returns TaskResult with status, outputs, provenance
```

### 7. run_agent_in_venv(wt_path, command, timeout=1800)
Run command in virtualenv
```python
result = await run_agent_in_venv(
    worktree_path,
    ['script.py', '--arg'],
    timeout=600
)
```

### 8. retry_with_backoff(func, retries=3, ...)
Retry with exponential backoff + jitter
```python
result = await retry_with_backoff(
    my_async_function,
    arg1, arg2,
    retries=3,
    base_delay=1.0,
    max_delay=60.0,
    jitter_range=0.1
)
```

### 9. run_with_timeout(coro, timeout_sec, operation_name="operation")
Execute with timeout
```python
result = await run_with_timeout(
    my_coroutine(),
    timeout_sec=300,
    operation_name="data_processing"
)
```

### 10. orchestrate_parallel(plan, requirements=None)
Main parallel orchestrator
```python
plan = [envelope1, envelope2, envelope3]
results = await orchestrate_parallel(plan, requirements=['requests'])
# Returns List[TaskResult]
```

### 11. aggregate_results(results)
Merge and validate results
```python
summary = aggregate_results(results)
# Returns dict with statistics, outputs, provenance, errors
```

### 12. main()
Entry point with example 4-agent plan
```python
asyncio.run(main())
```

## Data Models

### HandoffEnvelope
```python
envelope = HandoffEnvelope(
    task_id="unique_id",
    agent_name="agent_1",
    agent_type=AgentType.CODE_GENERATOR,
    task_description="Generate code",
    inputs={"key": "value"},
    context={},
    constraints={},
    expected_outputs=["output1", "output2"],
    timeout_seconds=1800,
    retry_config={},
    metadata={}
)
```

### TaskResult
```python
result = TaskResult(
    task_id="unique_id",
    agent_name="agent_1",
    status=TaskStatus.COMPLETED,
    outputs={"result": "data"},
    error_message=None,
    provenance=provenance_info,
    execution_time_seconds=45.2
)
```

## Quick Examples

### Simple 1-Agent Execution
```python
import asyncio
from orchestrator import build_envelope, run_subagent, AgentType

async def simple():
    envelope = build_envelope(
        agent_name="test_agent",
        task_name="Test task",
        inputs={"data": "value"},
        agent_type=AgentType.CUSTOM
    )
    result = await run_subagent("test-branch", envelope)
    print(f"Status: {result.status}")
    print(f"Outputs: {result.outputs}")

asyncio.run(simple())
```

### Parallel 3-Agent Execution
```python
import asyncio
from orchestrator import build_envelope, orchestrate_parallel, AgentType

async def parallel():
    plan = [
        build_envelope("agent1", "Task 1", {"x": 1}),
        build_envelope("agent2", "Task 2", {"x": 2}),
        build_envelope("agent3", "Task 3", {"x": 3}),
    ]
    results = await orchestrate_parallel(plan)
    for r in results:
        print(f"{r.agent_name}: {r.status}")

asyncio.run(parallel())
```

## Verification

```bash
# Verify implementation
python3 ~/claude-orchestrator/verify_implementation.py

# Run examples
python3 ~/claude-orchestrator/example_usage.py

# Run default orchestration
python3 ~/claude-orchestrator/orchestrator.py
```

## Output Files

- **orchestration_results.json** - Aggregated results
- **orchestrator_audit.log** - Complete audit trail

## Common Patterns

### With Custom Requirements
```python
results = await orchestrate_parallel(
    plan,
    requirements=['pandas', 'numpy', 'requests']
)
```

### With Custom Timeout
```python
envelope = build_envelope(
    agent_name="long_task",
    task_name="Long running task",
    inputs={},
    timeout_seconds=3600  # 1 hour
)
```

### With Retry Config
```python
envelope = build_envelope(
    agent_name="flaky_agent",
    task_name="Retry-able task",
    inputs={},
    retry_config={
        "max_retries": 5,
        "backoff_factor": 2.0
    }
)
```

## Constants

```python
DEFAULT_RETRIES = 3
DEFAULT_BASE_DELAY = 1.0
DEFAULT_MAX_DELAY = 60.0
DEFAULT_JITTER_RANGE = 0.1
DEFAULT_COMMAND_TIMEOUT = 300
DEFAULT_AGENT_TIMEOUT = 1800
DEFAULT_OPERATION_TIMEOUT = 60
```

## Error Handling

All functions include:
- Try-catch blocks
- Retry mechanisms
- Timeout protection
- Resource cleanup
- Detailed logging

## Provenance

Every execution tracks:
- Input hash (SHA-256)
- Output hash (SHA-256)
- Start/end timestamps (ISO 8601)
- Command history
- Retry count
- Worktree path
