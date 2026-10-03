"""Naibbe-type variants: do a larger table set or habitual reuse of the spelling
table reproduce the manuscript's vocabulary, repetition and section shift?"""
import json
import random
from collections import Counter

from common import corpus_words, DATA
from naibbe_like import NaibbeLike
from diag_wordseq2 import text_by_page, shuffle_by_class
from diag_topic import topic_test, chunk


class Sticky(NaibbeLike):
    """Keeps the previous letter's table with probability `stay`."""
    def __init__(self, *a, stay=0.8, **k):
        super().__init__(*a, **k)
        self.stay = stay

    def encrypt(self, letters, rng, opaque=True):
        out, i, t = [], 0, 0
        idx = {L: k for k, L in enumerate(self.alphabet)}

        def pick(t):
            return t if rng.random() < self.stay else rng.choices(range(self.tables), self.weights)[0]
        while i < len(letters):
            t = pick(t)
            if i == len(letters) - 1 or rng.random() < self.p_unigram:
                out.append((f'U{t}.{idx[letters[i]]}', letters[i]))
                i += 1
            else:
                t2 = pick(t)
                out.append((f'P{t}.{idx[letters[i]]}+S{t2}.{idx[letters[i + 1]]}', letters[i:i + 2]))
                i += 2
        return out


def rep_ratio(toks, rng, reps=50):
    bp = text_by_page(toks)

    def same(b):
        return sum(a == c for runs in b.values() for run, _ in runs for a, c in zip(run, run[1:]))
    obs = same(bp)
    null = sum(same(shuffle_by_class(bp, rng)) for _ in range(reps)) / reps
    return round(obs / null, 2) if null else None


if __name__ == '__main__':
    rng = random.Random(8)
    lat = corpus_words('latin')
    sec, bru = lat['Secreta_Secretorum_LAT'], lat['BrunoDeMagia']
    alpha = sorted(set(''.join(sec + bru)))
    rows = []
    for tables in (6, 12):
        w = (5, 2, 2, 2, 1, 1) if tables == 6 else (5, 3, 3, 2, 2, 2, 1, 1, 1, 1, 1, 1)
        for stay in (0.0, 0.5, 0.8, 0.95):
            ci = Sticky(alpha, seed=11, tables=tables, weights=w, stay=stay)
            toks = [t for t, _ in ci.encrypt(''.join(sec[:23000]), rng)][:34000]
            c = Counter(toks)
            hap = sum(1 for v in c.values() if v == 1)
            rr = rep_ratio(toks, rng)
            a = chunk([t for t, _ in ci.encrypt(''.join(sec[:9000]), rng)], 150)
            b = chunk([t for t, _ in ci.encrypt(''.join(bru[:9000]), rng)], 150)
            k = min(len(a), len(b), 60)
            tt = topic_test(f'tables={tables} stay={stay}', a[:k], b[:k], rng, perms=100)
            row = {'tables': tables, 'stay': stay, 'types_per_34k': len(c),
                   'hapax_share_of_types': round(hap / len(c), 2),
                   'repetition_ratio': rr, 'topic_excess_bits': tt['excess_bits']}
            print(json.dumps(row))
            rows.append(row)
    (DATA / 'diag_sticky_naibbe.json').write_text(json.dumps(rows, indent=1))
