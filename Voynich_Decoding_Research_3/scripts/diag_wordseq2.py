"""Diagnostic 3b: adjacent-word dependence with a position-aware null.

The Voynich text has strong line-position effects (first and last words of a
line differ from medial words; paragraph-first lines differ). A page-level
shuffle mixes those position-specific vocabularies and inflates the plug-in
MI of the shuffled data, so the null must preserve position classes.

Here tokens are shuffled only among slots of the same class within a page:
class = (first line of paragraph?, first/medial/last in line run).
"""
from collections import defaultdict
import json
import math
import random

from common import paragraph_lines, segments, corpus_words, DATA
from naibbe_like import NaibbeLike
from diag_boundaries import mi


def slot_class(i, n, par_first):
    pos = 'F' if i == 0 else ('L' if i == n - 1 else 'M')
    return (par_first, pos)


def build(lines_by_page):
    """lines_by_page: page -> list of (run, par_first)."""
    return lines_by_page


def pairs(by_page, medial_only):
    out = []
    for runs in by_page.values():
        for run, _ in runs:
            seq = run[1:-1] if medial_only else run
            out.extend(zip(seq, seq[1:]))
    return out


def shuffle_by_class(by_page, rng):
    new = {}
    for page, runs in by_page.items():
        pools = defaultdict(list)
        for run, pf in runs:
            for i, t in enumerate(run):
                pools[slot_class(i, len(run), pf)].append(t)
        for p in pools.values():
            rng.shuffle(p)
        its = {k: iter(v) for k, v in pools.items()}
        new[page] = [([next(its[slot_class(i, len(run), pf)]) for i in range(len(run))], pf)
                     for run, pf in runs]
    return new


def run_test(name, by_page, rng, shuffles=30, medial_only=False):
    obs = mi(pairs(by_page, medial_only))
    null = [mi(pairs(shuffle_by_class(by_page, rng), medial_only)) for _ in range(shuffles)]
    mean = sum(null) / len(null)
    sd = (sum((x - mean) ** 2 for x in null) / (len(null) - 1)) ** 0.5
    row = {'text': name, 'medial_only': medial_only,
           'pairs': len(pairs(by_page, medial_only)),
           'observed_bits': round(obs, 4), 'null_mean_bits': round(mean, 4),
           'excess_bits': round(obs - mean, 4), 'z': round((obs - mean) / sd, 1)}
    print(json.dumps(row))
    return row


def vms_by_page(require=None, source='IT'):
    by_page = defaultdict(list)
    for line in paragraph_lines(source, require):
        for run in segments(line):
            by_page[line['folio']].append((run, line['line_in_par'] == 0))
    return by_page


def text_by_page(words, line_len=9, page_len=270):
    by_page = defaultdict(list)
    for i in range(0, len(words) - line_len + 1, line_len):
        by_page[i // page_len].append((words[i:i + line_len], False))
    return by_page


if __name__ == '__main__':
    rng = random.Random(99)
    rows = []
    lat = corpus_words('latin')
    ita = corpus_words('italian')
    for medial in (False, True):
        rows.append(run_test('VMS IT all paragraphs', vms_by_page(), rng, medial_only=medial))
        rows.append(run_test('VMS IT Currier A', vms_by_page({'L': 'A'}), rng, medial_only=medial))
        rows.append(run_test('VMS IT Currier B', vms_by_page({'L': 'B'}), rng, medial_only=medial))
        rows.append(run_test('VMS ZL all paragraphs', vms_by_page(source='ZL'), rng, medial_only=medial))
        for nm in ['Secreta_Secretorum_LAT', 'Latin_Aix']:
            rows.append(run_test('Latin ' + nm, text_by_page(lat[nm][:34000]), rng, medial_only=medial))
        rows.append(run_test('Italian Rettorica', text_by_page(ita['Rettorica'][:34000]), rng, medial_only=medial))
        sec = lat['Secreta_Secretorum_LAT']
        cipher = NaibbeLike(sorted(set(''.join(sec))), seed=7)
        toks = [t for t, _ in cipher.encrypt(''.join(sec[:23000]), rng)][:34000]
        rows.append(run_test('Naibbe-like cipher of Latin Secreta', text_by_page(toks), rng, medial_only=medial))
    (DATA / 'diag_wordseq2.json').write_text(json.dumps(rows, indent=1))
