import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.dirname(fileURLToPath(import.meta.url));
const input=JSON.parse(fs.readFileSync(path.join(root,'attempt_input.json'),'utf8'));
const MODE=process.argv[2]||'controls';
const RESTARTS=Number(process.argv[3]||12), STEPS=Number(process.argv[4]||18000);
const B=27, SPACE=26, N=B**4;
let seed=4082026;
function random(){seed^=seed<<13; seed^=seed>>>17; seed^=seed<<5; return (seed>>>0)/4294967296;}
function shuffle(a){for(let i=a.length-1;i>0;i--){const j=(random()*(i+1))|0; [a[i],a[j]]=[a[j],a[i]];}return a;}
function model(corpus){
  const counts=new Float64Array(N), freq=new Float64Array(26); let total=0;
  const dictionary=new Set();
  for(const s of corpus.train){
    const cs=Array.from(' '+s+' ',c=>c===' '?26:c.charCodeAt(0)-97);
    for(const c of cs)if(c<26)freq[c]++;
    for(const w of s.split(' '))dictionary.add(w);
    for(let i=0;i+3<cs.length;i++){counts[((cs[i]*B+cs[i+1])*B+cs[i+2])*B+cs[i+3]]++;total++;}
  }
  for(let i=0;i<N;i++)counts[i]=Math.log10((counts[i]+0.05)/(total+0.05*N));
  return {scores:counts,freq,dictionary};
}
function encode(segments,alphabet){
  const index=new Map(alphabet.map((c,i)=>[c,i]));
  const count=new Map(); const freq=new Float64Array(26); let denominator=0;
  for(const s of segments){
    const cs=Array.from(' '+s+' ',c=>c===' '?SPACE:index.get(c));
    if(cs.some(c=>c===undefined))throw new Error('Unseen cipher symbol');
    for(const c of cs)if(c<26)freq[c]++;
    for(let i=0;i+3<cs.length;i++){
      const k=((cs[i]*B+cs[i+1])*B+cs[i+2])*B+cs[i+3];count.set(k,(count.get(k)||0)+1);denominator++;
    }
  }
  const quads=Array.from(count,([k,n])=>{let z=k;const d=z%B;z=(z/B)|0;const c=z%B;z=(z/B)|0;const b=z%B;return [((z/B)|0),b,c,d,n];});
  const q0=Int32Array.from(quads,q=>q[0]),q1=Int32Array.from(quads,q=>q[1]),q2=Int32Array.from(quads,q=>q[2]),q3=Int32Array.from(quads,q=>q[3]),weights=Int32Array.from(quads,q=>q[4]);
  const affected=[];
  for(let a=0;a<26;a++)for(let b=0;b<26;b++)affected[a*26+b]=Int32Array.from(quads.map((q,i)=>q.slice(0,4).some(c=>c===a||c===b)?i:-1).filter(i=>i>=0));
  return {q0,q1,q2,q3,weights,freq,affected,denominator};
}
function score(data,key,table){
  let s=0; const {q0,q1,q2,q3,weights}=data;
  for(let i=0;i<weights.length;i++)s+=weights[i]*table[((key[q0[i]]*B+key[q1[i]])*B+key[q2[i]])*B+key[q3[i]]];
  return s;
}
function partial(data,key,table,idx){
  let s=0; const {q0,q1,q2,q3,weights}=data;
  for(let z=0;z<idx.length;z++){const i=idx[z];s+=weights[i]*table[((key[q0[i]]*B+key[q1[i]])*B+key[q2[i]])*B+key[q3[i]]];}
  return s;
}
function decode(segments,alphabet,key){const map=new Map(alphabet.map((c,i)=>[c,String.fromCharCode(97+key[i])]));return segments.map(s=>Array.from(s,c=>c===' '?' ':map.get(c)||'?').join(''));}
function coverage(segments,dictionary){const ws=segments.join(' ').split(' ').filter(Boolean);const substantive=ws.filter(w=>w.length>=4);return {all:ws.filter(w=>dictionary.has(w)).length/ws.length,length4plus:substantive.filter(w=>dictionary.has(w)).length/substantive.length,tokens:ws.length};}
function accuracy(decoded,plain){let correct=0,total=0;for(let i=0;i<plain.length;i++){if(decoded[i].length!==plain[i].length)throw new Error('Length changed');for(let j=0;j<plain[i].length;j++)if(plain[i][j]!==' '){total++;correct+=decoded[i][j]===plain[i][j];}}return correct/total;}
function solve(train,test,lm,id,plain=null,testplain=null){
  const alphabet=[...new Set([...train,...test].join('').replaceAll(' ',''))].sort();
  if(alphabet.length>26)throw new Error('Too many symbols');
  const data=encode(train,alphabet), validation=encode(test,alphabet), table=lm.scores;
  const plainrank=Array.from({length:26},(_,i)=>i).sort((a,b)=>lm.freq[b]-lm.freq[a]);
  const cipherrank=Array.from({length:26},(_,i)=>i).sort((a,b)=>data.freq[b]-data.freq[a]);
  const base=new Int32Array(27);base[26]=26; cipherrank.forEach((c,i)=>base[c]=plainrank[i]);
  let best=-Infinity,bestKey=null;const runs=[];
  for(let restart=0;restart<RESTARTS;restart++){
    const key=Int32Array.from(base);
    if(restart%2){const a=shuffle(Array.from({length:26},(_,i)=>i));a.forEach((v,i)=>key[i]=v);}
    else if(restart)for(let k=0;k<5;k++){const a=(random()*26)|0,b=(random()*26)|0;[key[a],key[b]]=[key[b],key[a]];}
    let current=score(data,key,table),runbest=current,runkey=Int32Array.from(key);
    const temperatureScale=data.denominator/2500;
    for(let step=0;step<STEPS;step++){
      const a=(random()*26)|0;let b=(random()*25)|0;if(b>=a)b++;
      const idx=data.affected[a*26+b],old=partial(data,key,table,idx);
      [key[a],key[b]]=[key[b],key[a]];
      const delta=partial(data,key,table,idx)-old;
      const temperature=20*temperatureScale*Math.exp(-5.99*step/STEPS);
      if(delta>=0||random()<Math.exp(delta/temperature)){current+=delta;if(current>runbest){runbest=current;runkey.set(key);}}
      else [key[a],key[b]]=[key[b],key[a]];
    }
    key.set(runkey);current=score(data,key,table);
    // Deterministic all-pair descent, with no held-out score used to pick keys.
    let improved=true;
    while(improved){improved=false;for(let a=0;a<26;a++)for(let b=a+1;b<26;b++){
      const idx=data.affected[a*26+b],old=partial(data,key,table,idx);[key[a],key[b]]=[key[b],key[a]];
      const delta=partial(data,key,table,idx)-old;
      if(delta>1e-8){current+=delta;improved=true;}else [key[a],key[b]]=[key[b],key[a]];
    }}
    const full=score(data,key,table);if(Math.abs(full-current)>1e-6)throw new Error('Incremental score mismatch');
    if(full>best){best=full;bestKey=Int32Array.from(key);}
    runs.push({score:full/data.denominator,key:Array.from(key).slice(0,alphabet.length)});
  }
  const decoded=decode(train,alphabet,bestKey),decodedtest=decode(test,alphabet,bestKey);
  const out={id,alphabet,train_chars:train.reduce((s,t)=>s+t.length,0),test_chars:test.reduce((s,t)=>s+t.length,0),train_score:best/data.denominator,test_score:score(validation,bestKey,table)/validation.denominator,key:Object.fromEntries(alphabet.map((c,i)=>[c,String.fromCharCode(97+bestKey[i])])),train_coverage:coverage(decoded,lm.dictionary),test_coverage:coverage(decodedtest,lm.dictionary),decoded_train:decoded,decoded_test:decodedtest,restarts:runs};
  if(plain){out.train_accuracy=accuracy(decoded,plain);out.test_accuracy=accuracy(decodedtest,testplain);out.plain_test_score=score(encode(testplain,Array.from('abcdefghijklmnopqrstuvwxyz')),Int32Array.from({length:27},(_,i)=>i),table)/encode(testplain,Array.from('abcdefghijklmnopqrstuvwxyz')).denominator;}
  return out;
}
const results=[];const started=Date.now();
for(const [language,corpus] of Object.entries(input.corpora)){
  const lm=model(corpus);
  const tasks=MODE==='controls'?[{id:'control_'+language,train:corpus.control,test:corpus.control_test}]:input.samples;
  for(const task of tasks){
    const r=solve(task.train,task.test,lm,task.id,MODE==='controls'?corpus.control_plain:null,MODE==='controls'?corpus.control_test_plain:null);r.language=language;
    results.push(r);fs.writeFileSync(path.join(root,MODE+'_results.json'),JSON.stringify({mode:MODE,restarts:RESTARTS,steps:STEPS,seed_initial:4082026,seconds:(Date.now()-started)/1000,results},null,2));
    console.log(JSON.stringify({id:r.id,language,train_score:r.train_score,test_score:r.test_score,accuracy:r.train_accuracy,test_accuracy:r.test_accuracy,word_coverage:r.test_coverage.length4plus,sample:r.decoded_test.join(' ').slice(0,150),elapsed_seconds:Math.round((Date.now()-started)/1000)}));
  }
}
