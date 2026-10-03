"""Period German (and Old Czech) language models from HistCorp (Zenodo 10013189,
CC BY 4.0), downloaded to work/histcorp/.

  lm_de_herbal15.txt  - Buch der Natur 1482, Artzney Buechlein 1532, Brunfels 1532,
                        Bock 1539, Fuchs 1543 (Gart der Gesundheit 1487 held out for
                        the control)
  lm_de_herbal15_all.txt - the same plus Gart der Gesundheit (for the manuscript)
  lm_de_bible15.txt   - Mentelin Bible 1460 and Cologne Bible 1478
  lm_de_mhg.txt       - Reference Corpus of Middle High German (1050-1350)
  lm_cs_old.txt       - Diakorp Czech texts dated before 1600
Spelling: lower case, diacritics removed, long s -> s, u/v and i/j merged.
Control: Voynich-looking Naibbe-style cipher of Gart der Gesundheit (11,000 words).
"""
import json
import random
import re
import unicodedata
from pathlib import Path

from common import DATA
from prep_wordunit import split
from prep_splitunit import vms_looking_cipher, encrypt, add_analyses

HC = Path(__file__).resolve().parents[3] / 'work' / 'histcorp'
ALPHA = 'abcdefghiklmnopqrstuwxyz'


def body(path):
    lines = path.read_text(encoding='utf-8', errors='replace').splitlines()
    return '\n'.join(l for l in lines if not l.startswith('#'))


def norm(text):
    text = text.replace('ſ', 's').replace('ß', 'ss').replace('æ', 'ae').replace('œ', 'oe')
    text = unicodedata.normalize('NFKD', text.lower())
    text = ''.join(c for c in text if not unicodedata.combining(c))
    text = text.replace('v', 'u').replace('j', 'i')
    return re.sub(r'[^a-z]', '', text.replace('\n', ' '))


def write(name, texts):
    letters = ''.join(norm(t) for t in texts)
    letters = ''.join(c for c in letters if c in ALPHA)
    (DATA / name).write_text('\n'.join(letters[i:i + 5000] for i in range(0, len(letters), 5000)))
    print(name, len(letters))
    return letters


if __name__ == '__main__':
    rid = HC / 'german-ridges-txt' / 'german' / 'ridges' / 'txt'
    early = [p for p in rid.glob('*.txt') if re.search(r'_(14\d\d|15[0-4]\d)_', p.name) and '-VR' not in p.name
             and not re.search(r'-(c\d|C|X|L)', p.name.split('_')[0])]
    gart = [p for p in early if 'GartDerGesundheit' in p.name]
    others = [p for p in early if p not in gart]
    print('early herbals:', sorted(p.name for p in early))
    write('lm_de_herbal15.txt', [body(p) for p in others])
    write('lm_de_herbal15_all.txt', [body(p) for p in early])
    edges = HC / 'german-edges-txt' / 'german' / 'openEdges'
    write('lm_de_bible15.txt', [body(p) for d in ('de_1460_Mentelin', 'de_1478_Kölner') for p in (edges / d / 'txt').glob('*.txt')])
    write('lm_de_mhg.txt', [body(p) for p in (HC / 'german-ReM-txt' / 'german' / 'ReM' / 'txt').glob('*.txt')])
    cz = HC / 'czech-diakorp-txt' / 'czech' / 'diakorp' / 'txt'
    old = [p for p in cz.glob('*.txt') if int(re.search(r'-(\d{4})', p.name).group(1)) < 1600]
    print('old Czech files', len(old))
    cz_letters = ''.join(norm(body(p)) for p in old)
    cz_alpha = ''.join(sorted(c for c in set(cz_letters) if cz_letters.count(c) / max(1, len(cz_letters)) > 2e-4))
    (DATA / 'lm_cs_old.txt').write_text('\n'.join(cz_letters[i:i + 5000] for i in range(0, len(cz_letters), 5000)))
    print('lm_cs_old.txt', len(cz_letters), cz_alpha)
    json.dump({'de': ALPHA, 'cs_old': cz_alpha}, open(DATA / 'lm_period_alphabets.json', 'w'))
    # control: Gart der Gesundheit, held out from lm_de_herbal15
    rng = random.Random(1487)
    letters = ''.join(c for c in ''.join(norm(body(p)) for p in gart) if c in ALPHA)
    P, S, U, idx = vms_looking_cipher(sorted(set(letters)), rng)
    enc = encrypt(letters, P, S, U, idx, rng)[:11000]
    streams = [[t for t, _ in enc[i:i + 45]] for i in range(0, len(enc), 45)]
    truth = [[u for _, u in enc[i:i + 45]] for i in range(0, len(enc), 45)]
    obj, _, _ = add_analyses(split(streams, random.Random(1), truth=truth))
    (DATA / 'su_ctrl_gart_11k.json').write_text(json.dumps(obj))
    print('control from Gart der Gesundheit: letters available', len(letters))
