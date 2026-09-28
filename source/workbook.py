#!/usr/bin/env python3
"""Workbook <-> rows.json for the IDW Sonic tracker.

The workbook is the source of truth. This script converts between it and a flat
rows.json so row-level edits can be scripted, then written back.

    python3 source/workbook.py extract      # workbook -> source/rows.json
    python3 source/workbook.py build        # source/rows.json -> workbook
    python3 source/workbook.py verify       # run the verification block

An earlier version of these scripts existed only in a scratch directory and was
lost when that directory was wiped. They live in the repo now.
"""
import json, sys, os, re
from openpyxl import load_workbook, Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
WB   = os.path.join(REPO, 'IDW-Sonic-reading-order.xlsx')
ROWS = os.path.join(HERE, 'rows.json')

BANDS = {1: 'Before the Blue Blur', 2: 'The Long Modern Age', 3: 'A Mysterious Mastermind',
         4: 'The Metal Virus', 5: 'Rebuilding and the Starline Plot', 6: 'Frontiers',
         7: 'The Current Run', 8: 'Elsewhere'}

def band_of(note):
    m = re.search(r'Band (\d)', str(note or ''))
    return int(m.group(1)) if m else 0

# ---------------------------------------------------------------- extract
def extract():
    wb = load_workbook(WB, data_only=True)
    ic, am, gm = wb['Issue Checklist'], wb['Arc Master'], wb['Games']
    arc_band, arc_meta = {}, {}
    for r in am.iter_rows(min_row=2, values_only=True):
        if not r or not r[3]: continue
        arc_band[r[3]] = band_of(r[19])
        arc_meta[r[3]] = {'strand': r[7] or '', 'tier': r[10] or '', 'team': r[13] or '',
                          'collected': r[18] or ''}
    hours = {}
    for r in gm.iter_rows(min_row=2, values_only=True):
        if r and r[2]: hours[r[2]] = r[5]
    rows = []
    for r in ic.iter_rows(min_row=2, values_only=True):
        if r[2] is None: continue
        arc = r[5] or ''
        meta = arc_meta.get(arc, {})
        rows.append({'sortkey': int(r[2]), 'era': r[3] or '', 'title': r[4] or '', 'arc': arc,
                     'typ': r[6] or '', 'mo': r[7] or 'O', 'core': r[8] or '',
                     'flags': r[9] or '', 'note': r[10] or '', 'medium': r[12] or 'comic',
                     'band': arc_band.get(arc, 0), 'strand': meta.get('strand', 'Sonic'),
                     'tier': meta.get('tier', 'Everything'), 'team': meta.get('team', ''),
                     'collected': meta.get('collected', ''),
                     'hours': hours.get(r[4], '') if (r[12] or '') == 'game' else '',
                     'date': '%s-%s-01' % (str(r[2])[:4], str(r[2])[4:6])})
        rows[-1]['date'] = '%s-%s' % (rows[-1]['date'][:7], '01')
    json.dump(rows, open(ROWS, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('extracted %d rows -> %s' % (len(rows), ROWS))

# ---------------------------------------------------------------- verify
def verify():
    wb = load_workbook(WB, data_only=True)
    ic, am, bc, cx, gm = (wb['Issue Checklist'], wb['Arc Master'], wb['Basic Checklist'],
                          wb['Context'], wb['Games'])
    rows = [[c.value for c in r] for r in ic.iter_rows(min_row=2)]
    keys = [r[2] for r in rows]; nums = [r[1] for r in rows]; titles = [r[4] for r in rows]
    arcs = {r[3] for r in am.iter_rows(min_row=2, values_only=True)}
    ok = lambda b: 'PASS' if b else '*** FAIL ***'
    checkable = sum(1 for n in nums if n)
    print('rows %d | checkable %d' % (len(rows), checkable))
    print('  keys unique        ', ok(len(set(keys)) == len(keys)))
    print('  keys ascending     ', ok(all(keys[i] < keys[i+1] for i in range(len(keys)-1))))
    print('  keys 9 digits      ', ok(all(len(str(k)) == 9 for k in keys)))
    print('  # contiguous 1..N  ', ok([n for n in nums if n] == list(range(1, checkable+1))))
    print('  zero dup titles    ', ok(len(set(titles)) == len(titles)))
    print('  Basic == checkable ', ok(bc.max_row-1 == checkable))
    print('  arcs all resolve   ', ok(not {r[5] for r in rows if r[5] not in arcs}))
    print('  no malformed arcs  ', ok(not [a for a in arcs if a and (str(a).strip().endswith(':') or len(str(a).strip()) < 3)]))
    print('  context blurbs     ', ok(all(r[3].value for r in cx.iter_rows(min_row=2))))
    st = {s.strip() for r in am.iter_rows(min_row=2, values_only=True)
          for s in str(r[7] or '').split(',') if s.strip()}
    print('  atomic strands <=24', ok(0 < len(st) <= 24), len(st))
    g = [r for r in gm.iter_rows(min_row=2, values_only=True)]
    print('  games have hours   ', ok(all(r[5] for r in g)), '%d/%d' % (sum(1 for r in g if r[5]), len(g)))

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'verify'
    if cmd == 'extract': extract()
    elif cmd == 'verify': verify()
    else: print(__doc__)
