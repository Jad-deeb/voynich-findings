// Part-unit homophonic solver (Naibbe-family test with word structure).
//
// Every word token is parsed (by a fixed rule supplied in the input file) into
// one part (a 'unigram' word) or two parts (prefix + suffix). Every part symbol
// stands for exactly one plaintext letter; different symbols may stand for the
// same letter (homophones). The token therefore spells 1 or 2 plaintext letters.
// Plaintext spaces are not represented.
//
// Objective = exact log-likelihood up to constants:
//   sum log P_LM(letters)  -  sum_{role,letter} c log c
// (MLE homophone probabilities per role). Search = annealed Gibbs sampling over
// the letter of every part symbol, many restarts.
//
// Signal measure (as in wordunit_solve.mjs): held-out gain per token =
//   mean log2 [ P_LM(decoded string | preceding decoded letters) / P_train(string | length) ]
// over held-out tokens whose parts were all seen in training.
//
// usage: node partunit_solve.mjs data=../data/pu_x.json lm=../data/lm_latin_all.txt
//        sweeps=80 restarts=12 seed=1 out=../results/x.json
import fs from 'fs';

const argv = Object.fromEntries(process.argv.slice(2).map(a => {
  const i = a.indexOf('='); return [a.slice(0, i), a.slice(i + 1)];
}));
const ALPHA = argv.alpha ?? 'abcdefghilmnopqrstuxyz';   // plaintext alphabet (must match the LM text)
const A = ALPHA.length;
const ORDER = +(argv.order ?? 5);
const SWEEPS = +(argv.sweeps ?? 80);
const RESTARTS = +(argv.restarts ?? 12);
const TG0 = +(argv.tg0 ?? 6), TG1 = +(argv.tg1 ?? 0.1);
let seed = (+(argv.seed ?? 1)) >>> 0;
function rand() {
  seed = (seed + 0x6D2B79F5) >>> 0;
  let t = seed;
  t = Math.imul(t ^ (t >>> 15), t | 1);
  t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
}

// ---------------------------------------------------------------- LM (same as wordunit_solve.mjs)
const pow = [1];
for (let i = 1; i <= ORDER; i++) pow.push(pow[i - 1] * A);
const logP = [];
const uni = new Float64Array(A);
(function buildLM() {
  const lines = fs.readFileSync(argv.lm, 'utf8').split('\n').filter(Boolean);
  const cnt = [];
  for (let k = 1; k <= ORDER; k++) cnt[k] = new Float64Array(pow[k]);
  for (const line of lines) {
    const s = Array.from(line, ch => ALPHA.indexOf(ch)).filter(x => x >= 0);
    for (let i = 0; i < s.length; i++) {
      let idx = 0;
      for (let k = 1; k <= ORDER && i - k + 1 >= 0; k++) { idx += s[i - k + 1] * pow[k - 1]; cnt[k][idx]++; }
    }
  }
  for (let w = 0; w < A; w++) uni[w] = cnt[1][w];
  const use = [];
  use[ORDER] = cnt[ORDER];
  for (let k = ORDER - 1; k >= 1; k--) {
    const cc = new Float64Array(pow[k]);
    const hi = cnt[k + 1];
    for (let i = 0; i < hi.length; i++) if (hi[i] > 0) cc[i % pow[k]]++;
    use[k] = cc;
  }
  let prev = null;
  for (let k = 1; k <= ORDER; k++) {
    const u = use[k];
    let n1 = 0, n2 = 0;
    for (let i = 0; i < u.length; i++) { if (u[i] === 1) n1++; else if (u[i] === 2) n2++; }
    const D = n1 + n2 > 0 ? Math.min(0.95, Math.max(0.3, n1 / (n1 + 2 * n2))) : 0.75;
    const prob = new Float64Array(pow[k]);
    for (let h = 0; h < pow[k - 1]; h++) {
      let tot = 0, types = 0;
      for (let w = 0; w < A; w++) { const c = u[h * A + w]; tot += c; if (c > 0) types++; }
      const hb = k >= 2 ? h % pow[k - 2] : 0;
      for (let w = 0; w < A; w++) {
        const lower = k === 1 ? 1 / A : prev[hb * A + w];
        prob[h * A + w] = tot > 0 ? Math.max(u[h * A + w] - D, 0) / tot + D * types / tot * lower : lower;
      }
    }
    const lp = new Float32Array(pow[k]);
    for (let i = 0; i < lp.length; i++) lp[i] = Math.log(prob[i]);
    logP[k] = lp; prev = prob;
  }
})();
const uniCum = new Float64Array(A);
{ let s = 0; const tot = uni.reduce((a, b) => a + b, 0); for (let w = 0; w < A; w++) { s += uni[w] / tot; uniCum[w] = s; } }
function sampleLetter() { const r = rand(); for (let w = 0; w < A; w++) if (r < uniCum[w]) return w; return A - 1; }

// ---------------------------------------------------------------- data
const D = JSON.parse(fs.readFileSync(argv.data, 'utf8'));
const parts = D.parts;                       // token string -> [symbol, ...] (1 or 2)
const symCount = new Map();
for (const s of D.streams_train) for (const t of s) if (t !== null && parts[t]) for (const p of parts[t]) symCount.set(p, (symCount.get(p) || 0) + 1);
const syms = [...symCount.keys()].sort((a, b) => symCount.get(b) - symCount.get(a));
const symId = new Map(syms.map((s, i) => [s, i]));
const S = syms.length;
const roleOf = syms.map(s => s.split(':')[0]);
const roles = [...new Set(roleOf)];
const roleIdx = roleOf.map(r => roles.indexOf(r));
const R = roles.length;
// token kinds: a token is encoded as [nParts, sym0, sym1]
function flatten(streams, truths) {
  const n0 = [], s0 = [], s1 = [], tr = [];
  const push = (n, a, b, t) => { n0.push(n); s0.push(a); s1.push(b); tr.push(t); };
  streams.forEach((s, si) => {
    push(0, -1, -1, null);
    s.forEach((t, ti) => {
      const truth = truths ? truths[si][ti] : null;
      if (t === null || !parts[t] || parts[t].some(p => !symId.has(p))) { push(0, -1, -1, truth); return; }
      const ps = parts[t].map(p => symId.get(p));
      push(ps.length, ps[0], ps.length > 1 ? ps[1] : -1, truth);
    });
  });
  push(0, -1, -1, null);
  return { n: Int32Array.from(n0), a: Int32Array.from(s0), b: Int32Array.from(s1), truth: tr, len: n0.length };
}
const TR = flatten(D.streams_train, D.truth_train);
const TE = flatten(D.streams_test, D.truth_test);
const occ = Array.from({ length: S }, () => []);
for (let p = 0; p < TR.len; p++) { if (TR.n[p] >= 1) occ[TR.a[p]].push(p); if (TR.n[p] === 2 && TR.b[p] !== TR.a[p]) occ[TR.b[p]].push(p); }
const cs = syms.map(s => symCount.get(s));
let N = 0; for (let p = 0; p < TR.len; p++) if (TR.n[p] > 0) N++;

// ---------------------------------------------------------------- state
const key = new Int32Array(S);
const roleLet = new Float64Array(R * A);   // c_{role,letter}
const ts = new Float64Array(TR.len);
const stamp = new Int32Array(TR.len); let stampId = 0;
const aff = new Int32Array(TR.len);
const ctxBuf = new Int32Array(ORDER);
const f = x => x > 0 ? x * Math.log(x) : 0;

function scoreAt(t, X) {
  const n = X.n[t]; if (n === 0) return 0;
  let m = 0, p = t - 1;
  while (m < ORDER - 1 && p >= 0) {
    const np = X.n[p]; if (np === 0) break;
    if (np === 2) { ctxBuf[ORDER - 2 - m] = key[X.b[p]]; m++; if (m >= ORDER - 1) break; }
    ctxBuf[ORDER - 2 - m] = key[X.a[p]]; m++;
    p--;
  }
  let lp = 0;
  for (let j = 0; j < n; j++) {
    const c = key[j === 0 ? X.a[t] : X.b[t]];
    const k = Math.min(m, ORDER - 1);
    let idx = 0;
    for (let q = ORDER - 1 - k; q < ORDER - 1; q++) idx = idx * A + ctxBuf[q];
    lp += logP[k + 1][idx * A + c];
    for (let q = 0; q < ORDER - 2; q++) ctxBuf[q] = ctxBuf[q + 1];
    ctxBuf[ORDER - 2] = c;
    m++;
  }
  return lp;
}
let LMsum = 0;
function fullRecompute() {
  roleLet.fill(0);
  for (let s = 0; s < S; s++) roleLet[roleIdx[s] * A + key[s]] += cs[s];
  LMsum = 0;
  for (let t = 0; t < TR.len; t++) { ts[t] = scoreAt(t, TR); LMsum += ts[t]; }
}
function chTerm() { let x = 0; for (let i = 0; i < R * A; i++) x -= f(roleLet[i]); return x; }
const J = () => LMsum + chTerm();

function collectAff(s) {
  stampId++;
  let n = 0;
  for (const o of occ[s]) for (let t = o; t < o + ORDER && t < TR.len; t++) {
    if (TR.n[t] === 0) break;
    if (stamp[t] !== stampId) { stamp[t] = stampId; aff[n++] = t; }
  }
  return n;
}
const dBuf = new Float64Array(A);
const newScores = Array.from({ length: A }, () => null);
function gibbs(sweeps, T0, T1) {
  const order = Array.from({ length: S }, (_, i) => i);
  for (let sw = 0; sw < sweeps; sw++) {
    const T = T0 <= 0 ? 0 : T0 * Math.pow(T1 / T0, sweeps > 1 ? sw / (sweeps - 1) : 1);
    for (let i = S - 1; i > 0; i--) { const j = Math.floor(rand() * (i + 1)); [order[i], order[j]] = [order[j], order[i]]; }
    for (const s of order) {
      const nAff = collectAff(s);
      const old = key[s], r = roleIdx[s], c = cs[s];
      let mx = -Infinity;
      for (let L = 0; L < A; L++) {
        key[s] = L;
        let d = 0;
        for (let i = 0; i < nAff; i++) d += scoreAt(aff[i], TR) - ts[aff[i]];
        if (L !== old) {
          d -= f(roleLet[r * A + old] - c) - f(roleLet[r * A + old]);
          d -= f(roleLet[r * A + L] + c) - f(roleLet[r * A + L]);
        }
        dBuf[L] = d; if (d > mx) mx = d;
      }
      let pick = old;
      if (T === 0) { for (let L = 0; L < A; L++) if (dBuf[L] === mx) { pick = L; break; } }
      else {
        let z = 0; for (let L = 0; L < A; L++) { dBuf[L] = Math.exp((dBuf[L] - mx) / T); z += dBuf[L]; }
        let u = rand() * z; for (pick = 0; pick < A - 1; pick++) { u -= dBuf[pick]; if (u <= 0) break; }
      }
      key[s] = pick;
      if (pick !== old) {
        roleLet[r * A + old] -= c; roleLet[r * A + pick] += c;
        for (let i = 0; i < nAff; i++) { const t = aff[i]; const v = scoreAt(t, TR); LMsum += v - ts[t]; ts[t] = v; }
      }
    }
    if (argv.verbose && (sw % 10 === 9 || sw === sweeps - 1)) console.error(`  sweep ${sw} T=${T.toFixed(3)} J=${J().toFixed(1)}` + (TR.truth.some(x => x) ? ` acc=${accuracy(TR).toFixed(3)}` : ''));
  }
}

function unitOf(X, t) { let s = ALPHA[key[X.a[t]]]; if (X.n[t] === 2) s += ALPHA[key[X.b[t]]]; return s; }
function accuracy(X) {
  let ok = 0, n = 0;
  for (let t = 0; t < X.len; t++) if (X.n[t] > 0 && X.truth[t]) { n++; ok += unitOf(X, t) === X.truth[t]; }
  return n ? ok / n : null;
}
function unitStats() {
  const cu = new Map(), cl = [0, 0, 0];
  for (let t = 0; t < TR.len; t++) if (TR.n[t] > 0) { const u = unitOf(TR, t); cu.set(u, (cu.get(u) || 0) + 1); cl[TR.n[t]]++; }
  return { cu, cl };
}
function gains() {
  const { cu, cl } = unitStats();
  let sfu = 0; for (const c of cu.values()) sfu += f(c);
  const train = (LMsum - sfu + f(cl[1]) + f(cl[2])) / N / Math.LN2;
  let sum = 0, n = 0;
  for (let t = 0; t < TE.len; t++) {
    if (TE.n[t] === 0) continue;
    const u = unitOf(TE, t);
    const c = cu.get(u); if (!c) continue;       // decoded string never produced in training
    sum += scoreAt(t, TE) - Math.log(c / cl[TE.n[t]]); n++;
  }
  return { train_gain_bits_per_token: train, heldout_gain_bits_per_token: sum / n / Math.LN2, heldout_tokens_scored: n };
}
function decode(X, maxStreams = 8) {
  const out = []; let cur = '', count = 0;
  for (let t = 1; t < X.len && count < maxStreams; t++) {
    if (X.n[t] === 0 && X.a[t] === -1 && t > 0 && (X.n[t - 1] !== 0 || cur)) { /* break or stream boundary */ }
    if (X.n[t] > 0) cur += unitOf(X, t); else cur += '·';
    if (X.n[t] === 0 && t + 1 < X.len && X.n[t + 1] === 0) { out.push(cur); cur = ''; count++; }
  }
  return out;
}

const t0 = Date.now();
const restarts = [];
let best = null;
for (let r = 0; r < RESTARTS; r++) {
  if (argv.init === 'truth') {
    const votes = Array.from({ length: S }, () => new Float64Array(A));
    for (let t = 0; t < TR.len; t++) if (TR.n[t] > 0 && TR.truth[t]) {
      votes[TR.a[t]][ALPHA.indexOf(TR.truth[t][0])]++;
      if (TR.n[t] === 2 && TR.truth[t].length > 1) votes[TR.b[t]][ALPHA.indexOf(TR.truth[t][1])]++;
    }
    for (let s = 0; s < S; s++) { let b = 0; for (let L = 1; L < A; L++) if (votes[s][L] > votes[s][b]) b = L; key[s] = b; }
    fullRecompute();
  } else {
    for (let s = 0; s < S; s++) key[s] = sampleLetter();
    fullRecompute();
    gibbs(SWEEPS, TG0, TG1);
  }
  gibbs(3, 0, 0);
  fullRecompute();
  const rec = { restart: r, J: J(), ...gains(), accuracy_train: accuracy(TR), accuracy_test: accuracy(TE) };
  restarts.push(rec);
  console.error(JSON.stringify(rec));
  if (!best || rec.J > best.J) best = { ...rec, key: syms.map((s, i) => [s, cs[i], ALPHA[key[i]]]), decoded_train: decode(TR), decoded_test: decode(TE) };
}
const out = { params: { data: argv.data, lm: argv.lm, ORDER, SWEEPS, RESTARTS, TG0, TG1, seed: +(argv.seed ?? 1) },
  symbols: S, roles, train_tokens_scored: N, seconds: (Date.now() - t0) / 1000, restarts, best };
if (argv.out) fs.writeFileSync(argv.out, JSON.stringify(out, null, 1));
const js = restarts.map(r => r.J).sort((a, b) => b - a);
console.log(JSON.stringify({ data: argv.data, lm: argv.lm, symbols: S, best_J: best.J, second_J: js[1] ?? null,
  train_gain: best.train_gain_bits_per_token, heldout_gain: best.heldout_gain_bits_per_token,
  heldout_gain_all_restarts: restarts.map(r => +r.heldout_gain_bits_per_token.toFixed(3)),
  acc_train: best.accuracy_train, acc_test: best.accuracy_test, seconds: out.seconds }));
