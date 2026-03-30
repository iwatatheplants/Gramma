#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║  GRAMMA — Combined Launcher                             ║
║  Runs BOTH monitors simultaneously:                            ║
║    • Craigslist RSS Monitor (direct, zero-delay)               ║
║    • Swoopa Email Pipeline (Facebook Marketplace + more)       ║
╚══════════════════════════════════════════════════════════════════╝

Usage: python3 run_scout.py

This launches both scripts as parallel threads in a single process.
Ctrl+C stops both cleanly.

FULL COVERAGE:
  Craigslist  → craigslist.py (RSS, 30-second polling)
  FB Market   → swoopa.py (via Swoopa email alerts)
  OfferUp     → swoopa.py (via Swoopa email alerts)
  Nextdoor    → swoopa.py (via Swoopa email alerts)

Both send notifications to the same ntfy topic on your phone.
Both log to the same scout_data/ directory.
"""

import subprocess
import sys
import os
import signal
import time

SCRIPTS = [
    ("Craigslist Monitor", "craigslist.py"),
    ("Swoopa Pipeline", "swoopa.py"),
]

processes = []

def cleanup(sig=None, frame=None):
    print("\n🛑 Stopping all monitors...")
    for name, proc in processes:
        try:
            proc.terminate()
            proc.wait(timeout=5)
            print(f"  ✓ {name} stopped")
        except Exception:
            proc.kill()
            print(f"  ✕ {name} killed")
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

def main():
    print("\n" + "=" * 62)
    print("  ◈  GRAMMA — Combined Launch")
    print("     Running all monitors simultaneously")
    print("=" * 62)

    script_dir = os.path.dirname(os.path.abspath(__file__))

    for name, script in SCRIPTS:
        path = os.path.join(script_dir, script)
        if not os.path.exists(path):
            print(f"  ⚠️  {name}: {script} not found, skipping")
            continue
        try:
            proc = subprocess.Popen(
                [sys.executable, path],
                cwd=script_dir,
                env=os.environ.copy(),
            )
            processes.append((name, proc))
            print(f"  ✅ {name} started (PID {proc.pid})")
        except Exception as e:
            print(f"  ❌ {name} failed to start: {e}")

    if not processes:
        print("\n❌ No monitors started. Check that the scripts exist.")
        sys.exit(1)

    print(f"\n  {len(processes)} monitor(s) running. Ctrl+C to stop all.\n")

    # Wait for any process to exit
    while True:
        for name, proc in processes:
            ret = proc.poll()
            if ret is not None:
                print(f"\n⚠️  {name} exited with code {ret}. Restarting in 10s...")
                time.sleep(10)
                script = [s for n, s in SCRIPTS if n == name][0]
                path = os.path.join(script_dir, script)
                new_proc = subprocess.Popen(
                    [sys.executable, path],
                    cwd=script_dir,
                    env=os.environ.copy(),
                )
                # Replace in list
                for i, (n, p) in enumerate(processes):
                    if n == name:
                        processes[i] = (name, new_proc)
                        break
                print(f"  ✅ {name} restarted (PID {new_proc.pid})")
        time.sleep(2)

if __name__ == "__main__":
    main()
