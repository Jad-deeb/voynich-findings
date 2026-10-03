from pathlib import Path
from collections import Counter
import json, random, statistics, sys
from prepare_attempt import parse, segments, entropy, clean_text, LANG_FILES
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(__file__).parent
data=json.loads((ROOT/'attempt_input.json').read_text(encoding='utf-8'))
rng=random.Random(20261003)

def windows(ss,n=100,size=2500):
    vals=[]
    for _ in range(n):
        start=rng.randrange(max(1,len(ss)-60)); out=[]; count=0
        for s in ss[start:]:
            out.append(s); count+=len(s)
            if count>=size: break
        if count<size: # End of corpus: take a full window ending at its last segment.
            out=[]; count=0
            for s in reversed(ss):
                out.append(s); count+=len(s)
                if count>=size: break
            out.reverse()
        vals.append(entropy(out)['h2'])
    return dict(windows=n,target_characters=size,mean=statistics.mean(vals),min=min(vals),max=max(vals),stdev=statistics.stdev(vals))

result={'matched_entropy':[],'position_effects':[],'parser_inventory':[]}
for source in ['IT_ivtff_1a.txt','ZL3b-n.txt']:
    ls=parse(source)
    result['parser_inventory'].append(dict(source=source,paragraph_lines=len(ls),valid_tokens=sum(w is not None for ln in ls for w in ln['tokens']),excluded_tokens_or_gap_markers=sum(w is None for ln in ls for w in ln['tokens'])))
    for group,split in data['splits'].items():
        fs=set(split['train_folios']+split['test_folios'])
        selected=[x for x in ls if x['folio'] in fs]
        for scheme in ['eva','benches','minimal']:
            result['matched_entropy'].append(dict(source=source,group=group,scheme=scheme,**windows(segments(selected,scheme))))
        positions={p:Counter() for p in ['paragraph_start','other_line_start','line_interior']}
        for ln in selected:
            for i,w in enumerate(ln['tokens']):
                if not w: continue
                p='line_interior' if i>0 else 'paragraph_start' if ln['code'].startswith('@') else 'other_line_start'
                positions[p].update({'tokens':1,'contains_p_or_f':int('p' in w or 'f' in w),'begins_q':int(w.startswith('q')),'ends_y':int(w.endswith('y'))})
        result['position_effects'].append(dict(source=source,group=group,counts={p:dict(c) for p,c in positions.items()}))
for lang,files in LANG_FILES.items():
    ss=[]
    for fn in files:
        ws=clean_text((ROOT/'corpora'/fn).read_text(encoding='utf-8-sig')); ws=ws[int(len(ws)*.8):]
        ss.extend(' '.join(ws[i:i+15]) for i in range(0,len(ws),15))
    result['matched_entropy'].append(dict(source='comparison',group=lang,scheme='normalized_latin_alphabet',**windows(ss)))

# Record exact lines in each fitting and reserved evaluation sample.
lines=parse('IT_ivtff_1a.txt')
result['sample_locations']=[]
homopath=ROOT/'homophonic_input.json'
extra=json.loads(homopath.read_text(encoding='utf-8'))['samples'] if homopath.exists() else []
for sample in data['samples']+extra:
    location={}
    split=data['splits'][sample['group']]
    for phase in ['train','test']:
        fs=set(split[phase+'_folios']); selected=[ln for ln in lines if ln['folio'] in fs]
        loc=[]; chars=0; reconstructed=[]
        for ln in selected:
            for s in segments([ln],sample['scheme'],sample['reverse'],set(sample['allowed']) if 'allowed' in sample else None):
                reconstructed.append(s); chars+=len(s); loc.append(ln['locus'])
                if chars>=2500: break
            if chars>=2500: break
        assert reconstructed==sample[phase], sample['id']
        location[phase]={'loci':list(dict.fromkeys(loc)),'folios':list(dict.fromkeys(x.split('.')[0] for x in loc)),'characters':chars}
    assert not set(location['train']['folios'])&set(location['test']['folios'])
    result['sample_locations'].append(dict(id=sample['id'],**location))
(ROOT/'structural_results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
for r in result['matched_entropy']: print(r['source'],r['group'],r['scheme'],round(r['mean'],3),round(r['min'],3),round(r['max'],3))
for r in result['position_effects']: print(r['source'],r['group'],r['counts'])
print('Parser',result['parser_inventory'])
