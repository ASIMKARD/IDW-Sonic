import json, re
from openpyxl import load_workbook

# =====================================================================
# FRANCHISE CONFIG — everything franchise-specific lives in this block.
# For a new tracker: edit only what is between here and END CONFIG, point
# WORKBOOK at the new .xlsx, and run. Nothing below this block knows or
# cares which franchise it is building.
# =====================================================================
FRANCHISE = {
    'key':       'idw-sonic',               # repo/cache slug, lowercase. ALSO namespaces
                                            # localStorage and the QR prefix, so it MUST
                                            # differ from every other tracker you host.
    'wordmark':  'IDW Sonic',               # shown in the compact topbar
    'title':     'IDW Sonic \u2014 Comics, Games & Shows',
    'strapline': 'Sonic the Hedgehog tracker \u00b7 1991\u20132026',
    'theme':     '#0E1526',                 # PWA theme colour (ink)
    'span':      '1991\u20132026',
    'search_url': 'https://www.google.com/search?q=',   # publisher lookup for the row link
    # Optional dual-order toggle, for a saga with a debated reading order.
    # Set to None and the chip is hidden entirely.
    'dual_order': None,                     # e.g. {'label': 'Clone', 'a': 'Epic', 'b': 'Published'}
}
WORKBOOK = 'wb.xlsx'

# Super-era bands. Cut at real story hinges, not round years; aim for
# roughly a decade each. (name, label, start sort key, end sort key, blurb)
# Verify with: every row lands in exactly one band, and buckets ascend.

wb=load_workbook('wb.xlsx', data_only=True)
IC=wb['Issue Checklist']; AM=wb['Arc Master']; CX=wb['Context']; LG=wb['Legend']; MT=wb['Maintenance']

rows=[[c.value for c in r[:13]] for r in IC.iter_rows(min_row=2) if r[2].value is not None]
arows=[[c.value for c in r[:20]] for r in AM.iter_rows(min_row=2) if any(c.value is not None for c in r)]
print('issue rows %d | arc rows %d'%(len(rows),len(arows)))

# ---- Context lookup: name -> blurb/intro ----
ctx={}
for r in CX.iter_rows(values_only=True):
    if not r or not r[0]: continue
    name=str(r[0]).strip()
    best=''
    for v in list(r)[1:]:
        if v and len(str(v))>len(best) and len(str(v))>25: best=str(v).strip()
    if best and name not in ctx: ctx[name]=best

# ---- eras, in first-appearance order down the reading order ----
eras=[]
for d in rows:
    if d[3] and d[3] not in eras and d[3] != 'Elseworlds (ALT)': eras.append(d[3])
eras.append('Elseworlds (ALT)')   # appended last: keeps era indices 0-34 stable
ERA={e:i for i,e in enumerate(eras)}
print('eras:',len(eras))

# ---- strands: split Arc Master combinations into atomic bits ----
atomic=[]
for a in arows:
    for tok in re.split(r'[;,]', str(a[7] or '')):
        tok=tok.strip()
        if tok and tok!='None' and tok not in atomic: atomic.append(tok)
STR={s:i for i,s in enumerate(atomic)}
print('atomic strands: %d -> %s'%(len(atomic),atomic))
assert len(atomic)<=31, 'strand bitmask would overflow 32-bit'

types=[]
for d in rows:
    if d[6] and d[6] not in types: types.append(d[6])
TYP={t:i for i,t in enumerate(types)}
print('types:',types)

# ---- arcs, in Arc Master (timeline) order ----
arcs=[]; ARC={}
for a in arows:
    name=str(a[3])
    if name in ARC: continue
    mask=0
    for tok in re.split(r'[;,]', str(a[7] or '')):
        tok=tok.strip()
        if tok in STR: mask |= (1<<STR[tok])
    def num(v):
        try: return int(str(v).strip())
        except: return 0
    ARC[name]=len(arcs)
    arcs.append({'n':name,'e':ERA.get(a[2],0),'s':mask or 1,'t':TYP.get(a[8],0),
                 'm':1 if str(a[9]).upper().startswith('M') else 0,
                 'q':num(a[12]),'i':num(a[11]),'y':str(a[5] or ''),'ti':str(a[4] or ''),
                 'ch':str(a[6] or ''),'cr':str(a[13] or ''),'ke':str(a[14] or ''),
                 'co':str(a[18] or ''),'no':str(a[19] or ''),
                 'pr':(str(a[16]) if a[16] else None),'li':str(a[17] or ''),
                 'b':ctx.get(name,''),'syn':0})
print('arcs:',len(arcs))
missing=sorted({str(d[5]) for d in rows if d[5] and str(d[5]) not in ARC})
print('issue arc labels missing from Arc Master:',len(missing),missing[:5])
assert not missing

FB,SKIP,ALT,GAP,RENUM=1,2,4,8,16
issues=[]
for d in rows:
    fl=0
    f=str(d[9] or '')
    if 'FB' in f: fl|=FB
    if 'SKIP' in f: fl|=SKIP
    if 'ALT' in f: fl|=ALT
    if 'GAPNOTE' in f: fl|=GAP
    if 'RENUM' in f: fl|=RENUM
    row=[int(str(d[2])), str(d[4]), ARC[str(d[5])] if d[5] else 0, TYP.get(d[6],0),
         1 if str(d[7]).upper()=='M' else 0, 1 if d[8] else 0, fl, (str(d[10]) if d[10] else '')]
    if d[11]:
        try: row.append(int(str(d[11])))
        except: pass
    issues.append(row)
issues.sort(key=lambda r:r[0])
MEDIUM_BY_KEY={int(str(d[2])):{'comic':0,'game':1,'screen':2}.get(str(d[12] or 'comic'),0) for d in rows}
assert len(MEDIUM_BY_KEY)==len(issues), 'medium map lost rows: %d vs %d'%(len(MEDIUM_BY_KEY),len(issues))

INERT=GAP|RENUM
chk=[r for r in issues if not (r[6]&INERT)]
counts={'total':len(chk),
        'core':sum(1 for r in chk if r[5]),
        'mandatory':sum(1 for r in chk if r[4]),
        'essential':sum(1 for r in chk if r[4] or r[5]),
        'gapnotes':sum(1 for r in issues if r[6]&GAP),
        'renumbers':sum(1 for r in issues if r[6]&RENUM)}
print('counts:',counts)

legend=[[str(r[0] or ''),str(r[1] or '')] for r in LG.iter_rows(values_only=True) if r and (r[0] or r[1])]
maint=[str(c) for r in MT.iter_rows(values_only=True) if r for c in r if c]

# timeline order: arcs in Arc Master order, issues grouped by arc then sort key
tl=sorted(range(len(issues)), key=lambda i:(issues[i][2], issues[i][0]))

data={'franchise':FRANCHISE,'eras':[{'n':e,'intro':ctx.get(e,'')} for e in eras],
      'strands':atomic,'types':types,'tiers':['Barebones','Essential','Everything'],
      'arcs':arcs,'issues':issues,'legend':legend,'maintenance':maint,'counts':counts,
      'altOrder':{'note':'9th element on an issue row is its as-published key; absent means unchanged',
                  'diverging':sum(1 for r in issues if len(r)>8),'unverified':[]},
      'timeline':tl,
      'media':['comic','game','screen'],
      # keyed by sort key, NOT row order: `issues` is re-sorted above, so a
      # positional map silently misaligns the moment the workbook is not
      # already in key order.
      'issueMedium':[MEDIUM_BY_KEY.get(r[0],0) for r in issues]}


# ---- period bands ----
# Optional super-era bands. Leave empty for a franchise that does not need them.
# Cut at real story hinges, not round years; aim for roughly a decade each.
#   ('Name', 'label', start_sort_key, end_sort_key, 'blurb shown under the band')
# Example from a previous build:
#   ('Foundations', '1962-73', 196208000, 197308000, 'Where it all starts...'),
PERIODS = [
 ('Before the Blue Blur','1991-97',199101000,199801000,
  'Sixteen-bit speed, a spin dash, and a mascot war with a plumber. No comics yet \u2014 these are the games the line spends thirty years referring back to.'),
 ('The Long Modern Age','1998-2017',199801000,201804000,
  'Two decades of games with no IDW comic beside them. Sonic goes 3D, goes dark, goes werewolf, and comes back. Ends on Forces, where issue #1 picks up.'),
 ('A Mysterious Mastermind','2018-19',201804000,201905000,
  'Eggman has lost his memory and someone else is wearing the crown. Tangle and Whisper arrive; Neo Metal Sonic builds an empire out of the vacuum.'),
 ('The Metal Virus','2019-20',201905000,202101000,
  'A cure-all goes wrong and the world turns to Zombots. Twenty issues of the cast losing, and an alliance nobody wanted.'),
 ('Rebuilding and the Starline Plot','2021-22',202101000,202210000,
  'The world repairs itself while Starline builds the replacements. Angel Island, the Zeti, and two engineered hedgehogs faster than the originals.'),
 ('Frontiers','2022-24',202210000,202405000,
  'Sonic Frontiers sits here, placed before issue #68 rather than at #84 where its cast starts appearing \u2014 the comic\u2019s own writer confirmed it fits there and nowhere else.'),
 ('The Current Run','2024-26',202405000,300000000,
  'The line as it stands today: Surge, Shadow, a Godzilla crossover, and an anniversary. The band the Maintenance refresh exists to keep honest.'),
]

# NOTE: these MUST be defined before bucket() below. Leaving them further down
# raises NameError as soon as PERIODS is non-empty and ELSE_STORIES is empty.
ELSE_STORIES = [
 (re.compile(r'^Adventures of Sonic the Hedgehog:', re.I), 'Adventures of Sonic the Hedgehog (ALT)',
  '65 episodes of slapstick, 1993 \u2014 plus Sonic Christmas Blast, made three years after the show ended.'),
 (re.compile(r'^Sonic the Hedgehog / SatAM:', re.I), 'Sonic the Hedgehog / SatAM (ALT)',
  'The serious one. A conquered planet, a resistance cell, and a cliffhanger that never got resolved on screen.'),
 (re.compile(r'^Sonic the Hedgehog: The Movie', re.I), 'Sonic the Hedgehog: The Movie (ALT)',
  'The 1996 OVA \u2014 two half-hour episodes a month apart in Japan, later stitched into a film. Knuckles debuts in the brown hat.'),
 (re.compile(r'^Sonic Underground:', re.I), 'Sonic Underground (ALT)',
  '40 episodes, 1999. Sonic has siblings, a missing mother, and a medallion that turns into a guitar.'),
 (re.compile(r'^Sonic X:', re.I), 'Sonic X (ALT)',
  '78 episodes. Sonic lands on Earth, acquires a human boy, and eventually goes to space.'),
 (re.compile(r'^Sonic Boom: (?!Rise of Lyric|Shattered Crystal|Fire & Ice)', re.I), 'Sonic Boom (ALT)',
  '104 eleven-minute episodes, and the funniest thing in this band. A sitcom where Eggman files noise complaints.'),
 (re.compile(r'^Sonic the Comic #', re.I), 'Sonic the Comic (ALT)',
  "Britain's own fortnightly Sonic comic, 1993\u20132002. Its own continuity entirely. Original stories run to #184; the last 39 issues are reprints."),
 (re.compile(r'^DC x Sonic', re.I), 'DC x Sonic (ALT)',
  'Two crossovers with the DC Universe. Self-contained by design, and published by DC rather than IDW.'),
]
ELSE_RX = re.compile(r'^Sonic the Comic #|^Adventures of Sonic the Hedgehog:|^Sonic the Hedgehog / SatAM:|^Sonic Underground:|^Sonic X:|^Sonic Boom: (?!Rise of Lyric|Shattered Crystal|Fire & Ice)|^Sonic the Hedgehog: The Movie|^DC x Sonic', re.I)

def period_of(key):
    k=int(key)
    for i,(n,y,a,b,bl) in enumerate(PERIODS):
        if a <= k < b: return i
    return len(PERIODS)-1
periods=[{'n':n,'y':y,'b':bl} for n,y,a,b,bl in PERIODS]
if ELSE_STORIES: periods.append({'n':'Elsewhere','y':'other continuities',
  'b':'Stories from outside the main line \u2014 other realities and other lifetimes.'})
ELSE_IDX = len(periods)-1
for r in issues:
    r_period = period_of(r[0])
data['periods']=periods if PERIODS else []
def bucket(r):
    return ELSE_IDX if (ELSE_RX and ELSE_RX.search(r[1])) else period_of(r[0])
data['issuePeriod']=[bucket(r) for r in issues] if PERIODS else []

# Inside the Elseworlds band the fine eras are meaningless, so each story
# becomes its own second-tier heading and its issues group together.
# Optional alternate-reality groupings, each becoming its own heading inside
# the final band. Leave empty for none. (regex, display name, blurb)

story_era={}
for rx,name,blurb in ELSE_STORIES:
    story_era[name]=len(data['eras'])
    data['eras'].append({'n':name,'intro':blurb})

def era_of(r, i):
    if data['issuePeriod'][i]!=ELSE_IDX:
        return arcs[r[2]]['e']
    for rx,name,blurb in ELSE_STORIES:
        if rx.search(r[1]): return story_era[name]
    return arcs[r[2]]['e']
data['issueEra']=[era_of(r,i) for i,r in enumerate(issues)] if (PERIODS and ELSE_STORIES) else []

# ---- prune eras that no row lands in --------------------------------------
# ELSE_STORIES appends its own era per story, so the workbook's ALT eras end up
# empty and clutter the era filter (and break era-range bulk marking, because a
# zero-row era makes a range silently cover nothing). Drop them and reindex
# every reference: arcs, issueEra, and the era list itself.
if data['issueEra']:
    # An arc's era is not authoritative here: ELSE_STORIES re-homes its issues to
    # a story era, leaving the workbook era referenced by the arc but empty. Take
    # era membership from the ISSUES, then point each arc at the era its own
    # issues actually landed in.
    arc_era = {}
    for i, r in enumerate(issues):
        arc_era.setdefault(r[2], data['issueEra'][i])
    for ai, a in enumerate(arcs):
        if ai in arc_era: a['e'] = arc_era[ai]
    used = sorted(set(data['issueEra']))
    if len(used) != len(data['eras']):
        remap = {old: new for new, old in enumerate(used)}
        dropped = [data['eras'][i]['n'] for i in range(len(data['eras'])) if i not in remap]
        data['eras'] = [data['eras'][i] for i in used]
        data['issueEra'] = [remap[e] for e in data['issueEra']]
        for a in arcs: a['e'] = remap.get(a['e'], 0)
        print('pruned %d empty era(s): %s' % (len(dropped), ', '.join(dropped)))
    empty = [e['n'] for i, e in enumerate(data['eras']) if i not in set(data['issueEra'])]
    print('eras still without issues:', empty or 'none')

out='window.TRACKER_DATA='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n'
open('data.js','w').write(out)
print('data.js written: %d bytes'%len(out))
print('eras with intro: %d/%d'%(sum(1 for e in data['eras'] if e['intro']),len(eras)))
print('arcs with blurb: %d/%d'%(sum(1 for a in arcs if a['b']),len(arcs)))
print('timeline entries:',len(tl))


# =====================================================================
# NEW-FRANCHISE CHECKLIST (engine below this line is franchise-agnostic)
#   1. Build the 6-tab workbook to the schema in README-NEXT-FRANCHISE.md
#   2. Edit FRANCHISE above; set WORKBOOK
#   3. Redefine PERIODS at the story hinges for that franchise
#   4. Redefine ELSE_STORIES / ELSE_RX (or set both empty for none)
#   5. python3 gen.py, then node test.js
#   6. Bump the cache string in sw.js and the build tag in index.html
# =====================================================================
