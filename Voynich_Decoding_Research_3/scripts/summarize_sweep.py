"""Summarise every learned-split / segment solver log in results/: for each
(input, language model) pair, best restart by objective, its held-out gain, and
real-minus-shuffled differences. Writes results/sweep_summary.json."""
import json
import re
from collections import defaultdict
from pathlib import Path

RES = Path(__file__).resolve().parents[1] / 'results'


def read(log):
    rs = []
    for line in log.read_text(encoding='utf-8', errors='replace').splitlines():
        if line.startswith('{"restart"'):
            rs.append(json.loads(line))
    return rs


rows = {}
for log in RES.glob('*.log'):
    m = re.match(r'^(sw|sv|sq|sp|su|sg)_(.+?)__(.+)\.log$', log.name)
    if not m:
        continue
    rs = read(log)
    if not rs:
        continue
    best = max(rs, key=lambda r: r['J'])
    h = best.get('heldout_gain_all', best.get('heldout_gain'))
    rows[(m.group(2), m.group(3))] = {'input': m.group(2), 'lm': m.group(3), 'restarts': len(rs),
                                      'heldout_best': round(h, 3),
                                      'acc': best.get('acc_train'), 'J': round(best['J'], 1)}

out = []
for (inp, lm), r in sorted(rows.items()):
    if inp.endswith('_shuffled') or inp.startswith('ctrl'):
        continue
    sh = rows.get((inp + '_shuffled', lm)) or rows.get((inp.replace('vmsB_', 'vmsB_') + '_shuffled', lm))
    r = dict(r)
    if sh:
        r['heldout_shuffled'] = sh['heldout_best']
        r['real_minus_shuffled'] = round(r['heldout_best'] - sh['heldout_best'], 3)
        r['restarts_shuffled'] = sh['restarts']
    out.append(r)
ctrl = [r for (inp, _), r in rows.items() if inp.startswith('ctrl')]
out.sort(key=lambda r: -(r.get('real_minus_shuffled') or -99))
(RES / 'sweep_summary.json').write_text(json.dumps({'manuscript': out, 'controls': ctrl}, indent=1))
print(f"{'input':22s} {'language model':28s} {'real':>7s} {'shuf':>7s} {'diff':>7s}  restarts")
for r in out:
    print(f"{r['input']:22s} {r['lm'][:28]:28s} {r['heldout_best']:7.2f} {r.get('heldout_shuffled', float('nan')):7.2f} "
          f"{r.get('real_minus_shuffled', float('nan')):7.2f}  {r['restarts']}/{r.get('restarts_shuffled', '-')}")
print('controls:')
for r in ctrl:
    print(f"  {r['input']:22s} {r['lm'][:28]:28s} heldout {r['heldout_best']:6.2f} acc {r['acc']}")
