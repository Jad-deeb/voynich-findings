"""Word order test: dependence between words at distance d = 1, 2, 3 inside the
same line, each as excess over a position-aware page shuffle. Natural-language
order: dependence falls with distance. Words scrambled within lines: flat.
Also the glyph coupling (last glyph of word i, first glyph of word i+d)."""
import json, random
from collections import defaultdict
from common import corpus_words, DATA
from diag_boundaries import mi
from diag_wordseq2 import shuffle_by_class
from diag_bible import by_page_from_tokens, vms_by_page
from naibbe_like import NaibbeLike

def pairs_d(bp, d, edge=False):
    out = []
    for runs in bp.values():
        for run, _ in runs:
            for i in range(len(run) - d):
                a, b = run[i], run[i + d]
                out.append((a[-1], b[0]) if edge else (a, b))
    return out

def profile(name, bp, rng, reps=20):
    row = {'text': name}
    for d in (1, 2, 3):
        for edge in (False, True):
            obs = mi(pairs_d(bp, d, edge))
            null = sum(mi(pairs_d(shuffle_by_class(bp, rng), d, edge)) for _ in range(reps)) / reps
            row[f"{'edge' if edge else 'word'}_d{d}"] = round(obs - null, 4)
    print(json.dumps(row)); return row

def scramble_lines(bp, rng):
    out = {}
    for p, runs in bp.items():
        new = []
        for run, pf in runs:
            r = list(run); rng.shuffle(r); new.append((r, pf))
        out[p] = new
    return out

if __name__ == '__main__':
    rng = random.Random(12)
    rows = [profile('Voynich IT', vms_by_page(), rng)]
    lat = corpus_words('latin')
    sec = lat['Secreta_Secretorum_LAT'][:34000]
    bp = by_page_from_tokens(sec)
    rows.append(profile('Latin Secreta (prose order)', bp, rng))
    rows.append(profile('Latin Secreta, words scrambled within 9-word lines', scramble_lines(bp, rng), rng))
    ita = corpus_words('italian')['Rettorica'][:34000]
    rows.append(profile('Italian Rettorica (prose order)', by_page_from_tokens(ita), rng))
    ci = NaibbeLike(sorted(set(''.join(sec))), seed=7)
    toks = [t for t, _ in ci.encrypt(''.join(sec[:23000]), rng)][:34000]
    rows.append(profile('Naibbe-like cipher of Latin', by_page_from_tokens(toks), rng))
    (DATA / 'diag_distance.json').write_text(json.dumps(rows, indent=1))
