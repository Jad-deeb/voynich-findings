"""Baseline for diag_variants: the same context-divergence measure for Latin and
Italian word pairs that differ by one letter (c/t, e/i, o/u, a/e, m/s, n/m)."""
import json, math, random, re
from collections import Counter, defaultdict
from common import corpus_words, DATA
from diag_variants import jsd

PAIRS = [('c', 't'), ('e', 'i'), ('o', 'u'), ('a', 'e'), ('m', 's'), ('n', 'm')]

def run(name, words, rng):
    ctx = defaultdict(list)
    lines = [words[i:i + 9] for i in range(0, len(words) - 9, 9)]
    for run_ in lines:
        for i, w in enumerate(run_):
            ctx[w].append((run_[i - 1][-1] if i else '^', run_[i + 1][0] if i + 1 < len(run_) else '$'))
    rows = []
    for a, b in PAIRS:
        jp, js = [], []
        for w in list(ctx):
            for mm in re.finditer(a, w):
                w2 = w[:mm.start()] + b + w[mm.end():]
                if w2 == w or w2 not in ctx: continue
                o1, o2 = ctx[w], ctx[w2]
                if len(o1) < 10 or len(o2) < 10: continue
                jp.append((jsd(Counter(x[1] for x in o1), Counter(x[1] for x in o2)) + jsd(Counter(x[0] for x in o1), Counter(x[0] for x in o2))) / 2)
                big = o1 if len(o1) >= len(o2) else o2
                sh = big[:]; rng.shuffle(sh); h = len(sh) // 2
                js.append((jsd(Counter(x[1] for x in sh[:h]), Counter(x[1] for x in sh[h:])) + jsd(Counter(x[0] for x in sh[:h]), Counter(x[0] for x in sh[h:]))) / 2)
        if jp:
            r = {'text': name, 'pair': f'{a}/{b}', 'word_pairs': len(jp), 'context_divergence_pairs': round(sum(jp) / len(jp), 4),
                 'context_divergence_same_word_halves': round(sum(js) / len(js), 4)}
            print(json.dumps(r)); rows.append(r)
    return rows

if __name__ == '__main__':
    rng = random.Random(3)
    lat = corpus_words('latin'); ita = corpus_words('italian')
    rows = run('Latin (all, 300k words)', sum((lat[k] for k in lat), [])[:300000], rng)
    rows += run('Italian Rettorica', ita['Rettorica'], rng)
    (DATA / 'diag_variants_latin.json').write_text(json.dumps(rows, indent=1))
