"""Pharmaceutical-section labels that recur in the text of only one or two herbal
pages, with a baseline from ordinary pharmaceutical paragraph words."""
import json
from collections import defaultdict, Counter

from common import load_lines, DATA

if __name__ == '__main__':
    lines, pages = load_lines('IT')
    herbal = defaultdict(Counter)
    par = Counter()
    for l in lines:
        if l['utype'] == 'P':
            for t in l['tokens']:
                if t:
                    par[t] += 1
                    if pages.get(l['folio'], {}).get('I') == 'H':
                        herbal[t][l['folio']] += 1
    cands = []
    for l in lines:
        if l['utype'] == 'L' and pages.get(l['folio'], {}).get('I') == 'P':
            for t in l['tokens']:
                if t and len(t) >= 5 and 1 <= len(herbal.get(t, {})) <= 2 and par[t] <= 4:
                    cands.append({'label': t, 'label_locus': f"{l['folio']}.{l['line']}",
                                  'herbal_pages': dict(herbal[t]), 'paragraph_total': par[t]})
    for c in cands:
        print(c)
    labels = [t for l in lines if l['utype'] == 'L' and pages.get(l['folio'], {}).get('I') == 'P'
              for t in l['tokens'] if t and len(t) >= 5]
    words = [t for l in lines if l['utype'] == 'P' and pages.get(l['folio'], {}).get('I') == 'P'
             for t in l['tokens'] if t and len(t) >= 5]
    share_labels = sum(1 <= len(herbal.get(t, {})) <= 2 and par[t] <= 4 for t in labels) / len(labels)
    # a paragraph word is itself counted in `par`, so discount its own occurrence
    share_words = sum(1 <= len(herbal.get(t, {})) <= 2 and 1 <= par[t] - 1 <= 4 for t in words) / len(words)
    print(f'labels meeting criterion {share_labels:.3f}; ordinary pharmaceutical words {share_words:.3f}')
    (DATA / 'label_anchor_candidates.json').write_text(json.dumps(
        {'candidates': cands, 'share_labels': round(share_labels, 3),
         'share_paragraph_words': round(share_words, 3)}, indent=1))
