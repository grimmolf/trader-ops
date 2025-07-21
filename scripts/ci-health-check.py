#!/usr/bin/env python3
"""Monitor CI/CD pipeline health metrics and provide actionable insights."""

import json
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import sys
from collections import defaultdict

class Colors:
    """Terminal colors for output."""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color


def run_gh_command(args: List[str]) -> Optional[str]:
    """Run a GitHub CLI command and return output."""
    try:
        result = subprocess.run(
            ["gh"] + args,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"{Colors.RED}Error running gh command: {e}{Colors.NC}")
        return None
    except FileNotFoundError:
        print(f"{Colors.RED}GitHub CLI (gh) not found. Install it first.{Colors.NC}")
        sys.exit(1)


def get_recent_runs(limit: int = 20) -> List[Dict]:
    """Get recent workflow runs."""
    output = run_gh_command([
        "run", "list",
        "--limit", str(limit),
        "--json", "status,conclusion,createdAt,workflowName,headBranch,event,databaseId"
    ])
    
    if output:
        return json.loads(output)
    return []


def get_run_details(run_id: int) -> Optional[Dict]:
    """Get detailed information about a specific run."""
    output = run_gh_command([
        "run", "view", str(run_id),
        "--json", "jobs,conclusion,status"
    ])
    
    if output:
        return json.loads(output)
    return None


def analyze_failure_patterns(runs: List[Dict]) -> Dict:
    """Analyze patterns in CI/CD failures."""
    patterns = {
        "by_workflow": defaultdict(lambda: {"total": 0, "failed": 0}),
        "by_branch": defaultdict(lambda: {"total": 0, "failed": 0}),
        "by_event": defaultdict(lambda: {"total": 0, "failed": 0}),
        "common_failures": defaultdict(int),
        "time_patterns": defaultdict(int)
    }
    
    for run in runs:
        workflow = run.get("workflowName", "Unknown")
        branch = run.get("headBranch", "Unknown")
        event = run.get("event", "Unknown")
        conclusion = run.get("conclusion", "")
        
        # Track by workflow
        patterns["by_workflow"][workflow]["total"] += 1
        if conclusion == "failure":
            patterns["by_workflow"][workflow]["failed"] += 1
            
            # Get detailed failure info
            details = get_run_details(run.get("databaseId"))
            if details and "jobs" in details:
                for job in details["jobs"]:
                    if job.get("conclusion") == "failure":
                        job_name = job.get("name", "Unknown Job")
                        patterns["common_failures"][f"{workflow} - {job_name}"] += 1
        
        # Track by branch
        patterns["by_branch"][branch]["total"] += 1
        if conclusion == "failure":
            patterns["by_branch"][branch]["failed"] += 1
        
        # Track by event type
        patterns["by_event"][event]["total"] += 1
        if conclusion == "failure":
            patterns["by_event"][event]["failed"] += 1
        
        # Time patterns (hour of day)
        created_at = run.get("createdAt", "")
        if created_at:
            hour = datetime.fromisoformat(created_at.replace("Z", "+00:00")).hour
            if conclusion == "failure":
                patterns["time_patterns"][hour] += 1
    
    return patterns


def calculate_metrics(runs: List[Dict]) -> Dict:
    """Calculate key CI/CD metrics."""
    if not runs:
        return {
            "total_runs": 0,
            "success_rate": 0,
            "avg_time_to_fix": 0,
            "most_stable_branch": "N/A",
            "most_problematic_workflow": "N/A"
        }
    
    total = len(runs)
    successful = sum(1 for r in runs if r.get("conclusion") == "success")
    failed = sum(1 for r in runs if r.get("conclusion") == "failure")
    
    # Calculate time to fix (simplified - time between failure and next success)
    fix_times = []
    for i in range(len(runs) - 1):
        if runs[i]["conclusion"] == "failure" and runs[i+1]["conclusion"] == "success":
            fail_time = datetime.fromisoformat(runs[i]["createdAt"].replace("Z", "+00:00"))
            fix_time = datetime.fromisoformat(runs[i+1]["createdAt"].replace("Z", "+00:00"))
            fix_times.append((fix_time - fail_time).total_seconds() / 3600)  # hours
    
    avg_fix_time = sum(fix_times) / len(fix_times) if fix_times else 0
    
    return {
        "total_runs": total,
        "successful_runs": successful,
        "failed_runs": failed,
        "success_rate": (successful / total * 100) if total > 0 else 0,
        "avg_time_to_fix": avg_fix_time
    }


def print_health_report(metrics: Dict, patterns: Dict):
    """Print a comprehensive health report."""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.NC}")
    print(f"{Colors.BLUE}🏥 CI/CD Pipeline Health Report{Colors.NC}")
    print(f"{Colors.BLUE}{'='*60}{Colors.NC}")
    
    # Overall metrics
    print(f"\n{Colors.CYAN}📊 Overall Metrics:{Colors.NC}")
    success_rate = metrics["success_rate"]
    color = Colors.GREEN if success_rate >= 90 else Colors.YELLOW if success_rate >= 75 else Colors.RED
    print(f"  Success Rate: {color}{success_rate:.1f}%{Colors.NC}")
    print(f"  Total Runs: {metrics['total_runs']}")
    print(f"  Failed Runs: {metrics['failed_runs']}")
    if metrics["avg_time_to_fix"] > 0:
        print(f"  Avg Time to Fix: {metrics['avg_time_to_fix']:.1f} hours")
    
    # Workflow analysis
    print(f"\n{Colors.CYAN}🔄 Workflow Analysis:{Colors.NC}")
    for workflow, stats in sorted(patterns["by_workflow"].items(), 
                                 key=lambda x: x[1]["failed"], reverse=True)[:5]:
        if stats["total"] > 0:
            failure_rate = (stats["failed"] / stats["total"]) * 100
            color = Colors.GREEN if failure_rate < 10 else Colors.YELLOW if failure_rate < 25 else Colors.RED
            print(f"  {workflow}: {color}{failure_rate:.1f}% failure rate{Colors.NC} "
                  f"({stats['failed']}/{stats['total']} runs)")
    
    # Common failure points
    if patterns["common_failures"]:
        print(f"\n{Colors.CYAN}❌ Common Failure Points:{Colors.NC}")
        for failure, count in sorted(patterns["common_failures"].items(), 
                                   key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {failure}: {count} failures")
    
    # Branch stability
    print(f"\n{Colors.CYAN}🌳 Branch Stability:{Colors.NC}")
    for branch, stats in sorted(patterns["by_branch"].items(), 
                               key=lambda x: x[1]["total"], reverse=True)[:5]:
        if stats["total"] > 0:
            failure_rate = (stats["failed"] / stats["total"]) * 100
            color = Colors.GREEN if failure_rate < 10 else Colors.YELLOW if failure_rate < 25 else Colors.RED
            print(f"  {branch}: {color}{failure_rate:.1f}% failure rate{Colors.NC} "
                  f"({stats['failed']}/{stats['total']} runs)")
    
    # Recommendations
    print(f"\n{Colors.CYAN}💡 Recommendations:{Colors.NC}")
    
    if success_rate < 90:
        print(f"  {Colors.YELLOW}⚠️  Success rate below 90% - investigate common failures{Colors.NC}")
    
    # Find most problematic workflow
    worst_workflow = max(patterns["by_workflow"].items(), 
                        key=lambda x: x[1]["failed"] if x[1]["total"] > 0 else 0)
    if worst_workflow[1]["failed"] > 2:
        print(f"  {Colors.YELLOW}⚠️  '{worst_workflow[0]}' has {worst_workflow[1]['failed']} failures{Colors.NC}")
        print(f"     Run: ./scripts/fix-ci-issues.sh")
    
    # Check for branch-specific issues
    for branch, stats in patterns["by_branch"].items():
        if stats["total"] > 5 and (stats["failed"] / stats["total"]) > 0.3:
            print(f"  {Colors.YELLOW}⚠️  Branch '{branch}' has high failure rate{Colors.NC}")
    
    print(f"\n{Colors.BLUE}{'='*60}{Colors.NC}")


def print_recent_failures(runs: List[Dict], limit: int = 5):
    """Print recent failure details."""
    failures = [r for r in runs if r.get("conclusion") == "failure"][:limit]
    
    if failures:
        print(f"\n{Colors.CYAN}🚨 Recent Failures:{Colors.NC}")
        for run in failures:
            created = datetime.fromisoformat(run["createdAt"].replace("Z", "+00:00"))
            age = datetime.now(created.tzinfo) - created
            
            print(f"\n  {Colors.YELLOW}{run['workflowName']}{Colors.NC}")
            print(f"    Branch: {run.get('headBranch', 'Unknown')}")
            print(f"    Event: {run.get('event', 'Unknown')}")
            print(f"    Age: {age.days}d {age.seconds//3600}h ago")
            print(f"    ID: {run.get('databaseId', 'Unknown')}")
            
            # Get detailed failure info
            details = get_run_details(run.get("databaseId"))
            if details and "jobs" in details:
                failed_jobs = [j for j in details["jobs"] if j.get("conclusion") == "failure"]
                if failed_jobs:
                    print(f"    Failed Jobs:")
                    for job in failed_jobs[:3]:  # Limit to 3 jobs
                        print(f"      - {job.get('name', 'Unknown')}")


def main():
    """Main function to run health check."""
    print(f"{Colors.BLUE}Fetching CI/CD pipeline data...{Colors.NC}")
    
    # Get recent runs
    runs = get_recent_runs(30)
    
    if not runs:
        print(f"{Colors.RED}No workflow runs found. Check your GitHub CLI authentication.{Colors.NC}")
        return 1
    
    # Analyze patterns
    patterns = analyze_failure_patterns(runs)
    
    # Calculate metrics
    metrics = calculate_metrics(runs)
    
    # Print reports
    print_health_report(metrics, patterns)
    print_recent_failures(runs)
    
    # Provide quick actions
    print(f"\n{Colors.CYAN}🔧 Quick Actions:{Colors.NC}")
    print("  View specific run: gh run view <run-id>")
    print("  Watch latest run: gh run watch")
    print("  Rerun failed: gh run rerun <run-id> --failed")
    print("  Check compatibility: uv run python scripts/check-compatibility.py")
    print("  Fix issues: ./scripts/fix-ci-issues.sh")
    
    # Return exit code based on health
    if metrics["success_rate"] < 75:
        return 1  # Unhealthy
    return 0  # Healthy


if __name__ == "__main__":
    sys.exit(main()) 