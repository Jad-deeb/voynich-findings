"""Fill the placeholders of the round-4 report and write Voynich_Decoding_Attempt_4.md."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parent / 'Voynich_Decoding_Attempt_4.md'
head = OUT.read_text(encoding='utf-8')
body = (ROOT / 'report4_body.md').read_text(encoding='utf-8')

SUMMARY = """1. **The manuscript breaks a pattern every tested language follows.** In all 46 languages, a word still predicts the word two places on: 33–76% as much as it predicts its neighbour. In the manuscript that figure is 0.00 (0.09 after merging variant spellings). Its neighbour dependence is a quarter of the lowest language. Its share of once-only words is above every language. It does not avoid repeating a word immediately, while 45 of the 46 languages do.
2. **Its glyph variation behaves like interchangeable spellings.** Words that differ by `k`/`t`, `ch`/`sh`, `e`/`ee`, `aiin`/`ain`, `ol`/`or` or `al`/`ar` occur in the same contexts, unlike one-letter differences in Latin and Italian. The preferred variant shifts by section. About 60% of the neighbour dependence sits in the glyphs on either side of the space. Spaces can be predicted from the surrounding glyphs 96.6% of the time.
3. **No decoding.** I built a solver that learns the key and each word's division at the same time. It cracked hidden-key test ciphers in six languages at 93–99% of letters, including 15th-century German herbal text and medieval Occitan. On the manuscript, across 35 Bible languages and seven medieval or early-modern language models, the real text never beat its own shuffled words by more than 0.39 bits per word. A solved test cipher beats its shuffled version by about 4 bits.
4. **Even a wrong language finds more in a real cipher.** A known Latin cipher of this type, solved with German, Hungarian, Romanian, Somali or Turkish models, still scores 0.58–1.10 bits per word above its shuffled version. The manuscript with the same five models scores 0.04–0.39. If the manuscript is a cipher of this family, its plaintext has less letter-like order than the Latin used to test it."""

CONTROL = """| Plaintext (never seen by the model) | Language model | Letters correct | Held-out gain (bits/word) |
|---|---|---:|---:|
| Latin, *Secretum secretorum* | Latin corpus without it | 99.4% | +1.00 |
| Italian, *Rettorica* | Italian Bible | 99.3% | +0.85 |
| Spanish, *Picatrix* | Spanish Bible | 98.6% (4 of 4 restarts) | +1.28 |
| German, *Gart der Gesundheit* (1487) | German 1460–1543 without it | 99.1% | +1.23 |
| Old Occitan, BnF fr. 1049 | other COMETA texts | 98.8% | +1.38 |
| Middle English, *Cirurgie* | *Alphabet of Tales* + *Secretum* (period English) | 93.1% | −0.06 |
| Middle English, *Cirurgie* | modern Bible English | 14–26% (0 of 5 restarts) | −2.6 to −2.8 |
| Latin control with its words shuffled | Latin | 2.2% | −2.82 |

Every control has 11,000 cipher words and between 2,900 and 3,200 different word forms. The learned word division was 96–98% correct whenever the letters were."""

SWEEP = """Held-out gain on Currier B (22,797 words) and Currier A (11,081 words), real against the same words shuffled within pages (bits per word):

| Language model | Currier B real | B shuffled | B difference | Currier A difference |
|---|---:|---:|---:|---:|
| 35 Bible languages (range) | −2.88 to −1.39 | — | +0.04 to +0.39 (median +0.18) | — |
| Latin corpus (classical and medieval) | −2.17 | −2.37 | +0.20 | −0.04 |
| Italian corpus (13th century) | −2.09 | −2.18 | +0.09 | −0.11 |
| German 1460–1543 (herbals and Bibles) | −2.19 | −2.30 | +0.11 | +0.03 |
| Middle High German (1050–1350) | −1.77 | −2.06 | +0.30 | +0.18 |
| Old Czech (before 1600) | −1.79 | −2.11 | +0.33 | +0.12 |
| Middle English | −2.14 | −2.29 | +0.15 | −0.02 |
| Old Occitan | −1.83 | −2.15 | +0.31 | +0.07 |

No setting reached a positive held-out gain, and no restart came near a solved control. The highest differences were for Somali and Romanian (+0.39), Old Czech (+0.33), Hungarian (+0.32), Old Occitan (+0.31) and Middle High German (+0.30). For these, the best keys produce gibberish. The first Currier B paragraph in the training set begins `…fe…aao_maie…eu_eaiitoata…` with the Romanian key and `…we…isi_mbe…ua_iedtuansus…` with the Middle High German one. The commonest words get different letters from each language: `chedy` is *a* in one key, *i* or *e* in others.

**Calibration with a real cipher and the wrong language.** I solved the 23,000-word Latin control (a true cipher of this type) with five language models that are *not* Latin. I then did the same for the manuscript:

| Wrong-language model | Latin cipher: real minus shuffled | Manuscript (Currier B): real minus shuffled |
|---|---:|---:|
| German | +0.58 | +0.04 |
| Hungarian | +0.82 | +0.32 |
| Romanian | +0.69 | +0.39 |
| Somali | +1.10 | +0.39 |
| Turkish | +0.65 | +0.23 |

A wrong model still detects a real cipher's hidden letter order, because European-type spelling shares vowel-consonant rhythm. The manuscript gives about a third of that signal.

The control was shuffled across the whole text, the manuscript only within pages. That difference is more likely to shrink the control's margin than to enlarge it."""

SEGMENT = """I extended the model so that a word can be one to three pieces and any piece can stand for nothing (a null). The solver failed its own control twice. Letters stayed at about 2% correct, and once nulls were allowed it collapsed into reading 83–97% of pieces as nulls, which costs nothing when the letters are wrong. A two-phase search, with letters first and nulls late, did not fix this. The model was therefore not applied to the manuscript. Designs with nulls remain untested."""

CLUSTER = """On the control, solving the class stream gave 70% correct letters and a held-out gain of −0.65 bits per piece. With the control's words shuffled first, it gave 7% and −1.08. On the manuscript, 12 settings (Currier A and B, two word-division rules, Latin, Italian and 15th-century German models) give real-minus-shuffled differences of −0.14 to +0.19, within restart-to-restart noise.

A language-free version of the test does not separate the manuscript from a cipher: grouping into 40 classes captures 0.08–0.13 bits per word of order in the manuscript, 0.11 in the cipher control, and 0.50 for Latin words."""

SECTIONS = """These used the learned-split solver with the Latin and Italian corpora, real against shuffled (bits per word):

| Input | Latin | Italian |
|---|---:|---:|
| Herbal pages, scribe 1 (Currier A, 7,865 words) | −0.03 | −0.08 |
| Bathing pages, scribe 2 (Currier B, 6,227 words) | +0.13 | +0.15 |
| Star pages, scribe 3 (Currier B, 10,229 words) | +0.06 | +0.02 |
| Currier B read right to left | +0.10 | +0.08 |
| Currier B, each line as its own text | +0.21 | +0.22 |

Separate keys per section or scribe, right-to-left reading and line-by-line reading do not help."""

body = (body.replace('{{CONTROL_TABLE}}', CONTROL).replace('{{SWEEP_TABLE}}', SWEEP)
            .replace('{{SEGMENT_SECTION}}', SEGMENT).replace('{{CLUSTER_SECTION}}', CLUSTER)
            .replace('{{SECTION_SECTION}}', SECTIONS))
head = head.replace('{{SUMMARY_LIST}}', SUMMARY)
assert '{{' not in body, [x for x in body.split('{{')[1:]][:2]
text = head.replace('{{BODY}}', body)
assert '{{' not in text
OUT.write_text(text, encoding='utf-8', newline='\n')
print('written', OUT, len(text))
