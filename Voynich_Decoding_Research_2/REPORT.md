# Voynich manuscript: second decoding attempt

3 October 2026 · Controlled cipher searches and structural checks

**Result: no reliable decipherment, no established new word meanings, and no defensible English translation of the main script.** This attempt tested specific decoding rules and rejected the resulting passages as translations. It does not prove that the book is meaningless or that a solution is impossible.

## What was actually attempted

Your PDF supplied the page context. The numerical work used published symbol transcriptions: the Takahashi-derived IT file and the Zandbergen–Landini ZL file. EVA strings such as `daiin` are labels for written shapes, not known pronunciations or translations.

The new searches went substantially beyond the earlier frequency-rank substitution:

- **32 one-to-one substitution configurations:** four comparison languages × two text varieties × two symbol groupings × forward or reversed symbols inside each word. A single consistent key was fitted to each sample.
- **16 many-to-one substitution configurations:** the same four languages and two varieties, in both directions, using a more compressed grouping of common shapes. These searches allowed different written symbols to represent the same plaintext letter.
- **1,280 search starts:** 24 per ordinary configuration and 32 per many-to-one configuration, with 30,000 or 50,000 proposed changes per start, followed by local refinement. That is 48.64 million proposed changes before refinement; it is not an exhaustive search of all keys.
- **Reserved pages:** approximately 2,500 transcription characters were used to fit each key; another approximately 2,500 from different pages were used to inspect its predictions. The evaluation passages were not used to select keys.

The two varieties were herbal text marked Currier A / hand 1 and bathing text marked Currier B / hand 2. Those are the transcription metadata categories; A and B are not identified natural languages. Separating these groups avoids assuming one key works across all scribes and sections.

Ordinary substitution was tested on individual EVA code letters and on a grouping that combines `ch`, `sh`, and the four bench-and-gallows combinations. The many-to-one search used the published Minimal conversion, which also combines several stroke endings, `ee`, and `qo`. These are alternative hypotheses about writing units, not recovered sounds. The source conversion is documented in the [Lindemann–Bowern research repository](https://github.com/chirila/Voynich-public/blob/decc4caaa6515b86e42a219d1da8d81114736f2e/R%20code/1_Create_Voynich_Corpus.Rmd).

## Checking that the methods could solve known examples

I trained character-sequence models on 80% of each comparison work. I then deliberately encrypted passages from the remaining fifth, without giving the search the keys. Another passage encrypted with each same key tested whether its recovery carried over.

The table measures **correct letters in these artificial controls only**. It is not an accuracy claim for the Voynich manuscript.

| Language | One-to-one fitting passage | One-to-one reserved passage | Many-to-one fitting passage | Many-to-one reserved passage |
|---|---:|---:|---:|---:|
| Latin | 100.0% | 98.4% | 99.4% | 97.9% |
| Italian | 100.0% | 100.0% | 99.5% | 98.9% |
| English | 100.0% | 100.0% | 100.0% | 100.0% |
| Spanish | 100.0% | 100.0% | 99.2% | 99.3% |

The controls support using the solvers for these limited tests. The remaining errors also show that a high scoring key need not get every rare letter right. Controls made from the same reference works are easier than an unknown manuscript from another time, dialect, or writing system.

The comparison material was Latin works including *De magia* and *Secretum secretorum*, Italian *Rettorica*, English *Cirurgie*, *Secretum secretorum*, and *Alphabet of Tales*, and a Spanish edition of *Picatrix*, from the [research corpus](https://github.com/chirila/Voynich-public/tree/decc4caaa6515b86e42a219d1da8d81114736f2e/Corpora/Historical_texts). These editions have different dates and editorial histories. In particular, I have not established that the supplied Spanish wording represents medieval Spanish.

## Why the apparent matches failed

None of the 48 selected outputs yielded a convincing connected passage on the reserved pages. The ordinary searches often produced plausible fragments embedded in strings with no coherent grammar. Across those configurations, the highest share of reserved words of four or more letters found in the relevant training vocabulary was only **15.8%**. Vocabulary coverage is a rough diagnostic, not a translation test.

The more flexible search exposed a more serious failure mode. It could turn many different shapes into the same few common letters. For example, one Spanish-model output began:

> laas lla llas alas a las las las lla lla lla la las ella

**This is a failed search output, not Spanish recovered from the manuscript.** Its key used only four different output letters. Other configurations manufactured repeated English- or Italian-looking fragments. A best-case vocabulary match of 39.8% still did not produce coherent prose. This is a limitation of the unconstrained scoring method, and those outcomes cannot rule out more realistic many-to-one ciphers.

A method that permits arbitrary word-by-word substitutions, extra vowels, anagrams, or changing rules can produce much more fluent stories. Without a fixed rule that predicts unseen passages, those stories would not establish the book's meaning. I have not presented any such story as a translation.

## Structural evidence worth retaining

The next symbol remains unusually predictable, even after common shapes are grouped together. I measured conditional character entropy, in bits: lower values mean less uncertainty about the next character given the previous one. Spaces were included; no pairs crossed physical line boundaries or uncertain gaps in the manuscript sample.

These are means and observed ranges for 100 sampled windows of roughly 2,500 characters per condition. The ranges are **not confidence intervals**; windows can overlap. Comparison prose was divided into 15-word segments to limit boundary differences.

| Text | Grouping | Mean bits | Observed window range |
|---|---|---:|---:|
| Voynich A, herbal, hand 1 | eva | 2.005 | 1.834–2.183 |
| Voynich A, herbal, hand 1 | benches | 2.195 | 2.042–2.337 |
| Voynich A, herbal, hand 1 | minimal | 2.348 | 2.230–2.470 |
| Voynich B, bathing, hand 2 | eva | 1.708 | 1.542–1.848 |
| Voynich B, bathing, hand 2 | benches | 1.771 | 1.599–1.881 |
| Voynich B, bathing, hand 2 | minimal | 1.908 | 1.812–2.019 |
| Latin | normalized_latin_alphabet | 3.206 | 3.041–3.287 |
| Italian | normalized_latin_alphabet | 3.021 | 2.904–3.082 |
| English | normalized_latin_alphabet | 2.995 | 2.770–3.209 |
| Spanish | normalized_latin_alphabet | 3.012 | 2.809–3.140 |

The second transcription gave the same broad separation. A fixed one-to-one renaming preserves this kind of predictability exactly within a given representation. That makes ordinary substitution into the tested reference prose a poor fit. It does not identify the language or exclude a more complex encoding.

There is also a substantial association with paragraph position. Among accepted words in these subsets, the EVA symbols `p` or `f` occur as follows:

| Subset | First word of paragraph | Words inside a line |
|---|---:|---:|
| A herbal | 54/94 (57.4%) | 309/6645 (4.7%) |
| B bathing | 11/31 (35.5%) | 148/5484 (2.7%) |

The pattern persists in ZL. These are written shapes, not identified sounds /p/ and /f/. An interpretation must account for such position effects. Possibilities include special initial forms, textual conventions, or an encoding rule sensitive to position; this count cannot decide between them. It also cannot distinguish meaningful text from all possible methods of generating nonsemantic text.

## Data correction and practical limits

I corrected an issue in the earlier parser: the literal illustration-gap marker `<->` had not been recognized, so the neighboring words could be rejected together. The new parser retains those words and treats the gap as a break. The finalized searches use the corrected input. The accepted paragraph-token counts are now **34,409 for IT** and **29,398 for ZL**, replacing the earlier conservative sample counts of 32,222 and 28,159. They are not complete manuscript word counts.

Ambiguous tokens, alternative readings, and non-basic EVA forms were excluded, without joining across them. This loses information and can bias the samples. The two transcriptions concern the same manuscript and are not fully independent observations. The solvers used IT; ZL provided a structural cross-check, not an independently fitted decryption.

Reference texts were normalized to lowercase `a–z`; accents were removed and several historical characters expanded or approximated. Word spaces stayed fixed. Reversal changed symbol order within words, not the word order of a whole line. Many untested possibilities remain: other languages, spelling systems, variable-length codes, hidden or false spaces, null symbols, transposition, abbreviations, and rules changing with position. Failure of these heuristic searches is not a mathematical proof against those possibilities.

## What can be said about the book in English

The earlier illustrated reading guide remains an explanation of visible subject matter, not a translation. Plants, circular celestial diagrams, bathing figures, containers and plant parts suggest a collection concerned with natural knowledge and possibly medicine or astrology. That is an interpretation of the pictures. This second attempt has not recovered an author's statement that confirms it, a recipe, a plant name, or a sentence of the main script.

The most useful next research direction would be a constrained account of the writing units and their positions, tested on diagram labels and new pages. A securely identified bilingual phrase or name would be especially valuable. Guessing a plant or calling a repeated word “water” does not provide such an anchor.

## Audit material

The accompanying `Voynich_Decoding_Research_2.zip` contains all 48 selected manuscript outputs and keys, configuration scores, control metrics, exact sampled locations, source checksums, and the analysis scripts. Historical control passages and the comparison texts are not redistributed in the archive; pinned source download scripts reconstruct the inputs.

The original PDF is unchanged. This report records an unsuccessful but testable decoding attempt, rather than an English edition of the manuscript.
