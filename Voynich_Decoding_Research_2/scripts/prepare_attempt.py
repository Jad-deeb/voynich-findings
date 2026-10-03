from pathlib import Path
from collections import Counter, defaultdict
import json, re, unicodedata, math, random, hashlib, sys
sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).parent
LANG_FILES = {
    'Latin':['Latin_Adso','Latin_Aix','BrunoDeMagia','Secreta_Secretorum_LAT'],
    'Italian':['Rettorica'],
    'English':['Cirurgie','Secreta_Secretorum_ENG','AlphabetOfTales'],
    'Spanish':['Picatrix'],
}
MINIMAL = [('ch','S'),('sh','Z'),('iiil','1'),('iil','H'),('il','G'),('iiir','0'),('iir','U'),('ir','T'),('iiim','5'),('iim','L'),('im','K'),('iiin','3'),('iin','M'),('in','N'),('cth','Q'),('cph','W'),('ckh','X'),('cfh','Y'),('ee','E'),('qo','q')]
BENCHES = [('cth','Q'),('cph','W'),('ckh','X'),('cfh','Y'),('ch','S'),('sh','Z')]
def transform(word, scheme):
    for a,b in (BENCHES if scheme=='benches' else MINIMAL if scheme=='minimal' else []): word=word.replace(a,b)
    return word

def parse(name):
    lines=[]; meta={}
    for raw in (ROOT.parent/name).read_text(encoding='utf-8-sig').splitlines():
        m=re.match(r'^<(f[^>]+)>\s*(.*)$',raw)
        if not m: continue
        locus,body=m.groups()
        if '.' not in locus:
            meta[locus]=dict(re.findall(r'\$([A-Z])=([^\s>]+)',body)); continue
        folio=locus.split('.')[0]; code=locus.split(',')[-1]
        if not re.match(r'^[@+*=]P',code): continue
        body=re.sub(r'<![^>]*>','',body)
        body=body.replace('<%>','').replace('<$>','').replace('<->>','.?.').replace('<->','.?.')
        tokens=[w.strip() if re.fullmatch('[a-z]+',w.strip()) else None for w in body.split('.') if w.strip()]
        lines.append(dict(locus=locus,folio=folio,code=code,tokens=tokens,meta=meta.get(folio,{})))
    return lines

def segments(lines,scheme='eva',reverse=False,allowed=None):
    out=[]
    for line in lines:
        seg=[]
        for token in line['tokens']+[None]:
            w=transform(token,scheme) if token else None
            if w and (allowed is None or set(w)<=allowed): seg.append(w[::-1] if reverse else w)
            else:
                if seg: out.append(' '.join(seg)); seg=[]
    return out

def entropy(segments):
    uni=Counter(); bi=Counter()
    for s in segments:
        uni.update(s); bi.update(zip(s,s[1:]))
    den=Counter()
    for (a,b),n in bi.items(): den[a]+=n
    n=sum(bi.values()); u=sum(uni.values())
    return {'characters':u,'alphabet_including_space':len(uni),'h1':-sum(v/u*math.log2(v/u) for v in uni.values()),'h2':-sum(v/n*math.log2(v/den[a]) for (a,b),v in bi.items())}

def clean_text(s):
    s=s.lower().replace('þ','th').replace('ð','th').replace('ȝ','y').replace('æ','ae').replace('œ','oe').replace('&',' and ')
    s=''.join(c for c in unicodedata.normalize('NFKD',s) if not unicodedata.combining(c))
    return re.findall('[a-z]+',s)

def take_segments(ss,limit=2500):
    out=[]; n=0
    for s in ss:
        out.append(s); n+=len(s)
        if n>=limit: break
    return out

def main():
    lines=parse('IT_ivtff_1a.txt')
    other=parse('ZL3b-n.txt')
    corpora={}; corpus_stats=[]
    rng=random.Random(4082026)
    for lang,files in LANG_FILES.items():
        train=[]; tests=[]; provenance=[]
        for fn in files:
            raw=(ROOT/'corpora'/fn).read_text(encoding='utf-8-sig'); words=clean_text(raw)
            cut=int(len(words)*.8)
            train.append(' '.join(words[:cut])); tests.append(' '.join(words[cut:]))
            provenance.append(dict(file=fn,total_words=len(words),training_words=cut,test_words=len(words)-cut))
        # First 2500 characters from each source's held-out fifth; whole words retained.
        test_words=[test.split() for test in tests]
        control=take_segments([' '.join(ws[i:i+15]) for ws in test_words for i in range(0,len(ws),15)],2500)
        control_test=take_segments([' '.join(test_words[0][i:i+15]) for i in range(700,len(test_words[0]),15)],2500)
        if sum(map(len,control_test))<1000:
            control_test=take_segments([' '.join(test_words[-1][i:i+15]) for i in range(700,len(test_words[-1]),15)],2500)
        chars=list('abcdefghijklmnopqrstuvwxyz'); enc=chars.copy(); rng.shuffle(enc); encmap=dict(zip(chars,enc))
        encrypt=lambda ss:[''.join(encmap.get(c,c) for c in s) for s in ss]
        corpora[lang]=dict(train=train,control=encrypt(control),control_test=encrypt(control_test),control_plain=control,control_test_plain=control_test,provenance=provenance)
        corpus_stats.append(dict(language=lang,files=provenance,entropy=entropy(tests)))
    groups={
        'A_herbal_hand1':[x for x in lines if x['meta'].get('L')=='A' and x['meta'].get('H')=='1' and x['meta'].get('I')=='H'],
        'B_bathing_hand2':[x for x in lines if x['meta'].get('L')=='B' and x['meta'].get('H')=='2' and x['meta'].get('I')=='B'],
    }
    samples=[]; stats=[]; splits={}
    for group,ls in groups.items():
        folios=list(dict.fromkeys(x['folio'] for x in ls))
        # Whole-page split, fixed before fitting. Alternate pairs of pages.
        tr=set(f for i,f in enumerate(folios) if i%4<2); te=set(folios)-tr
        train=[x for x in ls if x['folio'] in tr]; test=[x for x in ls if x['folio'] in te]
        splits[group]={'train_folios':sorted(tr),'test_folios':sorted(te)}
        for scheme in ['eva','benches','minimal']:
            ss=segments(ls,scheme); counts=Counter(''.join(ss).replace(' ',''))
            stats.append(dict(group=group,scheme=scheme,entropy=entropy(ss),characters=counts.most_common()))
            if scheme=='minimal': continue # Inventory too large for the 26-letter bijection tested here.
            allowed={c for c,n in counts.most_common(26)}
            for reverse in [False,True]:
                trsegs=take_segments(segments(train,scheme,reverse,allowed)); teseqs=take_segments(segments(test,scheme,reverse,allowed))
                samples.append(dict(id=group+'_'+scheme+('_reversed' if reverse else '_forward'),group=group,scheme=scheme,reverse=reverse,train=trsegs,test=teseqs,allowed=sorted(allowed),excluded_rare_characters=sorted(set(counts)-allowed),total_characters=sum(counts.values()),retained_tokens=sum(len(s.split()) for s in segments(ls,scheme,False,allowed)),original_valid_tokens=sum(len(s.split()) for s in ss)))
    # Independent second transcription: structural check, not a new optimization input.
    replication=[]
    for group,split in splits.items():
        fs=set(split['train_folios']+split['test_folios'])
        for scheme in ['eva','benches','minimal']:
            replication.append(dict(group=group,scheme=scheme,entropy=entropy(segments([x for x in other if x['folio'] in fs],scheme))))
    data=dict(corpora=corpora,samples=samples,splits=splits,stats=stats,corpus_stats=corpus_stats,replication=replication)
    (ROOT/'attempt_input.json').write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8')
    for row in stats: print(row['group'],row['scheme'],len(row['characters']),row['entropy'])
    for row in corpus_stats: print(row['language'],row['entropy'])
    print('Samples',[(s['id'],sum(map(len,s['train'])),sum(map(len,s['test'])),s['excluded_rare_characters']) for s in samples])

if __name__=='__main__': main()
