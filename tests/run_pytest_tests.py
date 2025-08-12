#!/usr/bin/env python3
"""
Test runner for the DJLibrary testing suite using pytest framework.
"""

import sys
import os
import argparse
import subprocess

def run_unit_tests():
    """Run all unit tests using pytest."""
    print("Running Unit Tests with Pytest...")
    print("=" * 50)
    
    # Run the unit tests file directly
    result = subprocess.run([sys.executable, "-m", "pytest", "tests/test_library_operations.py", "-v"], 
                          cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return result.returncode == 0

def run_scenarios():
    """Run all test scenarios using pytest."""
    print("Running Test Scenarios with Pytest...")
    print("=" * 50)
    
    # Run the scenarios file directly
    result = subprocess.run([sys.executable, "-m", "pytest", "tests/test_scenarios.py", "-v", "-s"], 
                          cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return result.returncode == 0

def main():
    """Main test runner for pytest framework."""
    parser = argparse.ArgumentParser(description='Run DJLibrary tests with pytest')
    parser.add_argument('--unit', action='store_true', help='Run unit tests')
    parser.add_argument('--scenarios', action='store_true', help='Run test scenarios')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    
    args = parser.parse_args()
    
    if not any([args.unit, args.scenarios, args.all]):
        args.all = True  # Default to running all tests
    
    success = True
    
    if args.unit or args.all:
        unit_success = run_unit_tests()
        success = success and unit_success
        print()
    
    if args.scenarios or args.all:
        scenario_success = run_scenarios()
        success = success and scenario_success
        print()
    
    if success:
        print("✅ All pytest tests passed!")
        return 0
    else:
        print("❌ Some pytest tests failed!")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 