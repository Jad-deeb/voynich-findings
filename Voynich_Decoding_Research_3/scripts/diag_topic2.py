"""Topic test restricted to line-medial tokens of non-initial paragraph lines,
and the word types that contribute most to each contrast."""
from collections import Counter, defaultdict
import json, math, random
from common import paragraph_lines, segments, DATA
from diag_topic import topic_test


def medial_pages(require, source='IT'):
    pages = defaultdict(list)
    for line in paragraph_lines(source, require):
        if line['line_in_par'] == 0:
            continue
        for run in segments(line):
            pages[line['folio']].extend(run[1:-1])
    return [p for p in pages.values() if len(p) >= 15]


def contributors(pa, pb, top=12):
    ca, cb = Counter(t for p in pa for t in p), Counter(t for p in pb for t in p)
    na, nb = sum(ca.values()), sum(cb.values())
    rows = []
    for w in set(ca) | set(cb):
        a, b = ca[w], cb[w]
        if a + b < 10:
            continue
        # signed log-likelihood contribution
        e_a = (a + b) * na / (na + nb)
        e_b = (a + b) * nb / (na + nb)
        g = 2 * sum(o * math.log(o / e) for o, e in ((a, e_a), (b, e_b)) if o)
        rows.append((g, w, a, b, round(1000 * a / na, 1), round(1000 * b / nb, 1)))
    rows.sort(reverse=True)
    return rows[:top]


if __name__ == '__main__':
    rng = random.Random(5)
    groups = {
        'H1A herbal': {'H': '1', 'L': 'A', 'I': 'H'},
        'H1A pharma': {'H': '1', 'L': 'A', 'I': 'P'},
        'H2B herbal': {'H': '2', 'L': 'B', 'I': 'H'},
        'H2B bio': {'H': '2', 'L': 'B', 'I': 'B'},
    }
    P = {k: medial_pages(v) for k, v in groups.items()}
    out = []
    for a, b in [('H1A herbal', 'H1A pharma'), ('H2B herbal', 'H2B bio'), ('H1A herbal', 'H2B herbal')]:
        out.append(topic_test(f'medial tokens only: {a} vs {b}', P[a], P[b], rng))
        print('  top contributors (G, word, count_a, count_b, per-mille a, per-mille b):')
        for row in contributors(P[a], P[b]):
            print('   ', row)
    (DATA / 'diag_topic2.json').write_text(json.dumps(out, indent=1))
