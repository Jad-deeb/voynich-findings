"""Could a LOSSY word code of Latin (different plaintext words sharing a codeword)
reproduce the manuscript's fingerprint? Apply simple many-to-one word maps to
Latin prose and measure the Test 1 / Test 4 statistics."""
import json, random, re
from collections import Counter
from common import corpus_words, DATA
from diag_bible import by_page_from_tokens, fingerprint

V = set('aeiouy')
MAPS = {
    'plain words': lambda w: w,
    'consonant skeleton (vowels dropped)': lambda w: re.sub('[aeiouy]', '', w) or w[0],
    'first 3 letters': lambda w: w[:3],
    'first 2 + last 2': lambda w: w[:2] + '-' + w[-2:] if len(w) > 3 else w,
    'first letter + length': lambda w: w[0] + str(len(w)),
    'last 3 letters (endings)': lambda w: w[-3:],
    'stem (drop last 2 letters if long)': lambda w: w[:-2] if len(w) > 4 else w,
    'skeleton of first 4 letters': lambda w: re.sub('[aeiouy]', '', w[:4]) or w[0],
}
if __name__ == '__main__':
    rng = random.Random(6)
    lat = corpus_words('latin')
    words = lat['Secreta_Secretorum_LAT'][:34000]
    rows = []
    for name, f in MAPS.items():
        toks = [f(w) for w in words]
        rows.append(fingerprint('Latin Secreta, ' + name, by_page_from_tokens(toks), rng, reps=20))
    (DATA / 'diag_lossy.json').write_text(json.dumps(rows, indent=1))
