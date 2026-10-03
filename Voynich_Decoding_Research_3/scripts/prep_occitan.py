"""Medieval Occitan language model from COMETA (Zenodo 15300719, CC BY 4.0;
work/cometa/*.txt), with Fran_ais_1049.txt held out to build a control cipher."""
import json, random, re, unicodedata
from pathlib import Path
from common import DATA
from prep_wordunit import split
from prep_splitunit import vms_looking_cipher, encrypt, add_analyses
CM = Path(__file__).resolve().parents[3] / 'work' / 'cometa'
ALPHA = 'abcdefghilmnopqrstuxyz'
def norm(t):
    t = unicodedata.normalize('NFKD', t.lower())
    t = ''.join(c for c in t if not unicodedata.combining(c)).replace('v', 'u').replace('j', 'i').replace('k', 'c').replace('w', 'u')
    return ''.join(c for c in re.sub(r'[^a-z]', '', t) if c in ALPHA)
if __name__ == '__main__':
    files = sorted(CM.glob('*.txt'))
    held = [p for p in files if p.name == 'Fran_ais_1049.txt']
    rest = [p for p in files if p not in held]
    for name, ps in (('lm_oc_noheld.txt', rest), ('lm_oc.txt', files)):
        L = ''.join(norm(p.read_text(encoding='utf-8', errors='replace')) for p in ps)
        (DATA / name).write_text('\n'.join(L[i:i + 5000] for i in range(0, len(L), 5000)))
        print(name, len(L))
    letters = norm(held[0].read_text(encoding='utf-8', errors='replace'))
    rng = random.Random(1323)
    P, S, U, idx = vms_looking_cipher(sorted(set(letters)), rng)
    enc = encrypt(letters, P, S, U, idx, rng)[:11000]
    streams = [[t for t, _ in enc[i:i + 45]] for i in range(0, len(enc), 45)]
    truth = [[u for _, u in enc[i:i + 45]] for i in range(0, len(enc), 45)]
    obj, _, _ = add_analyses(split(streams, random.Random(1), truth=truth))
    (DATA / 'su_ctrl_oc_11k.json').write_text(json.dumps(obj))
    print('control letters', len(letters))
