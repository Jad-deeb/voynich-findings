"""Single-section inputs for the learned-split solver, in case each section or
scribe used its own key: herbal A (scribe 1), bathing/biological B (scribe 2),
stars B (scribe 3). Plus a Middle English language model from period texts and a
Middle English control solved with it."""
import json, random, re, unicodedata
from collections import defaultdict
from common import paragraph_lines, DATA, CORPORA
from prep_wordunit import split, shuffle_within_page
from prep_splitunit import add_analyses, vms_looking_cipher, encrypt

def streams_for(req):
    pars, pages = defaultdict(list), {}
    for line in paragraph_lines('IT', req):
        pars[line['par_id']].extend(line['tokens']); pages[line['par_id']] = line['folio']
    keys = sorted(pars)
    return [pars[k] for k in keys], [pages[k] for k in keys]

def me_letters(name):
    t = unicodedata.normalize('NFKD', (CORPORA / name).read_text(encoding='utf-8', errors='replace').lower())
    t = t.replace('þ', 'th').replace('ȝ', 'gh').replace('ð', 'th')
    t = ''.join(c for c in t if not unicodedata.combining(c))
    return re.sub(r'[^a-z]', '', t)

if __name__ == '__main__':
    rng = random.Random(8)
    for name, req in [('herbalA1', {'H': '1', 'L': 'A', 'I': 'H'}), ('bioB2', {'H': '2', 'L': 'B', 'I': 'B'}), ('starsB3', {'H': '3', 'L': 'B', 'I': 'S'})]:
        s, p = streams_for(req)
        obj, _, _ = add_analyses(split(s, random.Random(1)))
        (DATA / f'su_{name}.json').write_text(json.dumps(obj))
        obj2, _, _ = add_analyses(split(shuffle_within_page(s, p, rng), random.Random(1)))
        (DATA / f'su_{name}_shuffled.json').write_text(json.dumps(obj2))
        print(name, 'tokens', sum(t is not None for x in s for t in x))
    # Middle English language model (Alphabet of Tales + Secretum ENG) and a control from Cirurgie
    lm = me_letters('AlphabetOfTales') + me_letters('Secreta_Secretorum_ENG')
    alpha = ''.join(sorted(c for c in set(lm) if lm.count(c) / len(lm) > 2e-4))
    (DATA / 'lm_middle_english.txt').write_text('\n'.join(lm[i:i + 5000] for i in range(0, len(lm), 5000)))
    letters = ''.join(c for c in me_letters('Cirurgie') if c in alpha)
    P, S, U, idx = vms_looking_cipher(sorted(set(letters)), rng)
    enc = encrypt(letters, P, S, U, idx, rng)[:11000]
    streams = [[t for t, _ in enc[i:i + 45]] for i in range(0, len(enc), 45)]
    truth = [[u for _, u in enc[i:i + 45]] for i in range(0, len(enc), 45)]
    obj, _, _ = add_analyses(split(streams, random.Random(1), truth=truth))
    (DATA / 'su_ctrl_ME_11k.json').write_text(json.dumps(obj))
    json.dump({'alphabet': alpha}, open(DATA / 'lm_middle_english_alphabet.json', 'w'))
    print('Middle English LM letters', len(lm), 'alphabet', alpha)
