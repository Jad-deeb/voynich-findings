#!/bin/bash
# Runs the part-unit solver grid in parallel. Results go to ../results/pu_*.json
cd "$(dirname "$0")"
JOBS=jobs_partunit.txt
: > $JOBS
add() { echo "node partunit_solve.mjs data=../data/$1.json lm=../data/$2.txt sweeps=80 restarts=8 tg0=300 tg1=1 seed=$3 out=../results/pu_${1}__${2}.json > ../results/pu_${1}__${2}.log 2>&1" >> $JOBS; }
# controls: in-domain and out-of-domain language models, real and shuffled
for c in ctrl_naibbe6_11k ctrl_naibbe6_23k ctrl_naibbe12_23k; do
  for v in "" _shuffled; do
    add pu_${c}${v} lm_latin_ctrl_indomain 11
    add pu_${c}${v} lm_latin_noSecreta 12
  done
done
# Voynich: two Currier languages x three parse rules x two languages x real/shuffled
for s in vmsA vmsB; do
  for r in core suffix whole; do
    for v in "" _shuffled; do
      add pu_${s}_${r}${v} lm_latin_all 21
      add pu_${s}_${r}${v} lm_italian 22
    done
  done
done
cat $JOBS | xargs -P 10 -I{} bash -c "{}"
