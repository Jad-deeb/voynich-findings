# Reproduce the second Voynich decoding attempt

These are research experiments, not a decipherment. Read REPORT.md first.

Requirements: Python 3.9+ and Node.js 20+; only their standard libraries are used.
Run from the extracted archive directory. The downloads use the network, write
comparison texts under scripts/corpora, and put the two transliterations beside
this README. Source revisions and SHA-256 values are recorded in sources.json.

```
python scripts/download_transliterations.py
python scripts/fetch_corpora.py
python scripts/prepare_attempt.py
node scripts/solve_substitution.mjs controls 12 18000
node scripts/solve_substitution.mjs manuscript 24 30000
python scripts/prepare_homophonic.py
node scripts/solve_homophonic.mjs controls 24 40000
node scripts/solve_homophonic.mjs manuscript 32 50000
python scripts/structural_checks.py
```

Generated working JSON files are placed in scripts/. The included results.json
and configurations.csv are the completed run used in the report.

Methods: character tetragram log-likelihood with add-0.05 smoothing, simulated
annealing, and final local refinement. Each segment receives one boundary space
at each end. The one-to-one search swaps assignments; the many-to-one search
changes individual assignments and sometimes swaps whole plaintext-letter groups.
Spaces remain fixed. Keys are selected on fitting score only. Per-character
accuracy is measured only on deliberately encrypted controls with known plaintext.
Vocabulary matches are not translation accuracy. Conditional entropy counts
actual within-segment pairs, including spaces, without added endpoint spaces.

Random seeds: ordinary search 4082026; many-to-one search 384082026; ordinary
control encryption 4082026; many-to-one control encryption 40838; entropy
window sampling 20261003. Random generator state proceeds through configurations
in the recorded order. Node checks incremental score calculations against a
complete recomputation after each search start. The structural script checks
that sampled passages match their recorded locations and that fitting and
evaluation page IDs are disjoint.

The unconstrained many-to-one solver tends to collapse the manuscript into too
few plaintext letters. Its superficially improved scores are not evidence of
a language match. Control success does not remove that limitation.

Original analysis scripts were written for this investigation. The Minimal
conversion table follows Lindemann and Bowern's published research code, credited
in REPORT.md. Downloaded sources retain their original ownership and terms.
