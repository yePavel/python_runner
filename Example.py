# script_a.py
import sys
import time

def parse_args(argv):
    log_path = None
    user = None
    threshold = 50
    mode = "fast"
    dry = False

    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--log":
            log_path = argv[i+1]; i += 2
        elif a == "--user":
            user = argv[i+1]; i += 2
        elif a == "--threshold":
            threshold = int(argv[i+1]); i += 2
        elif a == "--mode":
            mode = argv[i+1]; i += 2
        elif a == "--dry-run":
            dry = True; i += 1
        else:
            i += 1

    if not log_path or not user:
        print("Missing required args: --log <path>, --user <name>")
        sys.exit(2)

    return log_path, user, threshold, mode, dry


if __name__ == "__main__":
    log, user, thr, mode, dry = parse_args(sys.argv[1:])
    print(f"Processing log: {log} | user={user} thr={thr} mode={mode} dry={dry}")
    for p in range(0, 101, 5):
        print(f"PROGRESS {p}")  # the GUI reads this to update progress
        time.sleep(0.1)
    print("Done.")
