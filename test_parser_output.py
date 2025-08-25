import sys
import time
import argparse
import random
import traceback

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def main():
    ap = argparse.ArgumentParser(description="Emit logs for GUI parser testing")
    ap.add_argument("--steps", type=int, default=10, help="How many progress updates")
    ap.add_argument("--delay", type=float, default=0.25, help="Delay between lines (sec)")
    ap.add_argument("--fail", action="store_true", help="Emit a real traceback at the end")
    ap.add_argument("--stderr", action="store_true", help="Also emit some lines to stderr")
    ap.add_argument("--mode", default="cli")  # harmless for your GUI
    ap.add_argument("--log", default="")      # harmless, if your GUI passes --log
    args = ap.parse_args()

    print("=== Parser Test: START ===", flush=True)
    if args.log:
        print(f"[info] Received --log: {args.log}", flush=True)
    print("[info] This test will include: normal, PROGRESS, error, traceback", flush=True)
    if args.stderr:
        eprint("[stderr] merged-channel test is ON")

    # Emit a couple of 'error' variants (case-insensitive test)
    samples = [
        "small error happened (lowercase error)",
        "Minor issue, not an Error but close",
        "no problem here",
        "TRACEBACK keyword appears alone",
        "ok line",
    ]

    # progress loop
    for i in range(args.steps + 1):
        pct = int(round(i * (100 / args.steps)))
        # 1) progress line that your GUI catches
        print(f"PROGRESS {pct}", flush=True)

        # 2) a normal/info line
        print(f"[info] working step {i}/{args.steps}", flush=True)

        # 3) occasionally inject interesting lines
        msg = random.choice(samples)
        print(msg, flush=True)

        # 4) sometimes write to stderr
        if args.stderr and i % 3 == 1:
            eprint(f"[stderr] warning at step {i}")

        time.sleep(args.delay)

    # Emit a clean “error” line right before finish
    print("ERROR: something went wrong but recovered", flush=True)

    # Optional real traceback block to test multi-line highlight
    if args.fail:
        print("\nSimulating exception with traceback...\n", flush=True)
        try:
            1 / 0
        except Exception:
            # real Python traceback text
            tb = traceback.format_exc()
            # Print a canonical header your highlighter likely looks for:
            print("Traceback (most recent call last):", flush=True)
            # Then the full formatted traceback
            for line in tb.strip().splitlines()[1:]:
                print(line, flush=True)

    print("=== Parser Test: END ===", flush=True)

if __name__ == "__main__":
    main()
