"""Prepare inputs for the word-unit homophonic solver (wordunit_solve.mjs).

Hypothesis tested: each Voynich word encodes a short plaintext string of 1 to
LMAX letters (a letter, letter pair, or syllable-sized group); one plaintext
string may have many Voynich spellings (homophones); plaintext spaces are not
represented. Greshko's Naibbe cipher belongs to this family.

Outputs (in ../data):
  lm_latin_all.txt, lm_latin_noSecreta.txt, lm_italian.txt  -- one document
      per line, letters only, alphabet ALPHA
  wu_<name>.json -- {streams_train, streams_test, truth_train?, truth_test?}
      each stream is a list of tokens (str) or null for a break
"""
import json
import random
from collections import defaultdict

from common import paragraph_lines, corpus_words, DATA, LATIN_FILES
from naibbe_like import NaibbeLike

ALPHA = 'abcdefghilmnopqrstuxyz'


def to_alpha(word):
    word = word.replace('j', 'i').replace('v', 'u').replace('k', 'c').replace('w', 'u')
    return ''.join(c for c in word if c in ALPHA)


def write_lm(name, docs):
    with open(DATA / name, 'w', encoding='utf-8') as fh:
        for words in docs:
            # split long documents into ~5,000-letter lines (context resets are rare)
            letters = ''.join(to_alpha(w) for w in words)
            for i in range(0, len(letters), 5000):
                fh.write(letters[i:i + 5000] + '\n')


def split(streams, rng, frac=0.2, truth=None):
    idx = list(range(len(streams)))
    rng.shuffle(idx)
    ntest = int(len(idx) * frac)
    test, train = sorted(idx[:ntest]), sorted(idx[ntest:])
    out = {'streams_train': [streams[i] for i in train],
           'streams_test': [streams[i] for i in test]}
    if truth is not None:
        out['truth_train'] = [truth[i] for i in train]
        out['truth_test'] = [truth[i] for i in test]
    return out


def vms_streams(require, source='IT'):
    """One stream per paragraph; unknown tokens become breaks (None).
    Drawing gaps and line ends do not break the stream."""
    pars = defaultdict(list)
    pages = {}
    for line in paragraph_lines(source, require):
        pars[line['par_id']].extend(line['tokens'])
        pages[line['par_id']] = line['folio']
    return [pars[k] for k in sorted(pars)], [pages[k] for k in sorted(pars)]


def shuffle_within_page(streams, pages, rng):
    by_page = defaultdict(list)
    for i, p in enumerate(pages):
        by_page[p].append(i)
    out = [list(s) for s in streams]
    for idxs in by_page.values():
        pool = [t for i in idxs for t in streams[i] if t is not None]
        rng.shuffle(pool)
        it = iter(pool)
        for i in idxs:
            out[i] = [next(it) if t is not None else None for t in streams[i]]
    return out


def control_streams(words, cipher, rng, n_tokens, stream_len=45):
    letters = ''.join(to_alpha(w) for w in words)
    enc = cipher.encrypt(letters, rng, opaque=True)[:n_tokens]
    streams, truth = [], []
    for i in range(0, len(enc), stream_len):
        chunk = enc[i:i + stream_len]
        streams.append([t for t, _ in chunk])
        truth.append([u for _, u in chunk])
    return streams, truth


if __name__ == '__main__':
    rng = random.Random(4082026)
    lat = corpus_words('latin')
    ita = corpus_words('italian')
    write_lm('lm_latin_all.txt', [lat[f] for f in LATIN_FILES])
    write_lm('lm_latin_noSecreta.txt', [lat[f] for f in LATIN_FILES if f != 'Secreta_Secretorum_LAT'])
    # in-domain LM for controls: everything except the first 25,000 Secreta words,
    # which are reserved as control plaintext
    write_lm('lm_latin_ctrl_indomain.txt', [lat[f] for f in LATIN_FILES if f != 'Secreta_Secretorum_LAT']
             + [lat['Secreta_Secretorum_LAT'][25000:]])
    write_lm('lm_italian.txt', [ita['Rettorica']])

    for name, req in [('vmsA', {'L': 'A'}), ('vmsB', {'L': 'B'})]:
        streams, pages = vms_streams(req)
        (DATA / f'wu_{name}.json').write_text(json.dumps(split(streams, random.Random(1))))
        shuf = shuffle_within_page(streams, pages, rng)
        (DATA / f'wu_{name}_shuffled.json').write_text(json.dumps(split(shuf, random.Random(1))))
        n = sum(t is not None for s in streams for t in s)
        print(name, 'paragraph streams', len(streams), 'tokens', n)

    sec = lat['Secreta_Secretorum_LAT']
    alphabet = sorted(set(''.join(to_alpha(w) for w in sec)))
    for name, tables, weights, ntok in [
            ('ctrl_naibbe6_11k', 6, (5, 2, 2, 2, 1, 1), 11000),
            ('ctrl_naibbe6_23k', 6, (5, 2, 2, 2, 1, 1), 23000),
            ('ctrl_naibbe12_23k', 12, (5, 3, 3, 2, 2, 2, 1, 1, 1, 1, 1, 1), 23000)]:
        cipher = NaibbeLike(alphabet, seed=11, tables=tables, weights=weights)
        streams, truth = control_streams(sec, cipher, rng, ntok)
        obj = split(streams, random.Random(1), truth=truth)
        (DATA / f'wu_{name}.json').write_text(json.dumps(obj))
        flat = [t for s in streams for t in s]
        sh = list(flat)
        rng.shuffle(sh)
        it = iter(sh)
        shuf = [[next(it) for _ in s] for s in streams]
        (DATA / f'wu_{name}_shuffled.json').write_text(json.dumps(split(shuf, random.Random(1), truth=truth)))
        print(name, 'tokens', len(flat), 'types', len(set(flat)))
