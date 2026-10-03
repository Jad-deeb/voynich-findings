"""Download a selection of the parallel Bible corpus (Christodouloupoulos and
Steedman 2015, github.com/christos-c/bible-corpus) into work/bible_corpus/.

The same text in many languages lets word-level statistics be compared across
languages without differences of subject matter. Files are plain XML."""
import hashlib
import json
import sys
import time
from pathlib import Path
from urllib.request import urlopen

OUT = Path(__file__).resolve().parents[3] / 'work' / 'bible_corpus'
BASE = 'https://raw.githubusercontent.com/christos-c/bible-corpus/master/bibles/'
LANGS = ['Latin', 'Italian', 'English', 'Spanish', 'French', 'German', 'Portuguese', 'Romanian',
         'Greek', 'Hebrew', 'Arabic', 'Syriac-NT', 'Coptic-NT', 'Farsi', 'Turkish', 'Hungarian',
         'Finnish', 'Estonian-PART', 'Basque-NT', 'Czech', 'Polish', 'Albanian', 'Lithuanian',
         'Armenian-PART', 'Romani-NT', 'Esperanto', 'Vietnamese', 'Chinese', 'Japanese-tok',
         'Korean', 'Thai-tok', 'Indonesian', 'Tagalog', 'Cebuano', 'Malagasy', 'Maori',
         'Swahili-NT', 'Somali', 'Shona', 'Zulu-NT', 'Amharic', 'Nahuatl-NT', 'Quichua-NT',
         'Q\'eqchi\'', 'Cherokee-NT', 'Hindi']

if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for lang in (sys.argv[1:] or LANGS):
        path = OUT / f'{lang}.xml'
        if not path.exists():
            for attempt in range(3):
                try:
                    data = urlopen(BASE + lang.replace("'", '%27') + '.xml', timeout=120).read()
                    path.write_bytes(data)
                    break
                except Exception as e:  # network hiccup: retry
                    print('retry', lang, e)
                    time.sleep(3)
        if path.exists():
            manifest[lang] = {'bytes': path.stat().st_size,
                              'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
            print(lang, manifest[lang]['bytes'])
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=1))
