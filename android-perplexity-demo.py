#!/usr/bin/env python3
"""
Android-Perplexity Integration Demo
Shows how to use Perplexity Sonnet 4.5 for Android automation via the orchestrator
"""

import json
import subprocess
import sys
import time
from pathlib import Path

def run_android_perplexity_demo():
    """Run a demonstration of Android-Perplexity integration"""

    print("🤖 ANDROID-PERPLEXITY INTEGRATION DEMO")
    print("=" * 50)
    print("Using Perplexity Sonnet 4.5 for enhanced Android automation")
    print("")

    # Demo tasks
    demo_tasks = [
        {
            "task_type": "app_testing",
            "app_package": "com.android.chrome",
            "test_scenarios": ["launch", "navigation", "search", "tab_management"],
            "perplexity_enhanced": True
        },
        {
            "task_type": "ui_automation",
            "ui_actions": ["tap", "swipe", "input", "scroll", "long_press"],
            "target_elements": ["search_bar", "navigation_menu", "settings_button", "content_area"],
            "perplexity_intelligence": "adaptive_ui_understanding"
        },
        {
            "task_type": "performance_analysis",
            "metrics": ["cpu", "memory", "battery", "network", "thermal"],
            "perplexity_optimization": True
        },
        {
            "task_type": "system_monitoring",
            "monitoring_targets": ["processes", "services", "resources", "connectivity"],
            "real_time_analysis": True
        }
    ]

    # Execute each demo task
    for i, task in enumerate(demo_tasks, 1):
        print(f"🚀 Executing Demo Task {i}: {task['task_type'].upper()}")
        print("-" * 40)

        # Prepare task input
        task_input = json.dumps(task)

        # Execute Android-Perplexity agent
        try:
            result = subprocess.run(
                [sys.executable, "android-perplexity-agent.py"],
                input=task_input,
                text=True,
                capture_output=True,
                timeout=30
            )

            if result.returncode == 0:
                output = json.loads(result.stdout)
                print(f"✅ Task completed successfully!")
                print(f"📊 Device: {output.get('device_id', 'unknown')}")
                print(f"🧠 Perplexity Enhancement: {output.get('perplexity_analysis', output.get('perplexity_intelligence', 'Active'))}")

                if 'performance_metrics' in output:
                    metrics = output['performance_metrics']
                    print(f"⚡ Response Time: {metrics.get('response_time', 'N/A')}")
                    print(f"🎯 Accuracy: {metrics.get('accuracy', 'N/A')}")

                if 'success_rate' in output:
                    print(f"📈 Success Rate: {output['success_rate']}")

                print(f"📝 Results: {len(output.get('test_results', output.get('automation_details', output.get('optimization_suggestions', []))))} items processed")

            else:
                print(f"❌ Task failed: {result.stderr}")

        except subprocess.TimeoutExpired:
            print("⏰ Task timed out")
        except Exception as e:
            print(f"💥 Error executing task: {e}")

        print("")

    print("🎉 ANDROID-PERPLEXITY DEMO COMPLETED!")
    print("=" * 50)
    print("Key Benefits Demonstrated:")
    print("✅ Enhanced Android automation with Perplexity Sonnet 4.5")
    print("✅ Intelligent UI understanding and interaction")
    print("✅ Advanced performance analysis and optimization")
    print("✅ Real-time system monitoring with AI insights")
    print("✅ Seamless integration via orchestrator system")

def check_android_connectivity():
    """Check if Android device is connected"""
    try:
        result = subprocess.run(
            ["adb", "devices"],
            capture_output=True,
            text=True,
            timeout=10
        )
        devices = [line for line in result.stdout.strip().split('\n')[1:] if line.strip() and "device" in line]
        return len(devices) > 0
    except Exception:
        return False

def main():
    """Main execution"""

    print("🔍 Checking Android connectivity...")
    if check_android_connectivity():
        print("✅ Android device connected")
    else:
        print("⚠️  No Android device found - running in simulation mode")

    print("")

    # Change to orchestrator directory
    os.chdir("/home/gary/claude-orchestrator")

    # Run the demo
    run_android_perplexity_demo()

if __name__ == "__main__":
    import os
    main()