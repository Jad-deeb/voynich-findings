"""Apply a saved part-unit key to the input streams and print decoded letters.

usage: python decode_sample.py ../results/pu_pu_vmsB_core__lm_latin_all.json [n_streams] [test|train]
'?' marks an unknown or unparsed token; '_' marks a token with a part never seen in training.
For the manuscript these strings are failed search outputs, not translations.
"""
import json
import sys
from pathlib import Path

res = json.loads(Path(sys.argv[1]).read_text())
n = int(sys.argv[2]) if len(sys.argv) > 2 else 4
which = sys.argv[3] if len(sys.argv) > 3 else 'train'
data = json.loads(Path(sys.argv[1]).parent.joinpath(res['params']['data']).read_text()) \
    if not Path(res['params']['data']).is_absolute() else json.loads(Path(res['params']['data']).read_text())
key = {s: L for s, _, L in res['best']['key']}
parts = data['parts']
for stream, truth in zip(data[f'streams_{which}'][:n],
                         (data.get(f'truth_{which}') or [None] * n)[:n]):
    out = []
    for tok in stream:
        if tok is None or tok not in parts:
            out.append('?')
            continue
        ps = parts[tok]
        out.append(''.join(key.get(p, '_') for p in ps))
    print('words  :', ' '.join(t or '?' for t in stream[:18]), '...' if len(stream) > 18 else '')
    print('letters:', ''.join(out))
    if truth:
        print('truth  :', ''.join(truth))
    print()
