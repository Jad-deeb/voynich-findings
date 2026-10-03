"""Is the manuscript's neighbour-word dependence fully explained by the glyphs at
the junction? Null: shuffle words within page, line-position class AND the same
(first glyph, last glyph) pair, so junction glyph statistics are kept exactly.
Remaining excess MI = dependence between neighbouring words beyond their edges."""
import json, random
from collections import defaultdict
from common import corpus_words, DATA
from diag_boundaries import mi
from diag_wordseq2 import slot_class
from diag_bible import by_page_from_tokens, vms_by_page
from naibbe_like import NaibbeLike

def edge_key(w): return (w[0], w[-1])

def shuffle_keep_edges(bp, rng):
    new = {}
    for page, runs in bp.items():
        pools = defaultdict(list)
        for run, pf in runs:
            for i, t in enumerate(run): pools[(slot_class(i, len(run), pf), edge_key(t))].append(t)
        for p in pools.values(): rng.shuffle(p)
        its = {k: iter(v) for k, v in pools.items()}
        new[page] = [([next(its[(slot_class(i, len(run), pf), edge_key(t))]) for i, t in enumerate(run)], pf) for run, pf in runs]
    return new

def pairs(bp): return [(a, b) for runs in bp.values() for run, _ in runs for a, b in zip(run, run[1:])]

def test(name, bp, rng, reps=30):
    obs = mi(pairs(bp))
    null = [mi(pairs(shuffle_keep_edges(bp, rng))) for _ in range(reps)]
    m = sum(null) / reps; sd = (sum((x - m) ** 2 for x in null) / (reps - 1)) ** 0.5
    row = {'text': name, 'excess_beyond_edges_bits': round(obs - m, 4), 'z': round((obs - m) / sd, 1)}
    print(json.dumps(row)); return row

if __name__ == '__main__':
    rng = random.Random(4)
    rows = [test('Voynich IT', vms_by_page(), rng)]
    lat = corpus_words('latin'); sec = lat['Secreta_Secretorum_LAT'][:34000]
    rows.append(test('Latin Secreta', by_page_from_tokens(sec), rng))
    rows.append(test('Latin Albert of Aix', by_page_from_tokens(lat['Latin_Aix'][:34000]), rng))
    rows.append(test('Italian Rettorica', by_page_from_tokens(corpus_words('italian')['Rettorica'][:34000]), rng))
    ci = NaibbeLike(sorted(set(''.join(sec))), seed=7)
    toks = [t.split(':')[-1] for t, _ in ci.encrypt(''.join(sec[:23000]), rng)][:34000]
    rows.append(test('Naibbe-like cipher (Voynich-looking strings)', by_page_from_tokens(toks), rng))
    (DATA / 'diag_junction.json').write_text(json.dumps(rows, indent=1))
