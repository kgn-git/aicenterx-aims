"""Run every film's shared controls test and its own test, then report. Exit code 1 if any run fails.

Usage: python tools/run_tests.py
Each film is a folder simulation/<slug>/ with one .html film; its own test, when present, is test/<slug>_test.py.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SIM = ROOT / "simulation"


def runs():
    for folder in sorted(p for p in SIM.iterdir() if p.is_dir() and not p.name.startswith("_")):
        films = sorted(folder.glob("*.html"))
        if len(films) != 1:
            yield folder.name, None
            continue
        yield f"{folder.name}: controls", [sys.executable, str(ROOT / "test" / "film_controls_test.py"), str(films[0])]
        own = ROOT / "test" / f"{folder.name}_test.py"
        if own.exists():
            yield f"{folder.name}: own test", [sys.executable, str(own)]


def main():
    failed = []
    for name, cmd in runs():
        if cmd is None:
            print(f"FAIL {name}: expected exactly one .html film")
            failed.append(name)
            continue
        code = subprocess.run(cmd, cwd=ROOT, stdout=subprocess.DEVNULL).returncode
        print(("ok   " if code == 0 else "FAIL ") + name)
        if code != 0:
            print("     rerun for the report: " + " ".join(f'"{c}"' for c in cmd))
            failed.append(name)
    print(f"{len(failed)} failed" if failed else "all passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
