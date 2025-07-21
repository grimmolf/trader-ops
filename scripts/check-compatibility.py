#!/usr/bin/env python3
"""Check version compatibility across the TraderTerminal project."""

import subprocess
import sys
from typing import Dict, List, Tuple
import json
import re

# Version compatibility matrix
COMPATIBILITY_MATRIX = {
    "python": {
        "min": (3, 11),
        "max": (3, 12),
        "recommended": "3.11.13"
    },
    "packages": {
        "pydantic": ">=2.0.0,<3.0.0",
        "pytest-asyncio": ">=0.21.0",
        "black": ">=23.11.0",
        "ruff": ">=0.1.6",
        "mypy": ">=1.7.0",
        "fastapi": ">=0.104.0",
        "uvicorn": ">=0.24.0"
    }
}

class Colors:
    """Terminal colors for output."""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color


def check_python_version() -> Tuple[bool, str, str]:
    """Check if Python version is compatible."""
    python_version = sys.version_info
    min_version = COMPATIBILITY_MATRIX["python"]["min"]
    max_version = COMPATIBILITY_MATRIX["python"]["max"]
    recommended = COMPATIBILITY_MATRIX["python"]["recommended"]
    
    version_str = f"{python_version.major}.{python_version.minor}.{python_version.micro}"
    
    if min_version <= python_version[:2] <= max_version:
        if version_str == recommended:
            return True, version_str, "✅ Recommended version"
        else:
            return True, version_str, f"⚠️  Works but {recommended} recommended"
    else:
        return False, version_str, f"❌ Need Python {min_version[0]}.{min_version[1]}-{max_version[0]}.{max_version[1]}"


def get_package_version(package: str) -> str:
    """Get installed package version."""
    try:
        result = subprocess.run(
            ["uv", "pip", "show", package],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line.startswith('Version:'):
                    return line.split(':')[1].strip()
    except Exception:
        pass
    return "Not installed"


def check_package_compatibility(package: str, constraint: str) -> Tuple[bool, str, str]:
    """Check if package version meets constraint."""
    version = get_package_version(package)
    
    if version == "Not installed":
        return False, version, f"❌ Required: {constraint}"
    
    # Simple version checking (could be enhanced with packaging library)
    if ">=" in constraint:
        min_version = constraint.split(">=")[1].split(",")[0]
        if version >= min_version:
            return True, version, f"✅ Meets {constraint}"
        else:
            return False, version, f"❌ Need {constraint}"
    
    return True, version, f"✅ Version {version}"


def check_deprecated_syntax() -> List[Tuple[str, bool, str]]:
    """Check for deprecated syntax patterns."""
    results = []
    
    # Check for Pydantic v1 syntax
    try:
        result = subprocess.run(
            ["grep", "-r", "@validator\\|class Config:", "src/", "--include=*.py"],
            capture_output=True,
            text=True
        )
        pydantic_v1_found = result.returncode == 0
        if pydantic_v1_found:
            results.append(("Pydantic v1 syntax", False, "❌ Found - run fix-ci-issues.sh"))
        else:
            results.append(("Pydantic v1 syntax", True, "✅ None found"))
    except Exception:
        results.append(("Pydantic v1 syntax", True, "⚠️  Could not check"))
    
    # Check for old pytest-asyncio syntax
    try:
        result = subprocess.run(
            ["grep", "-r", "@pytest_asyncio\\.async_test", "tests/", "--include=*.py"],
            capture_output=True,
            text=True
        )
        old_pytest_found = result.returncode == 0
        if old_pytest_found:
            results.append(("pytest-asyncio syntax", False, "❌ Old syntax - run fix-ci-issues.sh"))
        else:
            results.append(("pytest-asyncio syntax", True, "✅ Using modern syntax"))
    except Exception:
        results.append(("pytest-asyncio syntax", True, "⚠️  Could not check"))
    
    return results


def check_ci_config() -> List[Tuple[str, bool, str]]:
    """Check CI/CD configuration compatibility."""
    results = []
    
    # Check if .python-version file exists
    try:
        with open(".python-version", "r") as f:
            py_version = f.read().strip()
            if py_version.startswith("3.11"):
                results.append((".python-version", True, f"✅ {py_version}"))
            else:
                results.append((".python-version", False, f"❌ {py_version} (need 3.11.x)"))
    except FileNotFoundError:
        results.append((".python-version", False, "❌ Missing - create with '3.11.13'"))
    
    # Check if pre-commit config exists
    try:
        with open(".pre-commit-config.yaml", "r") as f:
            content = f.read()
            if "python3.11" in content:
                results.append(("pre-commit config", True, "✅ Python 3.11 configured"))
            else:
                results.append(("pre-commit config", False, "⚠️  Python version not specified"))
    except FileNotFoundError:
        results.append(("pre-commit config", False, "❌ Missing - run setup-dev-environment.sh"))
    
    return results


def main():
    """Run all compatibility checks."""
    print(f"{Colors.BLUE}🔍 TraderTerminal Compatibility Check{Colors.NC}")
    print("=" * 50)
    
    all_results = []
    
    # Check Python version
    print(f"\n{Colors.YELLOW}Python Version:{Colors.NC}")
    ok, version, message = check_python_version()
    all_results.append(("Python", ok, f"{version} - {message}"))
    print(f"  {message}")
    
    # Check package versions
    print(f"\n{Colors.YELLOW}Package Versions:{Colors.NC}")
    for package, constraint in COMPATIBILITY_MATRIX["packages"].items():
        ok, version, message = check_package_compatibility(package, constraint)
        all_results.append((package, ok, f"{version} - {message}"))
        print(f"  {package}: {message}")
    
    # Check for deprecated syntax
    print(f"\n{Colors.YELLOW}Code Syntax:{Colors.NC}")
    for name, ok, message in check_deprecated_syntax():
        all_results.append((name, ok, message))
        print(f"  {name}: {message}")
    
    # Check CI configuration
    print(f"\n{Colors.YELLOW}CI/CD Configuration:{Colors.NC}")
    for name, ok, message in check_ci_config():
        all_results.append((name, ok, message))
        print(f"  {name}: {message}")
    
    # Summary
    failed = sum(1 for _, ok, _ in all_results if not ok)
    total = len(all_results)
    
    print(f"\n{Colors.BLUE}Summary:{Colors.NC}")
    if failed == 0:
        print(f"{Colors.GREEN}✅ All {total} checks passed!{Colors.NC}")
        return 0
    else:
        print(f"{Colors.RED}❌ {failed}/{total} checks failed{Colors.NC}")
        print(f"\n{Colors.YELLOW}To fix issues:{Colors.NC}")
        print("1. Run './scripts/fix-ci-issues.sh' for syntax issues")
        print("2. Run './scripts/setup-dev-environment.sh' for environment setup")
        print("3. Check the CI/CD fixes PRP for detailed solutions")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 