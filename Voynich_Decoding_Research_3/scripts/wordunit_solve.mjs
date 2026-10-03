// Word-unit homophonic solver.
//
// Hypothesis: every Voynich word type w stands for a fixed plaintext string
// u(w) of 1..LMAX letters; plaintext spaces are dropped; many word types may
// share one string (homophones). This is the family of Greshko's Naibbe
// cipher (LMAX = 2) and of syllable-sized codes (LMAX = 3).
//
// Objective = exact log-likelihood of the token sequence under
//   letters ~ Kneser-Ney letter n-gram model of the candidate language,
//   string length ~ categorical (MLE),
//   token | string ~ categorical (MLE homophone choice).
// Up to constants this is  sum log P_LM(letters) + sum_l n_l log n_l
//   - sum_u c_u log c_u,  which penalises collapsing many words onto a few
// strings (the failure mode of the earlier unconstrained search).
//
// Signal measure: held-out gain = mean over held-out tokens of
//   log2 [ P(len) P_LM(string | preceding decoded letters) / P_train(string) ]
// i.e. how much better the decoded-language model predicts the next string
// than an order-free model of the same strings. It is compared with the same
// procedure run on shuffled text (negative control) and on enciphered Latin
// (positive control).
//
// usage: node wordunit_solve.mjs data=../data/wu_vmsA.json lm=../data/lm_latin_all.txt
//        lmax=2 order=5 iters=3000000 restarts=4 seed=1 out=../results/x.json
import fs from 'fs';

const argv = Object.fromEntries(process.argv.slice(2).map(a => {
  const i = a.indexOf('='); return [a.slice(0, i), a.slice(i + 1)];
}));
const ALPHA = 'abcdefghilmnopqrstuxyz';
const A = ALPHA.length;
const ORDER = +(argv.order ?? 5);
const LMAX = +(argv.lmax ?? 2);
const ITERS = +(argv.iters ?? 3000000);
const RESTARTS = +(argv.restarts ?? 4);
const MINCOUNT = +(argv.mincount ?? 2);
const T0 = +(argv.t0 ?? 6), T1 = +(argv.t1 ?? 0.05);
let seed = (+(argv.seed ?? 1)) >>> 0;
function rand() {
  seed = (seed + 0x6D2B79F5) >>> 0;
  let t = seed;
  t = Math.imul(t ^ (t >>> 15), t | 1);
  t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
}

// ---------------------------------------------------------------- LM
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
      for (let k = 1; k <= ORDER && i - k + 1 >= 0; k++) {
        idx += s[i - k + 1] * pow[k - 1];
        cnt[k][idx]++;
      }
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
    const nctx = pow[k - 1];
    for (let h = 0; h < nctx; h++) {
      let tot = 0, types = 0;
      for (let w = 0; w < A; w++) { const c = u[h * A + w]; tot += c; if (c > 0) types++; }
      const hb = k >= 2 ? h % pow[k - 2] : 0;
      for (let w = 0; w < A; w++) {
        const lower = k === 1 ? 1 / A : prev[hb * A + w];
        prob[h * A + w] = tot > 0
          ? Math.max(u[h * A + w] - D, 0) / tot + D * types / tot * lower
          : lower;
      }
    }
    const lp = new Float32Array(pow[k]);
    for (let i = 0; i < lp.length; i++) lp[i] = Math.log(prob[i]);
    logP[k] = lp;
    prev = prob;
  }
})();
const uniCum = new Float64Array(A);
{ let s = 0, tot = uni.reduce((a, b) => a + b, 0); for (let w = 0; w < A; w++) { s += uni[w] / tot; uniCum[w] = s; } }
function sampleLetter() { const r = rand(); for (let w = 0; w < A; w++) if (r < uniCum[w]) return w; return A - 1; }

// ---------------------------------------------------------------- data
const D = JSON.parse(fs.readFileSync(argv.data, 'utf8'));
const typeCount = new Map();
for (const s of D.streams_train) for (const t of s) if (t !== null) typeCount.set(t, (typeCount.get(t) || 0) + 1);
const types = [...typeCount.entries()].filter(([, c]) => c >= MINCOUNT).sort((a, b) => b[1] - a[1]).map(([t]) => t);
const typeId = new Map(types.map((t, i) => [t, i]));
const V = types.length;
function flatten(streams, truths) {
  const arr = [], tr = [];
  streams.forEach((s, si) => {
    arr.push(-1); tr.push(null);
    s.forEach((t, ti) => {
      arr.push(t === null ? -1 : (typeId.has(t) ? typeId.get(t) : -1));
      tr.push(truths ? truths[si][ti] : null);
    });
  });
  arr.push(-1); tr.push(null);
  return [Int32Array.from(arr), tr];
}
const [tok, truthTrain] = flatten(D.streams_train, D.truth_train);
const [tokTest, truthTest] = flatten(D.streams_test, D.truth_test);
const occ = Array.from({ length: V }, () => []);
for (let p = 0; p < tok.length; p++) if (tok[p] >= 0) occ[tok[p]].push(p);
const cw = occ.map(o => o.length);
const N = cw.reduce((a, b) => a + b, 0);
const weighted = []; for (let w = 0; w < V; w++) for (let i = 0; i < cw[w]; i++) weighted.push(w);
const totalTrainTokens = D.streams_train.reduce((a, s) => a + s.filter(t => t !== null).length, 0);
const totalTestTokens = D.streams_test.reduce((a, s) => a + s.filter(t => t !== null).length, 0);

// ---------------------------------------------------------------- state
const uLen = new Int32Array(V), uLet = new Int32Array(V * LMAX);
const NU = Math.pow(A + 1, LMAX);
const unitCount = new Float64Array(NU);
const lenCount = new Float64Array(LMAX + 1);
const ts = new Float64Array(tok.length);
const stamp = new Int32Array(tok.length); let stampId = 0;
const aff = new Int32Array(tok.length), newS = new Float64Array(tok.length);
const ctxBuf = new Int32Array(ORDER);
const f = x => x > 0 ? x * Math.log(x) : 0;
function ukeyOf(len, lets, off) { let k = 0; for (let j = 0; j < len; j++) k = k * (A + 1) + lets[off + j] + 1; for (let j = len; j < LMAX; j++) k = k * (A + 1); return k; }
const ukey = w => ukeyOf(uLen[w], uLet, w * LMAX);
function unitStr(w) { let s = ''; for (let j = 0; j < uLen[w]; j++) s += ALPHA[uLet[w * LMAX + j]]; return s; }

function scoreAt(t, arr) {
  const w = arr[t]; if (w < 0) return 0;
  let m = 0, p = t - 1;
  while (m < ORDER - 1 && p >= 0) {
    const v = arr[p]; if (v < 0) break;
    for (let j = uLen[v] - 1; j >= 0 && m < ORDER - 1; j--) { ctxBuf[ORDER - 2 - m] = uLet[v * LMAX + j]; m++; }
    p--;
  }
  let lp = 0;
  const L = uLen[w];
  for (let j = 0; j < L; j++) {
    const c = uLet[w * LMAX + j];
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

let LMsum = 0, CHsum = 0, LENsum = 0;
function fullRecompute() {
  unitCount.fill(0); lenCount.fill(0);
  for (let w = 0; w < V; w++) { unitCount[ukey(w)] += cw[w]; lenCount[uLen[w]] += cw[w]; }
  LMsum = 0;
  for (let t = 0; t < tok.length; t++) { ts[t] = scoreAt(t, tok); LMsum += ts[t]; }
  CHsum = 0; for (let u = 0; u < NU; u++) CHsum -= f(unitCount[u]);
  LENsum = 0; for (let l = 1; l <= LMAX; l++) LENsum += f(lenCount[l]);
}
const J = () => LMsum + CHsum + LENsum;

// Evaluate and optionally commit a change of the units of types ws.
const saveLen = new Int32Array(2), saveLet = new Int32Array(2 * LMAX);
function tryChange(ws, lens, lets, T) {
  // channel and length deltas first (cheap)
  const oldKeys = ws.map(ukey), oldLens = ws.map(w => uLen[w]);
  ws.forEach((w, i) => { saveLen[i] = uLen[w]; for (let j = 0; j < LMAX; j++) saveLet[i * LMAX + j] = uLet[w * LMAX + j]; });
  ws.forEach((w, i) => { uLen[w] = lens[i]; for (let j = 0; j < LMAX; j++) uLet[w * LMAX + j] = lets[i * LMAX + j]; });
  const newKeys = ws.map(ukey);
  // channel delta
  const touched = new Map();
  ws.forEach((w, i) => {
    touched.set(oldKeys[i], (touched.get(oldKeys[i]) ?? 0) - cw[w]);
    touched.set(newKeys[i], (touched.get(newKeys[i]) ?? 0) + cw[w]);
  });
  let dCH = 0;
  for (const [u, d] of touched) if (d !== 0) dCH -= f(unitCount[u] + d) - f(unitCount[u]);
  const lt = new Map();
  ws.forEach((w, i) => {
    lt.set(oldLens[i], (lt.get(oldLens[i]) ?? 0) - cw[w]);
    lt.set(lens[i], (lt.get(lens[i]) ?? 0) + cw[w]);
  });
  let dLEN = 0;
  for (const [l, d] of lt) if (d !== 0) dLEN += f(lenCount[l] + d) - f(lenCount[l]);
  // LM delta over affected positions
  stampId++;
  let n = 0;
  for (const w of ws) for (const o of occ[w]) {
    for (let t = o; t < o + ORDER && t < tok.length; t++) {
      if (tok[t] < 0) break;
      if (stamp[t] !== stampId) { stamp[t] = stampId; aff[n++] = t; }
    }
  }
  let dLM = 0;
  for (let i = 0; i < n; i++) { const t = aff[i]; const s = scoreAt(t, tok); newS[i] = s; dLM += s - ts[t]; }
  const delta = dLM + dCH + dLEN;
  if (delta >= 0 || rand() < Math.exp(delta / T)) {
    for (let i = 0; i < n; i++) ts[aff[i]] = newS[i];
    for (const [u, d] of touched) unitCount[u] += d;
    for (const [l, d] of lt) lenCount[l] += d;
    LMsum += dLM; CHsum += dCH; LENsum += dLEN;
    return true;
  }
  ws.forEach((w, i) => { uLen[w] = saveLen[i]; for (let j = 0; j < LMAX; j++) uLet[w * LMAX + j] = saveLet[i * LMAX + j]; });
  return false;
}

function randomUnit(buf, off) {
  const len = 1 + Math.floor(rand() * LMAX);
  for (let j = 0; j < LMAX; j++) buf[off + j] = j < len ? sampleLetter() : 0;
  return len;
}

const lets2 = new Int32Array(2 * LMAX);

// ---------------------------------------------------------------- annealed Gibbs
// Candidate strings: every string of length 1..min(LMAX,2), plus (LMAX=3) the
// most frequent letter trigrams of the language-model text.
const candidates = [];
(function buildCandidates() {
  for (let a = 0; a < A; a++) candidates.push([a]);
  if (LMAX >= 2) for (let a = 0; a < A; a++) for (let b = 0; b < A; b++) candidates.push([a, b]);
  if (LMAX >= 3) {
    const lines = fs.readFileSync(argv.lm, 'utf8').split('\n');
    const tri = new Map();
    for (const line of lines) {
      const s = Array.from(line, ch => ALPHA.indexOf(ch)).filter(x => x >= 0);
      for (let i = 0; i + 2 < s.length; i++) { const k = (s[i] * A + s[i + 1]) * A + s[i + 2]; tri.set(k, (tri.get(k) || 0) + 1); }
    }
    const top = [...tri.entries()].sort((x, y) => y[1] - x[1]).slice(0, +(argv.trigrams ?? 1500));
    for (const [k] of top) candidates.push([Math.floor(k / (A * A)), Math.floor(k / A) % A, k % A]);
  }
})();
const candLets = new Int32Array(LMAX);
const affW = new Int32Array(tok.length);
function deltaFor(w, cand, nAff) {
  // channel + length deltas
  const oldKey = ukey(w), oldLen = uLen[w];
  const L = cand.length;
  let newKey = 0; for (let j = 0; j < L; j++) newKey = newKey * (A + 1) + cand[j] + 1; for (let j = L; j < LMAX; j++) newKey *= (A + 1);
  let d = 0;
  if (newKey !== oldKey) {
    const c = cw[w];
    d -= f(unitCount[oldKey] - c) - f(unitCount[oldKey]);
    d -= f(unitCount[newKey] + c) - f(unitCount[newKey]);
  }
  if (L !== oldLen) {
    const c = cw[w];
    d += f(lenCount[oldLen] - c) - f(lenCount[oldLen]) + f(lenCount[L] + c) - f(lenCount[L]);
  }
  // LM delta with the candidate temporarily installed
  const save0 = uLet[w * LMAX], save1 = LMAX > 1 ? uLet[w * LMAX + 1] : 0, save2 = LMAX > 2 ? uLet[w * LMAX + 2] : 0;
  uLen[w] = L; for (let j = 0; j < L; j++) uLet[w * LMAX + j] = cand[j];
  let dLM = 0;
  for (let i = 0; i < nAff; i++) { const t = affW[i]; dLM += scoreAt(t, tok) - ts[t]; }
  uLen[w] = oldLen; uLet[w * LMAX] = save0; if (LMAX > 1) uLet[w * LMAX + 1] = save1; if (LMAX > 2) uLet[w * LMAX + 2] = save2;
  return d + dLM;
}
function collectAff(w) {
  stampId++;
  let n = 0;
  for (const o of occ[w]) for (let t = o; t < o + ORDER && t < tok.length; t++) {
    if (tok[t] < 0) break;
    if (stamp[t] !== stampId) { stamp[t] = stampId; affW[n++] = t; }
  }
  return n;
}
const dBuf = new Float64Array(candidates.length);
function gibbs(sweeps, Tstart, Tend) {
  const order = Array.from({ length: V }, (_, i) => i);
  for (let s = 0; s < sweeps; s++) {
    const T = Tstart <= 0 ? 0 : Tstart * Math.pow(Tend / Tstart, sweeps > 1 ? s / (sweeps - 1) : 1);
    for (let i = V - 1; i > 0; i--) { const j = Math.floor(rand() * (i + 1)); [order[i], order[j]] = [order[j], order[i]]; }
    for (const w of order) {
      const nAff = collectAff(w);
      let mx = -Infinity;
      for (let c = 0; c < candidates.length; c++) { const d = deltaFor(w, candidates[c], nAff); dBuf[c] = d; if (d > mx) mx = d; }
      let pick = 0;
      if (T <= 1e-6) { for (let c = 0; c < candidates.length; c++) if (dBuf[c] === mx) { pick = c; break; } }
      else {
        let z = 0; for (let c = 0; c < candidates.length; c++) { dBuf[c] = Math.exp((dBuf[c] - mx) / T); z += dBuf[c]; }
        let r = rand() * z; for (pick = 0; pick < candidates.length - 1; pick++) { r -= dBuf[pick]; if (r <= 0) break; }
      }
      const cand = candidates[pick];
      for (let j = 0; j < LMAX; j++) lets2[j] = j < cand.length ? cand[j] : 0;
      tryChange([w], [cand.length], lets2, 1e-12);   // commits (delta recomputed)
      // tryChange rejects a strictly worse move at this temperature; force it
      if (uLen[w] !== cand.length || cand.some((x, j) => uLet[w * LMAX + j] !== x)) tryChange([w], [cand.length], lets2, Infinity);
    }
    if (argv.verbose) console.error(`sweep ${s} T=${T.toFixed(3)} J=${J().toFixed(1)}` + (truthTrain.some(x => x) ? ` acc=${accuracy(tok, truthTrain).exact_string_accuracy.toFixed(3)}` : ''));
  }
}
function initTruth() {
  // majority true string per type (controls only), for checking the objective
  const votes = Array.from({ length: V }, () => new Map());
  for (let t = 0; t < tok.length; t++) if (tok[t] >= 0 && truthTrain[t]) {
    const m = votes[tok[t]]; m.set(truthTrain[t], (m.get(truthTrain[t]) || 0) + 1);
  }
  for (let w = 0; w < V; w++) {
    const best = [...votes[w].entries()].sort((a, b) => b[1] - a[1])[0][0];
    uLen[w] = best.length;
    for (let j = 0; j < best.length; j++) uLet[w * LMAX + j] = ALPHA.indexOf(best[j]);
  }
}
function anneal() {
  if (argv.init === 'truth') initTruth();
  else for (let w = 0; w < V; w++) uLen[w] = randomUnit(uLet, w * LMAX);
  fullRecompute();
  if (argv.debug) {
    let nl = 0; for (let w = 0; w < V; w++) nl += cw[w] * uLen[w];
    let sfu = 0, nu = 0; for (let u = 0; u < NU; u++) { sfu += f(unitCount[u]); nu += unitCount[u] > 0; }
    let sfl = 0; for (let l = 1; l <= LMAX; l++) sfl += f(lenCount[l]);
    const Hu = (Math.log(N) - sfu / N) / Math.LN2;
    console.error(JSON.stringify({ N, letters: nl, lm_bits_per_letter: -LMsum / nl / Math.LN2,
      lm_bits_per_token: -LMsum / N / Math.LN2, unit_entropy_bits: Hu, distinct_units: nu,
      len_term_bits_per_token: (sfl - f(N)) / N / Math.LN2, lenCount: Array.from(lenCount) }));
    // compare token-wise scoring with direct letter scoring on the first stream
    let p0 = 1, letters = [], sumTs = 0;
    while (tok[p0] !== -1 || p0 === 0) { const w = tok[p0]; if (w >= 0) { for (let j = 0; j < uLen[w]; j++) letters.push(uLet[w * LMAX + j]); sumTs += ts[p0]; } else break; p0++; }
    let lp = 0;
    for (let i = 0; i < letters.length; i++) { const k = Math.min(i, ORDER - 1); let idx = 0; for (let q = i - k; q < i; q++) idx = idx * A + letters[q]; lp += logP[k + 1][idx * A + letters[i]]; }
    console.error('first stream letters', letters.length, 'direct bits/letter', -lp / letters.length / Math.LN2, 'tokenwise', -sumTs / letters.length / Math.LN2, letters.map(x => ALPHA[x]).join(''));
  }
  if (argv.mode === 'gibbs') {
    gibbs(+(argv.sweeps ?? 60), +(argv.tg0 ?? 3), +(argv.tg1 ?? 0.05));
    gibbs(2, 0, 0);
    fullRecompute();
    return J();
  }
  for (let it = 0; it < ITERS; it++) {
    const T = T0 * Math.pow(T1 / T0, it / ITERS);
    const r = rand();
    if (r < 0.35 || r >= 0.9) {
      const w = r < 0.35 ? Math.floor(rand() * V) : weighted[Math.floor(rand() * weighted.length)];
      const len = randomUnit(lets2, 0);
      tryChange([w], [len], lets2, T);
    } else if (r < 0.55) {
      const w = weighted[Math.floor(rand() * weighted.length)];
      const len = randomUnit(lets2, 0);
      tryChange([w], [len], lets2, T);
    } else if (r < 0.7) {
      const w = Math.floor(rand() * V), v = weighted[Math.floor(rand() * weighted.length)];
      if (w === v) continue;
      for (let j = 0; j < LMAX; j++) lets2[j] = uLet[v * LMAX + j];
      tryChange([w], [uLen[v]], lets2, T);
    } else if (r < 0.8) {
      // tweak: change one letter or the length by one
      const w = rand() < 0.5 ? Math.floor(rand() * V) : weighted[Math.floor(rand() * weighted.length)];
      for (let j = 0; j < LMAX; j++) lets2[j] = uLet[w * LMAX + j];
      let len = uLen[w];
      const q = rand();
      if (q < 0.6) lets2[Math.floor(rand() * len)] = sampleLetter();
      else if (q < 0.8 && len < LMAX) { lets2[len] = sampleLetter(); len++; }
      else if (len > 1) len--;
      else lets2[0] = sampleLetter();
      tryChange([w], [len], lets2, T);
    } else {
      const w = Math.floor(rand() * V), v = weighted[Math.floor(rand() * weighted.length)];
      if (w === v || ukey(w) === ukey(v)) continue;
      for (let j = 0; j < LMAX; j++) { lets2[j] = uLet[v * LMAX + j]; lets2[LMAX + j] = uLet[w * LMAX + j]; }
      tryChange([w, v], [uLen[v], uLen[w]], lets2, T);
    }
  }
  // greedy polish: best single-letter replacement for frequent types
  for (let pass = 0; pass < 2; pass++) {
    for (let w = 0; w < Math.min(V, 300); w++) {
      for (let pos = 0; pos < uLen[w]; pos++) for (let c = 0; c < A; c++) {
        for (let j = 0; j < LMAX; j++) lets2[j] = uLet[w * LMAX + j];
        if (lets2[pos] === c) continue;
        lets2[pos] = c;
        tryChange([w], [uLen[w]], lets2, 1e-9);
      }
    }
  }
  fullRecompute();
  return J();
}

function heldOut() {
  // gain per held-out token with known type, using training string frequencies
  let sum = 0, n = 0;
  for (let t = 0; t < tokTest.length; t++) {
    const w = tokTest[t]; if (w < 0) continue;
    const lm = scoreAt(t, tokTest);
    sum += lm + Math.log(lenCount[uLen[w]] / N) - Math.log(unitCount[ukey(w)] / N);
    n++;
  }
  return { tokens: n, gain_bits_per_token: sum / n / Math.LN2 };
}

function accuracy(arr, truth) {
  if (!truth.some(x => x)) return null;
  let ok = 0, n = 0, okTop = 0, nTop = 0;
  for (let t = 0; t < arr.length; t++) {
    const w = arr[t]; if (w < 0 || !truth[t]) continue;
    n++; const hit = unitStr(w) === truth[t]; ok += hit;
    if (w < 100) { nTop++; okTop += hit; }
  }
  return { tokens: n, exact_string_accuracy: ok / n, top100_types_accuracy: okTop / nTop };
}

function decodeStreams(streams, max = 6) {
  return streams.slice(0, max).map(s => s.map(t => t === null ? '?' : (typeId.has(t) ? unitStr(typeId.get(t)) : '_')).join(''));
}

const t0 = Date.now();
let best = null;
const restarts = [];
for (let r = 0; r < RESTARTS; r++) {
  const j = anneal();
  const trainGain = (LMsum + LENsum + CHsum + 0) / N / Math.LN2; // CHsum excludes sum_w f(c_w), see below
  // exact train gain: LM + sum_l f(n_l) - sum_u f(c_u)
  let sfu = 0; for (let u = 0; u < NU; u++) sfu += f(unitCount[u]);
  let sfl = 0; for (let l = 1; l <= LMAX; l++) sfl += f(lenCount[l]);
  const gainTrain = (LMsum + sfl - sfu) / N / Math.LN2;
  const ho = heldOut();
  const rec = { restart: r, J: j, train_gain_bits_per_token: gainTrain, heldout: ho,
    distinct_strings_used: unitCount.reduce((a, c) => a + (c > 0), 0),
    accuracy_train: accuracy(tok, truthTrain), accuracy_test: accuracy(tokTest, truthTest) };
  restarts.push(rec);
  console.error(JSON.stringify(rec));
  if (!best || j > best.J) {
    best = { ...rec, key: types.slice(0, 400).map((t, w) => [t, cw[w], unitStr(w)]),
      decoded_test_sample: decodeStreams(D.streams_test), decoded_train_sample: decodeStreams(D.streams_train) };
  }
}
const out = { params: { data: argv.data, lm: argv.lm, ORDER, LMAX, ITERS, RESTARTS, MINCOUNT, T0, T1, seed: +(argv.seed ?? 1) },
  types_in_key: V, key_tokens_train: N, train_tokens: totalTrainTokens, test_tokens: totalTestTokens,
  seconds: (Date.now() - t0) / 1000, restarts, best };
if (argv.out) fs.writeFileSync(argv.out, JSON.stringify(out, null, 1));
console.log(JSON.stringify({ data: argv.data, lm: argv.lm, LMAX, best_J: best.J, train_gain: best.train_gain_bits_per_token,
  heldout_gain: best.heldout.gain_bits_per_token, acc_train: best.accuracy_train, acc_test: best.accuracy_test, seconds: out.seconds }));
