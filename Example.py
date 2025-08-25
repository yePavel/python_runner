import time
import sys

def main():
    log_path = None

    # Parse args manually (so you can test log passing)
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a in ("--log", "-l") and i+1 < len(args):
            log_path = args[i+1]

    print("=== Test Script Started ===")
    if log_path:
        print(f"Log file argument received: {log_path}")

    # Simulate work with progress updates
    for p in range(0, 101, 10):
        print(f"PROGRESS {p}%")  # GUI catches this
        print(f"Working... step {p//20+1}")
        sys.stdout.flush()
        time.sleep(0.5)

    print("=== Test Script Finished ===")

if __name__ == "__main__":
    main()