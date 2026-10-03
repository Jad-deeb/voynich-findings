from pathlib import Path
from urllib.request import urlopen, Request
import hashlib

# Files are written alongside the scripts directory, matching prepare_attempt.py.
root=Path(__file__).parent.parent
commit='472ef7366606a799fc8f1044c037e06b413f6ddd'
expected={
    'IT_ivtff_1a.txt':'db624a731114f26854bbfe3a59d40827fa8911be46d086b6c558d99e557241ee',
    'ZL3b-n.txt':'bf5b6d4ac1e3a51b1847a9c388318d609020441ccd56984c901c32b09beccafc',
}
for name,digest in expected.items():
    destination=root/name
    if destination.exists():
        if hashlib.sha256(destination.read_bytes()).hexdigest()!=digest:
            raise RuntimeError('Existing file differs; refusing to overwrite '+str(destination))
        print('Already verified:',name);continue
    url='https://raw.githubusercontent.com/noah-chelednik/voynich-data/'+commit+'/data_sources/cache/'+name
    data=urlopen(Request(url,headers={'User-Agent':'Codex manuscript research'}),timeout=60).read()
    if hashlib.sha256(data).hexdigest()!=digest: raise RuntimeError('Source checksum mismatch: '+name)
    destination.write_bytes(data)
    print('Downloaded and verified:',name)
