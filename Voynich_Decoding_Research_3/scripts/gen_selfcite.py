"""A simplified self-citation generator (after Timm and Schinner's description):
each new word is a copy of a word written shortly before, mostly from the line
above near the same position, changed by a few glyph substitutions or prefix /
ending changes. No plaintext is involved.

Generated pages are then measured with the same statistics used for the
manuscript, to see which parts of the manuscript's fingerprint such a process
reproduces. Line lengths and paragraph/page sizes are copied from the IT file.
"""
import json
import random
import re
from collections import defaultdict

from common import paragraph_lines, segments, DATA

SUBS = [('k', 't'), ('t', 'k'), ('p', 'f'), ('f', 'p'), ('k', 'p'), ('t', 'f'),
        ('ch', 'sh'), ('sh', 'ch'), ('ee', 'e'), ('e', 'ee'), ('a', 'o'), ('o', 'a'),
        ('l', 'r'), ('r', 'l'), ('aiin', 'ain'), ('ain', 'aiin'), ('aiin', 'ar'), ('ar', 'aiin'),
        ('dy', 'y'), ('y', 'dy'), ('edy', 'eey'), ('eey', 'edy'), ('ol', 'or'), ('or', 'ol'),
        ('d', 's'), ('s', 'd'), ('ckh', 'cth'), ('cth', 'ckh'), ('ok', 'ot'), ('ot', 'ok')]
PREFIXES = ['qo', 'o', 'y', 'l', 'd', 's', 'ch', 'sh', '']
ENDINGS = ['aiin', 'ain', 'eedy', 'edy', 'eey', 'ey', 'dy', 'y', 'ar', 'al', 'ol', 'or', 'am', 's', 'l', 'r', 'o']


def mutate(w, rng, rate):
    """Few local edits that keep words in the manuscript's length range:
    glyph substitutions, swapping the prefix, swapping the ending."""
    n = 0
    while rng.random() < rate and n < 3:
        n += 1
        r = rng.random()
        cand = w
        if r < 0.55:
            a, b = rng.choice(SUBS)
            idx = [m.start() for m in re.finditer(re.escape(a), w)]
            if idx:
                i = rng.choice(idx)
                cand = w[:i] + b + w[i + len(a):]
        elif r < 0.75:
            cur = next((p for p in sorted(PREFIXES, key=len, reverse=True) if p and w.startswith(p)), '')
            cand = rng.choice(PREFIXES) + w[len(cur):]
        else:
            cur = next((e for e in sorted(ENDINGS, key=len, reverse=True) if w.endswith(e)), '')
            cand = w[:len(w) - len(cur)] + rng.choice(ENDINGS)
        if 2 <= len(cand) <= 10:
            w = cand
    return w


def generate(shape, seeds, rng, rate=0.8, p_above=0.65, p_line=0.2, window=2, p_fresh=0.01):
    """shape: list of pages -> list of (line length, paragraph-first flag)."""
    pages, prev_lines = [], []
    for page in shape:
        lines = []
        for n, pf in page:
            line = []
            above = prev_lines[-1] if prev_lines else None
            for j in range(n):
                r = rng.random()
                if r < p_fresh or (not above and not line):
                    src = rng.choice(seeds)
                elif r < p_fresh + p_above and above:
                    k = min(len(above) - 1, max(0, j + rng.randint(-window, window)))
                    src = above[k]
                elif line and r < p_fresh + p_above + p_line:
                    src = rng.choice(line[-3:])
                else:
                    pool = [w for l in prev_lines[-4:] for w in l] or seeds
                    src = rng.choice(pool)
                line.append(mutate(src, rng, rate))
            lines.append((line, pf))
            prev_lines.append(line)
            prev_lines = prev_lines[-6:]
        pages.append(lines)
    return pages


def manuscript_shape(require=None):
    by_page = defaultdict(list)
    for line in paragraph_lines('IT', require):
        n = sum(len(r) for r in segments(line))
        if n:
            by_page[line['folio']].append((n, line['line_in_par'] == 0))
    return list(by_page.values())


if __name__ == '__main__':
    from diag_bible import fingerprint
    from diag_distance import profile
    from diag_topic import topic_test
    rng = random.Random(1)
    shape = manuscript_shape()
    seeds = ['daiin', 'chol', 'chedy', 'qokeedy', 'shedy', 'ol', 'or', 'ar', 'chey', 'okaiin', 'qokain', 'dar', 'shol', 'cthy', 'sain']
    rows = []
    for rate, p_above in [(0.6, 0.65), (0.9, 0.65), (0.9, 0.4), (1.2, 0.5)]:
        pages = generate(shape, seeds, random.Random(7), rate=rate, p_above=p_above)
        bp = {i: [(l, pf) for l, pf in p] for i, p in enumerate(pages)}
        name = f'self-citation rate={rate} p_above={p_above}'
        fp = fingerprint(name, bp, rng, reps=20)
        dp = profile(name, bp, rng, reps=10)
        # 'section' shift: first 40 pages vs pages 120-160 (positions of herbal vs biological blocks)
        pa = [[w for l, _ in p for w in l] for p in pages[:40]]
        pb = [[w for l, _ in p for w in l] for p in pages[120:160]]
        tt = topic_test(name + ' early vs late pages', pa, pb, rng, perms=100)
        near = [[w for l, _ in p for w in l] for p in pages[:40:2]], [[w for l, _ in p for w in l] for p in pages[1:40:2]]
        tn = topic_test(name + ' odd vs even pages', near[0], near[1], rng, perms=100)
        rows.append({**fp, **{k: v for k, v in dp.items() if k != 'text'}, 'block_shift_bits': tt['excess_bits'], 'odd_even_shift_bits': tn['excess_bits']})
    (DATA / 'gen_selfcite.json').write_text(json.dumps(rows, indent=1))
    print('sample line:', ' '.join(generate(shape[:2], seeds, random.Random(3), rate=0.9)[1][2][0]))
