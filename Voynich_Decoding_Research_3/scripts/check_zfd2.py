"""Same comparison restricted to manuscript PARAGRAPH lines: ZFD lines are kept
only when their EVA text equals an IT paragraph line, so the Voynich side is the
same text measured in round 4. Paragraph-first flags come from IT."""
import json, re, random, sys
from collections import defaultdict
from pathlib import Path
from common import paragraph_lines, DATA
from diag_bible import fingerprint
from diag_distance import profile

def norm(s): return ' '.join(s.replace('.', ' ').split())

if __name__ == '__main__':
    path = sys.argv[1]
    it = {}
    for line in paragraph_lines('IT'):
        raw = ' '.join(t for t in line['raw'])
        it.setdefault(norm(raw), (line['folio'], line['line_in_par'] == 0))
    text = Path(path).read_text(encoding='utf-8')
    layers = {k: defaultdict(list) for k in ('EVA', 'EXP', 'ENG')}
    matched = total = dups = 0
    seen = set()
    for m in re.finditer(r"```\nEVA: (.*?)\nCRO: (.*?)\nEXP: (.*?)\nENG: (.*?)\n```", text):
        total += 1
        key = norm(m.group(1))
        if key not in it: continue
        if key in seen:            # the ZFD file repeats some lines (folios decoded twice)
            dups += 1; continue
        seen.add(key)
        folio, pf = it[key]
        matched += 1
        for k, g in (('EVA', 1), ('EXP', 3), ('ENG', 4)):
            words = [w.lower() for w in m.group(g).split()]
            if len(words) >= 2: layers[k][folio].append((words, pf))
    print('ZFD lines', total, 'matched to IT paragraph lines', matched, 'duplicate lines dropped', dups)
    rng = random.Random(2); rows = []
    for k, bp in layers.items():
        n = sum(len(r) for runs in bp.values() for r, _ in runs)
        fp = fingerprint(f'ZFD {k}, paragraph lines ({n} words)', bp, rng, reps=15)
        dp = profile(k, bp, rng, reps=10)
        rows.append({**fp, **{x: v for x, v in dp.items() if x != 'text'}})
    (DATA / 'check_zfd_paragraphs.json').write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    print()
    for r in rows:
        print(f"{r['text'][:40]:40s} repeats/1000 {r['rep_per_1000']:6.2f} vs-chance {r['rep_ratio']:5.2f} | 1 apart {r['word_d1']:6.3f} 2 apart {r['word_d2']:6.3f} 3 apart {r['word_d3']:6.3f}")
