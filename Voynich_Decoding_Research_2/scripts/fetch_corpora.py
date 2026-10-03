from pathlib import Path
from urllib.request import urlopen, Request
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor
import hashlib, json, sys
sys.stdout.reconfigure(encoding='utf-8')

root = Path(__file__).parent
commit = 'decc4caaa6515b86e42a219d1da8d81114736f2e'
paths = ['Corpora/Historical_texts/'+s for s in ['Latin_Adso','Latin_Aix','BrunoDeMagia','Secreta_Secretorum_LAT','Steganographia','Cirurgie','Secreta_Secretorum_ENG','AlphabetOfTales','Rettorica','Picatrix']]
paths += ['R code/0_Process_Interlinear_File.Rmd','R code/1_Create_Voynich_Corpus.Rmd','R code/3_Create_Historical_Corpus.Rmd','README.md']
def fetch(p):
    url = 'https://raw.githubusercontent.com/chirila/Voynich-public/'+commit+'/'+quote(p)
    data = urlopen(Request(url,headers={'User-Agent':'Codex manuscript research'}),timeout=60).read()
    out = root/'corpora'/Path(p).name
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_bytes(data)
    return dict(path=p,url=url,local=out.name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),sample=data.decode('utf-8-sig')[:180])
with ThreadPoolExecutor(max_workers=6) as pool:
    results=list(pool.map(fetch,paths))
(root/'sources.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
for r in results: print(r['local'],r['bytes'],repr(r['sample']))
