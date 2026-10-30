"""Test for the AI Canvas excerpts the marketing video shows: video/data/canvas_hiring.json.

Usage:  python test/marketing_video_canvas_test.py

The canvas scene shows one plain-language line per block of the CV Screening Assistant's AI Canvas. The owner
approved this wording for non-expert viewers; it is the video's own and the prototype's canvas keeps its text.
Checks:
  - the file lists each of the seven blocks of CANVAS_BLOCKS in index.html once, in that order, with its label
  - each excerpt is the approved line for its block
  - each approved line has 3 to 14 words and says neither "use case" (the glossary word is "initiative") nor
    "requisition" (viewers read "job" or "job requirements")
  - the guard: a reworded excerpt and a wrong label are each rejected
Prints a JSON report; exit code 1 on any failure.
"""
import copy
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'video' / 'data' / 'canvas_hiring.json'
APPROVED = {
    'businessProblem': 'Recruiters cannot read every application when a job attracts hundreds',
    'businessValue': 'Recruiters review a shortlist instead of reading every application first',
    'objectiveFunction': 'How well each application matches the job requirements',
    'modelingApproach': 'It ranks applications for a recruiter and never decides on its own',
    'modelTraining': 'An independent bias audit must approve each new version first',
    'customerValue': 'Every candidate is considered, so no one is missed',
    'dataStrategy': 'The CV text and its key details, such as skills and experience',
}


def blocks_in(html):
    """[(key, label)] from CANVAS_BLOCKS in index.html."""
    return re.findall(r'\{f:"(\w+)",l:"([^"]+)"', html[html.index('var CANVAS_BLOCKS'):html.index('var CANVASES')])


def wording_problems(lines):
    """Every wording rule an approved line breaks."""
    bad = []
    for key, line in lines.items():
        if not 3 <= len(line.split()) <= 14:
            bad.append(f'{key}: must have 3 to 14 words')
        if re.search(r'use[\s-]+cases?', line, re.I):
            bad.append(f'{key}: says "use case"; the glossary word is "initiative"')
        if re.search(r'requisition', line, re.I):
            bad.append(f'{key}: says "requisition"; say "job" or "job requirements"')
    return bad


def problems(data, blocks):
    """Every rule the file breaks, as readable strings; empty when it is sound."""
    if not isinstance(data, dict) or set(data) != {'blocks'} or not isinstance(data['blocks'], list):
        return ['top level must be exactly {blocks: [...]}']
    got = [(b.get('key'), b.get('label')) for b in data['blocks'] if isinstance(b, dict)]
    bad = [] if got == blocks else [f'blocks must be {blocks} in that order']
    for b in data['blocks']:
        key = b.get('key') if isinstance(b, dict) else b
        if not isinstance(b, dict) or b.get('excerpt') != APPROVED.get(key):
            bad.append(f'{key}: the excerpt is not the approved line {APPROVED.get(key)!r}')
    return bad


def main():
    checks = {}

    def check(name, found):
        checks[name] = {'ok': not found, 'detail': json.dumps(found)[:1500] if found else 'sound'}

    blocks = blocks_in((ROOT / 'index.html').read_text(encoding='utf-8'))
    check('index.html has the seven canvas blocks the approved lines cover',
          [] if len(blocks) == 7 and {k for k, _ in blocks} == set(APPROVED) else blocks)
    check('each approved line reads plainly', wording_problems(APPROVED))
    try:
        data = json.loads(DATA.read_text(encoding='utf-8'))
    except (OSError, ValueError) as e:
        data = None
        check('video/data/canvas_hiring.json exists and parses', [repr(e)])
    if data is not None:
        found = problems(data, blocks)
        check('each excerpt is the approved line for its block', found)
        if not found:
            def edit(fn):
                d = copy.deepcopy(data)
                fn(d['blocks'][0])
                return d
            copies = {'a reworded excerpt': edit(lambda b: b.update(excerpt=b['excerpt'] + ' quickly')),
                      'a wrong label': edit(lambda b: b.update(label='Problem'))}
            check('each rule rejects a broken copy', [k for k, d in copies.items() if not problems(d, blocks)])
        check('the wording rules reject "requisition" and "use case"',
              [] if len(wording_problems({'a': 'Match each application to the requisition',
                                          'b': 'No value is claimed for this use case'})) == 2 else ['a rule let one through'])

    failed = [k for k, v in checks.items() if not v['ok']]
    print(json.dumps({'passed': len(checks) - len(failed), 'failed': failed, 'checks': checks}, indent=2))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
