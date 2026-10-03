---
title: "Attempt 3 — word-level tests and a structure-aware cipher solver"
layout: default
---

[← Back to the summary](index.html)

{% raw %}
# Voynich manuscript: third decoding attempt

3 October 2026 · Word-level hypotheses, controls and a structure-aware decryption test

**Result: no decipherment.** No word meaning, plant name or sentence of the main script has been established, and no English translation is offered. This attempt did produce four results that narrow what the text can be. Each one is measured against controls with a known answer.

1. **Words repeat immediately far more often than in prose.** The same word follows itself in 9.7 of every 1,000 word pairs, 1.18 times what a shuffle of each page predicts. Six prose texts in Latin, Italian and Middle English have 0.0 to 1.0 per 1,000, a small fraction of chance. In a word-for-word code, two identical codewords in a row need two identical plaintext words in a row, unless different plaintext words share a codeword. A codebook of ordinary prose therefore does not fit, whatever its codewords look like and however many spellings each word has.
2. **The same scribe uses different words on different subjects.** Within one scribe's hand, the word distribution shifts between herbal and pharmaceutical pages, and between herbal and bathing pages, by 0.08–0.12 bits per word. Latin shifts by 0.08 between two parts of one work and by 0.15 between two works. Every letter-level cipher variant tested shifts by 0.009 or less.
3. **A direct decryption test of the letter-level family (Greshko's Naibbe type) found nothing.** The test treats each word as one or two plaintext letters. The solver recovered hidden keys exactly in all positive controls, including one with a larger vocabulary than the manuscript. On the manuscript, the real text scored within about 0.2 bits per word of the same words shuffled, against a gap of about four bits in the controls. This held with Latin or Italian models and three ways of dividing words.
4. **Vocabulary size and adjacent-word dependence do not separate the hypotheses.** Both fall within the natural-language range and the cipher range tested. The glyph rules across word spaces are stronger than in either comparison language. This count cannot say whether they reflect spelling rules at word junctions or spaces that are not word boundaries.

These results do not prove the text is meaningless. They exclude the two assumptions behind most proposed solutions: that each Voynich word stands for a word of ordinary prose, and that the text is a letter cipher with a fixed spelling system. Some cases remain open; they are listed at the end.

## What the earlier attempts left open

The second attempt tested letter-for-letter substitution, one-to-one and many-to-one, with the word spaces kept as word spaces. All 48 configurations failed. That leaves the hypotheses in which a Voynich *word*, rather than a glyph, is the unit:

- a whole plaintext word (a codebook or nomenclator, or a natural language in an unknown script);
- one or two plaintext letters, with many spellings for each (a verbose homophonic cipher; Greshko's Naibbe cipher of 2025 is the worked example);
- a syllable.

René Zandbergen's summary of the field lists two related questions as open: how the manuscript's many once-only words compare with plain texts, and whether any word-for-word substitution can yield meaningful text ([word statistics](https://www.voynich.nu/a4_word.html)). Older sources note qualitatively that the same word may be "repeated two, three or more times" (D'Imperio 1978, quoted on [this page](https://www.voynich.nu/a5_synt.html)). Tests 1, 2 and 4 below measure these points against controls.

## Material

- Transcription: Takahashi (IT) as the main source; Zandbergen–Landini (ZL) as a cross-check. Only paragraph text is used: 34,411 readable words in IT, 7,069 different words, 772 paragraphs. Words containing an unreadable glyph are kept as gaps; their neighbours are never joined.
- Metadata from the transcription file: scribe (Lisa Fagin Davis's hands 1–5), Currier language A/B, and illustration type. These are labels for the pages, not decoded content.
- Comparison texts: the Latin, Italian and Middle English editions used in the second attempt (Lindemann–Bowern research corpus). Spelling was reduced to plain letters.
- Cipher controls: a Naibbe-style generator written for this attempt. It follows the published design: letters are grouped as singles and pairs, each group becomes one word, and the spelling table for each letter is drawn at random. It is **not** Greshko's table set and not a Voynich key.

## Test 1. Immediate repetition

Count how often a word is directly followed by the same word in the same line. Compare with a shuffle that moves words only within the same page and the same line position (first, middle or last word; first line of paragraph or not). The Voynich text has strong line-position effects, so a plain page shuffle would give a false baseline. For the comparison texts, lines of nine words and pages of 270 words were imposed.

| Text | Pairs | Same word twice | Per 1,000 pairs | Ratio to shuffle |
|---|---:|---:|---:|---:|
| Voynich, IT, all paragraphs | 29,477 | 286 | **9.7** | **1.18** |
| Voynich, IT, Currier A | 8,952 | 99 | 11.1 | 1.21 |
| Voynich, IT, Currier B | 20,097 | 184 | 9.2 | 1.17 |
| Voynich, ZL, all paragraphs | 29,294 | 279 | 9.5 | 1.11 |
| Latin, *Secretum secretorum* | 30,216 | 8 | 0.3 | 0.02 |
| Latin, Albert of Aix | 30,216 | 0 | 0.0 | 0.00 |
| Latin, Trithemius, *Steganographia* | 19,136 | 5 | 0.3 | 0.08 |
| Italian, Brunetto Latini, *Rettorica* | 28,648 | 6 | 0.2 | 0.02 |
| Middle English, *Cirurgie* | 30,216 | 31 | 1.0 | 0.05 |
| Middle English, *Alphabet of Tales* | 30,216 | 22 | 0.7 | 0.07 |
| Latin letters as units | 30,024 | 731 | 24.3 | 0.32 |
| Naibbe-type cipher, random table draws | 30,216 | 39 | 1.3 | 0.27 |

Prose avoids saying the same word twice in a row; the Voynich text does not. The excess is largest among less common words: excluding the 100 most frequent types, Voynich words repeat at 2.30 times chance, against 0.26 in the Latin control. Some very common words avoid repetition (`aiin`, `shey` and `s` never repeat; `daiin` repeats at 0.56), while `qokeedy`, `qokedy`, `qokeey`, `chol` and `okaiin` repeat at about twice chance.

What this rules out: a **word-for-word code of ordinary prose**. A codebook maps each plaintext word to one or more codewords. Two identical codewords in a row can then only come from two identical plaintext words in a row, so the code's rate of identical neighbours cannot exceed the plaintext's: at most about 1 per 1,000 pairs for prose like the comparison texts, against 9.7 in the manuscript. This holds however the codewords are spelled and however a writer chooses among several codewords for one word. It applies equally to prose of this kind written directly in an unknown script.

What it does not rule out: a plaintext that itself repeats words often (lists, litanies, tables, or a language with frequent word doubling); a code that maps different plaintext words to the same codeword; and letter-level ciphers whose writer tends to reuse the same spelling table. I simulated the last case. If the table is kept for the next letter with probability 0.5 to 0.95, the ratio rises to 0.8–1.7, which covers the manuscript's value.

## Test 2. Same scribe, different subject

For two groups of pages, measure the mutual information between word and group, in bits per word. Then subtract its average when whole pages are randomly reassigned between the groups. Pages stay intact, so words that cluster on particular pages do not inflate the result.

| Comparison | Pages | Words | Excess (bits/word) | z |
|---|---:|---:|---:|---:|
| Scribe 1, Currier A: herbal vs pharmaceutical | 95 / 16 | 7,865 / 2,282 | **0.084** | 29.9 |
| Scribe 2, Currier B: herbal vs bathing ("biological") | 20 / 19 | 2,307 / 6,227 | **0.117** | 18.5 |
| Scribe 1, herbal: odd vs even pages (null check) | 48 / 47 | 3,849 / 4,016 | 0.000 | 0.1 |
| Scribe 2, bathing: odd vs even pages (null check) | 10 / 9 | 3,320 / 2,907 | −0.005 | −0.8 |
| Herbal pages: scribe 1 (A) vs scribe 2 (B) | 95 / 20 | 7,865 / 2,307 | 0.148 | 39.2 |
| Latin: *Secretum* vs Bruno, *De magia* | 60 / 60 | 9,000 / 9,000 | 0.147 | 40.6 |
| Latin: Albert of Aix vs *Steganographia* | 60 / 60 | 9,000 / 9,000 | 0.149 | 51.5 |
| Latin: *Secretum*, part 1 vs part 3 | 60 / 60 | 9,000 / 9,000 | 0.081 | 18.7 |
| Naibbe-type cipher of the same Latin pairs | 60 / 60 | 9,000 / 9,000 | 0.003–0.004 | 1.6–2.4 |
| Naibbe-type variants (6 or 12 tables, habitual table reuse) | 60 / 60 | 9,000 / 9,000 | 0.000–0.009 | — |

ZL gives 0.079 and 0.115 for the two same-scribe comparisons; its odd/even checks give 0.000 and 0.001. Restricting the count to words in the middle of lines, outside first lines of paragraphs, gives 0.098 and 0.121. This shows the effect is not caused by the different shapes of paragraphs on the two kinds of page.

Which words carry the difference? For scribe 1, 26% of the excess comes from the 50 most frequent types, similar to the Latin contrasts (10–25%). For scribe 2, the share is 46%: the bathing pages use much more `qokain`, `qol`, `qokeedy`, `ol`, `shedy` and `qokal`, and the herbal pages more `aiin`, `ar`, `or` and `chdy`. Scribe 1's pharmaceutical pages favour forms with an `e` after the gallows (`okeol`, `okeey`, `qokeol`, `cheol`); the herbal pages favour `cthy`, `chy` and `cthol`.

In a letter-level cipher, a change of subject barely moves the word distribution, because letter frequencies hardly change between subjects. The manuscript's shifts are roughly 9 to 40 times larger than those of the letter-level variants tested. To fit, a letter-level cipher needs the writer's spelling preferences to change from section to section. That is possible, but it is an extra assumption, not a prediction. Gradual drift in a word-generating process, as proposed by Timm and Schinner, could also produce such shifts. This test cannot separate drift from meaning.

## Test 3. Decryption: each word stands for one or two letters

This is the direct test of the Naibbe family. Hypothesis: every word is either a single-letter word or a prefix plus suffix, and every prefix, suffix or single-letter word stands for one plaintext letter. Many symbols may stand for the same letter, and plaintext word spaces are not written.

**Method.** The solver chooses a letter for every symbol to maximise the exact likelihood of the word sequence. The likelihood combines a five-letter-context language model (Kneser–Ney) with the probability of choosing each spelling. This penalises keys that collapse many symbols onto a few common letters, which was the failure seen in the second attempt. The search is annealed Gibbs sampling over each symbol's letter, with 8 random restarts (4 for Currier B, which is twice as long, to save time). One fifth of the paragraphs is held back. On those, the decoded text is scored against an order-free model of the same decoded strings, in bits per word. Positive values mean the language model predicts the next decoded string better than its frequency alone.

The Voynich words were divided by three rules, which are hypotheses rather than findings:

- **core**: the prefix runs to the first gallows or bench glyph (`qok|eedy`, `ch|edy`, `d|aiin`);
- **suffix**: the suffix is the longest common ending (`qok|eedy`, `ch|ol`, `o|l`);
- **whole**: each word type is a single symbol for one letter.

**Controls.** Latin from the *Secretum secretorum* was enciphered with the generator; the solver was not given the key. The "out-of-domain" language model excludes that work entirely.

| Control | Words | Different words | Language model | Letters correct | Held-out gain (bits/word) |
|---|---:|---:|---|---:|---:|
| 6 tables | 11,000 | 3,015 | in-domain | 99.9% | +1.49 |
| 6 tables | 11,000 | 3,015 | out-of-domain | 99.9% | +1.18 |
| 6 tables | 23,000 | 4,418 | out-of-domain | 99.8% | +1.11 |
| 12 tables | 23,000 | 7,870 | out-of-domain | 99.8% | +1.13 |
| Same, words shuffled within the text | — | — | either | 2% | −2.8 to −2.9 |

All 8 restarts reached the same key on every control. For example, held-back paragraphs of the 12-table control decode to `tunacumnotabilibusqueipsemetfraterrogerusposuitsupratextuminmultislocis…` (*una cum notabilibus que ipsemet frater Rogerus posuit supra textum in multis locis*), identical to the hidden plaintext.

**Manuscript.**

| Text | Word division | Model | Held-out gain, real words (range over restarts) | Held-out gain, shuffled words | Real minus shuffled |
|---|---|---|---:|---:|---:|
| Currier A (11,081 words) | core | Latin | −3.33 (−3.33 to −3.12) | −3.11 | −0.22 |
| Currier A (11,081 words) | core | Italian | −3.23 (−3.23 to −3.17) | −3.03 | −0.20 |
| Currier A (11,081 words) | suffix | Latin | −2.93 (−3.35 to −2.93) | −3.03 | +0.10 |
| Currier A (11,081 words) | suffix | Italian | −3.02 (−3.32 to −3.02) | −3.03 | +0.01 |
| Currier A (11,081 words) | whole | Latin | −1.16 (−1.21 to −1.07) | −1.09 | −0.07 |
| Currier A (11,081 words) | whole | Italian | −1.11 (−1.20 to −1.08) | −1.09 | −0.02 |
| Currier B (22,797 words) | core | Latin | −3.20 (−3.35 to −3.20) | −3.32 | +0.12 |
| Currier B (22,797 words) | core | Italian | −3.28 (−3.37 to −3.28) | −3.35 | +0.08 |
| Currier B (22,797 words) | suffix | Latin | −3.03 (−3.10 to −3.03) | −3.16 | +0.13 |
| Currier B (22,797 words) | suffix | Italian | −3.18 (−3.50 to −3.12) | −3.26 | +0.08 |
| Currier B (22,797 words) | whole | Latin | −1.42 (−1.43 to −1.36) | −1.42 | 0.00 |
| Currier B (22,797 words) | whole | Italian | −1.40 (−1.42 to −1.32) | −1.38 | −0.02 |

Values are bits per word on held-back paragraphs, for the key with the best training likelihood (Currier A: 8 restarts; Currier B: 4 restarts). For comparison, solved controls score +1.11 to +1.49 and shuffled controls −2.8 to −2.9. Across the 12 manuscript settings, real minus shuffled ranges from −0.22 to +0.13 bits per word. Values cannot be compared between word divisions, because each division produces a different number of letters per word.

On Currier B, the real text scores slightly above its shuffled version with the core and suffix divisions (+0.08 to +0.13). That is about a thirtieth of the four-bit gap between solved and shuffled controls. It fits the weak dependence between neighbouring words reported under Test 4, which is stronger in Currier B than in Currier A.

The best manuscript keys produce Latin- or Italian-looking letter strings. For example, the first paragraph of f1r begins `dyatdrsororietutouareuetunedoutciuiuicaporeas…` under the core rule with the Latin model. Fragments such as `mihi`, `accipi` or `obscu` appear here and there. **These are failed search outputs, not readings.** The language model rewards Latin-like letter runs wherever it can make them. The same procedure on shuffled words produces equally plausible fragments, such as `multate` and `uiemenes`, and scores within 0.22 bits per word of the real text. The restarts also disagree with each other, unlike the controls.

**What this rules out:** a Naibbe-type cipher of Latin or Italian whose word division matches one of the three rules. The controls were solved with a wide margin, so the result does not hinge on fine tuning, but it does depend on the word division being right. The result is limited to those two languages and those three rules. A different prefix–suffix boundary, a different language, null words, or letter groups of other sizes remain untested. I also tried the hypothesis without any word division, where each word type stands for a free string of one or two letters. That solver failed its own positive control (4% of letters correct), so it says nothing about the manuscript and is not used here.

## Test 4. Properties that do not discriminate

**Vocabulary.** At 34,000 words, the manuscript has 7,025 different words in IT and 6,715 in ZL; 68% and 67% of them occur once. The comparison texts range from 3,635 different words (Middle English *Cirurgie*) to 9,276 (Latin, Albert of Aix), with 52–72% occurring once. A Naibbe-type cipher gives 5,258 (6 tables) to 10,025 (12 tables), with 40–63% occurring once. Both families can match the manuscript, so vocabulary size does not decide between them.

**Adjacent-word dependence.** Bias-corrected mutual information between neighbouring words, with the position-aware shuffle: Voynich 0.117 bits (Currier A 0.045, B 0.137); Latin 0.180–0.183; Italian 0.522; Naibbe-type cipher 0.119. The manuscript sits at the low end of the natural-language range and is level with the cipher.

**Glyph rules across spaces.** The last glyph of a word predicts the first glyph of the next more strongly than in Latin: 0.177 bits of excess mutual information against 0.038–0.055 in Latin and 0.122 in Italian. The pattern is specific. After `-y`, the next word starts with `qo-` 1.65 times as often as chance and with `a-` 0.14 times. After `-o`, the next word starts with `l-` 4.4 times and `k-` 2.0 times as often as chance. After `-s`, `a-` is 4.6 times as frequent, and after `-r`, 2.9 times. Some of these look like words split in the wrong place, such as `o l` for `ol`, which supports Zandbergen's caution that not every gap is a word boundary. The coupling exceeds both comparison languages. This count cannot tell whether it comes from spelling rules at word junctions or from gaps that are not word boundaries.

**Local similar words.** Words one glyph apart from a word among the previous 20 occur 1.20 times as often as on another page in the same section. The figure for natural-language prose is 0.88–1.11. That is a modest excess.

## What remains possible

Excluded, under the assumptions stated above:

- a word-for-word code (codebook or nomenclator) of ordinary prose, or ordinary prose in a known European language written in an unknown script (Test 1);
- a letter-level homophonic cipher with fixed, section-independent spelling preferences (Test 2);
- a Naibbe-type cipher of Latin or Italian with any of the three tested word divisions (Test 3).

Tested without success in the second attempt, which is not a proof: letter-for-letter substitution of Latin, Italian, Spanish or English with the word spaces kept.

Still open:

- a plaintext that repeats words often: lists, recipes in a fixed formula, litanies, charms, or a language with frequent word doubling, such as some East Asian languages. Testing this needs comparison texts that are not in the current corpus;
- codes that are lossy or partly null, where different plaintext words share a codeword or filler words are inserted;
- letter-level ciphers whose spelling preferences change by section and that also divide words differently from the three rules tested;
- a meaningless text produced by a copying-and-modifying procedure. Tests 1, 2 and the local-similarity figures are the measurements any such generator would now have to reproduce;
- a syllable-level code. The solver can be extended to letter groups of three; this was not run.

## Most useful next steps

1. **Comparison texts with frequent word doubling.** The manuscript's lack of repetition avoidance is the clearest new constraint. Texts that share it would be a lead. Candidates: formulaic recipe collections, litanies, and languages with reduplication. This needs new corpora, which I did not download without your approval.
2. **A generator test.** Implement the Timm–Schinner self-citation procedure and check whether it reproduces Tests 1 and 2 together. In particular, can it produce section shifts carried 26–46% by the most frequent words, as observed?
3. **Image-anchored labels.** Thirteen labels in the pharmaceutical section also occur in the text of only one or two herbal pages, for example `chtody` (label on f89v2, text on f4v only), `okcheor` (f100v; f93r only), `chols` (f100v; f5v) and `darar` (f99r; f33v). The list is in `data/label_anchor_candidates.json`. By text statistics alone these links mean nothing: ordinary pharmaceutical words of the same length meet the same criterion as often (7.5% against 7.3% for labels). Only a clear visual match between the labelled drawing and the herbal plant would count. This is the one route found here that could test meaning without assuming a cipher.
4. **More word divisions for Test 3.** The controls show that the solver works when the division is right, so trying more boundary rules is cheap.

## Files

- `Voynich_Decoding_Research_3/README.md`: how to reproduce every number above.
- `Voynich_Decoding_Research_3/scripts/`: parser, tests, generator and solvers (Python and Node.js, standard libraries only).
- `Voynich_Decoding_Research_3/data/`: derived line records and every test's JSON output.
- `Voynich_Decoding_Research_3/results/`: solver runs, keys, logs and `partunit_summary.json`.

The original PDF and the earlier attempts are unchanged.

{% endraw %}
