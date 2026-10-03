"""A Naibbe-style verbose homophonic cipher used only as a positive control.

This follows the general design described by Greshko (2025): plaintext letters
are regrouped into unigrams and bigrams; each unit becomes one cipher 'word';
a bigram word is a prefix for its first letter plus a suffix for its second;
the table used for each letter is drawn at random with unequal weights.

It is NOT Greshko's published table set and it is NOT a Voynich key. Glyph
strings are drawn from common Voynich word beginnings and endings so that the
control's word forms look superficially Voynich-like.
"""
import random

PREFIXES = ['qok', 'qot', 'ok', 'ot', 'ch', 'sh', 'd', 's', 'o', 'y', 'cth',
            'ckh', 'l', 'r', 'qo', 'p', 'f', 't', 'k', 'che', 'she', 'cho',
            'sho', 'ol', 'or', 'ar', 'al', 'da', 'sa', 'cph', 'yk', 'yt', 'lk',
            'qopch', 'op', 'tch', 'kch', 'pch', 'dch', 'lch', 'qoke', 'oke',
            'ote', 'chk', 'sch', 'cfh', 'dai', 'oka', 'ota', 'qoka']
SUFFIXES = ['edy', 'eedy', 'eey', 'ey', 'y', 'dy', 'aiin', 'ain', 'ar', 'al',
            'ol', 'or', 'am', 'an', 'iin', 'eol', 'eor', 'hy', 'o', 's', 'd',
            'l', 'r', 'eo', 'ody', 'oly', 'ory', 'aly', 'ary', 'om', 'airy',
            'aiiin', 'eeo', 'eody', 'ees', 'chy', 'shy', 'ckhy', 'cthy', 'ky',
            'ty', 'ldy', 'rdy', 'iir', 'eos', 'edar', 'kain', 'tain', 'keey',
            'teey']
UNIGRAMS = ['daiin', 'ol', 'or', 'ar', 'aiin', 'chol', 'chey', 's', 'y', 'dy',
            'al', 'dar', 'dal', 'sho', 'cho', 'qoky', 'oky', 'shy', 'chy',
            'okal', 'otar', 'sain', 'dain', 'saiin', 'qol', 'kar', 'tar', 'ky',
            'ty', 'am', 'dam', 'sam', 'okar', 'chor', 'shor', 'cheol', 'sheol',
            'chdy', 'shdy', 'kchy', 'tchy', 'oly', 'ory', 'aly', 'ary', 'chal',
            'shal', 'cham', 'oiin', 'yky']


class NaibbeLike:
    def __init__(self, alphabet, seed=1, tables=6, weights=(5, 2, 2, 2, 1, 1),
                 p_unigram=0.5):
        rng = random.Random(seed)
        self.alphabet = list(alphabet)
        self.weights = list(weights)[:tables]
        self.tables = tables
        self.p_unigram = p_unigram
        n = len(self.alphabet)
        assert n * tables <= len(PREFIXES) * 6
        # Every (table, letter) gets distinct strings in each role.
        def assign(pool):
            combos = []
            while len(combos) < n * tables:
                combos.extend(rng.sample(pool, len(pool)))
            combos = combos[:n * tables]
            return {(t, L): combos[t * n + i] + ('' if t == 0 else '')
                    for t in range(tables) for i, L in enumerate(self.alphabet)}
        self.pre = assign(PREFIXES)
        self.suf = assign(SUFFIXES)
        self.uni = assign(UNIGRAMS)
        # Make the decryption unambiguous by tagging repeated strings with a
        # table-specific variant marker in the generated token id.

    def encrypt(self, letters, rng, opaque=False):
        """Return list of (token_id, plaintext_unit).

        opaque=True returns unambiguous ids (table and letter index) instead of
        Voynich-looking strings, so that the true key is exactly recoverable."""
        out, i = [], 0
        idx = {L: k for k, L in enumerate(self.alphabet)}
        while i < len(letters):
            t1 = rng.choices(range(self.tables), self.weights)[0]
            if i == len(letters) - 1 or rng.random() < self.p_unigram:
                L = letters[i]
                out.append((f'U{t1}.{idx[L]}' if opaque else f'U{t1}:{self.uni[(t1, L)]}', L))
                i += 1
            else:
                t2 = rng.choices(range(self.tables), self.weights)[0]
                a, b = letters[i], letters[i + 1]
                out.append((f'P{t1}.{idx[a]}+S{t2}.{idx[b]}' if opaque
                            else f'{self.pre[(t1, a)]}{self.suf[(t2, b)]}', a + b))
                i += 2
        return out
