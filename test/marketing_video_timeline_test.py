"""Schema test for the marketing video's storyline: video/src/timeline.json and video/script/storyline.md.

Usage:  python test/marketing_video_timeline_test.py

The timeline is the only place the video's timing lives, and every later step (audio, fragments, join) builds on it,
so it must hold the story the user approved and point only at curated data. Checks:
  - shape: six scenes hook, canvas, risks, mitigations, enhancements, end, in that order, each in exactly one of the
    fragments f1 (hook, canvas), f2 (risks), f3 (mitigations), f4 (enhancements), f5 (end)
  - timing: f1 to f4 each run 10 to 15 s, f5 runs 8 s at most, 60.0 s in all, at most 2.5 words a second per scene
  - narration: 140 words at most; a hook of at most 10 words that names Amazon and says "allegedly"; no "use case";
    never says the model is trained; the AI-voice disclosure on screen in the end scene and nowhere else
  - the six button labels on screen
  - dataRefs: every id exists, saved is a subset of shown, each aiid is an incident of a CV Screening Assistant risk,
    and the chain holds: saved risks have mitigations, the mitigations shown are those of the saved risks, the
    enhancements shown are all of video/data/model_enhancements.json, and each one's mitigation is saved
  - the guard: a broken copy that saves a risk with no mitigations, and one that shows an enhancement whose mitigation
    is not saved, are each rejected for that rule
  - storyline.md: its table lists the scenes in order with the timeline's narration word for word
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
ENHANCEMENTS = ROOT / 'video' / 'data' / 'model_enhancements.json'
FRAGMENTS = {'f1': ['hook', 'canvas'], 'f2': ['risks'], 'f3': ['mitigations'], 'f4': ['enhancements'], 'f5': ['end']}
SCENES = [s for scenes in FRAGMENTS.values() for s in scenes]
LABELS = ('Simulate risks', 'Save selected risks', 'Generate mitigations', 'Save selected mitigations',
          'Suggest model enhancements', 'Save selected enhancements')
DISCLOSURE = 'The narration voice is AI-generated.'
MAX_WORDS, MAX_PACE, MAX_TOTAL, SHOWN_RISKS = 140, 2.5, 60.0, 5


def words(s):
    return len(s.split())


def number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and x > 0


def context(risk_data, mitigation_data, enhancement_data):
    """The curated facts a timeline may point at."""
    hiring = risk_data['initiatives']['hiring']['suggestions']
    return {'risks': {s['id'] for s in hiring},
            'incidents': {i['id'] for s in hiring for i in s['incidents']},
            'mitigations': hiring_mitigations(risk_data, mitigation_data),
            'enhancements': {e['id']: e['mitigationId'] for e in enhancement_data['enhancements']}}


def validate(t, ctx):
    """Every rule broken by timeline t, as readable strings; empty when it is sound."""
    if not isinstance(t, dict) or set(t) != {'scenes', 'fragments'}:
        return ['top level must be exactly {scenes: [...], fragments: [...]}']
    scenes = t['scenes']
    if [s.get('id') for s in scenes] != SCENES:
        return [f'scenes must be {SCENES} in that order']
    if [(f.get('id'), f.get('scenes')) for f in t['fragments']] != list(FRAGMENTS.items()):
        return [f'fragments must be exactly {FRAGMENTS}']
    bad, by_id = [], {s['id']: s for s in scenes}
    for s in scenes:
        sid = s['id']
        if not {'id', 'seconds', 'narration', 'onScreen', 'dataRefs'} <= set(s) <= {
                'id', 'seconds', 'narration', 'onScreen', 'dataRefs', 'audioSeconds'}:
            bad.append(f'{sid}: keys must be id, seconds, narration, onScreen, dataRefs and an optional audioSeconds')
            continue
        if not (number(s['seconds']) and isinstance(s['narration'], str) and s['narration'].strip()
                and isinstance(s['onScreen'], list) and s['onScreen']
                and all(isinstance(x, str) and x.strip() for x in s['onScreen'])
                and ('audioSeconds' not in s or number(s['audioSeconds']))):
            bad.append(f'{sid}: seconds and audioSeconds must be positive numbers, narration and onScreen non-empty text')
            continue
        if words(s['narration']) / s['seconds'] > MAX_PACE:
            bad.append(f'{sid}: {words(s["narration"])} words in {s["seconds"]} s is faster than {MAX_PACE} a second')
        if re.search(r'use case', s['narration'] + ' '.join(s['onScreen']), re.I):
            bad.append(f'{sid}: says "use case"; the glossary word is "initiative"')
        if re.search(r'\btrained\b', s['narration'], re.I):
            bad.append(f'{sid}: the narration must never say the model is trained')
        if (DISCLOSURE in s['onScreen']) != (sid == 'end'):
            bad.append(f'{sid}: "{DISCLOSURE}" belongs on screen in the end scene only')
    if bad:
        return bad
    for fid, members in FRAGMENTS.items():
        secs = sum(by_id[m]['seconds'] for m in members)
        if not (secs <= 8 if fid == 'f5' else 10 <= secs <= 15):
            bad.append(f'{fid} runs {secs} s, want {"8 s at most" if fid == "f5" else "10 to 15 s"}')
    if sum(s['seconds'] for s in scenes) > MAX_TOTAL:
        bad.append(f'the scenes run {sum(s["seconds"] for s in scenes)} s, more than {MAX_TOTAL}')
    if sum(words(s['narration']) for s in scenes) > MAX_WORDS:
        bad.append(f'the narration has {sum(words(s["narration"]) for s in scenes)} words, more than {MAX_WORDS}')
    hook = by_id['hook']['narration']
    if words(hook) > 10 or 'Amazon' not in hook or 'allegedly' not in hook:
        bad.append('the hook must have at most 10 words, name Amazon and say "allegedly"')
    on_screen = {x for s in scenes for x in s['onScreen']}
    bad += [f'button label "{label}" is not on screen' for label in LABELS if label not in on_screen]
    return bad + validate_refs(by_id, ctx)


def validate_refs(by_id, ctx):
    """The dataRefs rules: ids exist, saved within shown, and the scenes chain risk to mitigation to enhancement."""
    bad, groups = [], {}
    for sid, s in by_id.items():
        refs = s['dataRefs']
        if not isinstance(refs, dict) or not set(refs) <= {'sources', 'risks', 'mitigations', 'enhancements'}:
            bad.append(f'{sid}: dataRefs keys must be among sources, risks, mitigations, enhancements')
            continue
        for src in refs.get('sources', []):
            if not (isinstance(src, dict) and set(src) == {'aiid'} and src['aiid'] in ctx['incidents']):
                bad.append(f'{sid}: source {src!r} is not an incident of a CV Screening Assistant risk')
        for kind in ('risks', 'mitigations', 'enhancements'):
            if kind not in refs:
                continue
            g = refs[kind]
            if not (isinstance(g, dict) and set(g) == {'shown', 'saved'}
                    and all(isinstance(g[k], list) for k in g)):
                bad.append(f'{sid}: {kind} must be exactly {{shown: [...], saved: [...]}}')
                continue
            bad += [f'{sid}: unknown {kind} id {x!r}' for x in g['shown'] if x not in ctx[kind]]
            if not set(g['saved']) <= set(g['shown']):
                bad.append(f'{sid}: saved {kind} must be a subset of the {kind} shown')
            groups[kind] = g
    for kind in ('risks', 'mitigations', 'enhancements'):
        if kind not in by_id[kind]['dataRefs']:
            bad.append(f'the {kind} scene must carry dataRefs.{kind}')
    if not by_id['hook']['dataRefs'].get('sources'):
        bad.append('the hook must cite its incident in dataRefs.sources')
    if bad or set(groups) != {'risks', 'mitigations', 'enhancements'}:
        return bad
    risks, mits, enhs = groups['risks'], groups['mitigations'], groups['enhancements']
    if len(risks['shown']) != SHOWN_RISKS:
        bad.append(f'{len(risks["shown"])} risks shown, want {SHOWN_RISKS}')
    answers = {}
    for mid, sid in ctx['mitigations'].items():
        answers.setdefault(sid, []).append(mid)
    bad += [f'saved risk {r} has no mitigations' for r in risks['saved'] if not answers.get(r)]
    if set(mits['shown']) != {m for r in risks['saved'] for m in answers.get(r, [])}:
        bad.append('the mitigations shown must be exactly those of the saved risks')
    if set(enhs['shown']) != set(ctx['enhancements']):
        bad.append('the enhancements shown must be all of model_enhancements.json')
    bad += [f'enhancement {e} puts unsaved mitigation {ctx["enhancements"][e]} into effect'
            for e in enhs['shown'] if ctx['enhancements'].get(e) not in mits['saved']]
    return bad


def broken_copies(t, risk_data, mitigation_data, enhancement_data):
    """{rule: (timeline, context) breaking that rule, and a fragment its rejection must contain}."""
    risk = by_scene(t, 'risks')['saved'][-1]
    no_answers, orphan = copy.deepcopy(mitigation_data), copy.deepcopy(t)
    dropped = no_answers['risks'].pop(mitigation_key(next(
        s for s in risk_data['initiatives']['hiring']['suggestions'] if s['id'] == risk)))
    for k in ('shown', 'saved'):
        by_scene(orphan, 'mitigations')[k] = [m for m in by_scene(t, 'mitigations')[k]
                                              if m not in {d['id'] for d in dropped}]
    unsaved = copy.deepcopy(t)
    target = enhancement_data['enhancements'][0]['mitigationId']
    group = by_scene(unsaved, 'mitigations')
    group['saved'] = [m for m in group['saved'] if m != target]
    return {
        'a saved risk with no mitigations': (orphan, context(risk_data, no_answers, enhancement_data), 'has no mitigations'),
        "an enhancement whose mitigation is not saved": (
            unsaved, context(risk_data, mitigation_data, enhancement_data), 'puts unsaved mitigation'),
    }


def by_scene(t, kind):
    return next(s for s in t['scenes'] if s['id'] == kind)['dataRefs'][kind]


def storyline_rows(text):
    """(scene, narration) for each body row of the one markdown table with the columns Scene | Seconds | Narration |
    On screen; None when that table is missing."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip().startswith('|')]
    cells = [[c.strip() for c in ln.strip('|').split('|')] for ln in lines]
    if not cells or cells[0] != ['Scene', 'Seconds', 'Narration', 'On screen']:
        return None
    return [(c[0], c[2]) for c in cells[2:] if len(c) == 4]


def main():
    checks = {}

    def check(name, ok, detail=''):
        checks[name] = {'ok': bool(ok), 'detail': detail if isinstance(detail, str) else json.dumps(detail)[:1500]}

    def load(p):
        return json.loads(p.read_text(encoding='utf-8'))

    risk_data, mitigation_data, enhancement_data = load(RISK_DATA), load(MITIGATION_DATA), load(ENHANCEMENTS)
    ctx = context(risk_data, mitigation_data, enhancement_data)
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
            missed = [rule for rule, (bt, bctx, why) in broken_copies(t, risk_data, mitigation_data,
                                                                       enhancement_data).items()
                      if not any(why in x for x in validate(bt, bctx))]
            check('validator rejects each broken copy for its rule', not missed, missed or 'all rejected')
            try:
                rows = storyline_rows(STORYLINE.read_text(encoding='utf-8'))
            except OSError:
                rows = None
            want = [(s['id'], s['narration'].split()) for s in t['scenes']]
            got = rows and [(scene, narration.split()) for scene, narration in rows]
            check('storyline.md lists the scenes with the narration word for word', got == want,
                  'match' if got == want else {'storyline': got, 'timeline': want})

    failed = [k for k, v in checks.items() if not v['ok']]
    print(json.dumps({'passed': len(checks) - len(failed), 'failed': failed, 'checks': checks}, indent=2))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
