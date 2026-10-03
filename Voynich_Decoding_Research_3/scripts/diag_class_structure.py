"""Language-independent test of hidden letter structure.

Cluster the symbols of a stream into K classes so that the class-bigram
likelihood is maximal (cluster_parts.mjs), for the real stream and for the same
symbols shuffled. The gain per token, real minus shuffled, measures how much
order structure a K-class 'alphabet' can capture. A letter-level homophonic
cipher hides a strongly ordered letter stream, so it should score high even
though its individual symbols look unpredictable. No language model is used.
"""
import json
import random
import subprocess
import math
from pathlib import Path

from common import paragraph_lines, corpus_words, DATA
from prep_partunit import split_core

ROOT = Path(__file__).resolve().parent


def run_cluster(name, streams, K=40, seed=1):
    path = DATA / f'cs_{name}.json'
    path.write_text(json.dumps({'streams': streams}))
    out = subprocess.run(['node', str(ROOT / 'cluster_parts.mjs'), f'in={path}', f'K={K}', 'iters=40', f'seed={seed}'],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out.strip().splitlines()[-1])['objective']


def bigrams(streams):
    return sum(1 for s in streams for a, b in zip(s, s[1:]) if a is not None and b is not None)


def shuffled(streams, rng):
    flat = [x for s in streams for x in s if x is not None]
    rng.shuffle(flat)
    it = iter(flat)
    return [[None if x is None else next(it) for x in s] for s in streams]


def measure(name, words, rng, K=40, parse=None):
    """words: streams of word tokens. parse: word -> list of piece symbols.
    The null shuffles WORDS (never pieces), then parses, so within-word piece
    order is kept in both the real and the shuffled stream."""
    to = (lambda ws: [[p for t in s for p in ((parse(t) if t else None) or [None])] for s in ws]) if parse else (lambda ws: ws)
    streams = to(words)
    real = run_cluster(name, streams, K)
    shuf = run_cluster(name + '_shuffled', to(shuffled(words, rng)), K)
    n = bigrams(streams)
    row = {'text': name, 'tokens_in_bigrams': n, 'K': K,
           'gain_bits_per_token': round((real - shuf) / n / math.log(2), 4)}
    print(json.dumps(row))
    return row


def chunk(words, size=45):
    return [words[i:i + size] for i in range(0, len(words), size)]


if __name__ == '__main__':
    rng = random.Random(4)
    rows = []
    ctrl = json.loads((DATA / 'su_ctrl_vmslike_11k.json').read_text())
    cs = ctrl['streams_train'] + ctrl['streams_test']
    ta = ctrl['true_analysis']
    rows.append(measure('control_whole_words', cs, rng))
    rows.append(measure('control_true_pieces', cs, rng, parse=lambda t: ta.get(t)))
    core = lambda t: [f'{r}:{p}' for r, p in split_core(t)]
    rows.append(measure('control_core_rule_pieces', cs, rng, parse=core))
    for req, nm in (({'L': 'A'}, 'A'), ({'L': 'B'}, 'B')):
        pars = {}
        for line in paragraph_lines('IT', req):
            pars.setdefault(line['par_id'], []).extend(line['tokens'])
        vs = list(pars.values())
        if nm == 'B':
            # cut to the control's size for a like-for-like comparison
            flat = [t for s in vs for t in s][:11000]
            vs = chunk(flat)
        rows.append(measure(f'voynich_{nm}_whole_words', vs, rng))
        rows.append(measure(f'voynich_{nm}_core_rule_pieces', vs, rng, parse=core))
    lat = corpus_words('latin')['Secreta_Secretorum_LAT'][:11000]
    rows.append(measure('latin_words', chunk(lat), rng))
    rows.append(measure('latin_letters', chunk(list(''.join(lat[:3000]))[:16000]), rng))
    (DATA / 'diag_class_structure.json').write_text(json.dumps(rows, indent=1))
