"""Diagnostic 3: dependence between adjacent words.

A one-to-one word code (codebook, nomenclator, or a natural language simply
written in an unknown script) preserves adjacent-word statistics exactly, up
to relabelling. So the excess mutual information between adjacent word types
is directly comparable between the manuscript and candidate plaintexts of the
same size. The estimate is bias-corrected by shuffling tokens within pages.

Also reported: the same quantity after a line-position control, keeping only
pairs whose two words are both line-medial (neither first nor last in line).
"""
from collections import Counter, defaultdict
import json
import math
import random

from common import paragraph_lines, segments, corpus_words, DATA
from naibbe_like import NaibbeLike
from diag_boundaries import mi, page_shuffle


def pairs_of(by_page, medial_only=False):
    out = []
    for runs in by_page.values():
        for run in runs:
            seq = run[1:-1] if medial_only else run
            out.extend(zip(seq, seq[1:]))
    return out


def run_test(name, by_page, rng, shuffles=30, medial_only=False):
    obs = mi(pairs_of(by_page, medial_only))
    null = [mi(pairs_of({0: page_shuffle(by_page, rng)}, medial_only)) for _ in range(shuffles)]
    mean = sum(null) / len(null)
    sd = (sum((x - mean) ** 2 for x in null) / (len(null) - 1)) ** 0.5
    toks = [t for runs in by_page.values() for r in runs for t in r]
    row = {'text': name, 'medial_only': medial_only, 'tokens': len(toks),
           'types': len(set(toks)), 'pairs': len(pairs_of(by_page, medial_only)),
           'observed_bits': round(obs, 4), 'shuffle_mean_bits': round(mean, 4),
           'excess_bits': round(obs - mean, 4), 'z': round((obs - mean) / sd, 1)}
    print(json.dumps(row))
    return row


def vms_by_page(require=None, source='IT'):
    by_page = defaultdict(list)
    for line in paragraph_lines(source, require):
        by_page[line['folio']].extend(segments(line))
    return by_page


def text_by_page(words, line_len=9, page_len=270):
    by_page = defaultdict(list)
    for i in range(0, len(words) - line_len + 1, line_len):
        by_page[i // page_len].append(words[i:i + line_len])
    return by_page


if __name__ == '__main__':
    rng = random.Random(99)
    rows = []
    for medial in (False, True):
        rows.append(run_test('VMS IT all paragraphs', vms_by_page(), rng, medial_only=medial))
        rows.append(run_test('VMS IT Currier A', vms_by_page({'L': 'A'}), rng, medial_only=medial))
        rows.append(run_test('VMS IT Currier B', vms_by_page({'L': 'B'}), rng, medial_only=medial))
        rows.append(run_test('VMS ZL all paragraphs', vms_by_page(source='ZL'), rng, medial_only=medial))
        lat = corpus_words('latin')
        ita = corpus_words('italian')
        for nm in ['Secreta_Secretorum_LAT', 'Latin_Aix', 'Steganographia']:
            rows.append(run_test('Latin ' + nm, text_by_page(lat[nm][:34000]), rng, medial_only=medial))
        rows.append(run_test('Latin Bruno+Adso', text_by_page((lat['BrunoDeMagia'] + lat['Latin_Adso'])[:34000]), rng, medial_only=medial))
        rows.append(run_test('Italian Rettorica', text_by_page(ita['Rettorica'][:34000]), rng, medial_only=medial))
        sec = lat['Secreta_Secretorum_LAT']
        cipher = NaibbeLike(sorted(set(''.join(sec))), seed=7)
        toks = [t for t, _ in cipher.encrypt(''.join(sec[:23000]), rng)][:34000]
        rows.append(run_test('Naibbe-like cipher of Latin Secreta', text_by_page(toks), rng, medial_only=medial))
    (DATA / 'diag_wordseq.json').write_text(json.dumps(rows, indent=1))
