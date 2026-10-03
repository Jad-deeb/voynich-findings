"""Diagnostic 4: local self-similarity and reduplication.

For each word, look at the K preceding words on the same page. Count exact
repeats and near repeats (Levenshtein distance 1, not identical). Compare with
the same count when the K comparison words come from a different page of the
same section group (the 'distant' baseline). The local/distant ratio removes
alphabet and word-length differences between scripts.

Self-citation models (Timm and Schinner) predict strong local excess of near
repeats. Natural language shows some local excess from topic repetition.
A one-to-one word code preserves exact repeats exactly; near-repeat rates
depend on how the code spells related words.
"""
from collections import defaultdict
import json
import random

from common import paragraph_lines, corpus_words, DATA
from naibbe_like import NaibbeLike


def lev1(a, b):
    """0 if equal, 1 if one edit apart, 2 otherwise (fast bounded check)."""
    if a == b:
        return 0
    la, lb = len(a), len(b)
    if abs(la - lb) > 1:
        return 2
    if la == lb:
        return 1 if sum(x != y for x, y in zip(a, b)) == 1 else 2
    if la > lb:
        a, b, la, lb = b, a, lb, la
    i = 0
    while i < la and a[i] == b[i]:
        i += 1
    return 1 if a[i:] == b[i + 1:] else 2


def rates(pages, K, rng, groups=None):
    """pages: list of token lists; groups: parallel list of group labels."""
    groups = groups or [0] * len(pages)
    by_group = defaultdict(list)
    for i, g in enumerate(groups):
        by_group[g].append(i)
    loc = [0, 0, 0]   # exact, near, total
    dist = [0, 0, 0]
    for pi, toks in enumerate(pages):
        others = [j for j in by_group[groups[pi]] if j != pi and len(pages[j]) > K]
        if not others:
            continue
        for t in range(K, len(toks)):
            w = toks[t]
            window = toks[t - K:t]
            d = min(lev1(w, x) for x in window)
            loc[2] += 1
            if d == 0:
                loc[0] += 1
            elif d == 1:
                loc[1] += 1
            op = pages[rng.choice(others)]
            s = rng.randrange(0, len(op) - K + 1)
            d2 = min(lev1(w, x) for x in op[s:s + K])
            dist[2] += 1
            if d2 == 0:
                dist[0] += 1
            elif d2 == 1:
                dist[1] += 1
    return loc, dist


def adjacent_identical(pages):
    n = same = 0
    for toks in pages:
        for a, b in zip(toks, toks[1:]):
            n += 1
            same += a == b
    return same, n


def summarize(name, pages, rng, K=20, groups=None):
    loc, dist = rates(pages, K, rng, groups)
    same, n = adjacent_identical(pages)
    row = {'text': name, 'K': K, 'tokens_tested': loc[2],
           'exact_local': round(loc[0] / loc[2], 4), 'exact_distant': round(dist[0] / dist[2], 4),
           'exact_ratio': round(loc[0] / max(dist[0], 1), 2),
           'near_local': round(loc[1] / loc[2], 4), 'near_distant': round(dist[1] / dist[2], 4),
           'near_ratio': round(loc[1] / max(dist[1], 1), 2),
           'adjacent_identical_per_1000': round(1000 * same / n, 2)}
    print(json.dumps(row))
    return row


def vms_pages(source='IT'):
    pages = defaultdict(list)
    meta = {}
    for line in paragraph_lines(source):
        pages[line['folio']].extend(t for t in line['tokens'] if t)
        m = line['meta']
        meta[line['folio']] = (m.get('L'), m.get('I'))
    keys = [k for k in pages if len(pages[k]) > 40]
    return [pages[k] for k in keys], [meta[k] for k in keys]


def chunk(words, size):
    return [words[i:i + size] for i in range(0, len(words) - size + 1, size)]


if __name__ == '__main__':
    rng = random.Random(77)
    rows = []
    vp, vg = vms_pages('IT')
    rows.append(summarize('VMS IT (distant page from same language+section)', vp, rng, groups=vg))
    vp2, vg2 = vms_pages('ZL')
    rows.append(summarize('VMS ZL (distant page from same language+section)', vp2, rng, groups=vg2))
    lat = corpus_words('latin')
    ita = corpus_words('italian')
    eng = corpus_words('english', files=['Cirurgie'])
    for nm in ['Secreta_Secretorum_LAT', 'Latin_Aix', 'Steganographia']:
        rows.append(summarize('Latin ' + nm, chunk(lat[nm][:34000], 170), rng))
    rows.append(summarize('Italian Rettorica', chunk(ita['Rettorica'][:34000], 170), rng))
    rows.append(summarize('Middle English Cirurgie', chunk(eng['Cirurgie'][:34000], 170), rng))
    sec = lat['Secreta_Secretorum_LAT']
    cipher = NaibbeLike(sorted(set(''.join(sec))), seed=7)
    toks = [t.split(':')[-1] for t, _ in cipher.encrypt(''.join(sec[:23000]), rng)][:34000]
    rows.append(summarize('Naibbe-like cipher of Latin Secreta', chunk(toks, 170), rng))
    (DATA / 'diag_local.json').write_text(json.dumps(rows, indent=1))
