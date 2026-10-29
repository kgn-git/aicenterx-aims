"""Schema test for the marketing video's storyline: video/src/timeline.json and video/script/storyline.md.

Usage:  python test/marketing_video_timeline_test.py

Every later step (audio, fragments, join) builds on the timeline, so it must hold the story the user approved and point
only at curated data. storyline.md is its human copy and must not drift from it. Checks:
  - shape: seven scenes hook, problem, canvas, risks, mitigations, enhancements, end, in that order, each in exactly
    one of the fragments f1 (hook, problem, canvas), f2 (risks), f3 (mitigations), f4 (enhancements), f5 (end); each
    scene carries only its own dataRefs group (the hook its sources), with no repeated id
  - timing: f1 runs 10 to 21 s, f2 to f4 each 10 to 15 s, f5 8 s at most, 66 s at most in all (the user's
    tolerance until the combined review), at most 2.5 words a second
  - narration: 155 words at most; a hook of at most 10 words that names Amazon and says "allegedly"; no "use case";
    never says the model is trained or retrained
  - the end card: "Coming soon", the footnote "This is a product concept video." and the AI-voice disclosure,
    each as an on-screen item in the end scene only
  - the six button labels on screen, and the on-screen items each scene component reads by position in their places:
    the hook's milestones written "YYYY – label", the canvas trigger, and the risks trigger, save and next buttons
  - dataRefs: every id exists, saved is a subset of shown, the hook's aiid is an incident of a CV Screening Assistant
    risk and is cited on screen, and the chain holds: saved risks have mitigations, the mitigations shown are those of
    the saved risks, the enhancements shown are all of video/data/model_enhancements.json, and each one's mitigation
    is saved
  - the guard: a broken copy that saves a risk with no mitigations, and one that shows an enhancement whose mitigation
    is not saved, are each rejected for their own rule and no other
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
ENHANCEMENTS = ROOT / 'video' / 'data' / 'model_enhancements.json'
FRAGMENTS = {'f1': ['hook', 'problem', 'canvas'], 'f2': ['risks'], 'f3': ['mitigations'], 'f4': ['enhancements'], 'f5': ['end']}
SCENES = [s for scenes in FRAGMENTS.values() for s in scenes]
KINDS = ('risks', 'mitigations', 'enhancements')
REFS = {'hook': {'sources'}, **{k: {k} for k in KINDS}}
SCENE_KEYS, OPTIONAL_KEYS = {'id', 'seconds', 'narration', 'onScreen', 'dataRefs'}, {'audioSeconds'}
LABELS = ('Simulate risks', 'Save selected risks', 'Generate mitigations', 'Save selected mitigations',
          'Suggest model enhancements', 'Save selected enhancements')
END_CARD = ('Coming soon', 'This is a product concept video.', 'The narration voice is AI-generated.')
# {scene: {position in onScreen: text}} for the items video/src/scenes/ reads by position.
ROLES = {'canvas': {4: 'Simulate risks'},
         'risks': {0: 'Simulate risks', 3: 'Save selected risks', 4: 'Generate mitigations', 5: 'Selected risks saved'},
         'mitigations': {0: 'Generate mitigations', 3: 'Save selected mitigations', 4: 'Suggest model enhancements',
                         5: 'Selected mitigations saved'},
         'enhancements': {0: 'Suggest model enhancements', 3: 'Save selected enhancements',
                          4: 'Selected enhancements saved'},
         'end': {0: 'AI Center X', 1: 'Coming soon',
                 5: 'Making innovation, governance and change management work together.'}}
MILESTONE = re.compile(r'\d{4} – \S.*')
MAX_WORDS, MAX_PACE, MAX_TOTAL, SHOWN_RISKS, HOOK_WORDS = 155, 2.5, 66.0, 5, 10
FRAGMENT_SECONDS, OPENING_SECONDS, END_SECONDS = (10, 15), (10, 21), 8


def words(s):
    return len(s.split())


def positive(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and x > 0


def context(risk_data, mitigation_data, enhancement_data):
    """The curated facts a timeline may point at."""
    hiring = risk_data['initiatives']['hiring']['suggestions']
    return {'risks': {s['id'] for s in hiring},
            'incidents': {i['id'] for s in hiring for i in s['incidents']},
            'mitigations': hiring_mitigations(risk_data, mitigation_data),
            'enhancements': {e['id']: e['mitigationId'] for e in enhancement_data['enhancements']}}


def id_list(x):
    return isinstance(x, list) and all(isinstance(i, str) for i in x) and len(set(x)) == len(x)


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
        elif not isinstance(refs, dict) or set(refs) != REFS.get(sid, set()):
            bad.append(f'{sid}: dataRefs must hold exactly {sorted(REFS.get(sid, set()))}')
        elif sid == 'hook' and not (isinstance(refs['sources'], list) and refs['sources'] and all(
                isinstance(x, dict) and set(x) == {'aiid'} for x in refs['sources'])):
            bad.append('hook: dataRefs.sources must be a non-empty list of {aiid}')
        elif sid in KINDS and not (isinstance(refs[sid], dict) and set(refs[sid]) == {'shown', 'saved'}
                                   and all(id_list(refs[sid][k]) for k in refs[sid])):
            bad.append(f'{sid}: dataRefs.{sid} must be exactly {{shown: [...], saved: [...]}} of distinct ids')
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
        bad += [f'{sid}: "{item}" belongs on screen in the end scene only'
                for item in END_CARD if (item in s['onScreen']) != (sid == 'end')]
    for fid, members in FRAGMENTS.items():
        secs = sum(by_id[m]['seconds'] for m in members)
        lo, hi = (0, END_SECONDS) if fid == 'f5' else OPENING_SECONDS if fid == 'f1' else FRAGMENT_SECONDS
        if not lo <= secs <= hi:
            bad.append(f'{fid} runs {secs} s, want {f"{hi} s at most" if fid == "f5" else f"{lo} to {hi} s"}')
    if sum(s['seconds'] for s in scenes) > MAX_TOTAL:
        bad.append(f'the scenes run {sum(s["seconds"] for s in scenes)} s, more than {MAX_TOTAL}')
    if sum(words(s['narration']) for s in scenes) > MAX_WORDS:
        bad.append(f'the narration has {sum(words(s["narration"]) for s in scenes)} words, more than {MAX_WORDS}')
    hook = by_id['hook']['narration']
    if words(hook) > HOOK_WORDS or 'Amazon' not in hook or 'allegedly' not in hook:
        bad.append(f'the hook must have at most {HOOK_WORDS} words, name Amazon and say "allegedly"')
    on_screen = {x for s in scenes for x in s['onScreen']}
    bad += [f'button label "{label}" is not on screen' for label in LABELS if label not in on_screen]
    bad += [f'{sid}: onScreen[{i}] must be "{want}"' for sid, roles in ROLES.items() for i, want in roles.items()
            if by_id[sid]['onScreen'][i:i + 1] != [want]]
    milestones = by_id['hook']['onScreen'][2:]
    if not milestones or not all(MILESTONE.fullmatch(m) for m in milestones):
        bad.append('hook: onScreen[2:] must be milestones written "YYYY – label"')
    return bad + validate_refs(by_id, ctx)


def validate_refs(by_id, ctx):
    """The dataRefs rules: ids exist, saved within shown, and the scenes chain risk to mitigation to enhancement."""
    bad = []
    for src in by_id['hook']['dataRefs']['sources']:
        if src['aiid'] not in ctx['incidents']:
            bad.append(f'hook: aiid {src["aiid"]!r} is not an incident of a CV Screening Assistant risk')
        if not any(f'incident {src["aiid"]}' in x for x in by_id['hook']['onScreen']):
            bad.append(f'hook: aiid {src["aiid"]!r} is not cited on screen as "incident {src["aiid"]}"')
    risks, mits, enhs = groups = [by_id[k]['dataRefs'][k] for k in KINDS]
    for kind, g in zip(KINDS, groups):
        bad += [f'{kind}: unknown {kind[:-1]} id {x!r}' for x in g['shown'] if x not in ctx[kind]]
        if not set(g['saved']) <= set(g['shown']):
            bad.append(f'{kind}: saved {kind} must be a subset of the {kind} shown')
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
            for e in enhs['shown'] if e in ctx['enhancements'] and ctx['enhancements'][e] not in mits['saved']]
    return bad


def refs_group(t, kind):
    """The {shown, saved} group that the scene named kind carries."""
    return next(s for s in t['scenes'] if s['id'] == kind)['dataRefs'][kind]


def broken_copies(t, risk_data, mitigation_data, enhancement_data):
    """{rule: (timeline, context) breaking only that rule, and a fragment its rejection must contain}."""
    risk = refs_group(t, 'risks')['saved'][-1]
    no_answers, fewer, orphan = copy.deepcopy(mitigation_data), copy.deepcopy(enhancement_data), copy.deepcopy(t)
    dropped = {m['id'] for m in no_answers['risks'].pop(mitigation_key(next(
        s for s in risk_data['initiatives']['hiring']['suggestions'] if s['id'] == risk)))}
    fewer['enhancements'] = [e for e in fewer['enhancements'] if e['mitigationId'] not in dropped]
    for kind, gone in (('mitigations', dropped), ('enhancements', {e['id'] for e in enhancement_data['enhancements']
                                                                   if e['mitigationId'] in dropped})):
        group = refs_group(orphan, kind)
        for k in group:
            group[k] = [x for x in group[k] if x not in gone]
    unsaved = copy.deepcopy(t)
    group = refs_group(unsaved, 'mitigations')
    group['saved'] = [m for m in group['saved'] if m != enhancement_data['enhancements'][0]['mitigationId']]
    return {
        'a saved risk with no mitigations': (orphan, context(risk_data, no_answers, fewer), 'has no mitigations'),
        'an enhancement whose mitigation is not saved': (
            unsaved, context(risk_data, mitigation_data, enhancement_data), 'puts unsaved mitigation'),
    }


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
