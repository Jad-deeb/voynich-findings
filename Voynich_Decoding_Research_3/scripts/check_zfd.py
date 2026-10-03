"""Check the ZFD 'Croatian' reading (github.com/denoflore/ZFD,
translations/INTERLINEAR_QUADRILINGUAL.md) against real Croatian.

Because ZFD decodes every Voynich word the same way wherever it occurs, its
output inherits the manuscript's word-sequence statistics. Real Croatian prose
(the Croatian Bible from the same parallel corpus used in round 4) is measured
the same way for comparison."""
import json, re, random, sys
from collections import defaultdict, Counter
from pathlib import Path
from diag_bible import tokens_of, by_page_from_tokens, fingerprint
from diag_distance import profile
from common import DATA

def zfd_pages(path, layer):
    text = Path(path).read_text(encoding='utf-8')
    pages = defaultdict(list)
    for sec in re.split(r'\n## F', text)[1:]:
        folio = sec.split('\n', 1)[0].strip()
        for m in re.finditer(r"```\nEVA: (.*?)\nCRO: (.*?)\nEXP: (.*?)\nENG: (.*?)\n```", sec):
            words = m.group({'EVA': 1, 'CRO': 2, 'EXP': 3, 'ENG': 4}[layer]).split()
            words = [w.lower() for w in words if w.strip()]
            if len(words) >= 2:
                pages[folio].append((words, False))
    return pages

if __name__ == '__main__':
    path = sys.argv[1]
    rng = random.Random(1)
    rows = []
    for layer in ('EVA', 'EXP', 'ENG'):
        bp = zfd_pages(path, layer)
        n = sum(len(r) for runs in bp.values() for r, _ in runs)
        fp = fingerprint(f'ZFD {layer} layer ({n} words)', bp, rng, reps=15)
        dp = profile(f'ZFD {layer} layer', bp, rng, reps=10)
        rows.append({**fp, **{k: v for k, v in dp.items() if k != 'text'}})
    for lang in ('Croatian', 'Serbian'):
        bp = by_page_from_tokens(tokens_of(lang))
        fp = fingerprint(f'{lang} Bible (real)', bp, rng, reps=15)
        dp = profile(f'{lang} Bible', bp, rng, reps=10)
        rows.append({**fp, **{k: v for k, v in dp.items() if k != 'text'}})
    (DATA / 'check_zfd.json').write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    print()
    for r in rows:
        print(f"{r['text'][:34]:34s} repeats/1000 {r['rep_per_1000']:6.2f} vs-chance {r['rep_ratio']:5.2f} | dependence 1 apart {r['word_d1']:6.3f} 2 apart {r['word_d2']:6.3f} 3 apart {r['word_d3']:6.3f}")
