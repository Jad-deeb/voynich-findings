"""Test 4a: vocabulary size and once-only words at a matched 34,000 words."""
import json
from collections import Counter

from common import paragraph_lines, corpus_words, DATA


def stats(name, toks, rows):
    toks = toks[:34000]
    c = Counter(toks)
    h = sum(1 for v in c.values() if v == 1)
    r = {'text': name, 'tokens': len(toks), 'types': len(c),
         'hapax_share_of_types': round(h / len(c), 2), 'hapax_share_of_tokens': round(h / len(toks), 3)}
    print(json.dumps(r))
    rows.append(r)


if __name__ == '__main__':
    rows = []
    for src in ('IT', 'ZL'):
        stats('VMS ' + src, [t for l in paragraph_lines(src) for t in l['tokens'] if t], rows)
    lat = corpus_words('latin')
    ita = corpus_words('italian')
    eng = corpus_words('english', files=['Cirurgie', 'AlphabetOfTales'])
    stats('Latin Secreta', lat['Secreta_Secretorum_LAT'], rows)
    stats('Latin Albert of Aix', lat['Latin_Aix'], rows)
    stats('Italian Rettorica', ita['Rettorica'], rows)
    stats('Middle English Cirurgie', eng['Cirurgie'], rows)
    stats('Middle English Alphabet of Tales', eng['AlphabetOfTales'], rows)
    (DATA / 'diag_vocabulary.json').write_text(json.dumps(rows, indent=1))
