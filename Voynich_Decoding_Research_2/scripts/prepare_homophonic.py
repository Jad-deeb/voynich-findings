from pathlib import Path
import json, random
from prepare_attempt import parse, segments, take_segments
ROOT=Path(__file__).parent
data=json.loads((ROOT/'attempt_input.json').read_text(encoding='utf-8'))
rng=random.Random(40838)
for language,corpus in data['corpora'].items():
    # One code for every alphabet letter, an extra code for each of 12 common letters.
    symbols=list('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!?')
    rng.shuffle(symbols)
    codes={c:[symbols.pop()] for c in 'abcdefghijklmnopqrstuvwxyz'}
    common=sorted('abcdefghijklmnopqrstuvwxyz',key=lambda c:sum(s.count(c) for s in corpus['train']),reverse=True)[:12]
    for c in common: codes[c].append(symbols.pop())
    encrypt=lambda ss:[''.join(' ' if c==' ' else rng.choice(codes[c]) for c in s) for s in ss]
    corpus['control']=encrypt(corpus['control_plain'])
    corpus['control_test']=encrypt(corpus['control_test_plain'])
lines=parse('IT_ivtff_1a.txt'); samples=[]
for group,split in data['splits'].items():
    for reverse in [False,True]:
        phases={}
        for phase in ['train','test']:
            selected=[ln for ln in lines if ln['folio'] in set(split[phase+'_folios'])]
            phases[phase]=take_segments(segments(selected,'minimal',reverse),2500)
        samples.append(dict(id=group+'_minimal'+('_reversed' if reverse else '_forward'),group=group,scheme='minimal',reverse=reverse,**phases))
data['samples']=samples
(ROOT/'homophonic_input.json').write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8')
print('Prepared 4 controls and',len(samples),'minimal-grouping samples.')
