"""Collect part-unit solver results into results/partunit_summary.json and print a table."""
import json
import re
from pathlib import Path

RES = Path(__file__).resolve().parents[1] / 'results'

rows = []
for log in sorted(RES.glob('pu_pu_*.log')):
    final = None
    restarts = []
    for line in log.read_text(encoding='utf-8', errors='replace').splitlines():
        if line.startswith('{"restart"'):
            restarts.append(json.loads(line))
        elif line.startswith('{"data"'):
            final = json.loads(line)
    name = log.stem.replace('pu_pu_', '')
    data, lm = name.split('__')
    row = {'data': data, 'lm': lm, 'finished': final is not None, 'restarts_done': len(restarts)}
    if restarts:
        best = max(restarts, key=lambda r: r['J'])
        hs = [r['heldout_gain_bits_per_token'] for r in restarts]
        row.update({
            'best_J': round(best['J'], 1),
            'train_gain_best': round(best['train_gain_bits_per_token'], 3),
            'heldout_gain_best': round(best['heldout_gain_bits_per_token'], 3),
            'heldout_gain_min': round(min(hs), 3), 'heldout_gain_max': round(max(hs), 3),
            'accuracy_train_best': None if best['accuracy_train'] is None else round(best['accuracy_train'], 4),
            'restart_J_spread': round(max(r['J'] for r in restarts) - min(r['J'] for r in restarts), 1),
        })
    rows.append(row)

(RES / 'partunit_summary.json').write_text(json.dumps(rows, indent=1))
fmt = '{:<34} {:<24} {:>5} {:>9} {:>9} {:>17} {:>8} {:>10}'
print(fmt.format('data', 'language model', 'done', 'train', 'heldout', 'heldout range', 'acc', 'J spread'))
for r in rows:
    if 'best_J' not in r:
        print(fmt.format(r['data'], r['lm'], '0', '', '', '', '', ''))
        continue
    print(fmt.format(r['data'], r['lm'], f"{r['restarts_done']}{'' if r['finished'] else '*'}",
                     r['train_gain_best'], r['heldout_gain_best'],
                     f"{r['heldout_gain_min']}..{r['heldout_gain_max']}",
                     '' if r['accuracy_train_best'] is None else r['accuracy_train_best'],
                     r['restart_J_spread']))
