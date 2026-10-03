"""Insert the manuscript decryption table into the report from results/partunit_summary.json."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT.parent / 'Voynich_Decoding_Attempt_3.md'
rows = {(r['data'], r['lm']): r for r in json.loads((ROOT / 'results' / 'partunit_summary.json').read_text())}

LM = {'lm_latin_all': 'Latin', 'lm_italian': 'Italian'}
lines = ['| Text | Word division | Model | Held-out gain, real words (range over restarts) '
         '| Held-out gain, shuffled words | Real minus shuffled |',
         '|---|---|---|---:|---:|---:|']
diffs = []
restarts = {}
for sub, label in [('vmsA', 'Currier A (11,081 words)'), ('vmsB', 'Currier B (22,797 words)')]:
    for rule in ['core', 'suffix', 'whole']:
        for lm in ['lm_latin_all', 'lm_italian']:
            real = rows.get((f'{sub}_{rule}', lm))
            shuf = rows.get((f'{sub}_{rule}_shuffled', lm))
            if not real or not shuf or 'heldout_gain_best' not in real or 'heldout_gain_best' not in shuf:
                continue
            d = real['heldout_gain_best'] - shuf['heldout_gain_best']
            diffs.append(d)
            restarts.setdefault(sub, set()).update({real['restarts_done'], shuf['restarts_done']})
            lines.append(f"| {label} | {rule} | {LM[lm]} | {real['heldout_gain_best']:+.2f} "
                         f"({real['heldout_gain_min']:+.2f} to {real['heldout_gain_max']:+.2f}) | "
                         f"{shuf['heldout_gain_best']:+.2f} | {d:+.2f} |")
table = '\n'.join(lines)
counts = '; '.join(f"{'Currier A' if k == 'vmsA' else 'Currier B'}: {'/'.join(map(str, sorted(v)))} restarts"
                   for k, v in sorted(restarts.items()))
note = ("\n\nValues are bits per word on held-back paragraphs, for the key with the best training likelihood "
        f"({counts}). For comparison, solved controls score +1.11 to +1.49 and shuffled controls "
        f"−2.8 to −2.9. Across the {len(diffs)} manuscript settings, real minus shuffled ranges from "
        f"{min(diffs):+.2f} to {max(diffs):+.2f} bits per word. Values cannot be compared between word "
        "divisions, because each division produces a different number of letters per word.")
text = REPORT.read_text(encoding='utf-8')
assert 'VOYNICH_TABLE_PLACEHOLDER' in text
REPORT.write_text(text.replace('VOYNICH_TABLE_PLACEHOLDER', table + note), encoding='utf-8', newline='\n')
print(table + note)
