"""Dependence between words 1, 2 and 3 apart (position-aware shuffle) for every
Bible language, the manuscript, and the manuscript with variant spellings merged."""
import json, random
from pathlib import Path
from common import DATA
from diag_bible import tokens_of, by_page_from_tokens, vms_by_page, BIB
from diag_distance import profile
from diag_canonical import mapped, canon

if __name__ == '__main__':
    rng = random.Random(10)
    rows = [profile('VOYNICH', vms_by_page(), rng, reps=8), profile('VOYNICH variants merged', mapped(vms_by_page(), canon), rng, reps=8)]
    for p in sorted(BIB.glob('*.xml')):
        toks = tokens_of(p.stem)
        if len(toks) < 20000: continue
        rows.append(profile(p.stem, by_page_from_tokens(toks), rng, reps=8))
    (DATA / 'diag_bible_distance.json').write_text(json.dumps(rows, indent=1, ensure_ascii=False))
