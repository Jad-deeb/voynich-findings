"""Inputs for segunit_solve.mjs: every word type may be read as 1, 2 or 3
segments (U | P+S | P+M+S); every segment symbol stands for one plaintext letter
or for nothing (a null). Candidate segments must recur across word types.

Positive control: a Voynich-looking cipher in which plaintext letters are
grouped into units of 1-3 letters, each letter spelled by a role-specific
segment, and a null prefix is added to some words.
"""
import json
import random
from collections import Counter

from common import paragraph_lines, corpus_words, DATA
from prep_wordunit import vms_streams, shuffle_within_page, split, to_alpha
from prep_partunit import split_core

MIN_TYPES = 3
MAXSEG = 6
MAX3 = 12        # cap on three-segment readings per word type


def candidate_sets(types):
    pre, suf, mid = Counter(), Counter(), Counter()
    for w in types:
        n = len(w)
        for k in range(1, n):
            if k <= MAXSEG: pre[w[:k]] += 1
            if n - k <= MAXSEG: suf[w[k:]] += 1
        seen = set()
        for i in range(1, n - 1):
            for j in range(i + 1, min(n, i + 4)):
                seen.add(w[i:j])
        for m in seen: mid[m] += 1
    keep = lambda c: {x for x, n in c.items() if n >= MIN_TYPES}
    return keep(pre), keep(mid), keep(suf), pre, mid, suf


def analyses(types, P, M, S, pc, mc, sc):
    out = {}
    for w in types:
        opts = [['U:' + w]]
        n = len(w)
        for k in range(1, n):
            if w[:k] in P and w[k:] in S:
                opts.append(['P:' + w[:k], 'S:' + w[k:]])
        three = []
        for i in range(1, n - 1):
            for j in range(i + 1, n):
                a, b, c = w[:i], w[i:j], w[j:]
                if a in P and b in M and c in S:
                    three.append((min(pc[a], mc[b], sc[c]), ['P:' + a, 'M:' + b, 'S:' + c]))
        three.sort(key=lambda x: -x[0])
        opts.extend(o for _, o in three[:MAX3])
        out[w] = opts
    return out


def add_analyses(obj):
    types = {t for key in ('streams_train', 'streams_test') for s in obj[key] for t in s if t}
    P, M, S, pc, mc, sc = candidate_sets(types)
    obj['analyses'] = analyses(types, P, M, S, pc, mc, sc)
    return obj


def control_cipher(alphabet, rng, tables=4):
    """Role-specific spellings drawn from real Voynich word pieces."""
    toks = [t for l in paragraph_lines('IT') for t in l['tokens'] if t]
    pre, suf, uni = Counter(), Counter(), Counter()
    for t in toks:
        parts = split_core(t)
        if len(parts) == 2 and any(c in parts[0][1] for c in ('k', 't', 'p', 'f', 'ch', 'sh')):
            pre[parts[0][1]] += 1; suf[parts[1][1]] += 1
        else:
            uni[t] += 1
    n = len(alphabet) * tables
    P = [p for p, _ in pre.most_common(n)]
    S = [s for s, _ in suf.most_common(n)]
    U = [u for u, _ in uni.most_common(n)]
    MIDS = ['e', 'ee', 'o', 'a', 'eo', 'ch', 'sh', 'ol', 'ar', 'al', 'or', 'ai', 'eee', 'od', 'ed', 'cth', 'ckh', 'eey']
    Mx = [m1 + m2 for m1 in MIDS for m2 in ('', 'l', 'r', 'd', 'o', 's')][:n]
    for lst in (P, S, U, Mx): rng.shuffle(lst)
    nulls = ['q', 'qo', 'y', 'o', 'l', 'd']
    idx = {(t, L): t * len(alphabet) + i for t in range(tables) for i, L in enumerate(alphabet)}
    return P, Mx, S, U, nulls, idx


def encrypt(letters, P, Mx, S, U, nulls, idx, rng, tables=4, p_null=0.3):
    out, i = [], 0
    while i < len(letters):
        k = rng.choices([1, 2, 3], [0.3, 0.45, 0.25])[0]
        unit = letters[i:i + k]; i += len(unit)
        t = lambda: rng.randrange(tables)
        if len(unit) == 1:
            word = U[idx[(t(), unit[0])]]
            if rng.random() < p_null: word = rng.choice(nulls) + word            # null prefix + letter
        elif len(unit) == 2:
            word = P[idx[(t(), unit[0])]] + S[idx[(t(), unit[1])]]
            if rng.random() < p_null: word = rng.choice(nulls) + Mx[idx[(t(), unit[0])]] + S[idx[(t(), unit[1])]]
        else:
            word = P[idx[(t(), unit[0])]] + Mx[idx[(t(), unit[1])]] + S[idx[(t(), unit[2])]]
        out.append((word, unit))
    return out


if __name__ == '__main__':
    rng = random.Random(123)
    for name, req in [('vmsA', {'L': 'A'}), ('vmsB', {'L': 'B'})]:
        streams, pages = vms_streams(req)
        obj = add_analyses(split(streams, random.Random(1)))
        (DATA / f'sg_{name}.json').write_text(json.dumps(obj))
        obj2 = add_analyses(split(shuffle_within_page(streams, pages, rng), random.Random(1)))
        (DATA / f'sg_{name}_shuffled.json').write_text(json.dumps(obj2))
        nopt = Counter(len(v) for v in obj['analyses'].values())
        print(name, 'mean options per type', round(sum(k * v for k, v in nopt.items()) / sum(nopt.values()), 1))
    lat = corpus_words('latin')
    letters = ''.join(to_alpha(w) for w in lat['Secreta_Secretorum_LAT'])
    alphabet = sorted(set(letters))
    P, Mx, S, U, nulls, idx = control_cipher(alphabet, rng)
    enc = encrypt(letters, P, Mx, S, U, nulls, idx, rng)[:15000]
    streams = [[w for w, _ in enc[i:i + 45]] for i in range(0, len(enc), 45)]
    truth = [[u for _, u in enc[i:i + 45]] for i in range(0, len(enc), 45)]
    obj = add_analyses(split(streams, random.Random(1), truth=truth))
    (DATA / 'sg_ctrl_15k.json').write_text(json.dumps(obj))
    flat = [w for s in streams for w in s]
    print('control words', len(flat), 'types', len(set(flat)), 'letters/word', round(sum(len(u) for _, u in enc) / len(enc), 2))
    print('sample', flat[:16])
