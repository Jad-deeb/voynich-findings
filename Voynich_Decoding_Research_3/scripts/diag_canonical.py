"""Merge the free-variant glyph alternations (t->k, f->p, sh->ch, cth->ckh,
cph->ckh, cfh->ckh, ee(e)->e, ain/aiiin->aiin, or->ol, ar->al) and re-measure:
vocabulary, repetition, dependence by distance, and repeated word bigrams /
trigrams (phrases). Natural-language prose repeats phrases; the manuscript
famously does not."""
import json, random, re
from collections import Counter
from common import corpus_words, DATA
from diag_bible import vms_by_page, fingerprint, by_page_from_tokens
from diag_distance import profile

def canon(w):
    w = w.replace('cth', 'ckh').replace('cph', 'ckh').replace('cfh', 'ckh')
    w = w.replace('t', 'k').replace('f', 'p').replace('sh', 'ch')
    w = re.sub('e+', 'e', w)
    w = re.sub('ai+n', 'aiin', w)
    w = w.replace('or', 'ol').replace('ar', 'al')
    return w

def phrases(bp, n):
    c = Counter()
    for runs in bp.values():
        for run, _ in runs:
            for i in range(len(run) - n + 1):
                c[tuple(run[i:i + n])] += 1
    tot = sum(c.values())
    rep = sum(v for v in c.values() if v >= 2)
    return round(rep / tot, 4), len(c)

def mapped(bp, f):
    return {p: [([f(w) for w in run], pf) for run, pf in runs] for p, runs in bp.items()}

if __name__ == '__main__':
    rng = random.Random(9)
    rows = []
    vb = vms_by_page()
    lat = by_page_from_tokens(corpus_words('latin')['Secreta_Secretorum_LAT'][:34000])
    for name, bp in [('Voynich IT', vb), ('Voynich IT, variants merged', mapped(vb, canon)), ('Latin Secreta', lat)]:
        fp = fingerprint(name, bp, rng, reps=15)
        dp = profile(name, bp, rng, reps=10)
        r2, _ = phrases(bp, 2); r3, _ = phrases(bp, 3)
        row = {**fp, **{k: v for k, v in dp.items() if k != 'text'}, 'bigram_tokens_in_repeated_bigrams': r2, 'trigram_tokens_in_repeated_trigrams': r3}
        print(json.dumps(row)); rows.append(row)
    (DATA / 'diag_canonical.json').write_text(json.dumps(rows, indent=1))
