"""Static test for the marketing video's Remotion project in video/.

Usage:  python test/marketing_video_project_test.py

npm run check must pass on a clone where `npm --prefix video ci` was never run, so this reads the project's files as
text and never calls into video/node_modules. Checks:
  - video/package.json pins every dependency, devDependency and override to an exact x.y.z version, includes remotion,
    @remotion/cli, react, react-dom and typescript, and sets engines.node to >=22.9
  - video/package-lock.json exists and locks the same versions
  - video/src/theme.ts holds each named token with the value it has in index.html's midnight-executive block, and its
    two font stacks appear word for word in index.html
  - the bundled font files and their OFL licences exist under video/public/fonts/
  - video/src/compositions.json maps exactly the timeline's fragment ids to composition ids <fragment id>-<slug>
  - the root package.json runs video:studio and video:render:fragment through npm --prefix video, and .gitignore
    keeps video/out/ out of git
Prints a JSON report; exit code 1 on any failure.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VIDEO = ROOT / 'video'
REQUIRED = ('remotion', '@remotion/cli', 'react', 'react-dom', 'typescript')
TOKENS = ('--bg-base', '--bg-g1', '--surface', '--surface-2', '--border', '--ink', '--ink-muted',
          '--gov', '--val', '--arch', '--rag-low', '--rag-medium', '--rag-high')
FONTS = ('Fraunces-Variable.ttf', 'Fraunces-OFL.txt', 'IBMPlexSans-Variable.ttf', 'IBMPlexSans-OFL.txt')
EXACT = re.compile(r'\d+\.\d+\.\d+')


def camel(token):
    """'--bg-base' -> 'bgBase', the key theme.ts uses for a CSS token."""
    head, *rest = token.lstrip('-').split('-')
    return head + ''.join(p.capitalize() for p in rest)


def index_tokens(html):
    """{token: value} from the first theme block, which is the default midnight-executive theme."""
    block = re.search(r":root, \[data-theme='midnight-executive'\] \{(.*?)\}", html, re.S)
    return dict(re.findall(r'(--[a-z0-9-]+):([^;]+);', block.group(1))) if block else {}


def ts_string(ts, name):
    """The double-quoted or backtick value of `name: '...'` or `const name = "..."` in theme.ts, else None."""
    m = re.search(rf'\b{re.escape(name)}\s*[:=]\s*(?:"((?:[^"\\]|\\.)*)"|`([^`]*)`)', ts)
    return (m.group(1) if m.group(1) is not None else m.group(2)) if m else None


def main():
    checks = {}

    def check(name, ok, detail=''):
        checks[name] = {'ok': bool(ok), 'detail': detail if isinstance(detail, str) else json.dumps(detail)[:1500]}

    def load(p):
        try:
            return json.loads(p.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            return None

    pkg = load(VIDEO / 'package.json')
    check('video/package.json exists and parses', pkg is not None)
    if pkg is not None:
        deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {}), **pkg.get('overrides', {})}
        loose = {k: v for k, v in deps.items() if not EXACT.fullmatch(str(v))}
        check('every dependency is pinned to an exact version', deps and not loose, loose or sorted(deps))
        check('the required packages are dependencies', set(REQUIRED) <= set(deps), sorted(set(REQUIRED) - set(deps)))
        check('engines.node is >=22.9', pkg.get('engines', {}).get('node') == '>=22.9', str(pkg.get('engines')))
        lock = load(VIDEO / 'package-lock.json')
        locked = {k: (lock or {}).get('packages', {}).get(f'node_modules/{k}', {}).get('version') for k in deps}
        drift = {k: [deps[k], v] for k, v in locked.items() if v != deps[k]}
        check('video/package-lock.json locks the same versions', lock is not None and not drift, drift or 'match')

    html = (ROOT / 'index.html').read_text(encoding='utf-8')
    want = index_tokens(html)
    try:
        ts = (VIDEO / 'src' / 'theme.ts').read_text(encoding='utf-8')
    except OSError:
        ts = None
    check('video/src/theme.ts exists', ts is not None)
    if ts is not None:
        wrong = {t: [ts_string(ts, camel(t)), want.get(t)] for t in TOKENS
                 if want.get(t) is None or ts_string(ts, camel(t)) != want[t]}
        check("each token equals index.html's midnight-executive value", not wrong, wrong or 'match')
        stacks = {n: ts_string(ts, n) for n in ('headingFont', 'bodyFont')}
        check('both font stacks appear word for word in index.html',
              all(s and s in html for s in stacks.values()), stacks)

    missing = [f for f in FONTS if not (VIDEO / 'public' / 'fonts' / f).is_file()]
    check('the font files and their licences exist', not missing, missing or 'all present')

    timeline, comps = load(VIDEO / 'src' / 'timeline.json'), load(VIDEO / 'src' / 'compositions.json')
    ids = [f['id'] for f in (timeline or {}).get('fragments', [])]
    check("compositions.json maps exactly the timeline's fragments to <id>-<slug>",
          isinstance(comps, dict) and list(comps) == ids and ids
          and all(re.fullmatch(rf'{re.escape(k)}-[a-z]+', str(v)) for k, v in comps.items()), comps)

    scripts = (load(ROOT / 'package.json') or {}).get('scripts', {})
    check('root scripts video:studio and video:render:fragment run through npm --prefix video',
          all('npm --prefix video' in scripts.get(s, '') for s in ('video:studio', 'video:render:fragment')),
          {s: scripts.get(s) for s in ('video:studio', 'video:render:fragment')})
    ignored = [ln.strip() for ln in (ROOT / '.gitignore').read_text(encoding='utf-8').splitlines()]
    check('.gitignore keeps video/out/ out of git', 'video/out/' in ignored)

    failed = [k for k, v in checks.items() if not v['ok']]
    print(json.dumps({'passed': len(checks) - len(failed), 'failed': failed, 'checks': checks}, indent=2))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
