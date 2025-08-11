#!/usr/bin/env python3
"""
Test runner script for AI Keyword Tool
Usage: python run_tests.py
"""

import subprocess
import sys
import os

def run_tests():
    """Run the test suite using pytest."""
    print("🧪 Running AI Keyword Tool Test Suite...")
    print("=" * 50)
    
    # Change to the project directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)
    
    try:
        # Run pytest with verbose output
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/", 
            "-v", 
            "--tb=short",
            "--color=yes"
        ], capture_output=False)
        
        if result.returncode == 0:
            print("\n✅ All tests passed!")
        else:
            print(f"\n❌ Tests failed with exit code {result.returncode}")
            
        return result.returncode
        
    except FileNotFoundError:
        print("❌ pytest not found. Install it with: pip install pytest")
        return 1
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1

def run_coverage():
    """Run tests with coverage reporting (optional)."""
    print("📊 Running tests with coverage...")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "tests/",
            "--cov=app",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "-v"
        ], capture_output=False)
        
        if result.returncode == 0:
            print("\n✅ Coverage report generated in htmlcov/")
        
        return result.returncode
        
    except FileNotFoundError:
        print("❌ pytest-cov not found. Install it with: pip install pytest-cov")
        return 1

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--coverage":
        exit_code = run_coverage()
    else:
        exit_code = run_tests()
    
    sys.exit(exit_code)
