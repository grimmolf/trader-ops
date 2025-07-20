#!/usr/bin/env python3
"""
Development Log Management Script
Provides utilities for organizing, searching, and analyzing development logs
"""

import json
import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import shutil

class LogManager:
    """Manage and analyze development logs"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.log_dir = self.project_root / "docs" / "development-logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def list_logs(self, limit: int = 20, pattern: str = None) -> List[Path]:
        """List development logs with optional filtering"""
        if pattern:
            logs = list(self.log_dir.glob(f"**/*{pattern}*.json"))
        else:
            logs = list(self.log_dir.glob("**/*.json"))
        
        # Sort by modification time (newest first)
        logs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return logs[:limit]
    
    def search_logs(self, query: str, field: str = None) -> List[Dict[str, Any]]:
        """Search logs for specific content"""
        results = []
        
        for log_file in self.log_dir.glob("**/*.json"):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    log_data = json.load(f)
                
                # Search in specific field or entire log
                if field:
                    search_text = str(log_data.get(field, "")).lower()
                else:
                    search_text = json.dumps(log_data).lower()
                
                if query.lower() in search_text:
                    results.append({
                        "file": log_file,
                        "timestamp": log_data.get("timestamp"),
                        "objective": log_data.get("session_info", {}).get("objective", ""),
                        "branch": log_data.get("git_info", {}).get("branch", ""),
                        "commit": log_data.get("git_info", {}).get("commit_hash", "")
                    })
            except (json.JSONDecodeError, FileNotFoundError):
                continue
        
        # Sort by timestamp (newest first)
        results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return results
    
    def organize_logs(self, dry_run: bool = True):
        """Organize logs by date and feature"""
        organized = 0
        
        for log_file in self.log_dir.glob("*.json"):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    log_data = json.load(f)
                
                # Extract date from timestamp
                timestamp = log_data.get("timestamp", "")
                if timestamp:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    year_month = dt.strftime("%Y/%m-%B").lower()
                    date_dir = self.log_dir / year_month
                    
                    # Create date-based organization
                    if not dry_run:
                        date_dir.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(log_file), str(date_dir / log_file.name))
                        shutil.move(str(log_file.with_suffix('.md')), 
                                  str(date_dir / log_file.with_suffix('.md').name))
                    
                    organized += 1
                    print(f"{'Would move' if dry_run else 'Moved'}: {log_file.name} -> {year_month}/")
                
            except (json.JSONDecodeError, FileNotFoundError, ValueError):
                continue
        
        print(f"\n{'Would organize' if dry_run else 'Organized'} {organized} log files")
        if dry_run:
            print("Run with --execute to actually move files")
    
    def create_index(self):
        """Create searchable index of all logs"""
        index_data = {
            "generated": datetime.now().isoformat(),
            "total_logs": 0,
            "logs": []
        }
        
        for log_file in self.log_dir.glob("**/*.json"):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    log_data = json.load(f)
                
                index_entry = {
                    "filename": log_file.name,
                    "path": str(log_file.relative_to(self.project_root)),
                    "timestamp": log_data.get("timestamp"),
                    "objective": log_data.get("session_info", {}).get("objective", ""),
                    "git_info": log_data.get("git_info", {}),
                    "files_changed": log_data.get("implementation", {}).get("files_changed", ""),
                    "tags": self._extract_tags(log_data)
                }
                
                index_data["logs"].append(index_entry)
                index_data["total_logs"] += 1
                
            except (json.JSONDecodeError, FileNotFoundError):
                continue
        
        # Sort by timestamp
        index_data["logs"].sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # Save index
        index_file = self.log_dir / "index.json"
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False)
        
        # Create markdown index
        self._create_markdown_index(index_data)
        
        print(f"✅ Created index with {index_data['total_logs']} logs")
        print(f"   📄 {index_file}")
        print(f"   📝 {index_file.with_suffix('.md')}")
    
    def _extract_tags(self, log_data: Dict[str, Any]) -> List[str]:
        """Extract tags from log data for categorization"""
        tags = []
        
        # Add git branch as tag
        branch = log_data.get("git_info", {}).get("branch", "")
        if branch and branch != "main":
            tags.append(f"branch:{branch}")
        
        # Add objective-based tags
        objective = log_data.get("session_info", {}).get("objective", "").lower()
        if "bug" in objective or "fix" in objective:
            tags.append("bugfix")
        elif "feature" in objective or "implement" in objective:
            tags.append("feature")
        elif "refactor" in objective or "improve" in objective:
            tags.append("refactor")
        elif "test" in objective:
            tags.append("testing")
        
        # Add technology tags
        tech_keywords = {
            "react": "react", "vue": "vue", "typescript": "typescript",
            "python": "python", "fastapi": "fastapi", "electron": "electron",
            "websocket": "websocket", "tradingview": "tradingview",
            "database": "database", "api": "api", "performance": "performance",
            "security": "security"
        }
        
        full_text = json.dumps(log_data).lower()
        for keyword, tag in tech_keywords.items():
            if keyword in full_text:
                tags.append(tag)
        
        return list(set(tags))  # Remove duplicates
    
    def _create_markdown_index(self, index_data: Dict[str, Any]):
        """Create human-readable markdown index"""
        index_file = self.log_dir / "index.md"
        
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write("# Development Logs Index\n\n")
            f.write(f"**Generated**: {index_data['generated']}\n")
            f.write(f"**Total Logs**: {index_data['total_logs']}\n\n")
            
            # Group by month
            monthly_logs = {}
            for log in index_data["logs"]:
                if log["timestamp"]:
                    dt = datetime.fromisoformat(log["timestamp"].replace('Z', '+00:00'))
                    month_key = dt.strftime("%Y-%m")
                    if month_key not in monthly_logs:
                        monthly_logs[month_key] = []
                    monthly_logs[month_key].append(log)
            
            # Write monthly sections
            for month in sorted(monthly_logs.keys(), reverse=True):
                f.write(f"## {month}\n\n")
                
                for log in monthly_logs[month]:
                    dt = datetime.fromisoformat(log["timestamp"].replace('Z', '+00:00'))
                    date_str = dt.strftime("%m/%d")
                    
                    f.write(f"### {date_str} - {log['objective']}\n")
                    f.write(f"**File**: [{log['filename']}]({log['path']})\n")
                    f.write(f"**Branch**: `{log['git_info'].get('branch', 'unknown')}`\n")
                    f.write(f"**Commit**: `{log['git_info'].get('commit_hash', 'unknown')}`\n")
                    
                    if log.get("tags"):
                        f.write(f"**Tags**: {', '.join(f'`{tag}`' for tag in log['tags'])}\n")
                    
                    if log.get("files_changed"):
                        # Truncate long file lists
                        files_text = log["files_changed"][:200] + "..." if len(log["files_changed"]) > 200 else log["files_changed"]
                        f.write(f"**Files**: {files_text}\n")
                    
                    f.write("\n")
    
    def stats(self):
        """Show statistics about development logs"""
        logs = list(self.log_dir.glob("**/*.json"))
        
        if not logs:
            print("No development logs found.")
            return
        
        # Basic stats
        print(f"📊 Development Log Statistics")
        print(f"=" * 40)
        print(f"Total logs: {len(logs)}")
        
        # Analyze by time period
        dates = []
        branches = []
        objectives = []
        
        for log_file in logs:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    log_data = json.load(f)
                
                timestamp = log_data.get("timestamp")
                if timestamp:
                    dates.append(datetime.fromisoformat(timestamp.replace('Z', '+00:00')))
                
                branch = log_data.get("git_info", {}).get("branch", "")
                if branch:
                    branches.append(branch)
                
                objective = log_data.get("session_info", {}).get("objective", "")
                if objective:
                    objectives.append(objective)
                    
            except (json.JSONDecodeError, FileNotFoundError, ValueError):
                continue
        
        # Time range
        if dates:
            dates.sort()
            print(f"Date range: {dates[0].strftime('%Y-%m-%d')} to {dates[-1].strftime('%Y-%m-%d')}")
            
            # Logs per month
            monthly_counts = {}
            for date in dates:
                month_key = date.strftime("%Y-%m")
                monthly_counts[month_key] = monthly_counts.get(month_key, 0) + 1
            
            print(f"Most active month: {max(monthly_counts, key=monthly_counts.get)} ({max(monthly_counts.values())} logs)")
        
        # Branch activity
        if branches:
            branch_counts = {}
            for branch in branches:
                branch_counts[branch] = branch_counts.get(branch, 0) + 1
            
            print(f"Most active branch: {max(branch_counts, key=branch_counts.get)} ({max(branch_counts.values())} logs)")
            print(f"Unique branches: {len(set(branches))}")
        
        # Development patterns
        feature_logs = sum(1 for obj in objectives if any(word in obj.lower() for word in ["feature", "implement", "add"]))
        bug_logs = sum(1 for obj in objectives if any(word in obj.lower() for word in ["bug", "fix", "error"]))
        refactor_logs = sum(1 for obj in objectives if any(word in obj.lower() for word in ["refactor", "improve", "optimize"]))
        
        print(f"\nDevelopment patterns:")
        print(f"  Features: {feature_logs}")
        print(f"  Bug fixes: {bug_logs}")
        print(f"  Refactoring: {refactor_logs}")
        print(f"  Other: {len(objectives) - feature_logs - bug_logs - refactor_logs}")

def main():
    parser = argparse.ArgumentParser(description="Manage development logs")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List development logs')
    list_parser.add_argument('--limit', type=int, default=20, help='Maximum number of logs to show')
    list_parser.add_argument('--pattern', help='Filter logs by filename pattern')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search logs for content')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('--field', help='Search in specific field only')
    
    # Organize command
    org_parser = subparsers.add_parser('organize', help='Organize logs by date and feature')
    org_parser.add_argument('--execute', action='store_true', help='Actually move files (default is dry run)')
    
    # Index command
    subparsers.add_parser('index', help='Create searchable index of logs')
    
    # Stats command
    subparsers.add_parser('stats', help='Show development log statistics')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = LogManager()
    
    if args.command == 'list':
        logs = manager.list_logs(args.limit, args.pattern)
        if not logs:
            print("No logs found.")
            return
        
        print(f"📋 Found {len(logs)} development logs:")
        for log_file in logs:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    log_data = json.load(f)
                
                timestamp = log_data.get("timestamp", "")
                objective = log_data.get("session_info", {}).get("objective", "")
                branch = log_data.get("git_info", {}).get("branch", "")
                
                if timestamp:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    date_str = dt.strftime("%m/%d %H:%M")
                else:
                    date_str = "unknown"
                
                print(f"  {date_str} [{branch:15}] {objective}")
                
            except (json.JSONDecodeError, FileNotFoundError, ValueError):
                print(f"  [ERROR] {log_file.name}")
    
    elif args.command == 'search':
        results = manager.search_logs(args.query, args.field)
        if not results:
            print(f"No logs found matching '{args.query}'")
            return
        
        print(f"🔍 Found {len(results)} logs matching '{args.query}':")
        for result in results:
            timestamp = result.get("timestamp", "")
            if timestamp:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                date_str = dt.strftime("%m/%d %H:%M")
            else:
                date_str = "unknown"
            
            print(f"  {date_str} [{result['branch']:15}] {result['objective']}")
            print(f"    📄 {result['file'].name}")
    
    elif args.command == 'organize':
        manager.organize_logs(dry_run=not args.execute)
    
    elif args.command == 'index':
        manager.create_index()
    
    elif args.command == 'stats':
        manager.stats()

if __name__ == "__main__":
    main()