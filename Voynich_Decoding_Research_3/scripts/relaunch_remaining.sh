#!/bin/bash
# After the language sweep ends, re-spread the remaining queued jobs over more cores:
# stop the small xargs launchers (running solver processes continue), then start
# every job whose log does not exist yet with 9 in parallel.
cd "$(dirname "$0")"
until [ -f ../results/sweep_done.txt ]; do sleep 30; done
for pid in $(ps aux | grep '/usr/bin/xargs' | grep -v grep | awk '{print $1}'); do kill $pid 2>/dev/null; done
: > jobs_remaining.txt
for q in jobs_queue2.txt jobs_queue3.txt jobs_queue4.txt jobs_queue5.txt; do
  while IFS= read -r line; do
    log=$(echo "$line" | sed -n 's/.*> \(\.\.\/results\/[^ ]*\.log\) 2>&1.*/\1/p')
    [ -n "$log" ] && [ ! -f "$log" ] && echo "$line" >> jobs_remaining.txt
  done < $q
done
echo "remaining: $(wc -l < jobs_remaining.txt)"
cat jobs_remaining.txt | xargs -P 9 -I{} bash -c "{}"
echo REMAINING_DONE > ../results/remaining_done.txt
