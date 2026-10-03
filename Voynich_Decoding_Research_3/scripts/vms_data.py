"""Parse IVTFF transliterations (IT/Takahashi and ZL) into line records.

Each record keeps the manuscript position of every token, so later tests can
respect page, paragraph and line structure. Tokens that contain unknown or
non-basic glyphs are kept as None placeholders: neighbours are never joined
across them.
"""
from pathlib import Path
import json
import re
import sys

WORK = Path(__file__).resolve().parents[3] / 'work'
DATA = Path(__file__).resolve().parents[1] / 'data'

SOURCES = {
    'IT': WORK / 'IT_ivtff_1a.txt',
    'ZL': WORK / 'ZL3b-n.txt',
}

LOCUS = re.compile(r'^<(f[0-9a-zA-Z]+)\.(\d+)([a-z]?),(.)(.)([^>]*)>\s*(.*)$')
PAGE = re.compile(r'^<(f[0-9a-zA-Z]+)>\s*(.*)$')
GAP = '\x00'


def clean_body(body, source):
    body = re.sub(r'<![^>]*>', '', body)          # inline comments
    par_start = '<%>' in body
    par_end = '<$>' in body
    body = body.replace('<%>', '').replace('<$>', '')
    body = body.replace('<->', '.' + GAP + '.')   # drawing intrusion = break
    body = body.replace('<~>', '.' + GAP + '.')
    body = re.sub(r'<@[^>]*>', '', body)          # hand-change markers
    if source == 'ZL':
        body = re.sub(r'\[([^:\]]*):[^\]]*\]', r'\1', body)  # first reading
        body = body.replace(',', '.')            # uncertain space -> space
    return body, par_start, par_end


def split_tokens(body):
    tokens, raw_tokens, gap_after = [], [], []
    for piece in body.split('.'):
        piece = piece.strip()
        if not piece:
            continue
        if piece == GAP:
            if gap_after:
                gap_after[-1] = True
            continue
        raw_tokens.append(piece)
        tokens.append(piece if re.fullmatch(r'[a-z]+', piece) else None)
        gap_after.append(False)
    return tokens, raw_tokens, gap_after


def parse(source='IT'):
    path = SOURCES[source]
    pages, lines = {}, []
    par_counter = 0
    current_par = None
    line_in_par = 0
    for raw in path.read_text(encoding='utf-8-sig').splitlines():
        if raw.startswith('#') or not raw.strip():
            continue
        m = LOCUS.match(raw)
        if m:
            folio, num, sub, pos, utype, usub, body = m.groups()
            body, ps, pe = clean_body(body, source)
            tokens, raw_tokens, gap_after = split_tokens(body)
            if utype == 'P':
                if ps or current_par is None or current_par[0] != folio:
                    par_counter += 1
                    current_par = (folio, par_counter)
                    line_in_par = 0
                else:
                    line_in_par += 1
                par_id = current_par[1]
            else:
                par_id = None
            rec = {
                'folio': folio, 'line': int(num), 'sub': sub, 'pos': pos,
                'utype': utype, 'usub': usub,
                'par_id': par_id,
                'line_in_par': line_in_par if utype == 'P' else None,
                'par_start': ps, 'par_end': pe,
                'tokens': tokens, 'raw': raw_tokens, 'gap_after': gap_after,
                'meta': pages.get(folio, {}),
            }
            lines.append(rec)
            if utype == 'P' and pe:
                current_par = None
            continue
        m = PAGE.match(raw)
        if m:
            folio, body = m.groups()
            pages[folio] = dict(re.findall(r'\$([A-Z])=([^\s>]+)', body))
    # mark last line of each paragraph (some paragraphs lack <$>)
    by_par = {}
    for i, rec in enumerate(lines):
        if rec['par_id'] is not None:
            by_par.setdefault(rec['par_id'], []).append(i)
    for pid, idx in by_par.items():
        for j, i in enumerate(idx):
            lines[i]['par_nlines'] = len(idx)
            lines[i]['is_par_last'] = (j == len(idx) - 1)
    return lines, pages


if __name__ == '__main__':
    DATA.mkdir(exist_ok=True)
    for src in sys.argv[1:] or ['IT', 'ZL']:
        lines, pages = parse(src)
        out = DATA / f'{src}_lines.json'
        out.write_text(json.dumps({'pages': pages, 'lines': lines}), encoding='utf-8')
        ptoks = [t for r in lines if r['utype'] == 'P' for t in r['tokens']]
        good = [t for t in ptoks if t]
        print(src, 'lines', len(lines), 'paragraph lines',
              sum(r['utype'] == 'P' for r in lines),
              'paragraph tokens', len(ptoks), 'clean', len(good),
              'types', len(set(good)), 'paragraphs',
              len({r['par_id'] for r in lines if r['par_id']}))
