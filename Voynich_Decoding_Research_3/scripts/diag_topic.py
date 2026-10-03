"""Diagnostic 2: do word distributions follow subject matter or scribe?

For two groups of pages, measure mutual information between word type and
group label (bits per token). Bias is removed by subtracting the mean after
permuting whole pages between the two groups. Pages stay intact, so page-level
clustering of words is present in both observed and permuted data.

If Voynich words were homophonic codes for single letters or letter pairs
(a Naibbe-type cipher), a change of subject by the same scribe should move the
word distribution only slightly, as letter frequencies change little between
subjects. Plaintext words in a natural language move much more.
"""
from collections import Counter, defaultdict
import json
import math
import random

from common import paragraph_lines, corpus_words, DATA
from naibbe_like import NaibbeLike


def mi_from_pages(pages_a, pages_b, min_count=5):
    ca = Counter(t for p in pages_a for t in p)
    cb = Counter(t for p in pages_b for t in p)
    tot = ca + cb
    keep = {w for w, c in tot.items() if c >= min_count}
    def fold(c):
        out = Counter()
        for w, n in c.items():
            out[w if w in keep else '<rare>'] += n
        return out
    ca, cb = fold(ca), fold(cb)
    na, nb = sum(ca.values()), sum(cb.values())
    n = na + nb
    mi = 0.0
    for w in set(ca) | set(cb):
        for c, ng in ((ca[w], na), (cb[w], nb)):
            if c:
                mi += c / n * math.log2(c * n / (ng * (ca[w] + cb[w])))
    return mi


def topic_test(name, pages_a, pages_b, rng, perms=200):
    obs = mi_from_pages(pages_a, pages_b)
    pool = pages_a + pages_b
    null = []
    for _ in range(perms):
        rng.shuffle(pool)
        null.append(mi_from_pages(pool[:len(pages_a)], pool[len(pages_a):]))
    mean = sum(null) / perms
    sd = (sum((x - mean) ** 2 for x in null) / (perms - 1)) ** 0.5
    row = {'comparison': name, 'pages': [len(pages_a), len(pages_b)],
           'tokens': [sum(map(len, pages_a)), sum(map(len, pages_b))],
           'observed_bits': round(obs, 4), 'permuted_mean_bits': round(mean, 4),
           'excess_bits': round(obs - mean, 4),
           'z': round((obs - mean) / sd, 1) if sd else None}
    print(json.dumps(row))
    return row


def vms_pages(require, source='IT'):
    pages = defaultdict(list)
    for line in paragraph_lines(source, require):
        pages[line['folio']].extend(t for t in line['tokens'] if t)
    return [p for p in pages.values() if len(p) >= 20]


def chunk(words, size):
    return [words[i:i + size] for i in range(0, len(words) - size + 1, size)]


def naibbe_pages(words, size, cipher, rng):
    letters = ''.join(words)
    toks = [t for t, _ in cipher.encrypt(letters, rng)]
    return chunk(toks, size)


if __name__ == '__main__':
    rng = random.Random(408)
    rows = []
    H1A_herbal = vms_pages({'H': '1', 'L': 'A', 'I': 'H'})
    H1A_pharma = vms_pages({'H': '1', 'L': 'A', 'I': 'P'})
    H2B_herbal = vms_pages({'H': '2', 'L': 'B', 'I': 'H'})
    H2B_bio = vms_pages({'H': '2', 'L': 'B', 'I': 'B'})
    H3B_stars = vms_pages({'H': '3', 'L': 'B', 'I': 'S'})
    H3B_herbal = vms_pages({'H': '3', 'L': 'B', 'I': 'H'})
    H5B_herbal = vms_pages({'H': '5', 'L': 'B', 'I': 'H'})
    print('pages', len(H1A_herbal), len(H1A_pharma), len(H2B_herbal), len(H2B_bio),
          len(H3B_stars), len(H3B_herbal), len(H5B_herbal))
    rows.append(topic_test('VMS same scribe 1 (A): herbal vs pharma', H1A_herbal, H1A_pharma, rng))
    rows.append(topic_test('VMS same scribe 2 (B): herbal vs biological', H2B_herbal, H2B_bio, rng))
    rows.append(topic_test('VMS same scribe 3 (B): herbal vs stars', H3B_herbal, H3B_stars, rng))
    rows.append(topic_test('VMS same subject herbal: scribe 1 (A) vs scribe 2 (B)', H1A_herbal, H2B_herbal, rng))
    rows.append(topic_test('VMS same subject herbal B: scribe 2 vs scribe 3', H2B_herbal, H3B_herbal, rng))
    rows.append(topic_test('VMS same subject herbal B: scribe 2 vs scribe 5', H2B_herbal, H5B_herbal, rng))
    rows.append(topic_test('VMS split-half control: scribe 2 bio odd vs even pages', H2B_bio[::2], H2B_bio[1::2], rng))
    rows.append(topic_test('VMS split-half control: scribe 1 herbal odd vs even pages', H1A_herbal[::2], H1A_herbal[1::2], rng))

    lat = corpus_words('latin')
    sec, bru, aix, steg = (lat['Secreta_Secretorum_LAT'], lat['BrunoDeMagia'],
                           lat['Latin_Aix'], lat['Steganographia'])
    size = 150
    pa, pb = chunk(sec[:9000], size), chunk(bru[:9000], size)
    rows.append(topic_test('Latin words: Secreta vs Bruno De magia', pa, pb, rng))
    pa2, pb2 = chunk(sec[:9000], size), chunk(sec[20000:29000], size)
    rows.append(topic_test('Latin words: Secreta part 1 vs part 3 (same work)', pa2, pb2, rng))
    pa3, pb3 = chunk(aix[:9000], size), chunk(steg[:9000], size)
    rows.append(topic_test('Latin words: Albert of Aix vs Steganographia', pa3, pb3, rng))

    alphabet = sorted(set(''.join(sec + bru + aix + steg)))
    cipher = NaibbeLike(alphabet, seed=7)
    # Same plaintext as above; ~1.5 letters per token, so take enough letters
    # for a similar token count and page count.
    for label, wa, wb in [('Secreta vs Bruno De magia', sec[:9000], bru[:9000]),
                          ('Secreta part 1 vs part 3 (same work)', sec[:9000], sec[20000:29000]),
                          ('Albert of Aix vs Steganographia', aix[:9000], steg[:9000])]:
        na = naibbe_pages(wa, size, cipher, rng)
        nb = naibbe_pages(wb, size, cipher, rng)
        k = min(len(na), len(nb), 60)
        rows.append(topic_test('Naibbe-like cipher of Latin: ' + label, na[:k], nb[:k], rng))
    (DATA / 'diag_topic.json').write_text(json.dumps(rows, indent=1))
