"""Glyph alternations k/t, p/f, ch/sh, and e/ee inside otherwise identical words:
are the two variants used in the same contexts (free variation / homophones),
and do scribes or sections prefer one variant (spelling drift)?

For every word type w containing the first member of a pair, form its partner
by swapping one occurrence (e.g. qokeedy -> qoteedy). For pairs where both
occur 10+ times, compare (a) the next word's first glyph and the previous word's
last glyph distributions (Jensen-Shannon divergence, against the divergence
between two random halves of the same word), and (b) the share of the first
variant by section (Currier A herbal, A pharma, B herbal, B biological, B stars)."""
import json, math, random, re
from collections import Counter, defaultdict
from common import paragraph_lines, segments, DATA

PAIRS = [('k', 't'), ('p', 'f'), ('ch', 'sh'), ('ee', 'e'), ('ckh', 'cth'), ('aiin', 'ain'), ('ol', 'or'), ('al', 'ar')]

def jsd(c1, c2):
    keys = set(c1) | set(c2); n1, n2 = sum(c1.values()), sum(c2.values())
    if not n1 or not n2: return None
    d = 0.0
    for k in keys:
        p, q = c1[k] / n1, c2[k] / n2; m = (p + q) / 2
        if p: d += 0.5 * p * math.log2(p / m)
        if q: d += 0.5 * q * math.log2(q / m)
    return d

if __name__ == '__main__':
    rng = random.Random(3)
    ctx = defaultdict(list)   # word -> list of (prev last glyph, next first glyph, section)
    for line in paragraph_lines('IT'):
        m = line['meta']; sec = f"{m.get('L')}-{m.get('I')}"
        for run in segments(line):
            for i, w in enumerate(run):
                ctx[w].append((run[i - 1][-1] if i else '^', run[i + 1][0] if i + 1 < len(run) else '$', sec))
    rows = []
    for a, b in PAIRS:
        js_pair, js_self, shares = [], [], defaultdict(lambda: [0, 0])
        for w in list(ctx):
            for mm in re.finditer(re.escape(a), w):
                w2 = w[:mm.start()] + b + w[mm.end():]
                if w2 == w or w2 not in ctx: continue
                o1, o2 = ctx[w], ctx[w2]
                if len(o1) < 10 or len(o2) < 10: continue
                nxt1, nxt2 = Counter(x[1] for x in o1), Counter(x[1] for x in o2)
                prv1, prv2 = Counter(x[0] for x in o1), Counter(x[0] for x in o2)
                js_pair.append((jsd(nxt1, nxt2) + jsd(prv1, prv2)) / 2)
                # same-size random halves of the more frequent word, as a noise baseline
                big = o1 if len(o1) >= len(o2) else o2
                sh = big[:]; rng.shuffle(sh); h = len(sh) // 2
                js_self.append((jsd(Counter(x[1] for x in sh[:h]), Counter(x[1] for x in sh[h:])) + jsd(Counter(x[0] for x in sh[:h]), Counter(x[0] for x in sh[h:]))) / 2)
                for x in o1: shares[x[2]][0] += 1
                for x in o2: shares[x[2]][1] += 1
        if not js_pair: continue
        row = {'pair': f'{a}/{b}', 'word_pairs': len(js_pair),
               'context_divergence_pairs': round(sum(js_pair) / len(js_pair), 4),
               'context_divergence_same_word_halves': round(sum(js_self) / len(js_self), 4),
               'share_first_variant_by_section': {s: round(v[0] / (v[0] + v[1]), 2) for s, v in sorted(shares.items()) if v[0] + v[1] >= 50}}
        print(json.dumps(row)); rows.append(row)
    (DATA / 'diag_variants.json').write_text(json.dumps(rows, indent=1))
