"""Positive controls for the multi-language sweep: Voynich-looking Naibbe-style
ciphers of non-Bible texts in other languages, to be solved with the Bible
language model of that language (so the model is out of domain, as it would be
for the manuscript).

  Spanish: Picatrix (Spanish edition)    -> lm_bible_Spanish
  English: Cirurgie (Middle English)     -> lm_bible_English
  Italian: Rettorica                     -> lm_bible_Italian
"""
import json
import random
import re
import unicodedata

from common import CORPORA, DATA
from prep_splitunit import vms_looking_cipher, encrypt, add_analyses
from prep_wordunit import split

SOURCES = {'Spanish': 'Picatrix', 'English': 'Cirurgie', 'Italian': 'Rettorica'}


def letters_of(name, alphabet):
    t = unicodedata.normalize('NFKD', (CORPORA / name).read_text(encoding='utf-8', errors='replace').lower())
    t = t.replace('þ', 'th').replace('ȝ', 'gh')
    t = ''.join(c for c in t if not unicodedata.combining(c))
    return ''.join(c for c in t if c in alphabet)


if __name__ == '__main__':
    alph = json.loads((DATA / 'lm_bible_alphabets.json').read_text())
    rng = random.Random(99)
    for lang, src in SOURCES.items():
        alphabet = alph[lang]['alphabet']
        letters = letters_of(src, alphabet)
        P, S, U, idx = vms_looking_cipher(sorted(set(letters)), rng)
        enc = encrypt(letters, P, S, U, idx, rng)[:11000]
        streams = [[t for t, _ in enc[i:i + 45]] for i in range(0, len(enc), 45)]
        truth = [[u for _, u in enc[i:i + 45]] for i in range(0, len(enc), 45)]
        obj, nP, nS = add_analyses(split(streams, random.Random(1), truth=truth))
        pset, sset, uset = set(P), set(S), set(U)
        true_an = {}
        for t in obj['analyses']:
            if t in uset:
                true_an[t] = ['U:' + t]
            else:
                for k in range(1, len(t)):
                    if t[:k] in pset and t[k:] in sset:
                        true_an[t] = ['P:' + t[:k], 'S:' + t[k:]]
        obj['true_analysis'] = true_an
        (DATA / f'su_ctrl_{lang}_11k.json').write_text(json.dumps(obj))
        flat = [t for s in streams for t in s]
        print(lang, src, 'letters', len(letters), 'types', len(set(flat)), 'alphabet', alphabet)
