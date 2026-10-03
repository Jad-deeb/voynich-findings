"""Test 2 cross-check on the ZL transcription."""
import json
import random

from common import DATA
from diag_topic import vms_pages, topic_test

if __name__ == '__main__':
    rng = random.Random(408)
    src = 'ZL'
    h1 = vms_pages({'H': '1', 'L': 'A', 'I': 'H'}, src)
    p1 = vms_pages({'H': '1', 'L': 'A', 'I': 'P'}, src)
    h2 = vms_pages({'H': '2', 'L': 'B', 'I': 'H'}, src)
    b2 = vms_pages({'H': '2', 'L': 'B', 'I': 'B'}, src)
    rows = [topic_test('ZL same scribe 1 (A): herbal vs pharma', h1, p1, rng),
            topic_test('ZL same scribe 2 (B): herbal vs biological', h2, b2, rng),
            topic_test('ZL split-half: scribe 2 bio odd vs even', b2[::2], b2[1::2], rng),
            topic_test('ZL split-half: scribe 1 herbal odd vs even', h1[::2], h1[1::2], rng)]
    (DATA / 'diag_topic_ZL.json').write_text(json.dumps(rows, indent=1))
