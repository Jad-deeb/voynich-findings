"""Test 1: immediate repetition of the same word, against a position-aware shuffle
(tokens move only within the same page and line-position class), plus a per-word
breakdown for the manuscript and the Latin control."""
import json
import random
from collections import Counter

from common import corpus_words, DATA
from naibbe_like import NaibbeLike
from diag_wordseq2 import vms_by_page, text_by_page, shuffle_by_class


def same_rate(bp):
    n = s = 0
    for runs in bp.values():
        for run, _ in runs:
            for a, b in zip(run, run[1:]):
                n += 1
                s += (a == b)
    return s, n


def test(name, bp, rng, reps=100):
    s, n = same_rate(bp)
    null = [same_rate(shuffle_by_class(bp, rng))[0] for _ in range(reps)]
    m = sum(null) / reps
    row = {'text': name, 'pairs': n, 'identical_adjacent': s, 'per_1000': round(1000 * s / n, 2),
           'shuffle_mean': round(m, 1), 'ratio_to_shuffle': round(s / m, 2) if m else None}
    print(json.dumps(row))
    return row


def rep_counts(bp):
    c = Counter()
    for runs in bp.values():
        for run, _ in runs:
            for a, b in zip(run, run[1:]):
                if a == b:
                    c[a] += 1
    return c


def per_word(name, bp, rng, reps=200, top=25):
    obs = rep_counts(bp)
    exp = Counter()
    for _ in range(reps):
        exp.update(rep_counts(shuffle_by_class(bp, rng)))
    for k in exp:
        exp[k] /= reps
    freq = Counter(t for runs in bp.values() for run, _ in runs for t in run)
    out = {'text': name, 'words': [], 'excluding_top': {}}
    for w, f in freq.most_common(top):
        out['words'].append({'word': w, 'freq': f, 'observed': obs[w], 'expected': round(exp[w], 1),
                             'ratio': round(obs[w] / exp[w], 2) if exp[w] else None})
    for k in (10, 30, 100):
        topk = {w for w, _ in freq.most_common(k)}
        o = sum(v for w, v in obs.items() if w not in topk)
        e = sum(v for w, v in exp.items() if w not in topk)
        out['excluding_top'][k] = {'observed': o, 'expected': round(e, 1), 'ratio': round(o / e, 2)}
    print(name, json.dumps(out['excluding_top']))
    return out


if __name__ == '__main__':
    rng = random.Random(3)
    rows = [test('VMS IT all', vms_by_page(), rng),
            test('VMS IT Currier A', vms_by_page({'L': 'A'}), rng),
            test('VMS IT Currier B', vms_by_page({'L': 'B'}), rng),
            test('VMS ZL all', vms_by_page(source='ZL'), rng)]
    lat = corpus_words('latin')
    ita = corpus_words('italian')
    eng = corpus_words('english', files=['Cirurgie', 'AlphabetOfTales'])
    for nm in ['Secreta_Secretorum_LAT', 'Latin_Aix', 'Steganographia']:
        rows.append(test('Latin ' + nm, text_by_page(lat[nm][:34000]), rng))
    rows.append(test('Italian Rettorica', text_by_page(ita['Rettorica'][:34000]), rng))
    rows.append(test('Middle English Cirurgie', text_by_page(eng['Cirurgie'][:34000]), rng))
    rows.append(test('Middle English Alphabet of Tales', text_by_page(eng['AlphabetOfTales'][:34000]), rng))
    sec = lat['Secreta_Secretorum_LAT']
    cipher = NaibbeLike(sorted(set(''.join(sec))), seed=7)
    toks = [t for t, _ in cipher.encrypt(''.join(sec[:23000]), rng)][:34000]
    rows.append(test('Naibbe-like cipher of Latin', text_by_page(toks), rng))
    rows.append(test('Latin letters as tokens', text_by_page(list(''.join(sec[:6000]))[:34000]), rng))
    (DATA / 'diag_repetition.json').write_text(json.dumps(rows, indent=1))
    rng2 = random.Random(11)
    detail = [per_word('VMS IT all', vms_by_page(), rng2),
              per_word('Latin Secreta', text_by_page(sec[:34000]), rng2, top=10)]
    (DATA / 'diag_repetition_words.json').write_text(json.dumps(detail, indent=1))
