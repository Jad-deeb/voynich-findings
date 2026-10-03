"""Expert-matched plant drawings (herbal page <-> pharmaceutical drawing, from the
ZL file comments) as a meaning test: do the pharmaceutical page's plant labels
occur in the matched herbal page's text more often than in other herbal pages?"""
import json, random, re
from collections import defaultdict
from pathlib import Path
from common import load_lines, DATA

ZL = Path(__file__).resolve().parents[3] / 'work' / 'ZL3b-n.txt'

def lev1(a, b):
    if a == b: return 0
    la, lb = len(a), len(b)
    if abs(la - lb) > 1: return 2
    if la == lb: return 1 if sum(x != y for x, y in zip(a, b)) == 1 else 2
    if la > lb: a, b, la, lb = b, a, lb, la
    i = 0
    while i < la and a[i] == b[i]: i += 1
    return 1 if a[i:] == b[i + 1:] else 2

def expert_pairs():
    pairs, folio = [], None
    for line in ZL.read_text(encoding='utf-8', errors='replace').splitlines():
        m = re.match(r'^<(f[0-9a-z]+)>', line)
        if m: folio = m.group(1); continue
        m = re.match(r'^# Same plant as (f[0-9a-z]+)(\[[^\]]*\])?\s*(\?)?\s*\(([^)]*)\)', line)
        if m and folio:
            pairs.append({'herbal': folio, 'pharma': m.group(1), 'cell': m.group(2), 'uncertain': bool(m.group(3)), 'by': m.group(4)})
    return pairs

if __name__ == '__main__':
    lines, pages = load_lines('IT')
    text = defaultdict(list)       # herbal page -> paragraph words
    labels = defaultdict(list)     # pharma folio -> plant labels
    for l in lines:
        if l['utype'] == 'P':
            text[l['folio']].extend(t for t in l['tokens'] if t)
        elif l['utype'] == 'L':
            labels[l['folio']].extend(t for t in l['tokens'] if t)
    pairs = expert_pairs()
    herbal_pages = [f for f in text if pages.get(f, {}).get('I') == 'H' and len(text[f]) >= 20]
    def score(hp, ph, exact=True):
        words = set(text.get(hp, []))
        labs = [x for x in labels.get(ph, []) if len(x) >= 4]
        if exact: return sum(1 for x in labs if x in words), len(labs)
        return sum(1 for x in labs if any(lev1(x, w) <= 1 for w in words)), len(labs)
    rows = []
    for exact in (True, False):
        obs = 0; null = []
        rng = random.Random(5)
        for p in pairs:
            s, n = score(p['herbal'], p['pharma'], exact); obs += s
            p[f'hits_{"exact" if exact else "near"}'] = s; p['plant_labels_len4plus'] = n
        for _ in range(2000):
            tot = 0
            for p in pairs:
                hp = rng.choice(herbal_pages)
                tot += score(hp, p['pharma'], exact)[0]
            null.append(tot)
        mean = sum(null) / len(null)
        pval = sum(1 for x in null if x >= obs) / len(null)
        rows.append({'match': 'exact' if exact else 'within one glyph', 'observed_hits': obs,
                     'random_page_mean': round(mean, 2), 'p_value_one_sided': pval})
        print(json.dumps(rows[-1]))
    for p in pairs: print(p)
    (DATA / 'anchor_expert.json').write_text(json.dumps({'pairs': pairs, 'tests': rows}, indent=1))
