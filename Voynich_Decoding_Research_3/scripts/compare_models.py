"""Run the round-4 fingerprint on the two published 'how it was made' models:

  Timm and Schinner's self-citation generator (no message):
      github.com/TorstenTimm/SelfCitationTextgenerator, executable/generate/generated_text.txt
  Greshko's Naibbe cipher (a real Latin message, Pliny's Natural History):
      github.com/greshko/naibbe-cipher, encrypted/nathist_output_ciphertext.txt

Both texts were downloaded to work/models/. The manuscript is measured on the
same number of words as each model text where vocabulary size matters."""
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

from common import paragraph_lines, segments, DATA
from diag_bible import fingerprint
from diag_distance import profile
from diag_junction import test as junction_test
from diag_spaces import evaluate as space_eval
from diag_variants import jsd

MODELS = Path(__file__).resolve().parents[3] / 'work' / 'models'


def read_timm():
    lines = [l.split() for l in (MODELS / 'timm_generated_text.txt').read_text(encoding='utf-8').splitlines()
             if l.strip() and not l.startswith('#')]
    bp = defaultdict(list)
    for i, l in enumerate(lines):
        bp[i // 29].append((l, False))           # 29 lines per page, as configured
    return bp


def read_naibbe():
    raw = (MODELS / 'naibbe_nathist_ciphertext.txt').read_text(encoding='utf-8').splitlines()
    bp, page, n = defaultdict(list), 0, 0
    for l in raw:
        w = l.split()
        if not w:
            continue
        bp[page].append((w, False))
        n += 1
        if n % 29 == 0:
            page += 1
    return bp


def vms(limit=None):
    bp, n = defaultdict(list), 0
    for line in paragraph_lines('IT'):
        for run in segments(line):
            if limit and n >= limit:
                return bp
            bp[line['folio']].append((run, line['line_in_par'] == 0))
            n += len(run)
    return bp


def variant_ratios(bp):
    ctx = defaultdict(list)
    for runs in bp.values():
        for run, _ in runs:
            for i, w in enumerate(run):
                ctx[w].append((run[i - 1][-1] if i else '^', run[i + 1][0] if i + 1 < len(run) else '$'))
    out = {}
    rng = random.Random(3)
    for a, b in [('k', 't'), ('ch', 'sh'), ('ee', 'e'), ('aiin', 'ain'), ('ol', 'or')]:
        jp, js = [], []
        for w in list(ctx):
            i = w.find(a)
            if i < 0:
                continue
            w2 = w[:i] + b + w[i + len(a):]
            if w2 == w or w2 not in ctx or len(ctx[w]) < 10 or len(ctx[w2]) < 10:
                continue
            o1, o2 = ctx[w], ctx[w2]
            jp.append((jsd(Counter(x[1] for x in o1), Counter(x[1] for x in o2)) + jsd(Counter(x[0] for x in o1), Counter(x[0] for x in o2))) / 2)
            big = o1 if len(o1) >= len(o2) else o2
            sh = big[:]; rng.shuffle(sh); h = len(sh) // 2
            js.append((jsd(Counter(x[1] for x in sh[:h]), Counter(x[1] for x in sh[h:])) + jsd(Counter(x[0] for x in sh[:h]), Counter(x[0] for x in sh[h:]))) / 2)
        if jp:
            out[f'{a}/{b}'] = {'pairs': len(jp), 'ratio': round((sum(jp) / len(jp)) / (sum(js) / len(js)), 2)}
    return out


def run(name, bp, rng):
    fp = fingerprint(name, bp, rng, reps=12)
    dp = profile(name, bp, rng, reps=8)
    jt = junction_test(name, bp, rng, reps=12)
    lines = [run_ for runs in bp.values() for run_, _ in runs if len(run_) >= 2]
    sp = space_eval(lines, 2)
    row = {**fp, **{k: v for k, v in dp.items() if k != 'text'},
           'beyond_junction': jt['excess_beyond_edges_bits'],
           'space_accuracy': sp['accuracy'], 'space_explained': sp['explained_share'],
           'variants': variant_ratios(bp)}
    return row


if __name__ == '__main__':
    rng = random.Random(11)
    timm, naibbe = read_timm(), read_naibbe()
    nt = sum(len(r) for v in timm.values() for r, _ in v)
    nn = sum(len(r) for v in naibbe.values() for r, _ in v)
    rows = [run(f'Timm-Schinner generator ({nt} words)', timm, rng),
            run(f'Voynich, first {nt} words', vms(nt), rng),
            run(f'Greshko Naibbe cipher of Latin ({nn} words)', naibbe, rng),
            run('Voynich, all paragraph text', vms(), rng)]
    (DATA / 'compare_models.json').write_text(json.dumps(rows, indent=1))
    print()
    keys = ['rep_per_1000', 'rep_ratio', 'types', 'hapax_share', 'word_d1', 'word_d2', 'word_d3', 'edge_d1', 'beyond_junction', 'space_accuracy', 'wlen_mean', 'wlen_sd']
    print(f"{'':44s}" + ''.join(f'{k[:11]:>12s}' for k in keys))
    for r in rows:
        print(f"{r['text'][:44]:44s}" + ''.join(f'{r[k]:12.3f}' if isinstance(r[k], float) else f'{r[k]:12d}' for k in keys))
    for r in rows:
        print(r['text'][:44], 'variant context ratios:', r['variants'])
