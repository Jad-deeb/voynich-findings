"""Reading-order variants of the Currier B input for the learned-split solver:
  rev  - right-to-left: word order reversed within each paragraph and the glyphs
         of every word reversed (so the old suffix is read first);
  line - every manuscript line is its own stream (letter context resets at each line).
Each variant also gets a page-shuffled control."""
import json, random
from collections import defaultdict
from common import paragraph_lines, DATA
from prep_wordunit import split, shuffle_within_page
from prep_splitunit import add_analyses

def line_streams(require):
    streams, pages = [], []
    for line in paragraph_lines('IT', require):
        streams.append(list(line['tokens'])); pages.append(line['folio'])
    return streams, pages

def par_streams(require):
    pars, pages = defaultdict(list), {}
    for line in paragraph_lines('IT', require):
        pars[line['par_id']].extend(line['tokens']); pages[line['par_id']] = line['folio']
    keys = sorted(pars)
    return [pars[k] for k in keys], [pages[k] for k in keys]

if __name__ == '__main__':
    rng = random.Random(5)
    for name, req in [('vmsB', {'L': 'B'}), ('vmsA', {'L': 'A'})]:
        s, p = par_streams(req)
        rev = [[t[::-1] if t else None for t in reversed(x)] for x in s]
        for tag, streams in [('rev', rev)]:
            obj, _, _ = add_analyses(split(streams, random.Random(1)))
            (DATA / f'su_{name}_{tag}.json').write_text(json.dumps(obj))
            obj2, _, _ = add_analyses(split(shuffle_within_page(streams, p, rng), random.Random(1)))
            (DATA / f'su_{name}_{tag}_shuffled.json').write_text(json.dumps(obj2))
        ls, lp = line_streams(req)
        obj, _, _ = add_analyses(split(ls, random.Random(1)))
        (DATA / f'su_{name}_line.json').write_text(json.dumps(obj))
        obj2, _, _ = add_analyses(split(shuffle_within_page(ls, lp, rng), random.Random(1)))
        (DATA / f'su_{name}_line_shuffled.json').write_text(json.dumps(obj2))
        print(name, 'paragraph streams', len(s), 'line streams', len(ls))
