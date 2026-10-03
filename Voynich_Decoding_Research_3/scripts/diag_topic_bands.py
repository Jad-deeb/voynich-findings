"""Which words carry the subject/section difference? Split the excess mutual
information (word type vs page group) into the 50 most frequent types and the
rest. Excess = observed minus mean over page permutations, per band."""
from collections import Counter
import json, math, random
from common import corpus_words, DATA
from diag_topic import vms_pages, chunk

def band_mi(pa, pb, top):
    ca, cb = Counter(t for p in pa for t in p), Counter(t for p in pb for t in p)
    na, nb = sum(ca.values()), sum(cb.values()); n = na + nb
    out = {'top': 0.0, 'rest': 0.0}
    for w in set(ca) | set(cb):
        tw = ca[w] + cb[w]
        for c, ng in ((ca[w], na), (cb[w], nb)):
            if c:
                out['top' if w in top else 'rest'] += c / n * math.log2(c * n / (ng * tw))
    return out

def run(name, pa, pb, rng, perms=200, k=50):
    allc = Counter(t for p in pa + pb for t in p)
    top = {w for w, _ in allc.most_common(k)}
    obs = band_mi(pa, pb, top)
    pool = pa + pb; acc = {'top': 0.0, 'rest': 0.0}
    for _ in range(perms):
        rng.shuffle(pool)
        r = band_mi(pool[:len(pa)], pool[len(pa):], top)
        for key in acc: acc[key] += r[key] / perms
    ex = {key: obs[key] - acc[key] for key in obs}
    tot = ex['top'] + ex['rest']
    row = {'comparison': name, 'excess_top50_bits': round(ex['top'], 4), 'excess_rest_bits': round(ex['rest'], 4),
           'share_from_top50': round(ex['top'] / tot, 2) if tot > 0 else None,
           'top50_token_share': round(sum(allc[w] for w in top) / sum(allc.values()), 2)}
    print(json.dumps(row)); return row

rng = random.Random(21)
rows = []
rows.append(run('VMS scribe 1 (A): herbal vs pharma', vms_pages({'H': '1', 'L': 'A', 'I': 'H'}), vms_pages({'H': '1', 'L': 'A', 'I': 'P'}), rng))
rows.append(run('VMS scribe 2 (B): herbal vs biological', vms_pages({'H': '2', 'L': 'B', 'I': 'H'}), vms_pages({'H': '2', 'L': 'B', 'I': 'B'}), rng))
lat = corpus_words('latin')
sec, bru, aix, steg = lat['Secreta_Secretorum_LAT'], lat['BrunoDeMagia'], lat['Latin_Aix'], lat['Steganographia']
rows.append(run('Latin: Secreta vs Bruno De magia', chunk(sec[:9000], 150), chunk(bru[:9000], 150), rng))
rows.append(run('Latin: Secreta part 1 vs part 3', chunk(sec[:9000], 150), chunk(sec[20000:29000], 150), rng))
rows.append(run('Latin: Albert of Aix vs Steganographia', chunk(aix[:9000], 150), chunk(steg[:9000], 150), rng))
(DATA / 'diag_topic_bands.json').write_text(json.dumps(rows, indent=1))
