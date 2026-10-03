---
title: "Attempt 1 — first statistics and reading guide"
layout: default
---

[← Back to the summary](index.html)

{% raw %}
# Voynich manuscript: research notes

Prepared 3 October 2026. Companion to **Voynich_English_Reading_Guide.pdf**.

## Outcome and scope

This was a preliminary investigation, not a successful decipherment. No main-script word meaning or sentence translation was established. The English guide supplies visual descriptions and clearly labelled interpretations. The month renderings apply to familiar-script annotations, generally considered later additions.

The supplied PDF has **209 image-only pages**, including covers and foldout views. All pages were reviewed in contact sheets; selected pages were examined at their extracted image resolution. Every page returned zero characters from ordinary PDF text extraction. The PDF page map covers the entire supplied file; it does not assert that 209 scans equal 209 manuscript sides or panels.

Original PDF SHA-256: `4a74ebc44b92b09b93c1461974b1c432b7a62f30bd80ef89bba9517c4bf8224b`.

## Data provenance

The computation uses manuscript-wide published transliterations. It does **not** claim that every retained line was independently transcribed from this PDF. Some manuscript page/panel identifiers refer to material photographed together in a single scan.

- IT/Takahashi, IVTFF version 1a, dated 27 December 2022 in its header: [mirror file](https://raw.githubusercontent.com/noah-chelednik/voynich-data/main/data_sources/cache/IT_ivtff_1a.txt).
- Zandbergen-Landini ZL, version 3b, dated 13 May 2025 in its header: [mirror file](https://raw.githubusercontent.com/noah-chelednik/voynich-data/main/data_sources/cache/ZL3b-n.txt).
- [Original transliteration index and format discussion](https://www.voynich.nu/transcr.html).
- [Public mirror repository](https://github.com/noah-chelednik/voynich-data), used solely to acquire cached source files after direct downloads failed.

The downloaded ZL header and opening lines were compared with the original file as displayed by the web reader. The IT opening lines were compared with the corresponding published VT/Takahashi opening lines. This is a limited provenance check, not a complete byte comparison against the original hosting site. The hashes below define the exact downloaded snapshots.

Comments in transcription files, including speculative plant identifications, were excluded from the analysis and were not treated as facts or instructions.

## Filtering and measurement

1. Select IVTFF text loci whose type begins with a paragraph marker (`P`). Skip labels, circular text and other locus types for this computation.
2. Remove inline comments and paragraph markers. Treat a drawing intrusion marker `<->` as a token boundary.
3. Split on periods. Keep only tokens entirely made from lowercase ASCII letters `a-z`. Leave an exclusion slot for each uncertain or marked-up token instead of joining its neighbours. This deliberately excludes commas marking uncertain spaces, alternative readings, unknown symbols and marked ligatures.
4. Count EVA letters in retained tokens. EVA letters are transliteration units and do not necessarily correspond one-to-one to written graphemes, sounds or plaintext letters.
5. Count immediate identical neighbours only within each text line, excluding pairs that cross a removed token. Do not count line-end to next-line-start pairs.
6. For the IT shuffle comparison, shuffle retained tokens within each manuscript side/panel identifier, preserving every line slot and every exclusion slot. Repeat 200 times with random seed 408.
7. Read illustration-class codes from source metadata for the section comparison. `H` is herbal and `B` is biological/bathing. The source uses `S` for star-marked text. These classes are visual labels, not decoded headings.

Strict filtering makes IT and ZL sample sizes unequal. It is biased toward legible, unmarked text. Therefore the results should not be presented as complete manuscript totals or as a controlled comparison between languages.

The output key `folios_with_paragraphs` counts **side/panel identifiers** such as `f1r`, `f1v`, or a foldout panel. It does not count physical leaves.

## What the tests show

The nearly exclusive initial position of EVA `q`, its frequent following `o`, and the shift in common token frequencies between visual sections are stable across these two filtered samples. These are structural observations without known meanings.

In IT, 270 immediate identical pairs occur among 27,545 eligible pairs. The within-page/panel shuffled average is 197.99, with simulated totals ranging from 162 to 240. The observed count is about 1.36 times that average. This supports local dependence relative to this particular shuffle model. It does not establish a natural language, an encoded message or a meaningless generator; all could produce local dependence. No formal decipherment claim or multiple-hypothesis statistical significance claim is made.

`qokedy` appears in 2.56% of retained IT bathing tokens and 0.38% of herbal tokens, about a 6.8-fold difference. ZL gives a similar ratio. Illustration class, scribal hand, Currier variety and transcription conventions can be confounded. The contrast is not a translation of this token as “water”, “bath”, “woman”, or any other proposed English word.

The frequency substitution maps a ranked list of individual EVA letters to `etaoinshrdlcumwfgypbvkjxqz`, a common English frequency order. It is one deliberately simple baseline. It did not produce readable English. It does not exhaust all substitutions, test Latin or other plaintexts, model composite graphemes, or rule out any cipher family.

## Research references

- [Yale Beinecke overview](https://beinecke.library.yale.edu/beinecke/collections/beinecke-cipher-voynich-manuscript): manuscript identity and undeciphered status.
- [Yale MS 408 catalogue](https://pre1600ms.beinecke.library.yale.edu/docs/pre1600.ms408.HTM): physical structure. Some historical attributions in this older record have been superseded.
- [Zandbergen, The Writing System](https://www.voynich.nu/writing.html): readable month annotations and their later hand.
- [Lindemann and Bowern, Character Entropy in Modern and Historical Texts](https://arxiv.org/abs/2010.14697): constraints on written units.
- [Sterneck, Polish and Bowern, Topic Modeling in the Voynich Manuscript](https://arxiv.org/abs/2107.02858): text clustering in relation to illustrations and scribes.
- [Greshko, The Naibbe Cipher](https://www.michaelgreshko.com/naibbe-cipher), and [2025 Cryptologia paper](https://doi.org/10.1080/01611194.2025.2566408): a constructed cipher showing that some Voynich-like properties can arise in encoded text; not a manuscript decryption key. No Naibbe implementation was used in this analysis.
- [Davis, Multispectral Imaging and the Voynich Manuscript](https://manuscriptroadtrip.wordpress.com/2024/09/08/multispectral-imaging-and-the-voynich-manuscript/): difficult annotations, including the final leaf.
- [Hodgins, University of Arizona parchment dating report, 2009](https://www.voynich.nu/papers/Carbon_GH_2009.pdf): parchment dating and its distinction from ink dating.

## Numerical results

The following is the unedited output of the analysis script. All token forms are EVA spellings, not English words or established pronunciations.

```json
[
  {
    "filename": "IT_ivtff_1a.txt",
    "sha256": "db624a731114f26854bbfe3a59d40827fa8911be46d086b6c558d99e557241ee",
    "method": "Paragraph loci only; periods are boundaries; uncertain/non-basic-EVA tokens excluded without joining their neighbours; no cross-line adjacency.",
    "paragraph_loci": 4118,
    "folios_with_paragraphs": 206,
    "valid_tokens": 32222,
    "excluded_tokens": 1490,
    "unique_tokens": 6691,
    "mean_EVA_letter_length": 5.1014834585066104,
    "top_tokens": [
      [
        "daiin",
        738
      ],
      [
        "ol",
        494
      ],
      [
        "chedy",
        479
      ],
      [
        "shedy",
        415
      ],
      [
        "aiin",
        403
      ],
      [
        "chol",
        367
      ],
      [
        "or",
        327
      ],
      [
        "chey",
        323
      ],
      [
        "qokeey",
        303
      ],
      [
        "qokeedy",
        301
      ],
      [
        "ar",
        281
      ],
      [
        "qokain",
        276
      ]
    ],
    "top_EVA_letters": [
      [
        "o",
        21248
      ],
      [
        "e",
        17573
      ],
      [
        "h",
        15693
      ],
      [
        "y",
        15030
      ],
      [
        "a",
        11950
      ],
      [
        "c",
        11533
      ],
      [
        "d",
        11000
      ],
      [
        "i",
        10360
      ],
      [
        "k",
        9566
      ],
      [
        "l",
        8876
      ],
      [
        "r",
        6219
      ],
      [
        "s",
        6142
      ],
      [
        "t",
        5683
      ],
      [
        "n",
        5482
      ],
      [
        "q",
        5196
      ],
      [
        "p",
        1441
      ],
      [
        "m",
        887
      ],
      [
        "f",
        414
      ],
      [
        "g",
        62
      ],
      [
        "x",
        24
      ],
      [
        "z",
        1
      ]
    ],
    "q_occurrences": 5196,
    "q_at_token_start": 5164,
    "q_followed_by_o": 5072,
    "adjacent_identical_pairs": 270,
    "eligible_adjacent_pairs": 27545,
    "sections": {
      "T": {
        "tokens": 2236,
        "top_tokens": [
          [
            "chedy",
            41
          ],
          [
            "shedy",
            41
          ],
          [
            "ol",
            36
          ],
          [
            "or",
            34
          ],
          [
            "aiin",
            34
          ]
        ],
        "qokedy_count": 11,
        "daiin_count": 30
      },
      "H": {
        "tokens": 9590,
        "top_tokens": [
          [
            "daiin",
            390
          ],
          [
            "chol",
            218
          ],
          [
            "chor",
            144
          ],
          [
            "or",
            115
          ],
          [
            "shol",
            101
          ]
        ],
        "qokedy_count": 36,
        "daiin_count": 390
      },
      "S": {
        "tokens": 11400,
        "top_tokens": [
          [
            "aiin",
            203
          ],
          [
            "chedy",
            190
          ],
          [
            "qokeey",
            165
          ],
          [
            "ar",
            160
          ],
          [
            "al",
            144
          ]
        ],
        "qokedy_count": 61,
        "daiin_count": 131
      },
      "A": {
        "tokens": 260,
        "top_tokens": [
          [
            "aiin",
            6
          ],
          [
            "shey",
            5
          ],
          [
            "dy",
            4
          ],
          [
            "daiin",
            4
          ],
          [
            "sar",
            3
          ]
        ],
        "qokedy_count": 0,
        "daiin_count": 4
      },
      "C": {
        "tokens": 635,
        "top_tokens": [
          [
            "or",
            19
          ],
          [
            "daiin",
            15
          ],
          [
            "aiin",
            15
          ],
          [
            "ol",
            12
          ],
          [
            "qokal",
            9
          ]
        ],
        "qokedy_count": 2,
        "daiin_count": 15
      },
      "B": {
        "tokens": 5947,
        "top_tokens": [
          [
            "shedy",
            218
          ],
          [
            "ol",
            216
          ],
          [
            "chedy",
            180
          ],
          [
            "qokain",
            155
          ],
          [
            "qokedy",
            152
          ]
        ],
        "qokedy_count": 152,
        "daiin_count": 78
      },
      "P": {
        "tokens": 2154,
        "top_tokens": [
          [
            "daiin",
            90
          ],
          [
            "chol",
            43
          ],
          [
            "ol",
            38
          ],
          [
            "cheol",
            37
          ],
          [
            "or",
            33
          ]
        ],
        "qokedy_count": 1,
        "daiin_count": 90
      }
    },
    "sample": [
      "fachys",
      "ykal",
      "ar",
      "ataiin",
      "shol",
      "shory",
      "cthres",
      "y",
      "kor",
      "sholdy"
    ],
    "frequency_baseline_mapping": {
      "o": "e",
      "e": "t",
      "h": "a",
      "y": "o",
      "a": "i",
      "c": "n",
      "d": "s",
      "i": "h",
      "k": "r",
      "l": "d",
      "r": "l",
      "s": "c",
      "t": "u",
      "n": "m",
      "q": "w",
      "p": "f",
      "m": "g",
      "f": "y",
      "g": "p",
      "x": "b",
      "z": "v"
    },
    "frequency_baseline_f1r_line1": "yinaoc orid il iuihhm caed caelo nualtc o rel caedso",
    "within_folio_shuffle": {
      "runs": 200,
      "random_seed": 408,
      "mean_duplicate_pairs": 197.99,
      "minimum": 162,
      "maximum": 240,
      "observed_to_shuffle_mean": 1.3637052376382646
    }
  },
  {
    "filename": "ZL3b-n.txt",
    "sha256": "bf5b6d4ac1e3a51b1847a9c388318d609020441ccd56984c901c32b09beccafc",
    "method": "Paragraph loci only; periods are boundaries; uncertain/non-basic-EVA tokens excluded without joining their neighbours; no cross-line adjacency.",
    "paragraph_loci": 4130,
    "folios_with_paragraphs": 207,
    "valid_tokens": 28159,
    "excluded_tokens": 3701,
    "unique_tokens": 5928,
    "mean_EVA_letter_length": 5.211761781313257,
    "top_tokens": [
      [
        "daiin",
        707
      ],
      [
        "chedy",
        429
      ],
      [
        "shedy",
        369
      ],
      [
        "ol",
        347
      ],
      [
        "chol",
        305
      ],
      [
        "qokeey",
        298
      ],
      [
        "qokeedy",
        297
      ],
      [
        "chey",
        278
      ],
      [
        "aiin",
        278
      ],
      [
        "qokain",
        275
      ],
      [
        "qokaiin",
        263
      ],
      [
        "qokedy",
        263
      ]
    ],
    "top_EVA_letters": [
      [
        "o",
        18911
      ],
      [
        "e",
        15794
      ],
      [
        "h",
        13914
      ],
      [
        "y",
        13534
      ],
      [
        "a",
        10604
      ],
      [
        "c",
        10245
      ],
      [
        "d",
        10086
      ],
      [
        "i",
        9248
      ],
      [
        "k",
        8682
      ],
      [
        "l",
        7729
      ],
      [
        "s",
        5302
      ],
      [
        "r",
        5261
      ],
      [
        "t",
        5120
      ],
      [
        "n",
        4977
      ],
      [
        "q",
        4881
      ],
      [
        "p",
        1279
      ],
      [
        "m",
        746
      ],
      [
        "f",
        334
      ],
      [
        "g",
        72
      ],
      [
        "x",
        12
      ],
      [
        "b",
        10
      ],
      [
        "j",
        7
      ],
      [
        "u",
        7
      ],
      [
        "z",
        2
      ],
      [
        "v",
        1
      ]
    ],
    "q_occurrences": 4881,
    "q_at_token_start": 4854,
    "q_followed_by_o": 4782,
    "adjacent_identical_pairs": 238,
    "eligible_adjacent_pairs": 22033,
    "sections": {
      "T": {
        "tokens": 1933,
        "top_tokens": [
          [
            "shedy",
            36
          ],
          [
            "chedy",
            34
          ],
          [
            "or",
            31
          ],
          [
            "daiin",
            27
          ],
          [
            "dar",
            26
          ]
        ],
        "qokedy_count": 11,
        "daiin_count": 27
      },
      "H": {
        "tokens": 8530,
        "top_tokens": [
          [
            "daiin",
            383
          ],
          [
            "chol",
            184
          ],
          [
            "chor",
            128
          ],
          [
            "shol",
            97
          ],
          [
            "s",
            94
          ]
        ],
        "qokedy_count": 36,
        "daiin_count": 383
      },
      "S": {
        "tokens": 9755,
        "top_tokens": [
          [
            "chedy",
            179
          ],
          [
            "qokeey",
            162
          ],
          [
            "qokeedy",
            132
          ],
          [
            "aiin",
            129
          ],
          [
            "ar",
            125
          ]
        ],
        "qokedy_count": 60,
        "daiin_count": 119
      },
      "A": {
        "tokens": 250,
        "top_tokens": [
          [
            "aiin",
            7
          ],
          [
            "ar",
            7
          ],
          [
            "shey",
            5
          ],
          [
            "s",
            4
          ],
          [
            "dy",
            4
          ]
        ],
        "qokedy_count": 0,
        "daiin_count": 3
      },
      "C": {
        "tokens": 578,
        "top_tokens": [
          [
            "daiin",
            16
          ],
          [
            "or",
            11
          ],
          [
            "ol",
            11
          ],
          [
            "ar",
            8
          ],
          [
            "qokal",
            8
          ]
        ],
        "qokedy_count": 4,
        "daiin_count": 16
      },
      "B": {
        "tokens": 5236,
        "top_tokens": [
          [
            "shedy",
            184
          ],
          [
            "qokain",
            157
          ],
          [
            "chedy",
            156
          ],
          [
            "ol",
            152
          ],
          [
            "qokedy",
            151
          ]
        ],
        "qokedy_count": 151,
        "daiin_count": 74
      },
      "P": {
        "tokens": 1877,
        "top_tokens": [
          [
            "daiin",
            85
          ],
          [
            "chol",
            36
          ],
          [
            "cheol",
            33
          ],
          [
            "okeol",
            29
          ],
          [
            "or",
            28
          ]
        ],
        "qokedy_count": 1,
        "daiin_count": 85
      }
    },
    "sample": [
      "fachys",
      "ykal",
      "ar",
      "ataiin",
      "shol",
      "shory",
      null,
      "y",
      "kor",
      "sholdy"
    ]
  }
]
```

## Reproduce the calculation

Save the code below as `analyse_voynich.py` and run it with Python 3. It uses only the Python standard library. It downloads the two public text snapshots into a `voynich_data` subdirectory beside the script, verifies their hashes, and writes `analysis_results.json` there. If a public mirror snapshot changes, the hash check stops the run rather than silently producing a different result.

```python
from pathlib import Path
from collections import Counter, defaultdict
import json, re, random, statistics, hashlib

ROOT = Path(__file__).parent / 'voynich_data'
ROOT.mkdir(exist_ok=True)

# Download the precise public mirror snapshots used for this attempt.
from urllib.request import urlopen
BASE = 'https://raw.githubusercontent.com/noah-chelednik/voynich-data/main/data_sources/cache/'
EXPECTED = {
    'IT_ivtff_1a.txt': 'db624a731114f26854bbfe3a59d40827fa8911be46d086b6c558d99e557241ee',
    'ZL3b-n.txt': 'bf5b6d4ac1e3a51b1847a9c388318d609020441ccd56984c901c32b09beccafc',
}
for filename, expected in EXPECTED.items():
    path = ROOT / filename
    if not path.exists():
        path.write_bytes(urlopen(BASE + filename).read())
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        raise ValueError(f'Input snapshot changed: {filename}. Expected {expected}; got {actual}')

def parse(path):
    lines = []
    metadata = {}
    rejected = 0
    for raw in path.read_text(encoding='utf-8-sig').splitlines():
        if raw.startswith('#'):
            continue
        m = re.match(r'^<(f[^>]+)>\s*(.*)$', raw)
        if not m:
            continue
        locus, body = m.groups()
        if '.' not in locus:
            metadata[locus] = dict(re.findall(r'\$([A-Z])=([^\s>]+)', body))
            continue
        folio = locus.split('.')[0]
        code = locus.split(',',1)[1] if ',' in locus else ''
        if not re.match(r'^[@+*=]P', code):
            continue
        body = re.sub(r'<![^>]*>', '', body)
        body = body.replace('<%>', '').replace('<$>', '').replace('<->>', '.')
        tokens = []
        for token in body.split('.'):
            token = token.strip()
            if not token:
                continue
            if re.fullmatch(r'[a-z]+', token):
                tokens.append(token)
            else:
                tokens.append(None)
                rejected += 1
        lines.append({'locus':locus,'folio':folio,'tokens':tokens})
    return lines, metadata, rejected

def count_repeats(lines):
    pairs = [(a,b) for ln in lines for a,b in zip(ln['tokens'], ln['tokens'][1:]) if a is not None and b is not None]
    return sum(a==b for a,b in pairs),len(pairs)

def analyse(name):
    path=ROOT/name
    lines, metadata, rejected=parse(path)
    tokens=[w for ln in lines for w in ln['tokens'] if w is not None]
    counts=Counter(tokens)
    chars=Counter(''.join(tokens))
    sections=defaultdict(Counter)
    for ln in lines:
        sections[metadata.get(ln['folio'],{}).get('I','?')].update(w for w in ln['tokens'] if w is not None)
    repeats, pairs=count_repeats(lines)
    result={
        'filename':name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'method':'Paragraph loci only; periods are boundaries; uncertain/non-basic-EVA tokens excluded without joining their neighbours; no cross-line adjacency.',
        'paragraph_loci':len(lines),'folios_with_paragraphs':len(set(ln['folio'] for ln in lines)),
        'valid_tokens':len(tokens),'excluded_tokens':rejected,'unique_tokens':len(counts),
        'mean_EVA_letter_length':statistics.mean(map(len,tokens)),
        'top_tokens':counts.most_common(12),'top_EVA_letters':chars.most_common(),
        'q_occurrences':chars['q'], 'q_at_token_start':sum(w.startswith('q') for w in tokens),
        'q_followed_by_o':sum(w.count('qo') for w in tokens),
        'adjacent_identical_pairs':repeats,'eligible_adjacent_pairs':pairs,
        'sections':{s:{'tokens':sum(c.values()),'top_tokens':c.most_common(5),
                       'qokedy_count':c['qokedy'],'daiin_count':c['daiin']} for s,c in sections.items()},
        'sample':next(ln for ln in lines if ln['locus'].startswith('f1r.1,'))['tokens']
    }
    if name.startswith('IT'):
        # An illustrative baseline only: letter ranks mapped onto a common English rank order.
        # EVA letters are bookkeeping symbols, not established graphemes.
        rank='etaoinshrdlcumwfgypbvkjxqz'
        mapping={c:rank[i] for i,(c,n) in enumerate(chars.most_common())}
        result['frequency_baseline_mapping']=mapping
        result['frequency_baseline_f1r_line1']=' '.join(''.join(mapping[c] for c in w) for w in result['sample'] if w)
        page_lines=defaultdict(list)
        for ln in lines:
            page_lines[ln['folio']].append(ln)
        rng=random.Random(408)
        simulated=[]
        for run in range(200):
            new=[]
            for folio, group in page_lines.items():
                pool=[w for ln in group for w in ln['tokens'] if w is not None]
                rng.shuffle(pool)
                iterator=iter(pool)
                for ln in group:
                    new.append({'tokens':[next(iterator) if w is not None else None for w in ln['tokens']]})
            simulated.append(count_repeats(new)[0])
        result['within_folio_shuffle']={'runs':200,'random_seed':408,'mean_duplicate_pairs':statistics.mean(simulated),
                                       'minimum':min(simulated),'maximum':max(simulated),
                                       'observed_to_shuffle_mean':repeats/statistics.mean(simulated)}
    return result

results=[analyse('IT_ivtff_1a.txt'),analyse('ZL3b-n.txt')]
(ROOT/'analysis_results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
for r in results:
    print(json.dumps(r,indent=2))

```

{% endraw %}
