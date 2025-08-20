# add_numbers.py
import sys
import time

def parse_args(argv):
    log_path = None
    a = None
    b = None

    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--log":
            log_path = argv[i+1]; i += 2
        elif arg == "--a":
            a = int(argv[i+1]); i += 2
        elif arg == "--b":
            b = int(argv[i+1]); i += 2
        else:
            i += 1

    if log_path is None or a is None or b is None:
        print("Missing required args: --log <path> --a <int> --b <int>")
        sys.exit(2)

    return log_path, a, b

if __name__ == "__main__":
    log_path, a, b = parse_args(sys.argv[1:])

    # Simulate some work and report progress
    for p in range(0, 101, 20):
        print(f"PROGRESS {p}")
        time.sleep(0.08)

    s = a + b
    line = f"a={a}, b={b}, sum={s}\n"

    # Append to the provided log file
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(line)

    print(f"Written to log: {log_path} -> {line.strip()}")
    print("PROGRESS 100")
    print("Done.")
