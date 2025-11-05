# Claude Orchestrator Test Suite

## Overview

Comprehensive test script that validates all aspects of the Claude Orchestrator system.

## Quick Start

```bash
cd ~/claude-orchestrator
python3 test_orchestrator.py
```

## What's Tested

### Part 1: Core Function Tests
- **Hash Generation**: SHA-256 hashing for provenance tracking
- **Timestamp Generation**: ISO 8601 timestamp creation
- **Envelope Building**: HandoffEnvelope creation and serialization
- **Worktree Creation/Deletion**: Git worktree lifecycle management
- **Virtualenv Setup**: Python virtual environment creation
- **Schema Validation**: JSON schema validation against defined schemas

### Part 2: Full Orchestration Flow
- **Simple Parallel Orchestration**: 3-agent parallel execution
- **Provenance Tracking**: Verification of audit trail data
- **Output Schema Validation**: Validation of result structures
- **Cleanup**: Proper resource cleanup verification

### Part 3: Error Handling
- **Timeout Handling**: Task timeout scenarios
- **Retry with Backoff**: Exponential backoff retry logic
- **Failed Agent Simulation**: Graceful failure handling
- **Command Timeout**: Command execution timeout handling

### Part 4: Performance Benchmarks
- **Parallel vs Sequential**: Performance comparison of execution strategies
- **Resource Usage**: Memory and CPU tracking during orchestration

### Part 5: Integration Tests
- **End-to-End Workflow**: Complete workflow with real git operations
- **Multi-Level Delegation**: Nested orchestration (orchestrators spawning sub-orchestrators)

## Output

### Console Output
The script provides verbose output showing:
- Each test being run
- Pass/fail status with ✓/✗ indicators
- Execution times
- Detailed error messages for failures
- Summary statistics for each test suite

### Example Output:
```
================================================================================
PART 1: CORE FUNCTION TESTS
================================================================================

================================================================================
Running: Hash Generation
================================================================================
Testing hash generation...
  Generated hash: 9f86d081884c7d659a2f...
✓ Hash Generation PASSED
  Details: {
    "hash_length": 64,
    "hash_consistency": true,
    "sample_hash": "9f86d081884c7d65"
  }

...

================================================================================
TEST SUITE: Core Functions
================================================================================
Total Tests: 6
Passed: 6 ✓
Failed: 0 ✗
Success Rate: 100.0%
Total Duration: 12.45s
================================================================================
  ✓ PASS Hash Generation (0.12s)
  ✓ PASS Timestamp Generation (0.08s)
  ...
```

### JSON Output
Results are saved to:
```
~/claude-orchestrator/test_results/test_results_<timestamp>.json
```

Contains:
- Summary statistics
- Individual test results
- Performance metrics
- Error details

### Log Files
Detailed logs written to:
```
~/claude-orchestrator/test_results/test_orchestrator.log
```

## Test Configuration

### Adjusting Verbosity
Edit `test_orchestrator.py`:
```python
VERBOSE = True  # Set to False for less output
```

### Test Timeouts
Individual tests have timeouts configured:
```python
timeout_seconds=120  # Adjust as needed
```

### Number of Parallel Tasks
Modify test plans:
```python
# Increase from 3 to more agents
plan = [
    build_envelope(...) for i in range(10)  # 10 parallel agents
]
```

## Prerequisites

The test suite requires:
- Python 3.7+
- Git installed and configured
- psutil library (for resource tracking)
- All orchestrator dependencies

Install dependencies:
```bash
pip install -r requirements.txt
pip install psutil  # For resource benchmarks
```

## Troubleshooting

### Git Not Configured
If you see git configuration errors:
```bash
git config --global user.email "test@example.com"
git config --global user.name "Test User"
```

### Permission Errors
Ensure write permissions:
```bash
chmod -R u+w ~/claude-orchestrator/worktrees
chmod -R u+w ~/claude-orchestrator/test_results
```

### Timeout Errors
Increase timeout values in tests if your system is slower:
```python
timeout_seconds=300  # Increase from default 120
```

### Memory Issues
Reduce parallel task count:
```python
# In benchmark_parallel_vs_sequential
tasks = [build_envelope(...) for i in range(2)]  # Reduce from 3
```

## Continuous Testing

### Run specific test suites:
```python
# Edit main() to run only specific suites
async def run_all_tests():
    # Comment out suites you don't want to run
    # core_tests = [...]
    # orchestration_tests = [...]
    error_tests = [...]  # Run only error handling tests
```

### Automated Testing
Add to CI/CD pipeline:
```bash
#!/bin/bash
cd ~/claude-orchestrator
python3 test_orchestrator.py
if [ $? -eq 0 ]; then
    echo "All tests passed!"
else
    echo "Tests failed!"
    exit 1
fi
```

## Expected Results

On a properly configured system, you should see:
- **Core Functions**: 100% pass rate (6/6 tests)
- **Orchestration Flow**: 100% pass rate (4/4 tests)
- **Error Handling**: 100% pass rate (4/4 tests)
- **Performance**: All benchmarks complete (2/2 tests)
- **Integration**: 100% pass rate (2/2 tests)

**Total: 18 tests, ~100% success rate**

Execution time varies by system:
- Fast system: 30-60 seconds
- Average system: 60-120 seconds
- Slow system: 120-300 seconds

## Advanced Usage

### Custom Test Addition
Add your own tests:
```python
async def test_my_custom_feature():
    """Test description"""
    if VERBOSE:
        print("Testing my feature...")

    # Your test code here
    result = await some_async_operation()

    assert result is not None, "Result should exist"

    return {
        "metric": "value",
        "status": "success"
    }

# Add to appropriate suite
custom_tests = [
    (test_my_custom_feature, "My Custom Feature"),
]
```

### Performance Profiling
Enable detailed profiling:
```bash
python3 -m cProfile -o test_profile.prof test_orchestrator.py
python3 -m pstats test_profile.prof
```

## Test Data Cleanup

Tests clean up after themselves, but to manually clean:
```bash
# Remove test worktrees
rm -rf ~/claude-orchestrator/worktrees/*

# Remove test results
rm -rf ~/claude-orchestrator/test_results/*

# Remove main repo (will be recreated)
rm -rf ~/claude-orchestrator/main-repo
```

## Support

For issues with tests:
1. Check logs in `~/claude-orchestrator/test_results/`
2. Review orchestrator logs in `~/claude-orchestrator/orchestrator_audit.log`
3. Verify git configuration
4. Check disk space and permissions

## Version Compatibility

Tested with:
- Python 3.7, 3.8, 3.9, 3.10, 3.11
- Git 2.x
- Linux, macOS (Windows with WSL)

## License

Same license as Claude Orchestrator main project.
