"""Diagnostic 1: how strongly does a word's last glyph predict the next word's
first glyph?  Natural-language word spaces carry little such coupling; a
script whose spaces are inserted by rule, or whose 'words' are fragments of a
continuous stream, may carry much more.

Excess mutual information = observed MI minus the mean MI after shuffling
tokens within each page (keeps the page's vocabulary and all line slots).
"""
from collections import Counter, defaultdict
import json
import math
import random
import sys

from common import paragraph_lines, segments, corpus_words, DATA


def mi(pairs):
    n = len(pairs)
    joint = Counter(pairs)
    left = Counter(a for a, _ in pairs)
    right = Counter(b for _, b in pairs)
    return sum(c / n * math.log2(c * n / (left[a] * right[b]))
               for (a, b), c in joint.items())


def edge_pairs(runs, k=1):
    out = []
    for run in runs:
        for a, b in zip(run, run[1:]):
            out.append((a[-k:], b[:k]))
    return out


def page_shuffle(runs_by_page, rng):
    shuffled = []
    for runs in runs_by_page.values():
        pool = [t for run in runs for t in run]
        rng.shuffle(pool)
        it = iter(pool)
        shuffled.extend([[next(it) for _ in run] for run in runs])
    return shuffled


def vms_runs(require=None, source='IT'):
    by_page = defaultdict(list)
    for line in paragraph_lines(source, require):
        for run in segments(line):
            by_page[line['folio']].append(run)
    return by_page


def text_runs(words, line_len=9, page_len=300):
    by_page = defaultdict(list)
    for i in range(0, len(words) - line_len, line_len):
        by_page[i // page_len].append(words[i:i + line_len])
    return by_page


def report(name, by_page, rng, shuffles=50, k=1):
    runs = [r for rs in by_page.values() for r in rs]
    obs = mi(edge_pairs(runs, k))
    null = [mi(edge_pairs(page_shuffle(by_page, rng), k)) for _ in range(shuffles)]
    mean = sum(null) / len(null)
    sd = (sum((x - mean) ** 2 for x in null) / (len(null) - 1)) ** 0.5
    n = sum(len(r) - 1 for r in runs)
    row = {'text': name, 'k': k, 'pairs': n, 'observed_MI_bits': round(obs, 4),
           'shuffle_mean_bits': round(mean, 4), 'excess_bits': round(obs - mean, 4),
           'z': round((obs - mean) / sd, 1) if sd else None}
    print(json.dumps(row))
    return row


if __name__ == '__main__':
    rng = random.Random(20261003)
    rows = []
    for k in (1, 2):
        rows.append(report('VMS IT all paragraphs', vms_runs(), rng, k=k))
        rows.append(report('VMS IT Currier A', vms_runs({'L': 'A'}), rng, k=k))
        rows.append(report('VMS IT Currier B', vms_runs({'L': 'B'}), rng, k=k))
        rows.append(report('VMS ZL all paragraphs', vms_runs(source='ZL'), rng, k=k))
        lat = corpus_words('latin')
        ita = corpus_words('italian')
        rows.append(report('Latin Secreta (35k words)', text_runs(lat['Secreta_Secretorum_LAT'][:35000]), rng, k=k))
        rows.append(report('Latin Aix (35k words)', text_runs(lat['Latin_Aix'][:35000]), rng, k=k))
        rows.append(report('Italian Rettorica (35k words)', text_runs(ita['Rettorica'][:35000]), rng, k=k))
    (DATA / 'diag_boundaries.json').write_text(json.dumps(rows, indent=1))
