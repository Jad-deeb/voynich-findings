"""Language fingerprint: the manuscript's word-level statistics against the same
statistics for ~45 languages on identical content (the New Testament, from
Matthew, first 34,000 tokens of each translation).

Statistics (each computed exactly as in Tests 1 and 4):
  rep_per_1000   identical neighbouring words per 1,000 pairs
  rep_ratio      ... divided by a position-aware shuffle expectation
  types, hapax   vocabulary at 34,000 tokens
  adj_mi         excess mutual information between neighbouring words
  edge_mi        excess MI between a word's last character and the next word's first
  wlen_mean/sd   word length in characters (letters only)
Tokens: lower-cased words with punctuation removed; Chinese is taken character by
character (each character is one syllable/morpheme); Japanese and Thai use the
corpus's pre-tokenised files.
"""
import json
import random
import re
import statistics
import unicodedata
from collections import defaultdict
from pathlib import Path

from common import paragraph_lines, segments, DATA
from diag_boundaries import mi
from diag_wordseq2 import shuffle_by_class, pairs as pair_list

BIB = Path(__file__).resolve().parents[3] / 'work' / 'bible_corpus'
SEG = re.compile(r"""<seg id=["']b\.([A-Z0-9]+)\.(\d+)\.(\d+)["'] type=["']verse["']>(.*?)</seg>""", re.S)
NT_FIRST = 'MAT'


def clean_word(w):
    return ''.join(c for c in w if unicodedata.category(c)[0] in 'LM')


def tokens_of(lang, limit=34000):
    xml = (BIB / f'{lang}.xml').read_text(encoding='utf-8', errors='replace')
    verses = SEG.findall(xml)
    start = next((i for i, v in enumerate(verses) if v[0] == NT_FIRST), 0)
    toks = []
    for book, ch, vs, text in verses[start:]:
        text = unicodedata.normalize('NFC', text.lower())
        if lang == 'Chinese':
            toks.extend(c for c in text if unicodedata.category(c)[0] == 'L')
        else:
            for w in re.split(r"[\s\-‐–—]+", text):
                w = clean_word(w)
                if w:
                    toks.append(w)
        if len(toks) >= limit:
            break
    return toks[:limit]


def by_page_from_tokens(toks, line_len=9, page_len=270):
    bp = defaultdict(list)
    for i in range(0, len(toks) - line_len + 1, line_len):
        bp[i // page_len].append((toks[i:i + line_len], False))
    return bp


def vms_by_page():
    bp = defaultdict(list)
    for line in paragraph_lines('IT'):
        for run in segments(line):
            bp[line['folio']].append((run, line['line_in_par'] == 0))
    return bp


def fingerprint(name, bp, rng, reps=30, chars=True):
    toks = [t for runs in bp.values() for run, _ in runs for t in run]
    prs = pair_list(bp, False)
    same = sum(a == b for a, b in prs)
    null_same, null_mi, null_edge = 0.0, 0.0, 0.0
    obs_mi = mi(prs)
    edge = [(a[-1], b[0]) for a, b in prs]
    obs_edge = mi(edge)
    for _ in range(reps):
        sb = shuffle_by_class(bp, rng)
        sp = pair_list(sb, False)
        null_same += sum(a == b for a, b in sp) / reps
        null_mi += mi(sp) / reps
        null_edge += mi([(a[-1], b[0]) for a, b in sp]) / reps
    from collections import Counter
    c = Counter(toks)
    lens = [len(t) for t in toks]
    row = {'text': name, 'tokens': len(toks), 'pairs': len(prs),
           'rep_per_1000': round(1000 * same / len(prs), 2),
           'rep_ratio': round(same / null_same, 2) if null_same else None,
           'types': len(c), 'hapax_share': round(sum(1 for v in c.values() if v == 1) / len(c), 3),
           'adj_mi': round(obs_mi - null_mi, 4),
           'edge_mi': round(obs_edge - null_edge, 4) if chars else None,
           'wlen_mean': round(statistics.mean(lens), 2), 'wlen_sd': round(statistics.pstdev(lens), 2)}
    print(json.dumps(row, ensure_ascii=False))
    return row


if __name__ == '__main__':
    rng = random.Random(2026)
    rows = [fingerprint('VOYNICH (IT, EVA letters)', vms_by_page(), rng)]
    langs = sorted(p.stem for p in BIB.glob('*.xml'))
    for lang in langs:
        try:
            toks = tokens_of(lang)
        except Exception as e:  # unreadable file
            print('skip', lang, e)
            continue
        if len(toks) < 20000:
            print('short', lang, len(toks))
            continue
        rows.append(fingerprint(lang, by_page_from_tokens(toks), rng, chars=(lang != 'Chinese')))
    (DATA / 'diag_bible.json').write_text(json.dumps(rows, indent=1, ensure_ascii=False))
