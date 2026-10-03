// Learned-split homophonic solver (Naibbe family, word division unknown).
//
// Each word type chooses one analysis from its candidate list (whole word, or
// prefix + suffix at some position); each symbol stands for one plaintext letter.
// Objective = log-likelihood up to constants:
//   LM(letters) + sum_s c_s log c_s - sum_{role,letter} c log c + sum_struct n log n
// The second term rewards analyses that reuse the same prefixes and suffixes.
// Search: annealed Gibbs sampling alternating over symbol letters and type
// analyses, several random restarts.
//
// Held-out scoring also decodes UNSEEN word types whenever one of their
// analyses uses only symbols learned in training: a real cipher of this kind
// generalises to new prefix-suffix combinations, shuffled text should not.
//
// usage: node splitunit_solve.mjs data=../data/su_x.json lm=../data/lm_latin_all.txt
//        sweeps=60 restarts=4 tg0=300 tg1=1 seed=1 out=../results/su_x.json
import fs from 'fs';

const argv = Object.fromEntries(process.argv.slice(2).map(a => { const i = a.indexOf('='); return [a.slice(0, i), a.slice(i + 1)]; }));
const ALPHA = argv.alpha ?? 'abcdefghilmnopqrstuxyz';   // plaintext alphabet (must match the LM text)
const A = ALPHA.length;
const ORDER = +(argv.order ?? 5);
const SWEEPS = +(argv.sweeps ?? 60);
const RESTARTS = +(argv.restarts ?? 4);
const TG0 = +(argv.tg0 ?? 300), TG1 = +(argv.tg1 ?? 1);
let seed = (+(argv.seed ?? 1)) >>> 0;
function rand() { seed = (seed + 0x6D2B79F5) >>> 0; let t = seed; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }

// ---------------------------------------------------------------- LM
const pow = [1]; for (let i = 1; i <= ORDER; i++) pow.push(pow[i - 1] * A);
const logP = []; const uni = new Float64Array(A);
(function buildLM() {
  const lines = fs.readFileSync(argv.lm, 'utf8').split('\n').filter(Boolean);
  const cnt = []; for (let k = 1; k <= ORDER; k++) cnt[k] = new Float64Array(pow[k]);
  for (const line of lines) {
    const s = Array.from(line, ch => ALPHA.indexOf(ch)).filter(x => x >= 0);
    for (let i = 0; i < s.length; i++) { let idx = 0; for (let k = 1; k <= ORDER && i - k + 1 >= 0; k++) { idx += s[i - k + 1] * pow[k - 1]; cnt[k][idx]++; } }
  }
  for (let w = 0; w < A; w++) uni[w] = cnt[1][w];
  const use = []; use[ORDER] = cnt[ORDER];
  for (let k = ORDER - 1; k >= 1; k--) { const cc = new Float64Array(pow[k]); const hi = cnt[k + 1]; for (let i = 0; i < hi.length; i++) if (hi[i] > 0) cc[i % pow[k]]++; use[k] = cc; }
  let prev = null;
  for (let k = 1; k <= ORDER; k++) {
    const u = use[k]; let n1 = 0, n2 = 0;
    for (let i = 0; i < u.length; i++) { if (u[i] === 1) n1++; else if (u[i] === 2) n2++; }
    const D = n1 + n2 > 0 ? Math.min(0.95, Math.max(0.3, n1 / (n1 + 2 * n2))) : 0.75;
    const prob = new Float64Array(pow[k]);
    for (let h = 0; h < pow[k - 1]; h++) {
      let tot = 0, types = 0; for (let w = 0; w < A; w++) { const c = u[h * A + w]; tot += c; if (c > 0) types++; }
      const hb = k >= 2 ? h % pow[k - 2] : 0;
      for (let w = 0; w < A; w++) { const lower = k === 1 ? 1 / A : prev[hb * A + w]; prob[h * A + w] = tot > 0 ? Math.max(u[h * A + w] - D, 0) / tot + D * types / tot * lower : lower; }
    }
    const lp = new Float32Array(pow[k]); for (let i = 0; i < lp.length; i++) lp[i] = Math.log(prob[i]);
    logP[k] = lp; prev = prob;
  }
})();
const uniCum = new Float64Array(A); { let s = 0; const tot = uni.reduce((a, b) => a + b, 0); for (let w = 0; w < A; w++) { s += uni[w] / tot; uniCum[w] = s; } }
function sampleLetter() { const r = rand(); for (let w = 0; w < A; w++) if (r < uniCum[w]) return w; return A - 1; }

// ---------------------------------------------------------------- data
const D = JSON.parse(fs.readFileSync(argv.data, 'utf8'));
const cntMap = new Map();
for (const s of D.streams_train) for (const t of s) if (t !== null) cntMap.set(t, (cntMap.get(t) || 0) + 1);
const types = [...cntMap.keys()].sort((a, b) => cntMap.get(b) - cntMap.get(a));
const typeId = new Map(types.map((t, i) => [t, i]));
const V = types.length;
const cnt = types.map(t => cntMap.get(t));
const symId = new Map(); const symName = []; const symRole = [];
const ROLES = ['U', 'P', 'S'];
function sym(name) { if (!symId.has(name)) { symId.set(name, symName.length); symName.push(name); symRole.push(ROLES.indexOf(name[0])); } return symId.get(name); }
const opts = types.map(t => D.analyses[t].map(o => o.map(sym)));     // per type: list of [sym...] arrays
const S = symName.length;
// Lexicon cost of using a symbol at all (Dirichlet-process base measure):
// spelling it out costs ln(G) per glyph plus a constant. Without it, giving
// every word type its own one-letter symbol overfits freely.
const G = +(argv.glyphs ?? 20), KAPPA = +(argv.kappa ?? 2.3), LEXW = +(argv.lexw ?? 1);
const symCost = symName.map(n => LEXW * ((n.length - 2) * Math.log(G) + KAPPA));
function flatten(streams, truths) {
  const tk = [], tr = [];
  streams.forEach((s, si) => { tk.push(-1); tr.push(null); s.forEach((t, ti) => { tk.push(t === null ? -1 : (typeId.has(t) ? typeId.get(t) : -2 - unseen(t))); tr.push(truths ? truths[si][ti] : null); }); });
  tk.push(-1); tr.push(null);
  return { tok: Int32Array.from(tk), truth: tr };
}
const unseenTypes = []; const unseenId = new Map();
function unseen(t) { if (!unseenId.has(t)) { unseenId.set(t, unseenTypes.length); unseenTypes.push(t); } return unseenId.get(t); }
const TR = flatten(D.streams_train, D.truth_train);
const TE = flatten(D.streams_test, D.truth_test);
const occ = Array.from({ length: V }, () => []);
for (let p = 0; p < TR.tok.length; p++) if (TR.tok[p] >= 0) occ[TR.tok[p]].push(p);
const N = cnt.reduce((a, b) => a + b, 0);

// ---------------------------------------------------------------- state
const key = new Int32Array(S);
const an = new Int32Array(V);
const nP = new Int32Array(V), sA = new Int32Array(V), sB = new Int32Array(V);
const cs = new Float64Array(S);
const roleLet = new Float64Array(3 * A);
const struct = new Float64Array(3);
const symTypes = Array.from({ length: S }, () => new Set());
const ts = new Float64Array(TR.tok.length);
const stamp = new Int32Array(TR.tok.length); let stampId = 0;
const aff = new Int32Array(TR.tok.length);
const ctxBuf = new Int32Array(ORDER);
const f = x => x > 0 ? x * Math.log(x) : 0;

function setAnalysis(w, k) {
  an[w] = k; const o = opts[w][k]; nP[w] = o.length; sA[w] = o[0]; sB[w] = o.length > 1 ? o[1] : -1;
}
// letters of token at t (train): via type analysis
function scoreAt(t, tok, nPa, sAa, sBa) {
  const w = tok[t]; if (w === -1) return 0;
  const n = nPa(w);
  let m = 0, p = t - 1;
  while (m < ORDER - 1 && p >= 0) {
    const v = tok[p]; if (v === -1) break;
    const np = nPa(v);
    if (np === 2) { ctxBuf[ORDER - 2 - m] = key[sBa(v)]; m++; if (m >= ORDER - 1) break; }
    ctxBuf[ORDER - 2 - m] = key[sAa(v)]; m++;
    p--;
  }
  let lp = 0;
  for (let j = 0; j < n; j++) {
    const c = key[j === 0 ? sAa(w) : sBa(w)];
    const k = Math.min(m, ORDER - 1);
    let idx = 0; for (let q = ORDER - 1 - k; q < ORDER - 1; q++) idx = idx * A + ctxBuf[q];
    lp += logP[k + 1][idx * A + c];
    for (let q = 0; q < ORDER - 2; q++) ctxBuf[q] = ctxBuf[q + 1];
    ctxBuf[ORDER - 2] = c; m++;
  }
  return lp;
}
const trN = w => nP[w], trA = w => sA[w], trB = w => sB[w];
const sc = t => scoreAt(t, TR.tok, trN, trA, trB);
let LMsum = 0;
function fullRecompute() {
  cs.fill(0); roleLet.fill(0); struct.fill(0); for (const st of symTypes) st.clear();
  for (let w = 0; w < V; w++) {
    struct[nP[w]] += cnt[w];
    cs[sA[w]] += cnt[w]; symTypes[sA[w]].add(w); roleLet[symRole[sA[w]] * A + key[sA[w]]] += cnt[w];
    if (nP[w] === 2) { cs[sB[w]] += cnt[w]; symTypes[sB[w]].add(w); roleLet[symRole[sB[w]] * A + key[sB[w]]] += cnt[w]; }
  }
  LMsum = 0; for (let t = 0; t < TR.tok.length; t++) { ts[t] = sc(t); LMsum += ts[t]; }
}
function objective() {
  let x = LMsum; for (let s = 0; s < S; s++) { x += f(cs[s]); if (cs[s] > 0) x -= symCost[s]; } for (let i = 0; i < 3 * A; i++) x -= f(roleLet[i]); x += f(struct[1]) + f(struct[2]); return x;
}
function collect(typesList) {
  stampId++; let n = 0;
  for (const w of typesList) for (const o of occ[w]) for (let t = o; t < o + ORDER && t < TR.tok.length; t++) {
    if (TR.tok[t] === -1) break;
    if (stamp[t] !== stampId) { stamp[t] = stampId; aff[n++] = t; }
  }
  return n;
}
function lmDelta(n) { let d = 0; for (let i = 0; i < n; i++) d += sc(aff[i]) - ts[aff[i]]; return d; }
function lmCommit(n) { for (let i = 0; i < n; i++) { const v = sc(aff[i]); LMsum += v - ts[aff[i]]; ts[aff[i]] = v; } }
function pick(deltas, T) {
  let mx = -Infinity; for (const d of deltas) if (d > mx) mx = d;
  if (T <= 0) return deltas.indexOf(mx);
  let z = 0; const e = deltas.map(d => { const v = Math.exp((d - mx) / T); z += v; return v; });
  let r = rand() * z; for (let i = 0; i < e.length; i++) { r -= e[i]; if (r <= 0) return i; } return e.length - 1;
}

function letterSweep(T) {
  const order = []; for (let s = 0; s < S; s++) if (cs[s] > 0) order.push(s);
  for (let i = order.length - 1; i > 0; i--) { const j = Math.floor(rand() * (i + 1)); [order[i], order[j]] = [order[j], order[i]]; }
  for (const s of order) {
    const n = collect(symTypes[s]);
    const old = key[s], r = symRole[s], c = cs[s];
    const deltas = new Array(A);
    for (let L = 0; L < A; L++) {
      key[s] = L;
      let d = lmDelta(n);
      if (L !== old) { d -= f(roleLet[r * A + old] - c) - f(roleLet[r * A + old]); d -= f(roleLet[r * A + L] + c) - f(roleLet[r * A + L]); }
      deltas[L] = d;
    }
    const L = pick(deltas, T);
    key[s] = L;
    if (L !== old) { roleLet[r * A + old] -= c; roleLet[r * A + L] += c; lmCommit(n); }
  }
}

function analysisDelta(w, k, n) {
  // channel/struct part
  const c = cnt[w];
  const oldO = opts[w][an[w]], newO = opts[w][k];
  const dc = new Map(), dr = new Map();
  for (const s of oldO) { dc.set(s, (dc.get(s) || 0) - c); const rk = symRole[s] * A + key[s]; dr.set(rk, (dr.get(rk) || 0) - c); }
  for (const s of newO) { dc.set(s, (dc.get(s) || 0) + c); const rk = symRole[s] * A + key[s]; dr.set(rk, (dr.get(rk) || 0) + c); }
  let d = 0;
  for (const [s, x] of dc) if (x) {
    d += f(cs[s] + x) - f(cs[s]);
    if (cs[s] === 0 && cs[s] + x > 0) d -= symCost[s];
    else if (cs[s] > 0 && cs[s] + x <= 0) d += symCost[s];
  }
  for (const [rk, x] of dr) if (x) d -= f(roleLet[rk] + x) - f(roleLet[rk]);
  if (oldO.length !== newO.length) d += f(struct[oldO.length] - c) - f(struct[oldO.length]) + f(struct[newO.length] + c) - f(struct[newO.length]);
  const save = an[w]; setAnalysis(w, k); d += lmDelta(n); setAnalysis(w, save);
  return d;
}
function applyAnalysis(w, k, n) {
  const c = cnt[w];
  for (const s of opts[w][an[w]]) { cs[s] -= c; roleLet[symRole[s] * A + key[s]] -= c; symTypes[s].delete(w); }
  struct[opts[w][an[w]].length] -= c;
  setAnalysis(w, k);
  for (const s of opts[w][k]) { cs[s] += c; roleLet[symRole[s] * A + key[s]] += c; symTypes[s].add(w); }
  struct[opts[w][k].length] += c;
  lmCommit(n);
}
function analysisSweep(T) {
  const order = Array.from({ length: V }, (_, i) => i).filter(w => opts[w].length > 1);
  for (let i = order.length - 1; i > 0; i--) { const j = Math.floor(rand() * (i + 1)); [order[i], order[j]] = [order[j], order[i]]; }
  for (const w of order) {
    const n = collect([w]);
    // give unused symbols of each option their best letter first (cheap local fit)
    const deltas = [];
    for (let k = 0; k < opts[w].length; k++) {
      if (k === an[w]) { deltas.push(0); continue; }
      for (const s of opts[w][k]) if (cs[s] === 0) {
        let best = key[s], bd = -Infinity;
        const save = an[w]; setAnalysis(w, k);
        for (let L = 0; L < A; L++) { key[s] = L; const d = lmDelta(n); if (d > bd) { bd = d; best = L; } }
        setAnalysis(w, save); key[s] = best;
      }
      deltas.push(analysisDelta(w, k, n));
    }
    const k = pick(deltas, T);
    if (k !== an[w]) applyAnalysis(w, k, n);
  }
}

// ---------------------------------------------------------------- evaluation
function decodeType(w) { let s = ALPHA[key[sA[w]]]; if (nP[w] === 2) s += ALPHA[key[sB[w]]]; return s; }
// unseen test types: analysis whose symbols are all used in training, best channel probability
const unseenAn = unseenTypes.map(t => {
  let best = null, bscore = -Infinity;
  for (const o of (D.analyses[t] || [])) {
    if (!o.every(n => symId.has(n) && cs[symId.get(n)] > 0)) continue;
    const ids = o.map(n => symId.get(n));
    const sc_ = ids.reduce((a, s) => a + Math.log(cs[s] / roleLet[symRole[s] * A + key[s]]), 0) + Math.log(struct[o.length] / N);
    if (sc_ > bscore) { bscore = sc_; best = ids; }
  }
  return best;
});
function evaluate() {
  // recompute unseen analyses with the final key
  for (let i = 0; i < unseenTypes.length; i++) {
    let best = null, bscore = -Infinity;
    for (const o of (D.analyses[unseenTypes[i]] || [])) {
      if (!o.every(n => symId.has(n) && cs[symId.get(n)] > 0)) continue;
      const ids = o.map(n => symId.get(n));
      const v = ids.reduce((a, s) => a + Math.log(cs[s] / roleLet[symRole[s] * A + key[s]]), 0) + Math.log(struct[o.length] / N);
      if (v > bscore) { bscore = v; best = ids; }
    }
    unseenAn[i] = best;
  }
  const teN = w => w >= 0 ? nP[w] : (unseenAn[-2 - w] ? unseenAn[-2 - w].length : 0);
  const teA = w => w >= 0 ? sA[w] : unseenAn[-2 - w][0];
  const teB = w => w >= 0 ? sB[w] : unseenAn[-2 - w][1];
  // decoded-string frequencies in training, by length
  const cu = new Map(); for (let w = 0; w < V; w++) { const u = decodeType(w); cu.set(u, (cu.get(u) || 0) + cnt[w]); }
  // test tokens whose (seen or unseen) type has an analysis; others break
  const tok = Int32Array.from(TE.tok, w => (w <= -2 && !unseenAn[-2 - w]) ? -1 : w);
  let sum = 0, n = 0, sumSeen = 0, nSeen = 0, ok = 0, okN = 0;
  for (let t = 0; t < tok.length; t++) {
    const w = tok[t]; if (w === -1) continue;
    let u = ALPHA[key[teA(w)]]; if (teN(w) === 2) u += ALPHA[key[teB(w)]];
    if (TE.truth[t]) { okN++; ok += u === TE.truth[t]; }
    const c = cu.get(u); if (!c) continue;
    const g = scoreAt(t, tok, teN, teA, teB) - Math.log(c / struct[u.length]);
    sum += g; n++; if (w >= 0) { sumSeen += g; nSeen++; }
  }
  let trOk = 0, trN = 0;
  for (let t = 0; t < TR.tok.length; t++) { const w = TR.tok[t]; if (w >= 0 && TR.truth[t]) { trN++; trOk += decodeType(w) === TR.truth[t]; } }
  let sfu = 0; for (const c of cu.values()) sfu += f(c);
  const train = (LMsum - sfu + f(struct[1]) + f(struct[2])) / N / Math.LN2;
  let anOk = null;
  if (D.true_analysis) { let a = 0, b = 0; for (let w = 0; w < V; w++) { const tr = D.true_analysis[types[w]]; if (!tr) continue; b++; const cur = opts[w][an[w]].map(s => symName[s]); a += JSON.stringify(cur) === JSON.stringify(tr); } anOk = a / b; }
  return { train_gain: train, heldout_gain_all: sum / n / Math.LN2, heldout_tokens: n, heldout_gain_seen_types: sumSeen / nSeen / Math.LN2,
    acc_train: trN ? trOk / trN : null, acc_test: okN ? ok / okN : null, analysis_accuracy: anOk,
    share_pairs: struct[2] / N };
}

const t0 = Date.now(); const restarts = []; let best = null;
for (let r = 0; r < RESTARTS; r++) {
  for (let w = 0; w < V; w++) setAnalysis(w, Math.floor(rand() * opts[w].length));
  for (let s = 0; s < S; s++) key[s] = sampleLetter();
  if (argv.init === 'truth' && D.true_analysis) {
    const votes = Array.from({ length: S }, () => new Float64Array(A));
    for (let w = 0; w < V; w++) {
      const tr = D.true_analysis[types[w]]; if (!tr) continue;
      const k = opts[w].findIndex(o => JSON.stringify(o.map(x => symName[x])) === JSON.stringify(tr));
      if (k >= 0) setAnalysis(w, k);
    }
    for (let t = 0; t < TR.tok.length; t++) { const w = TR.tok[t]; if (w < 0 || !TR.truth[t]) continue;
      votes[sA[w]][ALPHA.indexOf(TR.truth[t][0])]++; if (nP[w] === 2 && TR.truth[t].length > 1) votes[sB[w]][ALPHA.indexOf(TR.truth[t][1])]++; }
    for (let x = 0; x < S; x++) { let b = 0; for (let L = 1; L < A; L++) if (votes[x][L] > votes[x][b]) b = L; if (votes[x][b] > 0) key[x] = b; }
  }
  fullRecompute();
  if (argv.init === 'truth') console.error('truth J', objective().toFixed(1), JSON.stringify(evaluate()));
  for (let sw = 0; sw < SWEEPS; sw++) {
    const T = TG0 * Math.pow(TG1 / TG0, SWEEPS > 1 ? sw / (SWEEPS - 1) : 1);
    letterSweep(T); analysisSweep(T);
    if (argv.verbose && sw % 10 === 9) { const e = evaluate(); console.error(`  r${r} sweep ${sw} T=${T.toFixed(2)} J=${objective().toFixed(0)} acc=${e.acc_train} an=${e.analysis_accuracy} pairs=${e.share_pairs.toFixed(2)}`); }
  }
  for (let g = 0; g < 3; g++) { letterSweep(0); analysisSweep(0); }
  fullRecompute();
  const rec = { restart: r, J: objective(), ...evaluate() };
  restarts.push(rec); console.error(JSON.stringify(rec));
  if (!best || rec.J > best.J) best = { ...rec, key: symName.map((n, s) => [n, cs[s], ALPHA[key[s]]]).filter(x => x[1] > 0),
    analyses: types.slice(0, 300).map((t, w) => [t, cnt[w], opts[w][an[w]].map(s => symName[s]).join(' + '), decodeType(w)]) };
}
const out = { params: { data: argv.data, lm: argv.lm, ORDER, SWEEPS, RESTARTS, TG0, TG1, seed: +(argv.seed ?? 1) }, types: V, symbols: S, seconds: (Date.now() - t0) / 1000, restarts, best };
if (argv.out) fs.writeFileSync(argv.out, JSON.stringify(out, null, 1));
console.log(JSON.stringify({ data: argv.data, lm: argv.lm, best_J: best.J, train_gain: best.train_gain, heldout_all: best.heldout_gain_all, heldout_seen: best.heldout_gain_seen_types,
  acc_train: best.acc_train, acc_test: best.acc_test, analysis_acc: best.analysis_accuracy, share_pairs: best.share_pairs, all_heldout: restarts.map(r => +r.heldout_gain_all.toFixed(3)), seconds: out.seconds }));
