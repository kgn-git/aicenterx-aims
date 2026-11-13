"""Schema test for the marketing video's storyline: video/src/timeline.json and video/script/storyline.md.

Usage:  python test/marketing_video_timeline_test.py

The video is a pitch of about 40 s in five beats: the world, the break, the pain, the fix and the proof. Every later step (voice,
footage, scenes, music) builds on the timeline, so it must hold the script the user approved and point only at
curated data. storyline.md is its human copy and must not drift from it. Checks:
  - shape: five scenes world, break, pain, fix, proof, in that order, in the fragments f1 (world, break, pain),
    f2 (fix) and f3 (proof); each scene carries only its own dataRefs: the stock footage it plays, the sources of its
    figures, and for the fix the risks and mitigations it shows
  - timing: at most 3 words a second, since the voice sets the pace; every voiced scene ends 0.3 s after its clip and
    the proof 1.0 s after its own, so no scene holds dead air (the played length is pinned in
    test/marketing_video_audio_test.py)
  - narration: 115 words at most; no "use case"; never says the model is trained; each scene's line is the one the
    user approved word for word
  - the figures: 56% in the world, then 40%+ and ~5% in the break, each on screen with its label, spoken with the
    qualifiers that keep it as narrow as its source (PwC, Gartner, MIT NANDA, cited in the order spoken)
  - the end card: "Coming soon", the footnote "This is a product concept video." and the AI-voice disclosure, each
    as an on-screen item in the proof only, beside the "< 10 min" outcome, the brand, the tagline and its promise
  - the on-screen items each scene component reads by position, in their places: the pain's three points, one for
    each line the voice says, and a footage clip for each
  - dataRefs: every footage list names distinct clips; every risk and mitigation id exists, saved is a subset of
    shown, and the chain holds: saved risks have mitigations, and the mitigations shown are those of the saved risks
  - the guard: a broken copy that saves a risk with no mitigations is rejected for that rule and no other
  - storyline.md: its table lists the scenes in order with the timeline's seconds and narration word for word
Prints a JSON report; exit code 1 on any failure.
"""
import copy
import json
import re
import sys
from pathlib import Path

from video_keys import hiring_mitigations, mitigation_key

ROOT = Path(__file__).resolve().parent.parent
TIMELINE = ROOT / 'video' / 'src' / 'timeline.json'
STORYLINE = ROOT / 'video' / 'script' / 'storyline.md'
RISK_DATA = ROOT / 'tools' / 'data' / 'risk_suggestions.json'
MITIGATION_DATA = ROOT / 'tools' / 'data' / 'mitigation_suggestions.json'
FRAGMENTS = {'f1': ['world', 'break', 'pain'], 'f2': ['fix'], 'f3': ['proof']}
SCENES = [s for scenes in FRAGMENTS.values() for s in scenes]
REFS = {'world': {'sources', 'footage'}, 'break': {'sources', 'footage'}, 'pain': {'footage'}, 'fix': {'risks', 'mitigations', 'footage'},
        'proof': {'footage'}}
KINDS = ('risks', 'mitigations')
SCENE_KEYS, OPTIONAL_KEYS = {'id', 'seconds', 'narration', 'onScreen', 'dataRefs'}, {'audioSeconds'}
MAX_WORDS, MAX_PACE, SHOWN_RISKS = 115, 3.0, 5
TAIL, CLOSE_TAIL, SLACK = 0.3, 1.0, 0.05
# The script the user approved on #63, word for word; the pain beat was approved on 13 November 2026.
APPROVED = {
    'world': 'Fifty-six per cent of CEOs see no financial gain from AI yet.',
    'break': 'Over forty per cent of agentic AI projects may be scrapped by 2027. Only about five per cent of AI pilots '
             'deliver measurable value.',
    'pain': "Delivering AI is hard, risky and complex. Organisations want to do it responsibly and safely. But most "
            "SMEs can't spend thousands on consultants to assess the risks.",
    'fix': "AI Center X lets managers and compliance officers simulate a project's risks, from documented incidents "
           'and industry standards, and select the mitigations that apply.',
    'proof': 'In under ten minutes. AI Center X: make AI deliver value.',
}
# (scene, on screen, its label, how the voice says it, the qualifiers that keep the claim as narrow as its source's,
# the source its citation opens with), in the order spoken.
FIGURES = (
    ('world', '56%', 'of CEOs see no financial gain from AI yet', 'fifty-six per cent',
     ('CEOs', 'no financial gain', 'yet'), 'PwC'),
    ('break', '40%+', 'of agentic AI projects may be scrapped by 2027', 'over forty per cent',
     ('agentic AI projects', 'may be scrapped', '2027'), 'Gartner'),
    ('break', '~5%', 'of AI pilots deliver measurable value', 'about five per cent',
     ('AI pilots', 'measurable value'), 'MIT NANDA'),
)
END_CARD = ('Coming soon', 'This is a product concept video.', 'The narration voice is AI-generated.')
# {scene: {position in onScreen: text}} for the items video/src/scenes/ reads by position.
ROLES = {'world': {0: '56%', 1: FIGURES[0][2]},
         'break': {0: '40%+', 1: FIGURES[1][2], 2: '~5%', 3: FIGURES[2][2]},
         'pain': {0: 'Hard, risky and complex', 1: 'Responsible and safe, by design', 2: 'No budget for risk consultants'},
         'fix': {0: 'CV Screening Assistant', 1: 'Simulate risks', 2: 'Generate mitigations'},
         'proof': {0: '< 10 min', 1: 'Risk profile ready', 2: 'AI Center X', 3: 'Make AI Deliver Value',
                   4: 'Govern your AI risks. Accelerate your projects.', 5: END_CARD[0],
                   6: 'Sources and licences of every cited dataset', 7: END_CARD[2], 8: END_CARD[1]}}


def words(s):
    return len(s.split())


def positive(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and x > 0


def id_list(x):
    return isinstance(x, list) and x and all(isinstance(i, str) for i in x) and len(set(x)) == len(x)


def context(risk_data, mitigation_data):
    """The curated facts a timeline may point at."""
    hiring = risk_data['initiatives']['hiring']['suggestions']
    return {'risks': {s['id'] for s in hiring}, 'mitigations': hiring_mitigations(risk_data, mitigation_data)}


def shape_problems(t):
    """What makes t unreadable by the content rules; the content rules run only on a timeline with none."""
    if not isinstance(t, dict) or set(t) != {'scenes', 'fragments'} or not isinstance(t['scenes'], list) \
            or not all(isinstance(s, dict) for s in t['scenes']) or not isinstance(t['fragments'], list):
        return ['top level must be exactly {scenes: [...], fragments: [...]}']
    if [s.get('id') for s in t['scenes']] != SCENES:
        return [f'scenes must be {SCENES} in that order']
    if [(f.get('id'), f.get('scenes')) if isinstance(f, dict) else f for f in t['fragments']] != list(FRAGMENTS.items()):
        return [f'fragments must be exactly {FRAGMENTS}']
    bad = []
    for s in t['scenes']:
        sid, refs = s['id'], s.get('dataRefs')
        if not SCENE_KEYS <= set(s) <= SCENE_KEYS | OPTIONAL_KEYS:
            bad.append(f'{sid}: keys must be id, seconds, narration, onScreen, dataRefs and an optional audioSeconds')
        elif not (positive(s['seconds']) and isinstance(s['narration'], str) and s['narration'].strip()
                  and isinstance(s['onScreen'], list) and s['onScreen']
                  and all(isinstance(x, str) and x.strip() for x in s['onScreen'])
                  and ('audioSeconds' not in s or positive(s['audioSeconds']))):
            bad.append(f'{sid}: seconds and audioSeconds must be positive numbers, narration and onScreen non-empty text')
        elif not isinstance(refs, dict) or set(refs) != REFS[sid]:
            bad.append(f'{sid}: dataRefs must hold exactly {sorted(REFS[sid])}')
        elif not id_list(refs['footage']) or (sid == 'pain' and len(refs['footage']) != len(ROLES['pain'])):
            bad.append(f'{sid}: dataRefs.footage must be a non-empty list of distinct clip ids, one for each pain point')
        elif 'sources' in refs and not (isinstance(refs['sources'], list) and refs['sources'] and all(
                isinstance(x, dict) and set(x) == {'cite'} and isinstance(x['cite'], str) for x in refs['sources'])):
            bad.append(f'{sid}: dataRefs.sources must be a non-empty list of {{cite}}')
        elif any(not (isinstance(refs[k], dict) and set(refs[k]) == {'shown', 'saved'}
                      and all(id_list(refs[k][g]) for g in refs[k])) for k in KINDS if k in refs):
            bad.append(f'{sid}: dataRefs.risks and .mitigations must be exactly {{shown: [...], saved: [...]}}')
    return bad


def validate(t, ctx):
    """Every rule broken by timeline t, as readable strings; empty when it is sound."""
    bad = shape_problems(t)
    if bad:
        return bad
    scenes, by_id = t['scenes'], {s['id']: s for s in t['scenes']}
    for s in scenes:
        sid = s['id']
        if words(s['narration']) / s['seconds'] > MAX_PACE:
            bad.append(f'{sid}: {words(s["narration"])} words in {s["seconds"]} s is faster than {MAX_PACE} a second')
        if re.search(r'\buse[\s-]+cases?\b', s['narration'] + ' ' + ' '.join(s['onScreen']), re.I):
            bad.append(f'{sid}: says "use case"; the glossary word is "initiative"')
        if re.search(r'\b(re)?trained\b', s['narration'], re.I):
            bad.append(f'{sid}: the narration must never say the model is trained')
        bad += [f'{sid}: "{item}" belongs on screen in the proof only'
                for item in END_CARD if (item in s['onScreen']) != (sid == 'proof')]
        tail = CLOSE_TAIL if sid == 'proof' else TAIL
        if 'audioSeconds' in s and abs(s['seconds'] - (s['audioSeconds'] + tail)) > SLACK:
            bad.append(f'{sid}: {s["seconds"]} s planned, want its {s["audioSeconds"]} s clip plus {tail:g} s')
    if sum(words(s['narration']) for s in scenes) > MAX_WORDS:
        bad.append(f'the narration has {sum(words(s["narration"]) for s in scenes)} words, more than {MAX_WORDS}')
    bad += [f'{sid}: the narration must be the approved "{line}"' for sid, line in APPROVED.items()
            if by_id[sid]['narration'] != line]
    bad += [f'{sid}: onScreen[{i}] must be "{want}"' for sid, roles in ROLES.items() for i, want in roles.items()
            if by_id[sid]['onScreen'][i:i + 1] != [want]]
    return bad + figure_problems(by_id) + validate_refs(by_id, ctx)


def figure_problems(by_id):
    """The figures: spoken in order with their qualifiers, each scene citing its sources in the order it speaks them."""
    bad = []
    for sid in ('world', 'break'):
        own = [f for f in FIGURES if f[0] == sid]
        said = by_id[sid]['narration'].lower()
        at = [said.find(f[3]) for f in own]
        if -1 in at or at != sorted(at):
            bad.append(f'{sid}: the narration must say {[f[3] for f in own]} in that order')
        bad += [f'{sid}: the {f[1]} figure is not spoken with "{q}"' for f in own for q in f[4] if q.lower() not in said]
        cites = [x['cite'] for x in by_id[sid]['dataRefs']['sources']]
        if len(cites) != len(own) or not all(c.startswith(f[5]) for c, f in zip(cites, own)):
            bad.append(f'{sid}: dataRefs.sources must cite {[f[5] for f in own]}, in that order')
    return bad


def validate_refs(by_id, ctx):
    """The fix's dataRefs: ids exist, saved within shown, and the saved risks' mitigations are the ones shown."""
    bad = []
    refs = by_id['fix']['dataRefs']
    risks, mits = refs['risks'], refs['mitigations']
    for kind in KINDS:
        bad += [f'{kind}: unknown {kind[:-1]} id {x!r}' for x in refs[kind]['shown'] if x not in ctx[kind]]
        if not set(refs[kind]['saved']) <= set(refs[kind]['shown']):
            bad.append(f'{kind}: saved {kind} must be a subset of the {kind} shown')
    if len(risks['shown']) != SHOWN_RISKS:
        bad.append(f'{len(risks["shown"])} risks shown, want {SHOWN_RISKS}')
    answers = {}
    for mid, sid in ctx['mitigations'].items():
        answers.setdefault(sid, []).append(mid)
    bad += [f'saved risk {r} has no mitigations' for r in risks['saved'] if not answers.get(r)]
    if set(mits['shown']) != {m for r in risks['saved'] for m in answers.get(r, [])}:
        bad.append('the mitigations shown must be exactly those of the saved risks')
    return bad


def broken_copies(t, risk_data, mitigation_data):
    """{rule: (timeline, context) breaking only that rule, and a fragment its rejection must contain}."""
    fix = next(s for s in t['scenes'] if s['id'] == 'fix')['dataRefs']
    risk = fix['risks']['saved'][-1]
    no_answers, orphan = copy.deepcopy(mitigation_data), copy.deepcopy(t)
    dropped = {m['id'] for m in no_answers['risks'].pop(mitigation_key(next(
        s for s in risk_data['initiatives']['hiring']['suggestions'] if s['id'] == risk)))}
    group = next(s for s in orphan['scenes'] if s['id'] == 'fix')['dataRefs']['mitigations']
    for k in group:
        group[k] = [x for x in group[k] if x not in dropped]
    return {'a saved risk with no mitigations': (orphan, context(risk_data, no_answers), 'has no mitigations')}


def storyline_rows(text):
    """(scene, seconds, narration) for each body row of the first markdown table with the columns
    Scene | Seconds | Narration | On screen; None when there is no such table."""
    lines = [ln.strip() for ln in text.splitlines()]
    header = '| Scene | Seconds | Narration | On screen |'
    if header not in lines:
        return None
    rows = []
    for ln in lines[lines.index(header) + 2:]:
        if not ln.startswith('|'):
            break
        cells = [c.strip() for c in ln.strip('|').split('|')]
        rows.append((cells[0], cells[1], cells[2]) if len(cells) == 4 else tuple(cells))
    return rows


def main():
    checks = {}

    def check(name, ok, detail=''):
        checks[name] = {'ok': bool(ok), 'detail': detail if isinstance(detail, str) else json.dumps(detail)[:1500]}

    def load(p):
        return json.loads(p.read_text(encoding='utf-8'))

    risk_data, mitigation_data = load(RISK_DATA), load(MITIGATION_DATA)
    ctx = context(risk_data, mitigation_data)
    try:
        t, why = load(TIMELINE), str(TIMELINE)
    except (OSError, ValueError) as e:
        t, why = None, repr(e)
    check('video/src/timeline.json exists and parses', t is not None, why)
    if t is not None:
        try:
            problems = validate(t, ctx)
        except Exception as e:  # noqa: BLE001 - a malformed shape is reported as a failure, never a crash
            problems = [f'validator crashed: {e!r}']
        check('timeline passes every rule', not problems, problems or 'sound')
        if not problems:
            missed = [rule for rule, (bt, bctx, why) in broken_copies(t, risk_data, mitigation_data).items()
                      if [why in x for x in validate(bt, bctx)] != [True]]
            check('validator rejects each broken copy for its own rule and no other', not missed,
                  missed or 'all rejected')
            try:
                rows = storyline_rows(STORYLINE.read_text(encoding='utf-8'))
            except OSError:
                rows = None
            want = [(s['id'], f'{s["seconds"]:g}', s['narration'].split()) for s in t['scenes']]
            got = rows and [(r[0], r[1], r[2].split()) if len(r) == 3 else r for r in rows]
            check('storyline.md lists the scenes with their seconds and the narration word for word', got == want,
                  'match' if got == want else {'storyline': got, 'timeline': want})

    failed = [k for k, v in checks.items() if not v['ok']]
    print(json.dumps({'passed': len(checks) - len(failed), 'failed': failed, 'checks': checks}, indent=2))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
