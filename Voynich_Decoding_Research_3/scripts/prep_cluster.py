"""Part streams for distributional clustering.
control: the Voynich-looking Naibbe control parsed with its TRUE analysis
         (truth letters per part are known);
vms:     Currier A / B parsed with the 'core' and 'suffix' rules.
After clustering, class streams are converted to the partunit solver format."""
import json, sys
from common import DATA
from prep_partunit import split_core, split_suffix

def parts_stream(streams, parse, truths=None):
    out, tr = [], []
    for si, s in enumerate(streams):
        ps, pt = [], []
        for ti, t in enumerate(s):
            if t is None:
                ps.append(None); pt.append(None); continue
            parts = parse(t)
            if parts is None:
                ps.append(None); pt.append(None); continue
            for j, p in enumerate(parts):
                ps.append(p)
                if truths: pt.append(truths[si][ti][j] if j < len(truths[si][ti]) else None)
        out.append(ps); tr.append(pt)
    return out, (tr if truths else None)

if __name__ == '__main__':
    c = json.loads((DATA / 'su_ctrl_vmslike_11k.json').read_text())
    ta = c['true_analysis']
    streams = c['streams_train'] + c['streams_test']
    truths = c['truth_train'] + c['truth_test']
    ps, pt = parts_stream(streams, lambda t: ta.get(t), truths)
    (DATA / 'cl_ctrl_parts.json').write_text(json.dumps({'streams': ps, 'truth': pt}))
    for name in ('vmsA', 'vmsB'):
        v = json.loads((DATA / f'su_{name}.json').read_text())
        st = v['streams_train'] + v['streams_test']
        for rule, fn in (('core', split_core), ('suffix', split_suffix)):
            ps, _ = parts_stream(st, lambda t, fn=fn: [f'{r}:{p}' for r, p in fn(t)])
            (DATA / f'cl_{name}_{rule}.json').write_text(json.dumps({'streams': ps}))
    print('ok')
