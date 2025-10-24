#!/usr/bin/env python3
"""
Test script for notifications functionality.

This script simulates different scenarios to test the notification system:
1. Successful completion (exit code 0)
2. Failure (non-zero exit code)
3. Progress updates
"""

import sys
import time
import argparse


def main():
    parser = argparse.ArgumentParser(description="Test notifications")
    parser.add_argument("--log", help="Log file path", required=False)
    parser.add_argument("--mode", help="Mode (gui or cli)", default="cli")
    parser.add_argument("--scenario", help="Test scenario", 
                       choices=["success", "failure", "error"], 
                       default="success")
    parser.add_argument("--steps", type=int, help="Number of progress steps", default=5)
    
    args = parser.parse_args()
    
    print(f"Starting notification test: {args.scenario}")
    print(f"Log file: {args.log if args.log else 'None'}")
    
    # Simulate progress
    for i in range(args.steps):
        progress = int((i + 1) / args.steps * 100)
        print(f"PROGRESS {progress}")
        time.sleep(0.5)
    
    if args.scenario == "success":
        print("Test completed successfully!")
        print("This should trigger a success notification.")
        sys.exit(0)
    
    elif args.scenario == "failure":
        print("ERROR: Test failed!")
        print("This should trigger a failure notification.")
        sys.exit(1)
    
    elif args.scenario == "error":
        print("ERROR: Simulating an error condition")
        print("Traceback: This is a fake traceback for testing")
        sys.exit(2)


if __name__ == "__main__":
    main()
