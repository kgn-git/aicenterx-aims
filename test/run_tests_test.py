"""Checks which runs tools/run_tests.py plans, without running them (issue #14, AC5).

Usage:  python test/run_tests_test.py

  - every film still gets its shared controls test, with its film, and its own test
  - every other test/*_test.py runs once, on its own, without a film
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

runs = list(run_tests.runs())
scripts = Counter(Path(cmd[1]).name for _, cmd in runs if cmd)
films = sorted(p.name for p in (ROOT / 'simulation').iterdir() if p.is_dir() and not p.name.startswith('_'))
others = sorted(p.name for p in (ROOT / 'test').glob('*_test.py')
                if p.name != 'film_controls_test.py' and p.stem[:-len('_test')] not in films)

checks = {
    'every film runs the shared controls test with its film': scripts['film_controls_test.py'] == len(films)
        and all(len(cmd) == 3 for _, cmd in runs if cmd and Path(cmd[1]).name == 'film_controls_test.py'),
    'every film with its own test runs it once': all(scripts[f'{f}_test.py'] == 1 for f in films if (ROOT / 'test' / f'{f}_test.py').exists()),
    'every other test runs once, without arguments': others != [] and all(scripts[o] == 1 for o in others)
        and all(len(cmd) == 2 for _, cmd in runs if cmd and Path(cmd[1]).name in others),
    'this test is among the others': 'run_tests_test.py' in others,
}
failed = [k for k, ok in checks.items() if not ok]
print(json.dumps({'passed': len(checks) - len(failed), 'failed': failed, 'others': others, 'planned': [n for n, _ in runs]}, indent=2))
sys.exit(1 if failed else 0)
