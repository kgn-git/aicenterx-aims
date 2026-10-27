"""Checks which runs tools/run_tests.py plans, without running them.

Usage:  python test/run_tests_test.py

  - every film gets the shared controls test with its own .html film, and its own test once
  - every other test/*_test.py, named here and found on disk, runs once without arguments
  - film_controls_test.py never runs without a film
Prints a JSON report; exit code 1 on any failure.
"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import run_tests  # noqa: E402

NAMED_OTHERS = ('inline_json_test.py', 'risk_suggestions_data_test.py', 'run_tests_test.py')


def main():
    runs = [cmd for _, cmd in run_tests.runs() if cmd]
    scripts = Counter(Path(cmd[1]).name for cmd in runs)
    films = sorted(p.name for p in (ROOT / 'simulation').iterdir() if p.is_dir() and not p.name.startswith('_'))
    controls = [cmd for cmd in runs if Path(cmd[1]).name == 'film_controls_test.py']
    others = sorted(p.name for p in (ROOT / 'test').glob('*_test.py')
                    if p.name != 'film_controls_test.py' and p.stem[:-len('_test')] not in films)
    checks = {
        'each film runs the shared controls test with its own .html film': len(controls) == len(films)
            and all(len(cmd) == 3 and cmd[2].endswith('.html') for cmd in controls)
            and sorted(Path(cmd[2]).parent.name for cmd in controls) == films,
        'each film with its own test runs it once': all(scripts[f'{f}_test.py'] == 1 for f in films if (ROOT / 'test' / f'{f}_test.py').exists()),
        'the named non-film tests each run once, without arguments': all(scripts[n] == 1 for n in NAMED_OTHERS)
            and all(len(cmd) == 2 for cmd in runs if Path(cmd[1]).name in NAMED_OTHERS),
        'every other test on disk runs once, without arguments': all(scripts[o] == 1 for o in others)
            and all(len(cmd) == 2 for cmd in runs if Path(cmd[1]).name in others),
    }
    failed = [k for k, ok in checks.items() if not ok]
    print(json.dumps({'passed': len(checks) - len(failed), 'failed': failed, 'others': others}, indent=2))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
