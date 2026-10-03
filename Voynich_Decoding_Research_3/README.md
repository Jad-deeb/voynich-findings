# Third Voynich decoding attempt: reproduction notes

Read `../Voynich_Decoding_Attempt_3.md` first. This is a research record, not a decipherment.

## Requirements

Python 3.9+ and Node.js 20+. Only standard libraries are used. The inputs are the two
transliteration snapshots and the comparison corpora already downloaded by attempt 2
(`work/IT_ivtff_1a.txt`, `work/ZL3b-n.txt`, `work/astra/corpora/`). Their sources and
SHA-256 values are recorded in `../Voynich_Decoding_Research_2/sources.json`.

## Order of execution (from `scripts/`)

```
python vms_data.py IT ZL          # parse transliterations -> data/IT_lines.json, data/ZL_lines.json
python diag_boundaries.py         # test: glyph coupling across word spaces
python diag_topic.py              # test: same-scribe subject change vs page permutation
python diag_topic2.py             # same, line-medial words only, with top contributors
python diag_topic_bands.py        # same, split into 50 most frequent types vs the rest
python diag_wordseq2.py           # test: adjacent-word dependence, position-aware null
python diag_local.py              # test: local exact and near repeats
python prep_wordunit.py           # solver inputs, controls and language-model texts
python prep_partunit.py           # word-parse rules for the structure-aware solver
bash run_partunit_grid.sh         # decryption grid (8 restarts per setting; several hours on 10 cores)
python summarize_grid.py          # results/partunit_summary.json (read from the solver logs)
python fill_report_table.py       # writes the manuscript table into the report
```

In the reported run, the Currier B settings were stopped after 4 completed restarts to save time
(`results/capped_runs.txt`); the two shuffled Currier B "whole" settings were started separately
with `restarts=4`. The summary is computed from the restarts recorded in each log, so stopped
runs have no final JSON with a saved key.

The repetition, vocabulary, Naibbe-variant, ZL section-shift and label-anchor checks were run as
short inline scripts; their outputs are `data/diag_repetition.json`, `data/diag_vocabulary.json`,
`data/diag_sticky_naibbe.json`, `data/diag_topic_ZL.json` and `data/label_anchor_candidates.json`.
`python decode_sample.py <result.json>` applies a saved key to the input text. `diag_wordseq.py` is the first
version of the adjacent-word test. Its page-level shuffle mixed line-position vocabularies and
produced misleading negative values; it is kept only as a record and superseded by
`diag_wordseq2.py`.

## Solvers

- `partunit_solve.mjs`: each word is parsed into one or two part symbols; each symbol stands
  for one plaintext letter; homophones allowed; plaintext spaces dropped. Exact likelihood
  objective; annealed Gibbs sampling; held-out gain against an order-free model.
- `wordunit_solve.mjs`: the same hypothesis without a word parse (each word type stands for
  a string of 1 to 3 letters). It failed its own positive control, so it was not used for
  conclusions about the manuscript.

Random seeds are given on each command line in `run_partunit_grid.sh` and in the scripts.

## Controls

`naibbe_like.py` is a Naibbe-style generator written for this attempt. It is not Greshko's
table set and not a Voynich key. Control plaintext is the first part of the Latin
*Secretum secretorum*; the in-domain language model excludes those words.

## Round 4 (see `../Voynich_Decoding_Attempt_4.md`)

Additional inputs (downloaded in this round, sources and licences in the report):
`work/bible_corpus/` (fetch_bibles.py), `work/histcorp/` (HistCorp, Zenodo 10013189) and
`work/cometa/` (COMETA, Zenodo 15300719).

```
python fetch_bibles.py; python prep_bible_lms.py; python prep_german_lms.py; python prep_occitan.py
python diag_bible.py; python diag_bible_distance.py; python diag_distance.py; python diag_junction.py
python diag_spaces.py; python diag_variants.py; python diag_variants_latin.py; python diag_canonical.py
python diag_lossy.py; python gen_selfcite.py; python anchor_expert.py; python diag_class_structure.py
python prep_splitunit.py; python prep_lang_controls.py; python prep_sections.py; python prep_order_variants.py
node splitunit_solve.mjs data=... lm=... [alpha=...] sweeps=100 restarts=2 seed=41 out=...   # see jobs_*.txt
python prep_cluster.py; node cluster_parts.mjs in=... K=40; python class_to_solver.py ...; node partunit_solve.mjs ...
python summarize_sweep.py
```

The exact solver command lines of the round are in `scripts/jobs_lang_sweep.txt`,
`jobs_queue2.txt` to `jobs_queue5.txt`, `jobs_wronglang.txt` and `jobs_remaining.txt`.
`segunit_solve.mjs` (null segments) failed its control and was not used for conclusions.
