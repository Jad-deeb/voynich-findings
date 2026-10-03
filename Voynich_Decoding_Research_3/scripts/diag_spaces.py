"""How predictable are word spaces from the glyphs around them?

Each text is turned into a stream of characters with the word breaks as labels
(only inside lines). For every position between two characters, predict
'space / no space' from the k characters before and after (k = 1, 2, 3).
Trained on even lines, tested on odd lines; reported as held-out conditional
entropy (bits per gap) and as the share of gaps whose label the best guess gets
right. If spaces are inserted by a glyph rule, they are nearly deterministic.
"""
import json
import math
from collections import Counter, defaultdict

from common import paragraph_lines, segments, corpus_words, DATA
from naibbe_like import NaibbeLike


def gaps(lines, k):
    out = []
    for words in lines:
        s = ' '.join(words)
        chars, labels = [], []
        for i, ch in enumerate(s):
            if ch == ' ':
                labels[-1] = 1
                continue
            chars.append(ch)
            labels.append(0)
        pad = '^' * k + ''.join(chars) + '$' * k
        for i in range(len(chars) - 1):
            left = pad[i + 1:i + k + 1]
            right = pad[i + k + 1:i + 2 * k + 1]
            out.append((left + '|' + right, labels[i]))
    return out


def evaluate(lines, k):
    train = gaps(lines[0::2], k)
    test = gaps(lines[1::2], k)
    c = defaultdict(Counter)
    for ctx, y in train:
        c[ctx][y] += 1
    prior = Counter(y for _, y in train)
    p1 = prior[1] / sum(prior.values())
    h = 0.0
    right = 0
    for ctx, y in test:
        n = c.get(ctx)
        if n:
            p = (n[1] + p1) / (n[0] + n[1] + 1)
        else:
            p = p1
        h -= math.log2(p if y == 1 else 1 - p)
        right += (p >= 0.5) == (y == 1)
    base = -(p1 * math.log2(p1) + (1 - p1) * math.log2(1 - p1))
    return {'k': k, 'gaps': len(test), 'space_rate': round(p1, 3),
            'entropy_bits_per_gap': round(h / len(test), 4), 'prior_entropy': round(base, 4),
            'explained_share': round(1 - (h / len(test)) / base, 3), 'accuracy': round(right / len(test), 4)}


def vms_lines(source='IT'):
    out = []
    for line in paragraph_lines(source):
        for run in segments(line):
            if len(run) >= 2:
                out.append(run)
    return out


def chunks(words, n=9):
    return [words[i:i + n] for i in range(0, len(words) - n + 1, n)]


if __name__ == '__main__':
    rows = []
    texts = {'Voynich IT': vms_lines('IT'), 'Voynich ZL': vms_lines('ZL')}
    lat = corpus_words('latin')
    texts['Latin Secreta'] = chunks(lat['Secreta_Secretorum_LAT'][:34000])
    texts['Italian Rettorica'] = chunks(corpus_words('italian')['Rettorica'][:34000])
    sec = lat['Secreta_Secretorum_LAT']
    import random
    ci = NaibbeLike(sorted(set(''.join(sec))), seed=7)
    toks = [t.split(':')[-1] for t, _ in ci.encrypt(''.join(sec[:23000]), random.Random(1))][:34000]
    texts['Naibbe-like cipher'] = chunks(toks)
    for name, lines in texts.items():
        for k in (1, 2, 3):
            r = evaluate(lines, k)
            r['text'] = name
            print(json.dumps(r))
            rows.append(r)
    (DATA / 'diag_spaces.json').write_text(json.dumps(rows, indent=1))
