"""Shared loaders for the third decoding attempt."""
from pathlib import Path
import json
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
CORPORA = Path(__file__).resolve().parents[3] / 'work' / 'astra' / 'corpora'

LATIN_FILES = ['Latin_Aix', 'Secreta_Secretorum_LAT', 'BrunoDeMagia',
               'Steganographia', 'Latin_Adso']
ITALIAN_FILES = ['Rettorica']


def load_lines(source='IT'):
    obj = json.loads((DATA / f'{source}_lines.json').read_text(encoding='utf-8'))
    return obj['lines'], obj['pages']


def paragraph_lines(source='IT', require=None):
    """Paragraph-text lines, optionally filtered by page metadata."""
    lines, pages = load_lines(source)
    out = []
    for r in lines:
        if r['utype'] != 'P':
            continue
        meta = pages.get(r['folio'], {})
        if require and any(meta.get(k) not in (v if isinstance(v, (set, list, tuple)) else {v})
                           for k, v in require.items()):
            continue
        r = dict(r)
        r['meta'] = meta
        out.append(r)
    return out


def segments(line):
    """Split a line's tokens into runs without unknown tokens or drawing gaps."""
    run = []
    for tok, gap in zip(line['tokens'], line['gap_after']):
        if tok is None:
            if run:
                yield run
            run = []
            continue
        run.append(tok)
        if gap:
            yield run
            run = []
    if run:
        yield run


def normalize_latin(text, merge_uv=True):
    text = unicodedata.normalize('NFKD', text.lower())
    text = ''.join(c for c in text if not unicodedata.combining(c))
    text = text.replace('æ', 'ae').replace('œ', 'oe').replace('ß', 'ss')
    text = text.replace('&', ' et ')
    text = re.sub(r'[^a-z]+', ' ', text)
    if merge_uv:
        text = text.replace('v', 'u').replace('j', 'i')
    return re.sub(r'\s+', ' ', text).strip()


def normalize_italian(text):
    text = unicodedata.normalize('NFKD', text.lower())
    text = ''.join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r'[^a-z]+', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def corpus_words(lang="latin", files=None):
    files = files or (LATIN_FILES if lang == 'latin' else ITALIAN_FILES)
    norm = normalize_latin if lang == 'latin' else normalize_italian
    if lang == 'english':
        norm = lambda t: re.sub(r'\s+', ' ', re.sub(r'[^a-z]+', ' ', unicodedata.normalize('NFKD', t.lower()).replace('þ', 'th').replace('ȝ', 'gh'))).strip()
    out = {}
    for name in files:
        raw = (CORPORA / name).read_text(encoding='utf-8', errors='replace')
        out[name] = norm(raw).split()
    return out
