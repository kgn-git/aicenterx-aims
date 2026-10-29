"""Test for the AI Canvas excerpts the marketing video shows: video/data/canvas_hiring.json.

Usage:  python test/marketing_video_canvas_test.py

The canvas scene shows a short excerpt of each block of the CV Screening Assistant's AI Canvas, so every excerpt
must be the prototype's own words. Checks:
  - the file lists each of the seven blocks of CANVAS_BLOCKS in index.html once, in that order, with its label
  - each excerpt appears word for word in that block of CANVASES.hiring, has 3 to 14 words, and never says "use case"
  - the guard: a reworded excerpt, a "use case" excerpt and a wrong label are each rejected
Prints a JSON report; exit code 1 on any failure.
"""
import copy
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'video' / 'data' / 'canvas_hiring.json'


def prototype(html):
    """[(key, label)] from CANVAS_BLOCKS and {key: text} from CANVASES.hiring in index.html."""
    blocks = re.findall(r'\{f:"(\w+)",l:"([^"]+)"', html[html.index('var CANVAS_BLOCKS'):html.index('var CANVASES')])
    start = html.index('hiring:{init:"hiring"')
    hiring = html[start:html.index('},', start)]
    return blocks, dict(re.findall(r'(\w+):"((?:[^"\\]|\\.)*)"', hiring))


def problems(data, blocks, hiring):
    """Every rule the excerpts break, as readable strings; empty when they are sound."""
    if not isinstance(data, dict) or set(data) != {'blocks'} or not isinstance(data['blocks'], list):
        return ['top level must be exactly {blocks: [...]}']
    got = [(b.get('key'), b.get('label')) for b in data['blocks'] if isinstance(b, dict)]
    bad = [] if got == blocks else [f'blocks must be {blocks} in that order']
    for b in data['blocks']:
        excerpt = b.get('excerpt') if isinstance(b, dict) else None
        if not isinstance(excerpt, str) or excerpt not in hiring.get(b.get('key'), ''):
            bad.append(f'{b.get("key") if isinstance(b, dict) else b}: the excerpt is not word for word in the block')
        elif not 3 <= len(excerpt.split()) <= 14:
            bad.append(f'{b["key"]}: the excerpt must have 3 to 14 words')
        if isinstance(excerpt, str) and re.search(r'use[\s-]+cases?', excerpt, re.I):
            bad.append(f'{b["key"]}: says "use case"; the glossary word is "initiative"')
    return bad


def main():
    checks = {}

    def check(name, found):
        checks[name] = {'ok': not found, 'detail': json.dumps(found)[:1500] if found else 'sound'}

    blocks, hiring = prototype((ROOT / 'index.html').read_text(encoding='utf-8'))
    check('index.html has seven canvas blocks and a CV Screening Assistant canvas',
          [] if len(blocks) == 7 and all(k in hiring for k, _ in blocks) else [blocks, sorted(hiring)])
    try:
        data = json.loads(DATA.read_text(encoding='utf-8'))
    except (OSError, ValueError) as e:
        data = None
        check('video/data/canvas_hiring.json exists and parses', [repr(e)])
    if data is not None:
        found = problems(data, blocks, hiring)
        check('each excerpt is the prototype\'s own words for its block', found)
        if not found:
            def edit(fn):
                d = copy.deepcopy(data)
                fn(d['blocks'][0])
                return d
            copies = {'a reworded excerpt': edit(lambda b: b.update(excerpt=b['excerpt'] + ' quickly')),
                      'a "use case" excerpt': edit(lambda b: b.update(key='businessValue', excerpt=hiring[
                          'businessValue'][hiring['businessValue'].index('no value'):])),
                      'a wrong label': edit(lambda b: b.update(label='Problem'))}
            check('each rule rejects a broken copy', [k for k, d in copies.items() if not problems(d, blocks, hiring)])

    failed = [k for k, v in checks.items() if not v['ok']]
    print(json.dumps({'passed': len(checks) - len(failed), 'failed': failed, 'checks': checks}, indent=2))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
