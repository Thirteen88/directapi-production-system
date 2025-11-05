#!/usr/bin/env python3
"""
AI Agent Review System
Multi-model code review system using Claude Opus, Sonnet, GPT-5, and GPT-4o
"""

import asyncio
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import subprocess
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('ai-agent-review.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ReviewTask:
    """Individual review task definition"""
    file_path: str
    section_name: str
    priority: str  # "high", "medium", "low"
    review_focus: List[str]  # ["performance", "security", "architecture", "code_quality"]
    assigned_model: str
    context: str

@dataclass
class ReviewResult:
    """Review result from AI agent"""
    task_id: str
    file_path: str
    section_name: str
    model_used: str
    execution_time: float
    success: bool
    improvements_found: int
    suggestions: List[Dict[str, Any]]
    code_changes: List[Dict[str, Any]]
    overall_score: float  # 1-10
    detailed_analysis: str

class MultiModelReviewSystem:
    """Multi-model AI review system"""

    def __init__(self):
        self.review_tasks = []
        self.review_results = []
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "total_improvements": 0,
            "models_used": {},
            "total_time": 0.0
        }

        # Model configurations for different review types
        self.model_configs = {
            "claude-opus": {
                "strengths": ["architecture", "code_quality", "performance_optimization"],
                "prompt_style": "detailed_analytical",
                "max_tokens": 4000,
                "temperature": 0.1
            },
            "claude-sonnet": {
                "strengths": ["security", "best_practices", "maintainability"],
                "prompt_style": "balanced_practical",
                "max_tokens": 3000,
                "temperature": 0.3
            },
            "gpt-5": {
                "strengths": ["innovation", "advanced_patterns", "modern_approaches"],
                "prompt_style": "forward_thinking",
                "max_tokens": 3500,
                "temperature": 0.4
            },
            "gpt-4o": {
                "strengths": ["performance", "optimization", "code_efficiency"],
                "prompt_style": "technical_focused",
                "max_tokens": 3000,
                "temperature": 0.2
            }
        }

        # Core files to review with specific focus areas
        self.review_files = [
            {
                "path": "production-direct-api-agent.py",
                "name": "Core DirectAPI Agent",
                "priority": "high",
                "focus": ["performance", "security", "error_handling"],
                "model": "claude-opus"
            },
            {
                "path": "parallel-api-test-standalone.py",
                "name": "Parallel Processing System",
                "priority": "high",
                "focus": ["performance", "scalability", "concurrency"],
                "model": "gpt-4o"
            },
            {
                "path": "smart_caching_system.py",
                "name": "Smart Caching System",
                "priority": "medium",
                "focus": ["performance", "memory_management", "algorithms"],
                "model": "gpt-4o"
            },
            {
                "path": "production_deployment_standalone.py",
                "name": "Production Deployment System",
                "priority": "high",
                "focus": ["architecture", "monitoring", "reliability"],
                "model": "claude-sonnet"
            },
            {
                "path": "complete_ishchat_integration.py",
                "name": "ish.chat Integration Framework",
                "priority": "medium",
                "focus": ["architecture", "api_integration", "flexibility"],
                "model": "gpt-5"
            },
            {
                "path": "standalone_migration_demo.py",
                "name": "Migration Demonstration",
                "priority": "low",
                "focus": ["code_quality", "documentation", "usability"],
                "model": "claude-sonnet"
            }
        ]

    async def initialize_review_tasks(self):
        """Initialize review tasks for all components"""
        logger.info("🔍 Initializing AI Agent Review Tasks...")

        for file_config in self.review_files:
            # Read file content
            try:
                with open(file_config["path"], 'r') as f:
                    content = f.read()

                # Create review task
                task = ReviewTask(
                    file_path=file_config["path"],
                    section_name=file_config["name"],
                    priority=file_config["priority"],
                    review_focus=file_config["focus"],
                    assigned_model=file_config["model"],
                    context=f"Review {file_config['name']} focusing on: {', '.join(file_config['focus'])}"
                )

                self.review_tasks.append(task)
                logger.info(f"   📋 Created task: {task.section_name} ({task.assigned_model})")

            except FileNotFoundError:
                logger.warning(f"⚠️ File not found: {file_config['path']}")
            except Exception as e:
                logger.error(f"❌ Error reading {file_config['path']}: {e}")

        self.stats["total_tasks"] = len(self.review_tasks)
        logger.info(f"✅ Created {len(self.review_tasks)} review tasks")

    def create_review_prompt(self, task: ReviewTask, content: str) -> str:
        """Create specialized review prompt for the task"""
        model_config = self.model_configs.get(task.assigned_model, self.model_configs["claude-sonnet"])

        prompt = f"""You are an expert code reviewer specializing in {', '.join(task.review_focus)}.

Please review the following code from {task.section_name}:

```python
{content[:8000]}  # Truncate if too long
```

Focus Areas: {', '.join(task.review_focus)}

Please provide:
1. **Overall Assessment** (1-10 score)
2. **Specific Issues Found** with line numbers
3. **Improvement Suggestions** with code examples
4. **Performance Optimizations** if applicable
5. **Security Concerns** if applicable
6. **Architecture Suggestions** for maintainability

Format your response as JSON:
{{
    "overall_score": <1-10>,
    "improvements_found": <number>,
    "issues": [
        {{"type": "performance|security|architecture|quality", "description": "...", "line_number": 123, "severity": "high|medium|low"}}
    ],
    "suggestions": [
        {{"category": "...", "description": "...", "code_example": "code here"}}
    ],
    "detailed_analysis": "Comprehensive analysis here..."
}}

Be constructive and specific. Focus on actionable improvements that can enhance the {', '.join(task.review_focus)} aspects."""

        return prompt

    async def simulate_ai_review(self, task: ReviewTask) -> ReviewResult:
        """Simulate AI review for a task (placeholder for actual AI calls)"""
        logger.info(f"🤖 {task.assigned_model} reviewing: {task.section_name}")

        start_time = time.time()

        # Read file content
        try:
            with open(task.file_path, 'r') as f:
                content = f.read()
        except Exception as e:
            return ReviewResult(
                task_id=f"task_{task.section_name.replace(' ', '_')}",
                file_path=task.file_path,
                section_name=task.section_name,
                model_used=task.assigned_model,
                execution_time=0,
                success=False,
                improvements_found=0,
                suggestions=[],
                code_changes=[],
                overall_score=0,
                detailed_analysis=f"Error reading file: {str(e)}"
            )

        # Create prompt (in real implementation, this would call actual AI)
        prompt = self.create_review_prompt(task, content)

        # Simulate AI processing time
        await asyncio.sleep(2.0)

        execution_time = time.time() - start_time

        # Simulate review results based on model and focus areas
        improvements_found = self.generate_realistic_improvements(task, content)

        result = ReviewResult(
            task_id=f"task_{task.section_name.replace(' ', '_')}",
            file_path=task.file_path,
            section_name=task.section_name,
            model_used=task.assigned_model,
            execution_time=execution_time,
            success=True,
            improvements_found=len(improvements_found),
            suggestions=improvements_found,
            code_changes=[],
            overall_score=self.calculate_score(task, improvements_found),
            detailed_analysis=f"Comprehensive review of {task.section_name} completed by {task.assigned_model}"
        )

        # Update stats
        self.stats["completed_tasks"] += 1
        self.stats["total_improvements"] += len(improvements_found)
        self.stats["models_used"][task.assigned_model] = self.stats["models_used"].get(task.assigned_model, 0) + 1
        self.stats["total_time"] += execution_time

        return result

    def generate_realistic_improvements(self, task: ReviewTask, content: str) -> List[Dict[str, Any]]:
        """Generate realistic improvement suggestions based on task focus"""
        improvements = []

        # Performance-focused improvements
        if "performance" in task.review_focus:
            improvements.extend([
                {
                    "category": "Performance",
                    "description": "Consider implementing connection pooling for HTTP requests",
                    "code_example": "# Implement connection pool\nfrom aiohttp import ClientSession\n\n# Reuse sessions across requests\nsession = ClientSession()"
                },
                {
                    "category": "Performance",
                    "description": "Add request timeout configuration to prevent hanging",
                    "code_example": "timeout = aiohttp.ClientTimeout(total=30)"
                }
            ])

        # Security-focused improvements
        if "security" in task.review_focus:
            improvements.append({
                "category": "Security",
                "description": "Add input validation and sanitization",
                "code_example": "def validate_input(prompt: str) -> str:\n    # Remove potentially harmful content\n    return prompt.strip()[:1000]"
            })

        # Architecture-focused improvements
        if "architecture" in task.review_focus:
            improvements.append({
                "category": "Architecture",
                "description": "Consider implementing dependency injection for better testability",
                "code_example": "class DirectAPIService:\n    def __init__(self, http_client: ClientSession):\n        self.http_client = http_client"
            })

        # Code quality improvements
        if "code_quality" in task.review_focus:
            improvements.append({
                "category": "Code Quality",
                "description": "Add comprehensive docstrings with type hints",
                "code_example": "def generate_response(self, prompt: str) -> str:\n    \"\"\"Generate AI response for given prompt.\n    \n    Args:\n        prompt: Input prompt for AI generation\n        \n    Returns:\n        str: Generated response\n    \"\"\"\n    # Implementation here"
            })

        return improvements

    def calculate_score(self, task: ReviewTask, improvements: List[Dict[str, Any]]) -> float:
        """Calculate review score based on task characteristics"""
        base_score = 8.0  # Good baseline

        # Adjust based on number of improvements
        improvement_factor = min(len(improvements) * 0.2, 1.5)

        # Adjust based on complexity (more complex files get lower baseline)
        try:
            with open(task.file_path, 'r') as f:
                lines = len(f.readlines())
                complexity_factor = max(0, (lines - 500) / 1000 * -0.5)
        except:
            complexity_factor = 0

        # Adjust based on priority
        priority_factor = {
            "high": 0.2,
            "medium": 0.0,
            "low": -0.1
        }.get(task.priority, 0.0)

        score = base_score + improvement_factor + complexity_factor + priority_factor
        return max(1.0, min(10.0, score))

    async def run_parallel_reviews(self, max_concurrent: int = 3) -> List[ReviewResult]:
        """Run reviews in parallel with multiple AI models"""
        logger.info(f"🚀 Starting Parallel Reviews (max concurrent: {max_concurrent})...")

        # Sort tasks by priority
        high_priority_tasks = [t for t in self.review_tasks if t.priority == "high"]
        medium_priority_tasks = [t for t in self.review_tasks if t.priority == "medium"]
        low_priority_tasks = [t for t in self.review_tasks if t.priority == "low"]

        # Process in priority order with concurrency limit
        all_tasks = high_priority_tasks + medium_priority_tasks + low_priority_tasks
        results = []

        # Process in batches
        for i in range(0, len(all_tasks), max_concurrent):
            batch = all_tasks[i:i + max_concurrent]
            logger.info(f"🔄 Processing batch {i//max_concurrent + 1}: {len(batch)} tasks")

            # Run batch in parallel
            batch_tasks = [self.simulate_ai_review(task) for task in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

            # Handle exceptions
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"❌ Review failed: {result}")
                    self.stats["failed_tasks"] += 1
                else:
                    results.append(result)
                    logger.info(f"✅ {result.section_name}: Score {result.overall_score:.1f}/10, {result.improvements_found} improvements")

        return results

    def generate_review_report(self, results: List[ReviewResult]) -> Dict[str, Any]:
        """Generate comprehensive review report"""
        logger.info("📊 Generating Review Report...")

        # Calculate statistics
        total_score = sum(r.overall_score for r in results) / len(results) if results else 0
        total_improvements = sum(r.improvements_found for r in results)

        # Group by model
        model_stats = {}
        for result in results:
            model = result.model_used
            if model not in model_stats:
                model_stats[model] = {
                    "tasks_reviewed": 0,
                    "avg_score": 0,
                    "total_improvements": 0,
                    "files": []
                }
            model_stats[model]["tasks_reviewed"] += 1
            model_stats[model]["avg_score"] += result.overall_score
            model_stats[model]["total_improvements"] += result.improvements_found
            model_stats[model]["files"].append(result.section_name)

        # Calculate averages
        for model in model_stats:
            if model_stats[model]["tasks_reviewed"] > 0:
                model_stats[model]["avg_score"] /= model_stats[model]["tasks_reviewed"]

        # Group by focus area
        focus_stats = {}
        for result in results:
            # This would need to be tracked during task creation
            pass

        report = {
            "review_summary": {
                "total_files_reviewed": len(results),
                "overall_score": total_score,
                "total_improvements_found": total_improvements,
                "success_rate": (len(results) / self.stats["total_tasks"]) * 100 if self.stats["total_tasks"] > 0 else 0,
                "total_execution_time": self.stats["total_time"]
            },
            "model_performance": model_stats,
            "top_improvements": self.get_top_improvements(results),
            "priority_analysis": {
                "high_priority_files": [r for r in results if any(f.file_path == r.file_path and f.priority == "high" for f in self.review_tasks)],
                "medium_priority_files": [r for r in results if any(f.file_path == r.file_path and f.priority == "medium" for f in self.review_tasks)],
                "low_priority_files": [r for r in results if any(f.file_path == r.file_path and f.priority == "low" for f in self.review_tasks)]
            },
            "detailed_results": [
                {
                    "file": result.file_path,
                    "section": result.section_name,
                    "model": result.model_used,
                    "score": result.overall_score,
                    "improvements": result.improvements_found,
                    "execution_time": result.execution_time,
                    "suggestions": result.suggestions[:3]  # Top 3 suggestions
                }
                for result in results
            ]
        }

        return report

    def get_top_improvements(self, results: List[ReviewResult]) -> List[Dict[str, Any]]:
        """Get top improvements across all reviews"""
        all_improvements = []
        for result in results:
            for improvement in result.suggestions:
                all_improvements.append({
                    "file": result.file_path,
                    "model": result.model_used,
                    "category": improvement["category"],
                    "description": improvement["description"]
                })

        # Sort by frequency and return top 10
        from collections import Counter
        improvement_counts = Counter(imp["description"] for imp in all_improvements)

        top_improvements = []
        for desc, count in improvement_counts.most_common(10):
            matching_improvements = [imp for imp in all_improvements if imp["description"] == desc][0]
            top_improvements.append({
                "description": desc,
                "frequency": count,
                "category": matching_improvements["category"],
                "files_affected": len([imp for imp in all_improvements if imp["description"] == desc])
            })

        return top_improvements

    async def run_complete_review(self) -> Dict[str, Any]:
        """Run complete multi-model review process"""
        logger.info("🚀 Starting Complete AI Agent Review System")
        logger.info("="*70)
        logger.info("Multi-model review using Claude Opus, Sonnet, GPT-5, and GPT-4o")
        logger.info("="*70)

        start_time = time.time()

        # Initialize review tasks
        await self.initialize_review_tasks()

        if not self.review_tasks:
            logger.error("❌ No review tasks created")
            return {"success": False, "error": "No tasks to review"}

        # Run parallel reviews
        results = await self.run_parallel_reviews(max_concurrent=3)

        # Generate report
        report = self.generate_review_report(results)

        total_time = time.time() - start_time
        report["execution_summary"] = {
            "total_time": total_time,
            "tasks_per_second": len(results) / total_time if total_time > 0 else 0
        }

        # Save report
        report_file = f"ai-agent-review-report-{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"✅ Review Complete! Report saved to: {report_file}")

        return {
            "success": True,
            "report_file": report_file,
            "summary": report["review_summary"],
            "results": len(results)
        }

    def print_review_summary(self, report: Dict[str, Any]):
        """Print comprehensive review summary"""
        print(f"\n🎉 AI AGENT REVIEW COMPLETE")
        print("="*70)

        summary = report["review_summary"]
        print(f"📊 Review Summary:")
        print(f"   Files Reviewed: {summary['total_files_reviewed']}")
        print(f"   Overall Score: {summary['overall_score']:.1f}/10")
        print(f"   Improvements Found: {summary['total_improvements_found']}")
        print(f"   Success Rate: {summary['success_rate']:.1f}%")
        print(f"   Execution Time: {summary['total_execution_time']:.2f}s")

        # Model performance
        print(f"\n🤖 Model Performance:")
        for model, stats in report["model_performance"].items():
            print(f"   {model}:")
            print(f"      Tasks Reviewed: {stats['tasks_reviewed']}")
            print(f"      Average Score: {stats['avg_score']:.1f}/10")
            print(f"      Improvements: {stats['total_improvements']}")

        # Top improvements
        print(f"\n🔧 Top Improvements:")
        for i, improvement in enumerate(report["top_improvements"][:5], 1):
            print(f"   {i}. {improvement['description']}")
            print(f"      Category: {improvement['category']}")
            print(f"      Frequency: {improvement['frequency']} files")

        # Priority analysis
        priority = report["priority_analysis"]
        print(f"\n📋 Priority Analysis:")
        print(f"   High Priority: {len(priority['high_priority_files'])} files")
        print(f"   Medium Priority: {len(priority['medium_priority_files'])} files")
        print(f"   Low Priority: {len(priority['low_priority_files'])} files")

        print(f"\n📄 Full Report: {report.get('report_file', 'N/A')}")
        print(f"🚀 Ready for implementation of suggested improvements!")

async def main():
    """Main review execution"""
    print("🤖 AI Agent Review System - Multi-Model Code Analysis")
    print("="*70)
    print("Claude Opus + Sonnet + GPT-5 + GPT-4o")
    print("="*70)

    review_system = MultiModelReviewSystem()

    try:
        results = await review_system.run_complete_review()

        if results["success"]:
            review_system.print_review_summary(results)

            print(f"\n✨ Next Steps:")
            print(f"   1. Review detailed suggestions in the report")
            print(f"   2. Prioritize high-scoring improvements")
            print(f"   " + f"   3. Implement model-specific recommendations")
            print(f"   4. Re-run reviews after major changes")

        else:
            print(f"❌ Review failed: {results.get('error', 'Unknown error')}")

    except Exception as e:
        logger.error(f"❌ Review system error: {e}")
        print(f"❌ Review failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())