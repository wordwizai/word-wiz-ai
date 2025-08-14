#!/usr/bin/env python3
"""
Test runner script for Word Wiz AI backend tests.
Provides convenient commands for running different test suites.
"""

import subprocess
import sys
import os

def run_command(cmd):
    """Run a command and return the exit code."""
    print(f"Running: {' '.join(cmd)}")
    return subprocess.call(cmd)

def main():
    """Main test runner."""
    if len(sys.argv) < 2:
        print("Usage: python run_tests.py [all|auth|user|integration|coverage]")
        sys.exit(1)
    
    # Change to backend directory
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(backend_dir)
    
    test_type = sys.argv[1].lower()
    
    if test_type == "all":
        exit_code = run_command(["python", "-m", "pytest", "tests/", "-v"])
    elif test_type == "auth":
        exit_code = run_command(["python", "-m", "pytest", "tests/test_auth.py", "-v"])
    elif test_type == "user":
        exit_code = run_command(["python", "-m", "pytest", "tests/test_user.py", "-v"])
    elif test_type == "integration":
        exit_code = run_command(["python", "-m", "pytest", "tests/test_main.py", "-v"])
    elif test_type == "coverage":
        # Install coverage if not present
        subprocess.call(["python", "-m", "pip", "install", "pytest-cov"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        exit_code = run_command(["python", "-m", "pytest", "tests/", "--cov=.", "--cov-report=term-missing"])
    else:
        print(f"Unknown test type: {test_type}")
        print("Available options: all, auth, user, integration, coverage")
        sys.exit(1)
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()