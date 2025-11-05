#!/usr/bin/env python3
"""
Example usage of the Claude Orchestrator
Demonstrates how to create custom orchestration plans
"""

import asyncio
import sys
from pathlib import Path

# Add orchestrator to path
sys.path.insert(0, str(Path.home() / "claude-orchestrator"))

from orchestrator import (
    build_envelope,
    orchestrate_parallel,
    aggregate_results,
    AgentType
)


async def simple_example():
    """Simple 2-agent example"""
    print("Running simple 2-agent example...\n")
    
    plan = [
        build_envelope(
            agent_name="data_processor",
            task_name="Process customer data",
            inputs={
                "dataset": "customers.csv",
                "operations": ["clean", "normalize", "validate"]
            },
            agent_type=AgentType.CUSTOM,
            timeout_seconds=180
        ),
        
        build_envelope(
            agent_name="report_generator",
            task_name="Generate summary report",
            inputs={
                "report_type": "monthly",
                "metrics": ["revenue", "growth", "churn"]
            },
            agent_type=AgentType.DOCUMENTER,
            timeout_seconds=180
        ),
    ]
    
    # Execute
    results = await orchestrate_parallel(plan)
    
    # Aggregate
    summary = aggregate_results(results)
    
    print(f"\nResults: {summary['successful']}/{summary['total_tasks']} succeeded")
    return summary


async def advanced_example():
    """Advanced example with dependencies and custom requirements"""
    print("Running advanced 5-agent example...\n")
    
    # Custom package requirements
    requirements = ['requests', 'pandas', 'numpy']
    
    plan = [
        build_envelope(
            agent_name="api_fetcher",
            task_name="Fetch data from external API",
            inputs={
                "endpoint": "https://api.example.com/data",
                "auth_type": "bearer"
            },
            agent_type=AgentType.CUSTOM,
            context={"retry_on_failure": True},
            timeout_seconds=300
        ),
        
        build_envelope(
            agent_name="data_validator",
            task_name="Validate fetched data",
            inputs={
                "schema": "customer_schema.json",
                "strict_mode": True
            },
            agent_type=AgentType.CUSTOM,
            expected_outputs=["validation_report", "cleaned_data"],
            timeout_seconds=240
        ),
        
        build_envelope(
            agent_name="code_generator",
            task_name="Generate ETL pipeline code",
            inputs={
                "source": "api",
                "destination": "database",
                "transformations": ["dedup", "enrich"]
            },
            agent_type=AgentType.CODE_GENERATOR,
            expected_outputs=["pipeline_code", "unit_tests"],
            timeout_seconds=360
        ),
        
        build_envelope(
            agent_name="test_runner",
            task_name="Run integration tests",
            inputs={
                "test_suite": "integration",
                "parallel": True,
                "coverage_threshold": 85
            },
            agent_type=AgentType.TESTER,
            expected_outputs=["test_results", "coverage_report"],
            timeout_seconds=420
        ),
        
        build_envelope(
            agent_name="doc_writer",
            task_name="Generate technical documentation",
            inputs={
                "sections": ["architecture", "api", "deployment"],
                "format": "markdown",
                "include_diagrams": True
            },
            agent_type=AgentType.DOCUMENTER,
            expected_outputs=["documentation"],
            timeout_seconds=300
        ),
    ]
    
    # Execute with custom requirements
    results = await orchestrate_parallel(plan, requirements=requirements)
    
    # Aggregate and analyze
    summary = aggregate_results(results)
    
    print(f"\n{'='*60}")
    print("EXECUTION SUMMARY")
    print('='*60)
    print(f"Total Tasks: {summary['total_tasks']}")
    print(f"Successful: {summary['successful']}")
    print(f"Failed: {summary['failed']}")
    print(f"Timeout: {summary['timeout']}")
    print(f"Success Rate: {summary['success_rate']:.1f}%")
    print(f"Total Time: {summary['total_execution_time']:.2f}s")
    
    if summary['errors']:
        print("\nErrors encountered:")
        for error in summary['errors']:
            print(f"  - {error['agent']}: {error['error']}")
    
    return summary


async def error_handling_example():
    """Example demonstrating error handling and retries"""
    print("Running error handling example...\n")
    
    plan = [
        build_envelope(
            agent_name="flaky_agent",
            task_name="Task that might fail",
            inputs={"simulate_failure": False},
            agent_type=AgentType.CUSTOM,
            retry_config={
                "max_retries": 3,
                "backoff_factor": 2.0
            },
            timeout_seconds=120
        ),
        
        build_envelope(
            agent_name="timeout_agent",
            task_name="Task with tight timeout",
            inputs={"work_duration": 60},
            agent_type=AgentType.CUSTOM,
            timeout_seconds=90  # Should succeed
        ),
    ]
    
    results = await orchestrate_parallel(plan)
    summary = aggregate_results(results)
    
    print(f"\nHandled {len(results)} tasks with error recovery")
    return summary


async def main():
    """Run all examples"""
    print("="*60)
    print("CLAUDE ORCHESTRATOR - USAGE EXAMPLES")
    print("="*60)
    print()
    
    # Run examples
    try:
        print("[1/3] Simple Example")
        print("-" * 60)
        await simple_example()
        
        print("\n" + "="*60)
        print("[2/3] Advanced Example")
        print("-" * 60)
        await advanced_example()
        
        print("\n" + "="*60)
        print("[3/3] Error Handling Example")
        print("-" * 60)
        await error_handling_example()
        
        print("\n" + "="*60)
        print("ALL EXAMPLES COMPLETED")
        print("="*60)
        
    except Exception as e:
        print(f"\nExample failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
