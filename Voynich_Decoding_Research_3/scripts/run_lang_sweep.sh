#!/bin/bash
# Learned-split solver against every Bible language model, on Currier B (real and
# shuffled within pages). 2 restarts x 100 sweeps each. Results: ../results/sw_*.json/.log
cd "$(dirname "$0")"
JOBS=jobs_lang_sweep.txt
: > $JOBS
python -c "
import json
a=json.load(open('../data/lm_bible_alphabets.json'))
for lang,v in sorted(a.items()):
    for var in ('', '_shuffled'):
        safe=lang.replace(\"'\",'')
        print(f\"node splitunit_solve.mjs data=../data/su_vmsB{var}.json lm=\\\"../data/lm_bible_{lang}.txt\\\" alpha={v['alphabet']} sweeps=100 restarts=2 seed=41 out=../results/sw_vmsB{var}__{safe}.json > ../results/sw_vmsB{var}__{safe}.log 2>&1\")
" > $JOBS
wc -l $JOBS
cat $JOBS | xargs -P ${PAR:-10} -I{} bash -c "{}"
echo SWEEP_DONE
