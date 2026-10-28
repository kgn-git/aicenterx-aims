"""Checks that curated data injected into the page's <script> cannot change how the HTML around it is parsed.

Usage:  python test/inline_json_test.py

  - text that would end the script ("</script>") or open a script comment ("<!--<script>") comes out with no <, > or &
  - non-ASCII text, including the U+2028 and U+2029 line separators, comes out escaped
  - the literal still parses back to the same data
Prints a JSON report; exit code 1 on any failure.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'tools'))
from inline_json import script_literal  # noqa: E402


def main():
    hostile = {'a': '</script><script>alert(1)</script>', 'b': '<!--<script>', 'c': 'x & y > z',
               'd': 'credit‑scoring — line para end', 'n': [1, None, True]}
    out = script_literal(hostile)
    checks = {
        'no <, > or & survives': not any(ch in out for ch in '<>&'),
        'only ASCII survives': out.isascii(),
        'parses back to the same data': json.loads(out) == hostile,
    }
    failed = [k for k, ok in checks.items() if not ok]
    print(json.dumps({'passed': len(checks) - len(failed), 'failed': failed, 'literal': out}, indent=2))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
