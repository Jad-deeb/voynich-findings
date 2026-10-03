"""Letter-only language-model texts from the parallel Bible corpus, one file per
language: data/lm_bible_<lang>.txt plus data/lm_bible_alphabets.json.
Latin-script languages: diacritics removed, lower case, a-z only.
Greek, Hebrew, Arabic and Farsi: simple letter-by-letter romanisation
(consonantal for Hebrew/Arabic/Farsi, as written)."""
import json, re, unicodedata
from collections import Counter
from pathlib import Path
from common import DATA

BIB = Path(__file__).resolve().parents[3] / 'work' / 'bible_corpus'
SEG = re.compile(r"""<seg id=["']b\.([A-Z0-9]+)\.(\d+)\.(\d+)["'] type=["']verse["']>(.*?)</seg>""", re.S)
GREEK = dict(zip('αβγδεζηθικλμνξοπρσςτυφχψω', ['a','b','g','d','e','z','e','th','i','k','l','m','n','x','o','p','r','s','s','t','u','f','ch','ps','o']))
HEBREW = dict(zip('אבגדהוזחטיכךלמםנןסעפףצץקרשת', ['a','b','g','d','h','u','z','h','t','i','c','c','l','m','m','n','n','s','o','p','p','s','s','q','r','s','t']))
ARABIC = dict(zip('ابتثجحخدذرزسشصضطظعغفقكلمنهويءآأإةىپچژگک', ['a','b','t','t','g','h','h','d','d','r','z','s','s','s','d','t','z','o','g','f','q','c','l','m','n','h','u','i','a','a','a','a','h','i','p','c','z','g','c']))
SKIP = {'Chinese', 'Japanese-tok', 'Korean', 'Thai-tok', 'Amharic', 'Hindi', 'Cherokee-NT', 'Syriac-NT', 'Coptic-NT', 'Armenian-PART'}

def romanize(text, lang):
    text = unicodedata.normalize('NFKD', text.lower())
    if lang == 'Greek':
        return ''.join(GREEK.get(c, c if 'a' <= c <= 'z' else ' ') for c in text if not unicodedata.combining(c))
    if lang == 'Hebrew':
        return ''.join(HEBREW.get(c, ' ') for c in text if not unicodedata.combining(c))
    if lang in ('Arabic', 'Farsi'):
        return ''.join(ARABIC.get(c, ' ') for c in text if not unicodedata.combining(c))
    return ''.join(c if 'a' <= c <= 'z' else ' ' for c in text if not unicodedata.combining(c))

if __name__ == '__main__':
    alph = {}
    for f in sorted(BIB.glob('*.xml')):
        lang = f.stem
        if lang in SKIP: continue
        verses = SEG.findall(f.read_text(encoding='utf-8', errors='replace'))
        lines = []
        for _, _, _, t in verses:
            letters = re.sub(r'[^a-z]', '', romanize(t, lang))
            if letters: lines.append(letters)
        text = '\n'.join(lines)
        c = Counter(text.replace('\n', ''))
        tot = sum(c.values())
        letters = ''.join(sorted(L for L, n in c.items() if n / tot >= 2e-4))
        # drop rare letters from the text so the alphabet is closed
        keep = set(letters)
        text = '\n'.join(''.join(ch for ch in l if ch in keep) for l in lines)
        (DATA / f'lm_bible_{lang}.txt').write_text(text, encoding='utf-8')
        alph[lang] = {'alphabet': letters, 'letters': tot}
        print(lang, letters, tot)
    (DATA / 'lm_bible_alphabets.json').write_text(json.dumps(alph, indent=1))
