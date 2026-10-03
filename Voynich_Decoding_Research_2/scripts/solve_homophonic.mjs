import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.dirname(fileURLToPath(import.meta.url));
const input=JSON.parse(fs.readFileSync(path.join(root,'homophonic_input.json'),'utf8'));
const MODE=process.argv[2]||'controls';
const RESTARTS=Number(process.argv[3]||24), STEPS=Number(process.argv[4]||40000);
const B=27,N=B**4;
let seed=384082026;
function random(){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return(seed>>>0)/4294967296;}
function model(corpus){
  const counts=new Float64Array(N),dictionary=new Set();let total=0;
  for(const s of corpus.train){
    const cs=Array.from(' '+s+' ',c=>c===' '?26:c.charCodeAt(0)-97);
    for(const w of s.split(' '))dictionary.add(w);
    for(let i=0;i+3<cs.length;i++){counts[((cs[i]*B+cs[i+1])*B+cs[i+2])*B+cs[i+3]]++;total++;}
  }
  for(let i=0;i<N;i++)counts[i]=Math.log10((counts[i]+0.05)/(total+0.05*N));
  return{scores:counts,dictionary};
}
function encode(segments,alphabet){
  const index=new Map(alphabet.map((c,i)=>[c,i])),space=alphabet.length,C=space+1;
  const count=new Map();let denominator=0;
  for(const s of segments){
    const cs=Array.from(' '+s+' ',c=>c===' '?space:index.get(c));
    if(cs.some(c=>c===undefined))throw new Error('Unseen cipher symbol');
    for(let i=0;i+3<cs.length;i++){const k=((cs[i]*C+cs[i+1])*C+cs[i+2])*C+cs[i+3];count.set(k,(count.get(k)||0)+1);denominator++;}
  }
  const quads=Array.from(count,([k,n])=>{let z=k;const d=z%C;z=(z/C)|0;const c=z%C;z=(z/C)|0;const b=z%C;return [((z/C)|0),b,c,d,n];});
  const q0=Int32Array.from(quads,q=>q[0]),q1=Int32Array.from(quads,q=>q[1]),q2=Int32Array.from(quads,q=>q[2]),q3=Int32Array.from(quads,q=>q[3]),weights=Int32Array.from(quads,q=>q[4]);
  const affected=Array.from({length:space},(_,a)=>Int32Array.from(quads.map((q,i)=>q.slice(0,4).includes(a)?i:-1).filter(i=>i>=0)));
  return {q0,q1,q2,q3,weights,affected,denominator};
}
function score(data,key,table){let s=0;const{q0,q1,q2,q3,weights}=data;for(let i=0;i<weights.length;i++)s+=weights[i]*table[((key[q0[i]]*B+key[q1[i]])*B+key[q2[i]])*B+key[q3[i]]];return s;}
function partial(data,key,table,idx){let s=0;const{q0,q1,q2,q3,weights}=data;for(let z=0;z<idx.length;z++){const i=idx[z];s+=weights[i]*table[((key[q0[i]]*B+key[q1[i]])*B+key[q2[i]])*B+key[q3[i]]];}return s;}
function decode(segments,alphabet,key){const map=new Map(alphabet.map((c,i)=>[c,String.fromCharCode(97+key[i])]));return segments.map(s=>Array.from(s,c=>c===' '?' ':map.get(c)||'?').join(''));}
function coverage(segments,dictionary){const ws=segments.join(' ').split(' ').filter(Boolean),long=ws.filter(w=>w.length>=4);return{all:ws.filter(w=>dictionary.has(w)).length/ws.length,length4plus:long.filter(w=>dictionary.has(w)).length/long.length,tokens:ws.length};}
function accuracy(decoded,plain){let good=0,n=0;for(let i=0;i<plain.length;i++)for(let j=0;j<plain[i].length;j++)if(plain[i][j]!==' '){n++;good+=decoded[i][j]===plain[i][j];}return good/n;}
function solve(train,test,lm,id,plain=null,testplain=null){
  const alphabet=[...new Set([...train,...test].join('').replaceAll(' ',''))].sort(),C=alphabet.length;
  const data=encode(train,alphabet),validation=encode(test,alphabet),table=lm.scores;
  let best=-Infinity,bestKey=null;const runs=[];
  for(let restart=0;restart<RESTARTS;restart++){
    const key=Int32Array.from({length:C+1},(_,i)=>i===C?26:(random()*26)|0);
    let current=score(data,key,table),runbest=current,runkey=Int32Array.from(key);
    for(let step=0;step<STEPS;step++){
      const temperature=20*(data.denominator/2500)*Math.exp(-5.99*step/STEPS);
      let delta,old,idx,a,original,b;
      const grouped=random()<0.15;
      if(grouped){
        a=(random()*26)|0;b=(random()*25)|0;if(b>=a)b++;
        const next=Int32Array.from(key,c=>c===a?b:c===b?a:c);
        delta=score(data,next,table)-current;
        if(delta>=0||random()<Math.exp(delta/temperature)){key.set(next);current+=delta;}
      }else{
        a=(random()*C)|0;original=key[a];b=(random()*25)|0;if(b>=original)b++;
        idx=data.affected[a];old=partial(data,key,table,idx);key[a]=b;delta=partial(data,key,table,idx)-old;
        if(delta>=0||random()<Math.exp(delta/temperature))current+=delta;else key[a]=original;
      }
      if(current>runbest){runbest=current;runkey.set(key);}
    }
    key.set(runkey);current=score(data,key,table);
    let improved=true;
    while(improved){improved=false;for(let a=0;a<C;a++)for(let b=0;b<26;b++){
      const original=key[a];if(original===b)continue;
      const idx=data.affected[a],old=partial(data,key,table,idx);key[a]=b;
      const delta=partial(data,key,table,idx)-old;
      if(delta>1e-8){current+=delta;improved=true;}else key[a]=original;
    }}
    const full=score(data,key,table);if(Math.abs(full-current)>1e-6)throw new Error('Incremental score mismatch');
    if(full>best){best=full;bestKey=Int32Array.from(key);}
    runs.push({score:full/data.denominator,key:Array.from(key).slice(0,C)});
  }
  const decoded=decode(train,alphabet,bestKey),decodedtest=decode(test,alphabet,bestKey);
  const out={id,alphabet,train_chars:train.reduce((s,t)=>s+t.length,0),test_chars:test.reduce((s,t)=>s+t.length,0),train_score:best/data.denominator,test_score:score(validation,bestKey,table)/validation.denominator,key:Object.fromEntries(alphabet.map((c,i)=>[c,String.fromCharCode(97+bestKey[i])])),train_coverage:coverage(decoded,lm.dictionary),test_coverage:coverage(decodedtest,lm.dictionary),decoded_train:decoded,decoded_test:decodedtest,restarts:runs};
  if(plain){out.train_accuracy=accuracy(decoded,plain);out.test_accuracy=accuracy(decodedtest,testplain);}
  return out;
}
const results=[];const started=Date.now();
for(const [language,corpus]of Object.entries(input.corpora)){
  const lm=model(corpus),tasks=MODE==='controls'?[{id:'homophonic_control_'+language,train:corpus.control,test:corpus.control_test}]:input.samples;
  for(const task of tasks){
    const r=solve(task.train,task.test,lm,task.id,MODE==='controls'?corpus.control_plain:null,MODE==='controls'?corpus.control_test_plain:null);r.language=language;results.push(r);
    fs.writeFileSync(path.join(root,'homophonic_'+MODE+'_results.json'),JSON.stringify({mode:MODE,restarts:RESTARTS,steps:STEPS,seed_initial:384082026,seconds:(Date.now()-started)/1000,results},null,2));
    console.log(JSON.stringify({id:r.id,language,train_score:r.train_score,test_score:r.test_score,accuracy:r.train_accuracy,test_accuracy:r.test_accuracy,word_coverage:r.test_coverage.length4plus,sample:r.decoded_test.join(' ').slice(0,140),elapsed_seconds:Math.round((Date.now()-started)/1000)}));
  }
}
