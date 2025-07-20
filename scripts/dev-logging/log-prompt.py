#!/usr/bin/env python3
"""
Development Logging System - Interactive Log Prompt
Captures detailed development information for reproducibility
"""

import os
import sys
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

class DevLogger:
    """Interactive development logger with structured prompts"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.log_dir = self.project_root / "docs" / "development-logs"
        self.templates_dir = self.project_root / "scripts" / "dev-logging" / "templates"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
    def get_git_info(self) -> Dict[str, str]:
        """Extract current git information"""
        try:
            # Get current branch
            branch = subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"], 
                cwd=self.project_root, text=True
            ).strip()
            
            # Get current commit hash
            commit_hash = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], 
                cwd=self.project_root, text=True
            ).strip()[:8]
            
            # Get staged files
            staged_files = subprocess.check_output(
                ["git", "diff", "--cached", "--name-only"], 
                cwd=self.project_root, text=True
            ).strip().split('\n') if subprocess.check_output(
                ["git", "diff", "--cached", "--name-only"], 
                cwd=self.project_root, text=True
            ).strip() else []
            
            # Get modified files
            modified_files = subprocess.check_output(
                ["git", "diff", "--name-only"], 
                cwd=self.project_root, text=True
            ).strip().split('\n') if subprocess.check_output(
                ["git", "diff", "--name-only"], 
                cwd=self.project_root, text=True
            ).strip() else []
            
            return {
                "branch": branch,
                "commit_hash": commit_hash,
                "staged_files": staged_files,
                "modified_files": modified_files
            }
        except subprocess.CalledProcessError:
            return {
                "branch": "unknown",
                "commit_hash": "unknown", 
                "staged_files": [],
                "modified_files": []
            }
    
    def prompt_user(self, question: str, multiline: bool = False, required: bool = True) -> str:
        """Prompt user for input with validation"""
        while True:
            if multiline:
                print(f"\n{question}")
                print("(Enter 'END' on a new line to finish, or press Ctrl+D)")
                lines = []
                try:
                    while True:
                        line = input()
                        if line.strip() == 'END':
                            break
                        lines.append(line)
                except EOFError:
                    pass
                response = '\n'.join(lines).strip()
            else:
                response = input(f"{question}: ").strip()
            
            if response or not required:
                return response
            print("This field is required. Please provide a response.")
    
    def get_development_context(self) -> Dict:
        """Gather comprehensive development context"""
        print("\n" + "="*80)
        print("🔄 DEVELOPMENT LOG CAPTURE")
        print("="*80)
        print("Capturing detailed development information for reproducibility...")
        
        git_info = self.get_git_info()
        
        context = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "git_info": git_info,
            "session_info": {}
        }
        
        # Development Session Context
        print(f"\n📋 SESSION CONTEXT")
        print(f"Branch: {git_info['branch']}")
        print(f"Commit: {git_info['commit_hash']}")
        if git_info['staged_files']:
            print(f"Staged files: {', '.join(git_info['staged_files'])}")
        if git_info['modified_files']:
            print(f"Modified files: {', '.join(git_info['modified_files'])}")
        
        context["session_info"]["objective"] = self.prompt_user(
            "\n🎯 What is the primary objective of this development session?"
        )
        
        context["session_info"]["context"] = self.prompt_user(
            "🔍 What context or background led to this work? (prior issues, requirements, etc.)",
            multiline=True
        )
        
        # Technical Implementation Details
        print(f"\n🔧 TECHNICAL IMPLEMENTATION")
        
        context["technical"] = {
            "approach": self.prompt_user(
                "📐 Describe your technical approach and methodology", 
                multiline=True
            ),
            "decisions": self.prompt_user(
                "🤔 What key technical decisions were made and why?", 
                multiline=True
            ),
            "challenges": self.prompt_user(
                "⚠️ What challenges or obstacles were encountered?", 
                multiline=True, 
                required=False
            ),
            "solutions": self.prompt_user(
                "💡 How were challenges resolved? Include failed attempts.", 
                multiline=True, 
                required=False
            )
        }
        
        # Implementation Specifics
        print(f"\n⚙️ IMPLEMENTATION SPECIFICS")
        
        context["implementation"] = {
            "files_changed": self.prompt_user(
                "📝 Which specific files were modified and what changes were made?", 
                multiline=True
            ),
            "dependencies": self.prompt_user(
                "📦 Were any new dependencies added or removed? Why?", 
                multiline=True, 
                required=False
            ),
            "configuration": self.prompt_user(
                "⚙️ Were configuration changes made? What and why?", 
                multiline=True, 
                required=False
            ),
            "testing": self.prompt_user(
                "🧪 What testing was performed? Include manual and automated tests.", 
                multiline=True
            )
        }
        
        # Quality and Performance
        print(f"\n📊 QUALITY & PERFORMANCE")
        
        context["quality"] = {
            "validation": self.prompt_user(
                "✅ How was the implementation validated? (builds, tests, manual verification)", 
                multiline=True
            ),
            "performance": self.prompt_user(
                "🚀 Any performance considerations or optimizations?", 
                multiline=True, 
                required=False
            ),
            "security": self.prompt_user(
                "🔒 Security implications or considerations?", 
                multiline=True, 
                required=False
            ),
            "edge_cases": self.prompt_user(
                "🎯 Edge cases considered or encountered?", 
                multiline=True, 
                required=False
            )
        }
        
        # Future Implications
        print(f"\n🔮 FUTURE IMPLICATIONS")
        
        context["future"] = {
            "implications": self.prompt_user(
                "🔗 How does this change affect the overall system architecture?", 
                multiline=True, 
                required=False
            ),
            "follow_up": self.prompt_user(
                "📋 Any follow-up work required or recommended?", 
                multiline=True, 
                required=False
            ),
            "documentation": self.prompt_user(
                "📚 Documentation updates needed?", 
                multiline=True, 
                required=False
            ),
            "deployment": self.prompt_user(
                "🚀 Any deployment or environment considerations?", 
                multiline=True, 
                required=False
            )
        }
        
        # Reproducibility Information
        print(f"\n🔄 REPRODUCIBILITY")
        
        context["reproducibility"] = {
            "environment": self.prompt_user(
                "💻 Describe the development environment (OS, tools, versions)", 
                multiline=True
            ),
            "prerequisites": self.prompt_user(
                "📋 What prerequisites or setup steps are needed to reproduce this work?", 
                multiline=True
            ),
            "commands": self.prompt_user(
                "⚡ List the exact commands/steps used in this session", 
                multiline=True
            ),
            "resources": self.prompt_user(
                "📖 Any external resources, documentation, or references used?", 
                multiline=True, 
                required=False
            )
        }
        
        return context
    
    def save_log(self, context: Dict) -> Path:
        """Save development log with structured naming"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        branch = context["git_info"]["branch"].replace("/", "_")
        commit = context["git_info"]["commit_hash"]
        
        # Create descriptive filename
        objective_slug = context["session_info"]["objective"][:50].lower()
        objective_slug = "".join(c if c.isalnum() else "_" for c in objective_slug).strip("_")
        
        filename = f"{timestamp}_{branch}_{commit}_{objective_slug}.json"
        filepath = self.log_dir / filename
        
        # Save detailed JSON log
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(context, f, indent=2, ensure_ascii=False)
        
        # Also create a markdown summary
        md_filepath = filepath.with_suffix('.md')
        self.create_markdown_summary(context, md_filepath)
        
        return filepath
    
    def create_markdown_summary(self, context: Dict, filepath: Path):
        """Create human-readable markdown summary"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# Development Log - {context['session_info']['objective']}\n\n")
            f.write(f"**Date**: {context['timestamp']}\n")
            f.write(f"**Branch**: {context['git_info']['branch']}\n")
            f.write(f"**Commit**: {context['git_info']['commit_hash']}\n\n")
            
            if context['git_info']['staged_files']:
                f.write(f"**Staged Files**: {', '.join(context['git_info']['staged_files'])}\n\n")
            
            f.write("## Session Context\n\n")
            f.write(f"**Objective**: {context['session_info']['objective']}\n\n")
            f.write(f"**Background**: {context['session_info']['context']}\n\n")
            
            f.write("## Technical Implementation\n\n")
            f.write(f"**Approach**: {context['technical']['approach']}\n\n")
            f.write(f"**Key Decisions**: {context['technical']['decisions']}\n\n")
            
            if context['technical']['challenges']:
                f.write(f"**Challenges**: {context['technical']['challenges']}\n\n")
            if context['technical']['solutions']:
                f.write(f"**Solutions**: {context['technical']['solutions']}\n\n")
            
            f.write("## Implementation Details\n\n")
            f.write(f"**Files Changed**: {context['implementation']['files_changed']}\n\n")
            f.write(f"**Testing**: {context['implementation']['testing']}\n\n")
            
            if context['implementation']['dependencies']:
                f.write(f"**Dependencies**: {context['implementation']['dependencies']}\n\n")
            if context['implementation']['configuration']:
                f.write(f"**Configuration**: {context['implementation']['configuration']}\n\n")
            
            f.write("## Quality & Validation\n\n")
            f.write(f"**Validation**: {context['quality']['validation']}\n\n")
            
            if context['quality']['performance']:
                f.write(f"**Performance**: {context['quality']['performance']}\n\n")
            if context['quality']['security']:
                f.write(f"**Security**: {context['quality']['security']}\n\n")
            if context['quality']['edge_cases']:
                f.write(f"**Edge Cases**: {context['quality']['edge_cases']}\n\n")
            
            f.write("## Reproducibility\n\n")
            f.write(f"**Environment**: {context['reproducibility']['environment']}\n\n")
            f.write(f"**Prerequisites**: {context['reproducibility']['prerequisites']}\n\n")
            f.write(f"**Commands**: \n```bash\n{context['reproducibility']['commands']}\n```\n\n")
            
            if context['reproducibility']['resources']:
                f.write(f"**Resources**: {context['reproducibility']['resources']}\n\n")
            
            if any(context['future'].values()):
                f.write("## Future Considerations\n\n")
                if context['future']['implications']:
                    f.write(f"**Architecture Impact**: {context['future']['implications']}\n\n")
                if context['future']['follow_up']:
                    f.write(f"**Follow-up Work**: {context['future']['follow_up']}\n\n")
                if context['future']['documentation']:
                    f.write(f"**Documentation**: {context['future']['documentation']}\n\n")
                if context['future']['deployment']:
                    f.write(f"**Deployment**: {context['future']['deployment']}\n\n")

def main():
    """Main entry point for development logging"""
    if len(sys.argv) > 1 and sys.argv[1] == "--skip":
        print("Development logging skipped.")
        sys.exit(0)
    
    logger = DevLogger()
    
    try:
        context = logger.get_development_context()
        filepath = logger.save_log(context)
        
        print(f"\n✅ Development log saved to:")
        print(f"   📄 {filepath}")
        print(f"   📝 {filepath.with_suffix('.md')}")
        print(f"\n🔍 You can review the log before committing.")
        
        # Ask if they want to add the log to the commit
        add_to_commit = input("\nAdd development log to this commit? (y/N): ").strip().lower()
        if add_to_commit == 'y':
            subprocess.run(["git", "add", str(filepath), str(filepath.with_suffix('.md'))], 
                         cwd=logger.project_root)
            print("✅ Development log added to commit.")
        
    except KeyboardInterrupt:
        print("\n❌ Development logging cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during logging: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()