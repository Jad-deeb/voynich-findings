"""Glyph-level Markov chains as the simplest possible 'no deeper structure' model.

Train an order-k model over EVA glyphs plus the word space (line breaks reset the
context) on the manuscript's paragraph text, sample text with the manuscript's
exact line lengths (in words) and page layout, and measure the same fingerprint.
If a short glyph context reproduces every word-sequence statistic, the word
stream carries no measurable structure beyond k glyphs. The same is done with
Latin prose as a reference (a Latin letter chain loses Latin's word grammar)."""
import json
import random
from collections import defaultdict, Counter

from common import paragraph_lines, segments, corpus_words, DATA
from diag_bible import fingerprint, by_page_from_tokens
from diag_distance import profile


def train(lines, k):
    model = defaultdict(Counter)
    for words in lines:
        s = '^' * k + ' '.join(words) + '$'
        for i in range(k, len(s)):
            model[s[i - k:i]][s[i]] += 1
    return model


def sample_line(model, k, nwords, rng, maxlen=400):
    ctx, out, words = '^' * k, [], 0
    while len(out) < maxlen:
        c = model.get(ctx)
        if not c:
            break
        chars, weights = zip(*c.items())
        ch = rng.choices(chars, weights)[0]
        if ch == '$' or (ch == ' ' and words + 1 >= nwords):
            break
        if ch == ' ':
            words += 1
        out.append(ch)
        ctx = (ctx + ch)[-k:]
    return [w for w in ''.join(out).split(' ') if w]


def vms_layout():
    bp = defaultdict(list)
    for line in paragraph_lines('IT'):
        for run in segments(line):
            bp[line['folio']].append((run, line['line_in_par'] == 0))
    return bp


if __name__ == '__main__':
    rng = random.Random(21)
    real = vms_layout()
    lines = [r for runs in real.values() for r, _ in runs]
    rows = []
    for k in (2, 3, 4, 6):
        m = train(lines, k)
        gen = {p: [(sample_line(m, k, len(r), rng) or ['y'], pf) for r, pf in runs] for p, runs in real.items()}
        name = f'Voynich glyph Markov chain, order {k}'
        fp = fingerprint(name, gen, rng, reps=10)
        dp = profile(name, gen, rng, reps=8)
        rows.append({**fp, **{x: v for x, v in dp.items() if x != 'text'}})
    lat = corpus_words('latin')['Secreta_Secretorum_LAT'][:34000]
    lbp = by_page_from_tokens(lat)
    m = train([r for runs in lbp.values() for r, _ in runs], 4)
    gen = {p: [(sample_line(m, 4, len(r), rng) or ['et'], pf) for r, pf in runs] for p, runs in lbp.items()}
    fp = fingerprint('Latin letter Markov chain, order 4', gen, rng, reps=10)
    dp = profile('Latin letter Markov chain, order 4', gen, rng, reps=8)
    rows.append({**fp, **{x: v for x, v in dp.items() if x != 'text'}})
    (DATA / 'markov_baseline.json').write_text(json.dumps(rows, indent=1))
    print()
    keys = ['rep_per_1000', 'rep_ratio', 'types', 'hapax_share', 'word_d1', 'word_d2', 'edge_d1', 'wlen_mean', 'wlen_sd']
    print(f"{'':40s}" + ''.join(f'{k[:11]:>12s}' for k in keys))
    for r in rows:
        print(f"{r['text'][:40]:40s}" + ''.join(f'{r[k]:12.3f}' if isinstance(r[k], float) else f'{r[k]:12d}' for k in keys))
