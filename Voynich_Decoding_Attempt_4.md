---
title: "Attempt 4 — 46 languages, period corpora, three new solvers, outside claims"
layout: default
---

[← Back to the summary](index.html)

{% raw %}
# Voynich manuscript: fourth decoding attempt

3 October 2026 · Every decoding route I could build and test, with controls

**Result: no translation.** This round tried every decoding route I could build and check against controls. Every solver that cracked a hidden test cipher found nothing in the manuscript. No word meaning, plant name or sentence has been established.

The round did produce a clearer picture of what the text is. Its word sequence lacks properties that every tested language has, above all any dependence between words two apart, and in that respect it resembles a letter-level cipher. Within the cipher designs, languages and spelling periods tested, that cipher type still did not decode.

1. **The manuscript breaks a pattern every tested language follows.** In all 46 languages, a word still predicts the word two places on: 33–76% as much as it predicts its neighbour. In the manuscript that figure is 0.00 (0.09 after merging variant spellings). Its neighbour dependence is a quarter of the lowest language. Its share of once-only words is above every language. It does not avoid repeating a word immediately, while 45 of the 46 languages do.
2. **Its glyph variation behaves like interchangeable spellings.** Words that differ by `k`/`t`, `ch`/`sh`, `e`/`ee`, `aiin`/`ain`, `ol`/`or` or `al`/`ar` occur in the same contexts, unlike one-letter differences in Latin and Italian. The preferred variant shifts by section. About 60% of the neighbour dependence sits in the glyphs on either side of the space. Spaces can be predicted from the surrounding glyphs 96.6% of the time.
3. **No decoding.** I built a solver that learns the key and each word's division at the same time. It cracked hidden-key test ciphers in six languages at 93–99% of letters, including 15th-century German herbal text and medieval Occitan. On the manuscript, across 35 Bible languages and seven medieval or early-modern language models, the real text never beat its own shuffled words by more than 0.39 bits per word. A solved test cipher beats its shuffled version by about 4 bits.
4. **Even a wrong language finds more in a real cipher.** A known Latin cipher of this type, solved with German, Hungarian, Romanian, Somali or Turkish models, still scores 0.58–1.10 bits per word above its shuffled version. The manuscript with the same five models scores 0.04–0.39. If the manuscript is a cipher of this family, its plaintext has less letter-like order than the Latin used to test it.

## What this round added

- **46 languages on identical content.** The parallel Bible corpus of Christodouloupoulos and Steedman (2015) was used to compare the manuscript's word statistics with 46 languages translating the same text.
- **Period language models.** Medieval and early modern texts were added for German, Czech, English and Occitan:
  - German herbals of 1482–1543, including *Buch der Natur* and *Gart der Gesundheit*, from the RIDGES corpus;
  - German Bibles of 1460 and 1478;
  - Middle High German (ReM);
  - Old Czech texts before 1600 (Diakorp);
  - Middle English (*Alphabet of Tales*, *Secretum*);
  - medieval Occitan (COMETA).
  The German and Czech texts come from the HistCorp collection on Zenodo (CC BY 4.0); the Occitan from Zenodo record 15300719 (CC BY 4.0).
- **Three new solvers**, each tested on hidden-key controls before use. Two passed; the null-segment solver did not and was not used:
  1. **Learned split.** Each word is divided into a prefix and a suffix (or kept whole), each piece stands for a letter, and the division is learned together with the key.
  2. **Null segments.** Words of one to three pieces, any of which may stand for nothing.
  3. **Clustering then substitution.** Pieces are first grouped by the contexts they occur in, then the class stream is solved as a substitution cipher.
- **New structural tests:**
  - dependence between words one, two and three apart;
  - how much of it the junction glyphs carry;
  - how predictable the word spaces are;
  - whether one-glyph spelling differences change a word's contexts;
  - lossy word codes;
  - a copy-and-modify text generator.
- **Meaning anchors.** Thirteen herbal pages that earlier researchers matched to pharmaceutical drawings were tested for shared label words.

## 1. The word sequence is not built like a language

### 1a. A fingerprint against 46 languages

All 46 translations were cut to the first 34,000 words from Matthew onward and measured exactly like the manuscript. "Repeats" means immediate repetition of a word, against a shuffle that keeps page and line position (Test 1 of the third attempt). "Neighbour dependence" is the bias-corrected mutual information between adjacent words. "Junction coupling" is the same quantity between a word's last character and the next word's first.

| Text | Repeats per 1,000 | Repeats vs chance | Different words | Share occurring once | Neighbour dependence (bits) | Junction coupling (bits) | Word length, mean / sd |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Voynich (IT)** | **9.7** | **1.20** | **7,069** | **0.678** | **0.118** | **0.176** | **5.07 / 1.71** |
| Latin | 1.2 | 0.09 | 5,898 | 0.503 | 0.506 | 0.037 | 5.25 / 2.67 |
| Italian | 1.1 | 0.13 | 4,574 | 0.493 | 0.812 | 0.087 | 4.56 / 2.59 |
| German | 1.7 | 0.12 | 3,360 | 0.410 | 0.843 | 0.087 | 4.55 / 2.19 |
| Czech | 0.3 | 0.03 | 5,863 | 0.507 | 0.611 | 0.082 | 4.48 / 2.46 |
| Hungarian | 1.0 | 0.06 | 6,844 | 0.578 | 0.575 | 0.143 | 5.07 / 3.11 |
| Hebrew (consonants) | 1.2 | 0.20 | 7,086 | 0.519 | 0.662 | 0.083 | 3.89 / 1.38 |
| Arabic (consonants) | 0.8 | 0.17 | 7,764 | 0.530 | 0.689 | 0.089 | 4.25 / 1.55 |
| Turkish | 1.2 | 0.32 | 7,765 | 0.497 | 0.713 | 0.070 | 6.14 / 2.78 |
| Vietnamese (syllables) | 1.7 | 0.19 | 1,616 | 0.231 | 1.452 | 0.135 | 3.23 / 1.00 |
| Chinese (characters) | 2.9 | 0.25 | 1,482 | 0.207 | 1.622 | — | — |
| Amharic (syllabary) | 0.7 | 0.20 | 9,937 | 0.593 | 0.613 | 0.244 | 3.90 / 1.52 |
| Cherokee (syllabary) | 0.8 | 0.08 | 9,610 | 0.664 | 0.495 | 0.232 | 4.16 / 1.88 |
| Indonesian | 29.6 | 2.68 | 3,038 | 0.393 | 1.096 | 0.075 | 5.57 / 2.21 |
| Range over all 46 languages | 0.2–29.6 | 0.01–2.68 | 1,444–9,937 | 0.207–0.664 | **0.495–1.622** | 0.023–1.287 | sd 1.0–3.9 |

The manuscript is outside the range of every language on two measures. Its neighbour dependence (0.118 bits) is a quarter of the lowest language (Cherokee, 0.495). Its share of once-only words (0.678) is above the highest (Cherokee, 0.664).

On immediate repetition, only Indonesian exceeds it. That is because Indonesian writes doubled words with a hyphen ("orang-orang"), which I split into two words. In every other language, repeats occur at 0.42 of chance or less.

Bible text is formulaic, so its neighbour dependence is higher than ordinary prose: Latin prose (*Secretum secretorum*) gives 0.18. The manuscript is below that too. Its narrow word-length spread matches scripts that leave out vowels or write syllables (Hebrew, Arabic, Amharic), as Reddy and Knight noted in 2011.

### 1b. Dependence stops at the next word

Mutual information between words one, two and three apart in the same line, above the position-aware shuffle (bits):

| Text | 1 apart | 2 apart | 3 apart | 2-apart as share of 1-apart |
|---|---:|---:|---:|---:|
| **Voynich (IT)** | **0.119** | **0.001** | **−0.057** | **0.00** |
| Voynich, variant spellings merged (1e) | 0.184 | 0.017 | −0.040 | 0.09 |
| Naibbe-type letter cipher of Latin (control) | 0.114 | 0.016 | −0.002 | 0.14 |
| Latin prose, *Secretum* | 0.184 | 0.125 | 0.072 | 0.68 |
| Italian prose, *Rettorica* | 0.521 | 0.176 | 0.057 | 0.34 |
| Latin prose with words shuffled inside each line | −0.007 | −0.008 | −0.006 | — |
| 46 Bible languages: lowest share (Hungarian) | 0.576 | 0.188 | 0.126 | 0.33 |
| 46 Bible languages: highest share (Tagalog) | 0.874 | 0.662 | 0.223 | 0.76 |
| 46 Bible languages: range | 0.495–1.627 | 0.188–1.009 | 0.104–0.347 | 0.33–0.76 |

Every one of the 46 languages, across about 15 families, keeps a third to three quarters of its neighbour dependence at two words' distance and still has some at three. That comes from syntax and repeated phrasing. The manuscript keeps none, even after the variant spellings are merged. The only comparison text with a similar profile is the letter-level cipher control, where each "word" is one or two letters.

### 1c. The neighbour dependence sits mostly in the junction glyphs

Shuffling words only among those with the same first and last glyph keeps all junction statistics. What remains measures dependence between neighbours beyond their edge glyphs:

| Text | Neighbour dependence | Left after keeping junction glyphs |
|---|---:|---:|
| Voynich | 0.117 | 0.048 |
| Latin *Secretum* | 0.184 | 0.173 |
| Latin, Albert of Aix | 0.180 | 0.147 |
| Italian *Rettorica* | 0.521 | 0.353 |
| Naibbe-type cipher control | 0.114 | 0.072 |

About 60% of the manuscript's neighbour dependence is carried by the glyph pair at the space, against 6–32% in Latin and Italian. The junction rules are specific. After a word ending in `-y`, the next word starts with `qo-` 1.65 times as often as chance and with `a-` 0.14 times. After `-o`, `l-` is 4.4 times as likely and `k-` 2.0 times. After `-s`, `a-` is 4.6 times as likely, and after `-r`, 2.9 times. Beyond the next word, the coupling disappears (0.006 bits at distance two).

### 1d. The spaces are predictable from the glyphs around them

Predicting space or no space between two glyphs from the two glyphs on each side, trained on half the lines and tested on the rest:

| Text | Spaces guessed right | Space uncertainty explained |
|---|---:|---:|
| Voynich IT / ZL | 96.6% / 96.2% | 80% / 78% |
| Latin *Secretum* | 94.0% | 62% |
| Italian *Rettorica* | 92.5% | 59% |
| Naibbe-type cipher control | 97.4% | 85% |

Manuscript words have rigid beginnings and endings, as the tokens of a cipher with spelling tables do.

### 1e. One-glyph spelling differences do not change a word's company

Take pairs of manuscript words that differ only by one alternation, such as `qokeedy` and `qoteedy`. Compare the glyphs that precede and follow each. As a noise baseline, compare two random halves of the same word's occurrences:

| Alternation | Word pairs | Divergence between the pair | Divergence between halves of one word | Ratio |
|---|---:|---:|---:|---:|
| `k`/`t` | 85 | 0.132 | 0.174 | 0.76 |
| `ch`/`sh` | 47 | 0.155 | 0.151 | 1.02 |
| `ee`/`e` | 47 | 0.137 | 0.156 | 0.87 |
| `ckh`/`cth` | 9 | 0.104 | 0.154 | 0.67 |
| `aiin`/`ain` | 24 | 0.119 | 0.146 | 0.81 |
| `ol`/`or` | 37 | 0.155 | 0.157 | 0.99 |
| `al`/`ar` | 23 | 0.163 | 0.181 | 0.90 |
| Latin one-letter pairs (c/t, e/i, o/u, a/e, m/s, n/m) | 3–93 | 0.30–0.38 | 0.21–0.32 | 1.1–1.5 |
| Italian one-letter pairs | 2–25 | 0.28–0.53 | 0.05–0.17 | 1.8–6.4 |

In Latin and Italian, changing one letter usually changes the word's grammatical role, and its neighbours change with it. In the manuscript, these alternations leave the neighbours unchanged. They behave like interchangeable spellings of one unit.

Their proportions shift by section. `aiin` makes up 85–86% of `aiin`/`ain` uses in Currier A but 48% on the bathing pages. `k` makes up 47% of `k`/`t` uses in herbal A but 77% in pharmaceutical A. That pattern would explain the large same-scribe section shifts found in the third attempt.

Merging these alternations reduces 7,069 word types to 4,656. Repeated three-word phrases rise from 1.1% to 6.5% of trigrams (Latin: 8.1%), and neighbour dependence rises to Latin's level (0.186 against 0.184). Two anomalies survive the merge: repeats stay at chance (1.16), and words two apart remain nearly independent (0.021 against Latin 0.123).

### 1f. Two candidate explanations that do not reproduce it

**Lossy word codes do not reproduce it.** I tried codes that let several Latin words share one codeword: dropping vowels, first three letters, first two plus last two, first letter plus length, endings only, stems. They raise the repeat rate to at most 9.3 per 1,000 but only to 0.46 of chance, because merging also raises the chance level. They also lose the vocabulary size.

**A simple copy-and-modify generator does not reproduce it either.** This was my implementation of the Timm–Schinner idea: copy a recent word, often from the line above, and change a glyph, prefix or ending. It produces 3.7–5.2 times chance repetition and no junction coupling (0.004 bits). My version is simpler than theirs, so this does not rule the idea out. It does show that junction coupling and near-chance repetition are what such a generator must also explain.

## 2. Decryption attempts

### 2a. Learned-split solver: controls

Each control enciphers a text the language model has not seen. The cipher is Naibbe-style, with prefixes, endings and whole words taken from real Voynich words. The solver is told neither the key nor where the words split.

| Plaintext (never seen by the model) | Language model | Letters correct | Held-out gain (bits/word) |
|---|---|---:|---:|
| Latin, *Secretum secretorum* | Latin corpus without it | 99.4% | +1.00 |
| Italian, *Rettorica* | Italian Bible | 99.3% | +0.85 |
| Spanish, *Picatrix* | Spanish Bible | 98.6% (4 of 4 restarts) | +1.28 |
| German, *Gart der Gesundheit* (1487) | German 1460–1543 without it | 99.1% | +1.23 |
| Old Occitan, BnF fr. 1049 | other COMETA texts | 98.8% | +1.38 |
| Middle English, *Cirurgie* | *Alphabet of Tales* + *Secretum* (period English) | 93.1% | −0.06 |
| Middle English, *Cirurgie* | modern Bible English | 14–26% (0 of 5 restarts) | −2.6 to −2.8 |
| Latin control with its words shuffled | Latin | 2.2% | −2.82 |

Every control has 11,000 cipher words and between 2,900 and 3,200 different word forms. Where the true word division was recorded (Latin, Italian, Spanish), the learned division was 96–99% correct.

The solver needs a language model close to the plaintext's spelling. Middle English enciphered and solved with a modern Bible-English model failed. The same text with a period Middle English model succeeded. So a negative result means "not this language in this spelling". It does not mean "no language".

### 2b. Learned-split solver: the manuscript

Held-out gain on Currier B (22,797 words) and Currier A (11,081 words), real against the same words shuffled within pages (bits per word):

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

The control was shuffled across the whole text, the manuscript only within pages. That difference is more likely to shrink the control's margin than to enlarge it.

### 2c. Words of one to three pieces, with null pieces

I extended the model so that a word can be one to three pieces and any piece can stand for nothing (a null). The solver failed its own control twice. Letters stayed at about 2% correct, and once nulls were allowed it collapsed into reading 83–97% of pieces as nulls, which costs nothing when the letters are wrong. A two-phase search, with letters first and nulls late, did not fix this. The model was therefore not applied to the manuscript. Designs with nulls remain untested.

### 2d. Clustering, then substitution

Grouping cipher pieces by their contexts (exchange clustering into 40 classes) recovered the control's letters with 72% purity. Solving the resulting class stream as a substitution cipher gave 70% correct letters and a held-out gain of −0.65 bits per piece, without the joint search. With the control's words shuffled first, it gave 7% and −1.08.

On the manuscript, the clusters are readable: `ch`/`sh` prefixes together, `ok`/`ot` together, `qok`/`lk`/`lt` together, `p`/`f` together, and endings `edy`/`ey`/`eol` together. This is the same interchangeability found in 1e.

On the manuscript, 12 settings (Currier A and B, two word-division rules, Latin, Italian and 15th-century German models) give real-minus-shuffled differences of −0.14 to +0.19, within restart-to-restart noise.

A language-free version of the test does not separate the manuscript from a cipher: grouping into 40 classes captures 0.08–0.13 bits per word of order in the manuscript, 0.11 in the cipher control, and 0.50 for Latin words.

### 2e. Single sections, reading order and line-by-line reading

These used the learned-split solver with the Latin and Italian corpora, real against shuffled (bits per word):

| Input | Latin | Italian |
|---|---:|---:|
| Herbal pages, scribe 1 (Currier A, 7,865 words) | −0.03 | −0.08 |
| Bathing pages, scribe 2 (Currier B, 6,227 words) | +0.13 | +0.15 |
| Star pages, scribe 3 (Currier B, 10,229 words) | +0.06 | +0.02 |
| Currier B read right to left | +0.10 | +0.08 |
| Currier B, each line as its own text | +0.21 | +0.22 |

Separate keys per section or scribe, right-to-left reading and line-by-line reading do not help.

## 3. Meaning anchors

Transcription notes record 13 herbal pages whose plant earlier researchers (Petersen, Stolfi, FSG, Landini) matched to a drawing in the pharmaceutical section. If labels name plants, a label near the matched drawing should tend to occur in that herbal page's text. Observed: 2 exact matches, against 1.64 for random herbal pages (p = 0.49). Within one glyph: 15 against 11.7 (p = 0.20). There is no detectable link, but most of those pharmaceutical pages have very few labels, so the test is weak.

## 4. What this means

The manuscript's word stream has a consistent set of properties:

- it does not avoid immediate repetition;
- it has no dependence beyond the next word;
- its neighbour dependence sits mostly in junction-glyph rules;
- its spaces are almost predictable from the glyphs around them;
- much of its glyph variation consists of interchangeable spellings whose preference drifts by section.

The second property separates the manuscript from all 46 languages. The first separates it from all except Indonesian, and there only because of how I split hyphenated words. The other three were compared only with Latin and Italian prose, which differ from the manuscript on each. My letter-level cipher control shares the second and fourth properties. It shares the first only if the writer tends to reuse the same spelling table, and the fifth only if spelling preferences change between sections. It does not reproduce the third: only about 37% of its neighbour dependence sits at the junction, against 60% in the manuscript. A cipher would need spelling tables whose word edges depend on the letters to do that.

So the strongest reading of the statistics is now this: the manuscript is not a sequence of plaintext words in any tested language, coded or not. If it carries a message, the units are smaller than words: letters, pairs or syllables, spelled with interchangeable variants. The alternative is that it was produced by a process with similar local rules and no message.

Within the letter-level family, every design I could build and validate failed on the manuscript. This held for every tested language and period spelling, both reading directions, line-by-line reading, and single sections. What remains is a cipher of this kind with:

- a structure outside the tested designs (for example, pieces standing for whole syllables, or a rule that depends on position in the line);
- a plaintext language or spelling not covered by the models;
- or no plaintext at all.

## 5. What would move this forward

1. **A crib.** One securely identified plaintext word would let the solver fix part of the key. The best candidates are the Latin-script German on f116v (`…so nim gaf mich…`, possibly a recipe line) and the month names, if any Voynich-script label near them can be tied to them.
2. **The structure.** The next solver should let pieces stand for syllables, and let the reading rule depend on position in the line. The manuscript's line-start and line-end effects are strong, and a cipher that changes at line ends would defeat every model used here.
3. **Generators held to the same statistics.** Run a faithful Timm–Schinner generator, and Greshko's own Naibbe tables, through sections 1a–1e. Whichever reproduces all five properties, including junction coupling, is the better model of how the text was made.

## Files

- `Voynich_Decoding_Research_3/scripts/`: all code. New in this round:
  - `diag_bible.py`, `diag_bible_distance.py`, `diag_distance.py`, `diag_junction.py`, `diag_spaces.py`, `diag_variants*.py`, `diag_canonical.py`, `diag_lossy.py`, `gen_selfcite.py`, `anchor_expert.py`;
  - solvers `splitunit_solve.mjs`, `segunit_solve.mjs`, `cluster_parts.mjs`;
  - corpus builders `fetch_bibles.py`, `prep_bible_lms.py`, `prep_german_lms.py`, `prep_occitan.py`, `prep_sections.py`, `prep_order_variants.py`, `prep_lang_controls.py`, `prep_cluster.py`, `class_to_solver.py`;
  - `summarize_sweep.py`.
- `Voynich_Decoding_Research_3/results/`: every solver log and key; `sweep_summary.json`.
- Downloaded corpora are in `work/bible_corpus/`, `work/histcorp/` and `work/cometa/`, with their sources and licences in this report.


## Appendix: two outside proposals checked (4 October 2026)

### ZFD: "15th-century Croatian apothecary shorthand" (github.com/denoflore/ZFD)

ZFD reads each Voynich word through a fixed positional glyph-to-sound table and a morpheme dictionary. Its published interlinear translation (`translations/INTERLINEAR_QUADRILINGUAL.md`) was measured with the same tests as above. Only lines identical to Takahashi paragraph lines were used.

The file repeats 189 paragraph lines (some folios are decoded twice). Duplicates create false long-range dependence, so they were removed. With them removed, ZFD's EVA layer reproduces the manuscript values of section 1b exactly.

| Text | Same word twice per 1,000 pairs | vs chance | Dependence 1 apart | 2 apart | 3 apart |
|---|---:|---:|---:|---:|---:|
| ZFD "expanded Croatian" layer | 11.5 | 0.61 | 0.621 | 0.038 | −0.026 |
| ZFD English layer | 334.7 | 1.07 | 0.370 | 0.025 | 0.009 |
| Croatian Bible (real) | 0.6 | 0.07 | 0.571 | 0.282 | 0.127 |
| Serbian Bible (real) | 0.5 | 0.03 | 0.634 | 0.381 | 0.176 |

ZFD decodes each Voynich word the same way everywhere, so its "Croatian" keeps the manuscript's lack of dependence between words two apart: 0.038 bits, against 0.282 in real Croatian. It also repeats words immediately about 19 times as often as real Croatian. In the English layer, 66% of words are glossed only as "?", so a third of all neighbouring pairs are "? ?".

The project's "blind decode test" scores each folio as a weighted sum of the share of known stems, the number of distinct operators and categories, and average confidence. That score ignores word order, so a word-shuffled manuscript would score the same as the real one. Its null texts (letters shuffled inside words, synthetic EVA, random Latin) all break the Voynich word shapes its dictionary was built from. The project's own notes say character-shuffled gibberish reaches about 94% coverage under the current configuration.

Neither test can distinguish a meaningful reading from a dictionary fitted to Voynich word shapes.

### "Mostly Hebrew, words written right to left, sentences left to right, mixed with two other languages, symbols and shorthand"

This proposal reaches me unsourced; there is no key to apply, so only its testable part was checked.

- **Letter level.** Read letter for letter, the manuscript would have to be as unpredictable as Hebrew writing. It is far more predictable. The next glyph given the previous one costs 2.11 bits in EVA, 2.31 with compound glyphs merged, and 2.17 with every word reversed. Consonantal Hebrew (the Hebrew Bible, as written) costs 3.42 bits. A one-to-one reading keeps this value unchanged, in either direction. Lindemann and Bowern found that regrouping glyphs does not close gaps of this size for any language they tested.
- **Word level.** Hebrew words behave like every other language in section 1: a repeat ratio of 0.20, and dependence 0.662 / 0.315 / 0.168 at one, two and three words apart. If 65% of the manuscript's words were Hebrew words, dependence two and three words apart would be clearly present, even with other tokens mixed in. It is absent.
- **Hebrew as a cipher plaintext.** A Hebrew plaintext was tested in the solver sweep (consonantal Bible Hebrew, learned word division) and gave nothing: +0.08 bits per word over shuffled.

A reading that switches freely between three languages, symbols and shorthand can produce some interpretation for any text. To count as evidence, it needs a fixed key that predicts pages it was not built from.

## Appendix: the published models, and a plain glyph chain (4 October 2026)

The same fingerprint was run on three texts:

- Timm and Schinner's own self-citation generator output (`executable/generate/generated_text.txt` from github.com/TorstenTimm/SelfCitationTextgenerator, 10,832 words; their program itself was not run);
- Greshko's own Naibbe ciphertext of a Latin natural-history text (`encrypted/nathist_output_ciphertext.txt` from github.com/greshko/naibbe-cipher, 34,764 words);
- samples from a glyph-level Markov chain trained on the manuscript itself: each glyph, including the space, predicted from the previous k glyphs, with the manuscript's line lengths and page layout.

| Text | Repeats per 1,000 | vs chance | Different words | Share occurring once | Dependence 1 apart | 2 apart | Junction coupling | Word length |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **Voynich, all paragraph text** | 9.7 | 1.19 | 7,069 | 0.68 | 0.118 | −0.01 | **0.176** | 5.07 ± 1.71 |
| Voynich, first 10,832 words | 11.1 | 1.13 | 3,243 | 0.69 | 0.041 | −0.03 | 0.123 | 4.84 ± 1.73 |
| Timm–Schinner generator (10,832 words) | 10.2 | 0.80 | 2,228 | 0.54 | 0.067 | −0.02 | 0.012 | 4.70 ± 1.56 |
| Greshko Naibbe cipher (34,764 words) | 1.4 | 0.31 | 5,600 | 0.41 | 0.102 | −0.01 | 0.002 | 5.23 ± 1.62 |
| Voynich glyph chain, 2 glyphs of memory | 4.1 | 0.90 | 5,684 | 0.74 | 0.019 | −0.03 | 0.183 | 5.06 ± 2.21 |
| Voynich glyph chain, 4 glyphs of memory | 4.2 | 1.25 | 4,926 | 0.64 | 0.033 | −0.02 | 0.182 | 5.08 ± 1.78 |
| Voynich glyph chain, 6 glyphs of memory | 5.6 | 1.52 | 4,395 | 0.51 | 0.147 | −0.05 | 0.189 | 5.07 ± 1.72 |

All three models share the absence of dependence two words apart, so that property marks the text as not word-level language without choosing between them. On the remaining measures:

- **Timm–Schinner** matches the repeat rate but not the junction coupling or the share of once-only words.
- **Naibbe** matches neither: like ordinary writing, it avoids immediate repeats (0.31 of chance), and its junction coupling is nil.
- **A Markov chain with four to six glyphs of memory** reproduces almost every word-sequence measure in this report from the manuscript's own glyph statistics: junction coupling, repeats at or above chance, word length, and nothing two words apart.

The junction coupling is therefore a short-range glyph effect, the space behaving like one more glyph, not evidence of syntax. What a stationary chain does not capture is the section-to-section drift of spellings (section 1e and Test 2 of the third attempt).

**Overall conclusion.** At the level of word sequence, the manuscript carries no measurable structure beyond a few glyphs of memory, apart from slow drift in spelling preferences. A message hidden letter by letter under heavy homophony could in principle be invisible to these statistics. Every solver able to find such a message in the controls found none here. The simpler explanation, a text produced by a short-memory writing procedure whose habits drifted over time, now fits the measurements at least as well as any cipher tested.

{% endraw %}
