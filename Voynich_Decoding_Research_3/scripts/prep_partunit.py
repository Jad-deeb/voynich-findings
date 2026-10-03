"""Prepare inputs for partunit_solve.mjs.

Each input adds a 'parts' map: token -> list of role-tagged part symbols.
Roles: U (whole word = one letter), P (prefix = first letter of a pair),
S (suffix = second letter of a pair).

Voynich parse rules (hypotheses about where a Naibbe-type prefix ends):
  core   - prefix runs up to and including the first gallows or bench
           (ckh cth cph cfh ch sh k t p f); words without one split after the
           first glyph if 3+ glyphs long; otherwise the word is a unigram.
  suffix - suffix is the longest match from a list of common word endings;
           the remainder is the prefix; a word that is entirely an ending is a
           unigram.
  whole  - every word type is a unigram (plain homophonic substitution with
           word types as cipher symbols).
Controls use the generator's own unambiguous parts.
"""
import json
from pathlib import Path

from common import DATA

CORES = ['ckh', 'cth', 'cph', 'cfh', 'ch', 'sh', 'k', 't', 'p', 'f']
ENDINGS = sorted(['aiiin', 'eedy', 'aiin', 'eody', 'eey', 'edy', 'ain', 'iin', 'eol',
                  'eor', 'ody', 'oly', 'ory', 'aly', 'ary', 'ey', 'dy', 'ar', 'al',
                  'ol', 'or', 'am', 'an', 'om', 'in', 'ir', 'y', 's', 'l', 'r', 'd',
                  'o', 'm', 'n'], key=len, reverse=True)


def split_core(w):
    for i in range(len(w)):
        for c in CORES:
            if w.startswith(c, i):
                pre, suf = w[:i + len(c)], w[i + len(c):]
                return [('P', pre), ('S', suf)] if suf else [('U', w)]
    if len(w) >= 3:
        return [('P', w[0]), ('S', w[1:])]
    return [('U', w)]


def split_suffix(w):
    for e in ENDINGS:
        if w.endswith(e) and len(w) > len(e):
            return [('P', w[:-len(e)]), ('S', e)]
    return [('U', w)]


RULES = {'core': split_core, 'suffix': split_suffix, 'whole': lambda w: [('U', w)]}


def add_parts(obj, rule):
    toks = {t for key in ('streams_train', 'streams_test') for s in obj[key] for t in s if t}
    obj['parts'] = {t: [f'{r}:{p}' for r, p in RULES[rule](t)] for t in toks}
    return obj


def control_parts(obj):
    toks = {t for key in ('streams_train', 'streams_test') for s in obj[key] for t in s if t}
    parts = {}
    for t in toks:
        if t.startswith('U'):
            parts[t] = ['U:' + t]
        else:
            a, b = t.split('+')
            parts[t] = ['P:' + a, 'S:' + b]
    obj['parts'] = parts
    return obj


if __name__ == '__main__':
    for name in ['vmsA', 'vmsB']:
        for variant in ['', '_shuffled']:
            src = json.loads((DATA / f'wu_{name}{variant}.json').read_text())
            for rule in RULES:
                obj = add_parts(dict(src), rule)
                (DATA / f'pu_{name}_{rule}{variant}.json').write_text(json.dumps(obj))
                syms = {p for v in obj['parts'].values() for p in v}
                if not variant:
                    print(name, rule, 'symbols', len(syms),
                          'roles', {r: sum(1 for s in syms if s.startswith(r + ':')) for r in 'UPS'})
    for name in ['ctrl_naibbe6_11k', 'ctrl_naibbe6_23k', 'ctrl_naibbe12_23k']:
        for variant in ['', '_shuffled']:
            obj = control_parts(json.loads((DATA / f'wu_{name}{variant}.json').read_text()))
            (DATA / f'pu_{name}{variant}.json').write_text(json.dumps(obj))
    # example parses
    for w in ['qokeedy', 'chedy', 'shedy', 'daiin', 'ol', 'chol', 'qokain', 'okaiin', 'aiin', 'dy', 'lchedy', 'cthy']:
        print(w, split_core(w), split_suffix(w))
