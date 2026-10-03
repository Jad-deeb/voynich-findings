"""Convert a clustering result into partunit_solve input (each class = one
single-letter symbol). usage: python class_to_solver.py cl_result.json cl_input.json out.json"""
import json, random, sys
res = json.load(open(sys.argv[1])); inp = json.load(open(sys.argv[2]))
streams = [[None if c is None else f'c{c}' for c in s] for s in res['classStreams']]
truth = inp.get('truth')
idx = list(range(len(streams))); random.Random(1).shuffle(idx)
ntest = len(idx) // 5; test, train = sorted(idx[:ntest]), sorted(idx[ntest:])
obj = {'streams_train': [streams[i] for i in train], 'streams_test': [streams[i] for i in test],
       'parts': {f'c{k}': [f'U:c{k}'] for k in range(res['K'])}}
if truth:
    obj['truth_train'] = [truth[i] for i in train]; obj['truth_test'] = [truth[i] for i in test]
json.dump(obj, open(sys.argv[3], 'w'))
print('streams', len(streams), 'classes', res['K'])
