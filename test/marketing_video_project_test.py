"""Static test for the marketing video's Remotion project in video/.

Usage:  python test/marketing_video_project_test.py

npm run check must pass on a clone where `npm --prefix video ci` was never run, so this reads the project's files as
text and runs only the render script's argument guard, which exits before Remotion loads. Checks:
  - video/package.json pins every dependency, devDependency and override to an exact x.y.z version, includes
    remotion, @remotion/cli, react, react-dom and typescript, and sets engines.node to >=22.9
  - video/package-lock.json locks the same versions, each from registry.npmjs.org with an integrity hash
  - the color object in video/src/theme.ts holds exactly the named tokens, each with its value in index.html's
    midnight-executive block; headingFont and bodyFont equal the font-family of index.html's h1-h4 and html,body
    rules; the video is 1920x1080 at 30 fps with an 18% caption safe area
  - video/src/fonts.ts loads each bundled font under the first family of a font stack, and the font files are real
    TrueType files beside their SIL Open Font Licences
  - video/remotion.config.ts encodes every fragment as H.264 yuv420p BT.709 with an AAC track, which the join needs
  - video/src/compositions.json maps exactly the timeline's fragment ids to composition ids <fragment id>-<slug>
  - the render script refuses a missing, unknown or extra id with the list of valid ids, and names the install
    command when the project is not installed
  - the root package.json runs video:studio and video:render:fragment through npm --prefix video, and .gitignore
    keeps video/out/ and every .env file but .env.example out of git
  - the guard: one broken copy per rule above that parses project text is rejected
Prints a JSON report; exit code 1 on any failure.
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VIDEO = ROOT / 'video'
FONT_DIR = VIDEO / 'public' / 'fonts'
REQUIRED = ('remotion', '@remotion/cli', 'react', 'react-dom', 'typescript')
TOKENS = ('--bg-base', '--bg-g1', '--surface', '--surface-2', '--border', '--ink', '--ink-muted',
          '--gov', '--val', '--arch', '--rag-low', '--rag-medium', '--rag-high')
FONTS = {'Fraunces-Variable.ttf': 'Fraunces-OFL.txt', 'IBMPlexSans-Variable.ttf': 'IBMPlexSans-OFL.txt'}
ENCODING = ('setCodec("h264")', 'setPixelFormat("yuv420p")', 'setColorSpace("bt709")', 'setAudioCodec("aac")',
            'setEnforceAudioTrack(true)')
SCRIPTS = {'video:studio': 'npm --prefix video run studio',
           'video:render:fragment': 'npm --prefix video run render:fragment --'}
EXACT = re.compile(r'\d+\.\d+\.\d+')
REGISTRY = 'https://registry.npmjs.org/'


def camel(token):
    """'--bg-base' -> 'bgBase', the key theme.ts uses for a CSS token."""
    head, *rest = token.lstrip('-').split('-')
    return head + ''.join(p.capitalize() for p in rest)


def index_tokens(html):
    """{token: value} from index.html's `:root, [data-theme='midnight-executive']` block, the default theme."""
    block = re.search(r":root, \[data-theme='midnight-executive'\] \{(.*?)\}", html, re.S)
    return dict(re.findall(r'(--[a-z0-9-]+):([^;]+);', block.group(1))) if block else {}


def index_stacks(html):
    """{'headingFont', 'bodyFont': the font-family of index.html's h1,h2,h3,h4 and html,body rules}."""
    heading = re.search(r'^h1,h2,h3,h4 \{[^}]*?font-family:([^;]+);', html, re.M)
    body = re.search(r'^html,body \{[^}]*?font-family:([^;]+);', html, re.M)
    return {'headingFont': heading and heading.group(1).strip(), 'bodyFont': body and body.group(1).strip()}


def ts_strings(ts):
    """{name: value} for every `name: "..."` or `const name = "..."` in TypeScript text, comments stripped first."""
    code = re.sub(r'//[^\n]*|/\*.*?\*/', '', ts, flags=re.S)
    return dict(re.findall(r'\b(\w+)\s*[:=]\s*"((?:[^"\\]|\\.)*)"', code))


def pin_problems(pkg):
    deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {}), **pkg.get('overrides', {})}
    bad = [f'{k}@{v} is not an exact x.y.z version' for k, v in deps.items() if not EXACT.fullmatch(str(v))]
    bad += [f'{k} is not a dependency' for k in REQUIRED if k not in deps]
    return bad + ([] if pkg.get('engines', {}).get('node') == '>=22.9' else ['engines.node must be >=22.9'])


def lock_problems(pkg, lock):
    deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {})}
    packages = lock.get('packages', {})
    bad = [f'{k} is locked at {packages.get(f"node_modules/{k}", {}).get("version")}, package.json says {v}'
           for k, v in deps.items() if packages.get(f'node_modules/{k}', {}).get('version') != v]
    return bad + [f'{k} does not come from {REGISTRY} with an integrity hash' for k, e in packages.items()
                  if k and not (str(e.get('resolved', '')).startswith(REGISTRY) and e.get('integrity'))]


def theme_problems(ts, html):
    want, color = index_tokens(html), re.search(r'export const color = \{(.*?)\};', ts, re.S)
    got = ts_strings(color.group(1)) if color else {}
    bad = [] if set(got) == {camel(t) for t in TOKENS} else [f'color keys {sorted(got)} are not exactly the tokens']
    bad += [f'{t} is {got.get(camel(t))!r}, index.html has {want.get(t)!r}' for t in TOKENS
            if want.get(t) is None or got.get(camel(t)) != want[t]]
    strings, stacks = ts_strings(ts), index_stacks(html)
    bad += [f'{n} is {strings.get(n)!r}, index.html has {s!r}' for n, s in stacks.items() if not s or strings.get(n) != s]
    if not re.search(r'video = \{width: 1920, height: 1080, fps: 30\}', ts) or 'video.height * 0.18' not in ts:
        bad.append('the video must be 1920x1080 at 30 fps with a caption safe area of 0.18 of its height')
    return bad


def font_problems(fonts_ts, ts):
    stacks = ts_strings(ts)
    families = {m.group(1) for m in (re.match(r"'([^']+)'", stacks.get(n, '')) for n in ('headingFont', 'bodyFont'))
                if m}
    loaded = dict(re.findall(r'family: "([^"]+)", file: "fonts/([^"]+)"', fonts_ts))
    bad = [] if set(loaded) == families else [f'fonts.ts loads {sorted(loaded)}, the stacks name {sorted(families)}']
    return bad + [f'fonts.ts loads {f}, which is not a bundled font' for f in loaded.values() if f not in FONTS]


def asset_problems():
    bad = []
    for ttf, ofl in FONTS.items():
        try:
            head, licence = (FONT_DIR / ttf).read_bytes()[:4], (FONT_DIR / ofl).read_text(encoding='utf-8')
        except OSError as e:
            bad.append(f'{e.filename} is missing')
            continue
        if head not in (b'\x00\x01\x00\x00', b'true'):
            bad.append(f'{ttf} is not a TrueType file')
        if 'SIL Open Font License' not in licence:
            bad.append(f'{ofl} is not an SIL Open Font License')
    return bad


def render_guard(node, ids):
    """Each refused call of the render script that does not exit 1 naming the valid ids or the install command."""
    script, bad = VIDEO / 'scripts' / 'render-fragment.mjs', []

    def run(*args):
        return subprocess.run([node, str(script), *args], capture_output=True, text=True, timeout=60, cwd=VIDEO)

    for args in ([], ['../x'], [ids[0], ids[-1]]):
        r = run(*args)
        if r.returncode != 1 or ', '.join(ids) not in r.stderr:
            bad.append(f'{args}: exit {r.returncode}, stderr {r.stderr[-200:]!r}')
    if not (VIDEO / 'node_modules').exists():
        r = run(ids[0])
        if r.returncode != 1 or 'npm --prefix video ci' not in r.stderr:
            bad.append(f'not installed: exit {r.returncode}, stderr {r.stderr[-200:]!r}')
    return bad


def broken_copies(pkg, lock, ts, html, fonts_ts):
    """{rule: its validator's problems for a copy that breaks only that rule}; each must be non-empty."""
    first = next(iter(pkg['dependencies']))
    loose = {**pkg, 'dependencies': {**pkg['dependencies'], first: '^' + pkg['dependencies'][first]}}
    drift = {**pkg, 'dependencies': {**pkg['dependencies'], first: '0.0.1'}}
    return {
        'a ^ version': pin_problems(loose),
        'a lock version that differs': lock_problems(drift, lock),
        'a token value that differs': theme_problems(ts.replace('"#0e1320"', '"#0e1321"', 1), html),
        'a font stack cut short': theme_problems(ts.replace(", 'Segoe UI', sans-serif\"", '"', 1), html),
        'a font family that no stack names': font_problems(fonts_ts.replace('family: "Fraunces"', 'family: "Frances"'),
                                                           ts),
    }


def main():
    checks = {}

    def check(name, problems):
        checks[name] = {'ok': not problems, 'detail': json.dumps(problems)[:1500] if problems else 'sound'}

    def load(p):
        try:
            return json.loads(p.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            return None

    def text(p):
        try:
            return p.read_text(encoding='utf-8')
        except OSError:
            return None

    pkg, lock = load(VIDEO / 'package.json'), load(VIDEO / 'package-lock.json')
    html = (ROOT / 'index.html').read_text(encoding='utf-8')
    ts, fonts_ts = text(VIDEO / 'src' / 'theme.ts'), text(VIDEO / 'src' / 'fonts.ts')
    config = text(VIDEO / 'remotion.config.ts')
    missing = [p for p, v in (('video/package.json', pkg), ('video/package-lock.json', lock),
                              ('video/src/theme.ts', ts), ('video/src/fonts.ts', fonts_ts),
                              ('video/remotion.config.ts', config)) if v is None]
    check('the project files exist and parse', missing)
    if not missing:
        check('every dependency is pinned exactly, with the required packages and engines', pin_problems(pkg))
        check('the lockfile locks the same versions from the npm registry', lock_problems(pkg, lock))
        check("theme.ts matches index.html's default theme and the video frame", theme_problems(ts, html))
        check('fonts.ts loads each bundled font under its stack family', font_problems(fonts_ts, ts))
        check('every fragment is encoded the same way, with an audio track',
              [c for c in ENCODING if f'Config.{c};' not in config])
        missed = [rule for rule, problems in broken_copies(pkg, lock, ts, html, fonts_ts).items() if not problems]
        check('each rule rejects a broken copy', missed)
    check('the font files are TrueType with their licences', asset_problems())

    timeline, comps = load(VIDEO / 'src' / 'timeline.json'), load(VIDEO / 'src' / 'compositions.json')
    ids = [f['id'] for f in (timeline or {}).get('fragments', [])]
    sound = isinstance(comps, dict) and list(comps) == ids and ids and all(
        re.fullmatch(rf'{re.escape(k)}-[a-z]+', str(v)) for k, v in comps.items())
    check("compositions.json maps exactly the timeline's fragments to <id>-<slug>", [] if sound else [comps])
    node = shutil.which('node')
    if sound:
        check('the render script refuses any id it does not list',
              render_guard(node, list(comps.values())) if node else ['node is not on PATH'])

    scripts = (load(ROOT / 'package.json') or {}).get('scripts', {})
    check('root scripts run through npm --prefix video',
          [f'{k} is {scripts.get(k)!r}' for k, v in SCRIPTS.items() if scripts.get(k) != v])
    ignored = [ln.strip() for ln in (ROOT / '.gitignore').read_text(encoding='utf-8').splitlines()]
    check('.gitignore keeps video/out/ and .env files but .env.example out of git',
          [r for r in ('video/out/', '.env', '.env.*', '!.env.example') if r not in ignored])

    failed = [k for k, v in checks.items() if not v['ok']]
    print(json.dumps({'passed': len(checks) - len(failed), 'failed': failed, 'checks': checks}, indent=2))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
