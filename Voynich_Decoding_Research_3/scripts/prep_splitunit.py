"""Inputs for splitunit_solve.mjs: the Naibbe-family test with the word division
LEARNED rather than fixed by a rule.

For every word type, the candidate analyses are: the whole word as one symbol
(U), or any split into prefix + suffix where the prefix occurs as a prefix of
at least MIN_TYPES different word types and the suffix as a suffix of at least
MIN_TYPES types. The solver chooses one analysis per type and a letter per symbol.

Positive control: a Naibbe-style cipher whose word forms are built from real
Voynich prefixes and endings, so the true split is hidden among the same kind
of alternatives the manuscript offers.
"""
import json
import random
from collections import Counter, defaultdict

from common import paragraph_lines, corpus_words, DATA
from prep_wordunit import vms_streams, shuffle_within_page, split, to_alpha
from prep_partunit import split_core

MIN_TYPES = 3
MAXLEN = 6


def candidate_sets(types):
    pre, suf = Counter(), Counter()
    for w in types:
        for k in range(1, len(w)):
            if k <= MAXLEN:
                pre[w[:k]] += 1
            if len(w) - k <= MAXLEN:
                suf[w[k:]] += 1
    return ({p for p, c in pre.items() if c >= MIN_TYPES},
            {s for s, c in suf.items() if c >= MIN_TYPES})


def analyses(types, P, S):
    out = {}
    for w in types:
        opts = [['U:' + w]]
        for k in range(1, len(w)):
            if w[:k] in P and w[k:] in S:
                opts.append(['P:' + w[:k], 'S:' + w[k:]])
        out[w] = opts
    return out


def add_analyses(obj):
    types = {t for key in ('streams_train', 'streams_test') for s in obj[key] for t in s if t}
    P, S = candidate_sets(types)
    obj['analyses'] = analyses(types, P, S)
    return obj, len(P), len(S)


def vms_looking_cipher(alphabet, rng, tables=6):
    """Prefix, suffix and single-word spellings taken from real Voynich words.
    Prefixes end at the first gallows/bench glyph; suffixes contain none, so the
    true division is unique, but the solver is not told where it is."""
    toks = [t for l in paragraph_lines('IT') for t in l['tokens'] if t]
    pre, suf, uni = Counter(), Counter(), Counter()
    for t in toks:
        parts = split_core(t)
        if len(parts) == 2 and any(c in parts[0][1] for c in 'ktpf') or (len(parts) == 2 and ('ch' in parts[0][1] or 'sh' in parts[0][1])):
            if not any(x in parts[1][1] for x in ('k', 't', 'p', 'f', 'ch', 'sh')):
                pre[parts[0][1]] += 1
                suf[parts[1][1]] += 1
        elif len(parts) == 1 or not any(x in t for x in ('k', 't', 'p', 'f', 'ch', 'sh')):
            uni[t] += 1
    n = len(alphabet) * tables
    P = [p for p, _ in pre.most_common(n)]
    S = [s for s, _ in suf.most_common(n)]
    combos = {p + s for p in P for s in S}
    U = [u for u, _ in uni.most_common(4 * n) if u not in combos][:n]
    assert len(P) == n and len(S) == n and len(U) == n, (len(P), len(S), len(U))
    rng.shuffle(P); rng.shuffle(S); rng.shuffle(U)
    idx = {(t, L): t * len(alphabet) + i for t in range(tables) for i, L in enumerate(alphabet)}
    return P, S, U, idx


def encrypt(letters, P, S, U, idx, rng, tables=6, weights=(5, 2, 2, 2, 1, 1), p_uni=0.5):
    out, i = [], 0
    while i < len(letters):
        t1 = rng.choices(range(tables), weights)[0]
        if i == len(letters) - 1 or rng.random() < p_uni:
            out.append((U[idx[(t1, letters[i])]], letters[i])); i += 1
        else:
            t2 = rng.choices(range(tables), weights)[0]
            out.append((P[idx[(t1, letters[i])]] + S[idx[(t2, letters[i + 1])]], letters[i:i + 2])); i += 2
    return out


if __name__ == '__main__':
    rng = random.Random(77)
    for name, req in [('vmsA', {'L': 'A'}), ('vmsB', {'L': 'B'})]:
        streams, pages = vms_streams(req)
        obj, nP, nS = add_analyses(split(streams, random.Random(1)))
        (DATA / f'su_{name}.json').write_text(json.dumps(obj))
        obj2, _, _ = add_analyses(split(shuffle_within_page(streams, pages, rng), random.Random(1)))
        (DATA / f'su_{name}_shuffled.json').write_text(json.dumps(obj2))
        nopt = Counter(len(v) for v in obj['analyses'].values())
        print(name, 'prefix candidates', nP, 'suffix candidates', nS, 'options per type', sorted(nopt.items())[:8])

    lat = corpus_words('latin')
    sec = lat['Secreta_Secretorum_LAT']
    letters = ''.join(to_alpha(w) for w in sec)
    alphabet = sorted(set(letters))
    P, S, U, idx = vms_looking_cipher(alphabet, rng)
    for ntok in (11000, 23000):
        enc = encrypt(letters, P, S, U, idx, rng)[:ntok]
        streams = [[t for t, _ in enc[i:i + 45]] for i in range(0, len(enc), 45)]
        truth = [[u for _, u in enc[i:i + 45]] for i in range(0, len(enc), 45)]
        obj, nP, nS = add_analyses(split(streams, random.Random(1), truth=truth))
        # record the true analysis of each control type, for scoring only
        true_an = {}
        pset, sset, uset = set(P), set(S), set(U)
        for t in obj['analyses']:
            if t in uset:
                true_an[t] = ['U:' + t]
            else:
                for k in range(1, len(t)):
                    if t[:k] in pset and t[k:] in sset:
                        true_an[t] = ['P:' + t[:k], 'S:' + t[k:]]
        obj['true_analysis'] = true_an
        covered = sum(1 for t, a in true_an.items() if a in obj['analyses'][t]) / len(true_an)
        (DATA / f'su_ctrl_vmslike_{ntok // 1000}k.json').write_text(json.dumps(obj))
        flat = [t for s in streams for t in s]
        print('control', ntok, 'types', len(set(flat)), 'prefix cands', nP, 'suffix cands', nS,
              'true analysis among options', round(covered, 3))
        sh = list(flat); rng.shuffle(sh); it = iter(sh)
        shuf = [[next(it) for _ in s] for s in streams]
        obj2, _, _ = add_analyses(split(shuf, random.Random(1), truth=truth))
        (DATA / f'su_ctrl_vmslike_{ntok // 1000}k_shuffled.json').write_text(json.dumps(obj2))
    print('sample control words:', [t for t, _ in encrypt(letters[:60], P, S, U, idx, random.Random(3))][:20])
