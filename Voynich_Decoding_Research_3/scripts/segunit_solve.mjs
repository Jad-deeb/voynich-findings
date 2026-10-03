// Segment solver with nulls (generalised Naibbe family).
//
// Every word type is read as 1, 2 or 3 segments (U | P+S | P+M+S), chosen per
// type from candidate readings. Every segment symbol stands for one plaintext
// letter or for nothing (null). Plaintext spaces are not represented.
//
// Generative model and objective (log-likelihood up to constants):
//   segments per word ~ categorical (MLE)                      sum_k f(n_k)
//   each segment null with prob q, else a letter from the LM   f(n_null)+f(n_let)-f(n_seg) + LM
//   symbol | (role, value) ~ categorical (MLE)                 sum_s f(c_s) - sum_{role,val} f(c_rv)
//   lexicon cost for every symbol in use                       - sum_used cost(s)
// Search: annealed Gibbs sampling over symbol values (22 letters + null) and
// over each type's reading; random restarts.
//
// usage: node segunit_solve.mjs data=../data/sg_x.json lm=../data/lm_latin_all.txt
//        [alpha=...] sweeps=120 restarts=3 tg0=300 tg1=1 seed=1 out=...
import fs from 'fs';

const argv = Object.fromEntries(process.argv.slice(2).map(a => { const i = a.indexOf('='); return [a.slice(0, i), a.slice(i + 1)]; }));
const ALPHA = argv.alpha ?? 'abcdefghilmnopqrstuxyz';
const A = ALPHA.length, NUL = A;              // value A = null
const ORDER = +(argv.order ?? 5);
const SWEEPS = +(argv.sweeps ?? 120), RESTARTS = +(argv.restarts ?? 3);
const TG0 = +(argv.tg0 ?? 300), TG1 = +(argv.tg1 ?? 1);
const G = +(argv.glyphs ?? 20), KAPPA = +(argv.kappa ?? 2.3);
const WIN = ORDER + 3;
// Two-phase search: nulls are only allowed after this fraction of the sweeps,
// otherwise 'everything null' (gain 0) is an attractor from a random start.
const NULLFROM = +(argv.nullfrom ?? 0.6);                         // window of tokens affected by one change
let seed = (+(argv.seed ?? 1)) >>> 0;
function rand() { seed = (seed + 0x6D2B79F5) >>> 0; let t = seed; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }
const f = x => x > 0 ? x * Math.log(x) : 0;

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
const V = types.length, cnt = types.map(t => cntMap.get(t));
const ROLES = ['U', 'P', 'M', 'S'];
const symId = new Map(), symName = [], symRole = [];
function sym(name) { if (!symId.has(name)) { symId.set(name, symName.length); symName.push(name); symRole.push(ROLES.indexOf(name[0])); } return symId.get(name); }
const opts = types.map(t => D.analyses[t].map(o => o.map(sym)));
const S = symName.length;
const symCost = symName.map(n => (n.length - 2) * Math.log(G) + KAPPA);
const unseen = [], unseenId = new Map();
function flatten(streams, truths) {
  const tk = [], tr = [];
  streams.forEach((s, si) => { tk.push(-1); tr.push(null); s.forEach((t, ti) => {
    let id = -1;
    if (t !== null) { if (typeId.has(t)) id = typeId.get(t); else { if (!unseenId.has(t)) { unseenId.set(t, unseen.length); unseen.push(t); } id = -2 - unseenId.get(t); } }
    tk.push(id); tr.push(truths ? truths[si][ti] : null); }); });
  tk.push(-1); tr.push(null);
  return { tok: Int32Array.from(tk), truth: tr };
}
const TR = flatten(D.streams_train, D.truth_train), TE = flatten(D.streams_test, D.truth_test);
const occ = Array.from({ length: V }, () => []);
for (let p = 0; p < TR.tok.length; p++) if (TR.tok[p] >= 0) occ[TR.tok[p]].push(p);
const N = cnt.reduce((a, b) => a + b, 0);

// ---------------------------------------------------------------- state
const val = new Int32Array(S);                        // 0..A-1 letter, A = null
const an = new Int32Array(V);
const cs = new Float64Array(S), rv = new Float64Array(4 * (A + 1)), nseg = new Float64Array(4);
let nNull = 0, nLet = 0;
const symTypes = Array.from({ length: S }, () => new Set());
const ts = new Float64Array(TR.tok.length);
const stamp = new Int32Array(TR.tok.length); let stampId = 0;
const aff = new Int32Array(TR.tok.length);
const ctx = new Int32Array(ORDER);
let segOf = w => opts[w][an[w]];                      // current reading of a training type

function scoreAt(t, tok, segs) {
  const w = tok[t]; if (w === -1) return 0;
  const my = segs(w); if (!my) return 0;
  let m = 0, p = t - 1;
  while (m < ORDER - 1 && p >= 0) {
    const v = tok[p]; if (v === -1) break;
    const sg = segs(v); if (!sg) break;
    for (let j = sg.length - 1; j >= 0 && m < ORDER - 1; j--) { const x = val[sg[j]]; if (x !== NUL) { ctx[ORDER - 2 - m] = x; m++; } }
    p--;
  }
  let lp = 0;
  for (const s of my) {
    const c = val[s]; if (c === NUL) continue;
    const k = Math.min(m, ORDER - 1);
    let idx = 0; for (let q = ORDER - 1 - k; q < ORDER - 1; q++) idx = idx * A + ctx[q];
    lp += logP[k + 1][idx * A + c];
    for (let q = 0; q < ORDER - 2; q++) ctx[q] = ctx[q + 1];
    ctx[ORDER - 2] = c; m++;
  }
  return lp;
}
const sc = t => scoreAt(t, TR.tok, segOf);
let LMsum = 0;
function fullRecompute() {
  cs.fill(0); rv.fill(0); nseg.fill(0); nNull = 0; nLet = 0; for (const st of symTypes) st.clear();
  for (let w = 0; w < V; w++) {
    const o = segOf(w); nseg[o.length] += cnt[w];
    for (const s of o) { cs[s] += cnt[w]; rv[symRole[s] * (A + 1) + val[s]] += cnt[w]; symTypes[s].add(w); if (val[s] === NUL) nNull += cnt[w]; else nLet += cnt[w]; }
  }
  LMsum = 0; for (let t = 0; t < TR.tok.length; t++) { ts[t] = sc(t); LMsum += ts[t]; }
}
function objective() {
  let x = LMsum + f(nNull) + f(nLet) - f(nNull + nLet) + f(nseg[1]) + f(nseg[2]) + f(nseg[3]);
  for (let s = 0; s < S; s++) if (cs[s] > 0) x += f(cs[s]) - symCost[s];
  for (let i = 0; i < rv.length; i++) x -= f(rv[i]);
  return x;
}
function collect(typeList) {
  stampId++; let n = 0;
  for (const w of typeList) for (const o of occ[w]) for (let t = o; t < o + WIN && t < TR.tok.length; t++) {
    if (TR.tok[t] === -1) break;
    if (stamp[t] !== stampId) { stamp[t] = stampId; aff[n++] = t; }
  }
  return n;
}
const lmDelta = n => { let d = 0; for (let i = 0; i < n; i++) d += sc(aff[i]) - ts[aff[i]]; return d; };
const lmCommit = n => { for (let i = 0; i < n; i++) { const v = sc(aff[i]); LMsum += v - ts[aff[i]]; ts[aff[i]] = v; } };
function pick(deltas, T) {
  let mx = -Infinity; for (const d of deltas) if (d > mx) mx = d;
  if (T <= 0) return deltas.indexOf(mx);
  let z = 0; const e = deltas.map(d => { const v = Math.exp((d - mx) / T); z += v; return v; });
  let r = rand() * z; for (let i = 0; i < e.length; i++) { r -= e[i]; if (r <= 0) return i; } return e.length - 1;
}
function nullCoinDelta(dNull, dLet) { return f(nNull + dNull) + f(nLet + dLet) - f(nNull + nLet + dNull + dLet) - (f(nNull) + f(nLet) - f(nNull + nLet)); }

function valueSweep(T, allowNull) {
  const order = []; for (let s = 0; s < S; s++) if (cs[s] > 0) order.push(s);
  for (let i = order.length - 1; i > 0; i--) { const j = Math.floor(rand() * (i + 1)); [order[i], order[j]] = [order[j], order[i]]; }
  for (const s of order) {
    const n = collect(symTypes[s]);
    const old = val[s], r = symRole[s], c = cs[s];
    const nv = allowNull ? A + 1 : A;
    const deltas = new Array(nv);
    for (let L = 0; L < nv; L++) {
      val[s] = L;
      let d = lmDelta(n);
      if (L !== old) {
        d -= f(rv[r * (A + 1) + old] - c) - f(rv[r * (A + 1) + old]);
        d -= f(rv[r * (A + 1) + L] + c) - f(rv[r * (A + 1) + L]);
        if ((old === NUL) !== (L === NUL)) d += old === NUL ? nullCoinDelta(-c, c) : nullCoinDelta(c, -c);
      }
      deltas[L] = d;
    }
    const L = pick(deltas, T); val[s] = L;
    if (L !== old) {
      rv[r * (A + 1) + old] -= c; rv[r * (A + 1) + L] += c;
      if (old === NUL && L !== NUL) { nNull -= c; nLet += c; } else if (old !== NUL && L === NUL) { nNull += c; nLet -= c; }
      lmCommit(n);
    }
  }
}
function readingDelta(w, k, n) {
  const c = cnt[w], oldO = opts[w][an[w]], newO = opts[w][k];
  const dc = new Map(), dr = new Map(); let dN = 0, dL = 0;
  for (const s of oldO) { dc.set(s, (dc.get(s) || 0) - c); const key = symRole[s] * (A + 1) + val[s]; dr.set(key, (dr.get(key) || 0) - c); if (val[s] === NUL) dN -= c; else dL -= c; }
  for (const s of newO) { dc.set(s, (dc.get(s) || 0) + c); const key = symRole[s] * (A + 1) + val[s]; dr.set(key, (dr.get(key) || 0) + c); if (val[s] === NUL) dN += c; else dL += c; }
  let d = nullCoinDelta(dN, dL);
  for (const [s, x] of dc) if (x) { d += f(cs[s] + x) - f(cs[s]); if (cs[s] === 0 && cs[s] + x > 0) d -= symCost[s]; else if (cs[s] > 0 && cs[s] + x <= 0) d += symCost[s]; }
  for (const [key, x] of dr) if (x) d -= f(rv[key] + x) - f(rv[key]);
  if (oldO.length !== newO.length) d += f(nseg[oldO.length] - c) - f(nseg[oldO.length]) + f(nseg[newO.length] + c) - f(nseg[newO.length]);
  const save = an[w]; an[w] = k; d += lmDelta(n); an[w] = save;
  return d;
}
function applyReading(w, k, n) {
  const c = cnt[w];
  for (const s of opts[w][an[w]]) { cs[s] -= c; rv[symRole[s] * (A + 1) + val[s]] -= c; symTypes[s].delete(w); if (val[s] === NUL) nNull -= c; else nLet -= c; }
  nseg[opts[w][an[w]].length] -= c;
  an[w] = k;
  for (const s of opts[w][k]) { cs[s] += c; rv[symRole[s] * (A + 1) + val[s]] += c; symTypes[s].add(w); if (val[s] === NUL) nNull += c; else nLet += c; }
  nseg[opts[w][k].length] += c;
  lmCommit(n);
}
function readingSweep(T, allowNull) {
  const order = Array.from({ length: V }, (_, i) => i).filter(w => opts[w].length > 1);
  for (let i = order.length - 1; i > 0; i--) { const j = Math.floor(rand() * (i + 1)); [order[i], order[j]] = [order[j], order[i]]; }
  for (const w of order) {
    const n = collect([w]);
    const deltas = [];
    for (let k = 0; k < opts[w].length; k++) {
      if (k === an[w]) { deltas.push(0); continue; }
      for (const s of opts[w][k]) if (cs[s] === 0) {           // fit unused symbols locally
        let best = val[s], bd = -Infinity; const save = an[w]; an[w] = k;
        for (let L = 0; L < (allowNull ? A + 1 : A); L++) { val[s] = L; const d = lmDelta(n); if (d > bd) { bd = d; best = L; } }
        an[w] = save; val[s] = best;
      }
      deltas.push(readingDelta(w, k, n));
    }
    const k = pick(deltas, T);
    if (k !== an[w]) applyReading(w, k, n);
  }
}

// ---------------------------------------------------------------- evaluation
const decode = segs => segs.map(s => val[s] === NUL ? '' : ALPHA[val[s]]).join('');
const tupleKey = segs => segs.length + ':' + segs.map(s => val[s]).join(',');
function evaluate() {
  // value-tuple frequencies by number of segments (training)
  const tc = new Map(); for (let w = 0; w < V; w++) { const k = tupleKey(segOf(w)); tc.set(k, (tc.get(k) || 0) + cnt[w]); }
  const q = nNull / (nNull + nLet);
  const coin = segs => segs.reduce((a, s) => a + (val[s] === NUL ? Math.log(q) : Math.log(1 - q)), 0);
  // readings for unseen test types: best reading made of symbols seen in training
  const unseenSeg = unseen.map(t => {
    let best = null, bs = -Infinity;
    for (const o of (D.analyses[t] || [])) {
      if (!o.every(nm => symId.has(nm) && cs[symId.get(nm)] > 0)) continue;
      const ids = o.map(nm => symId.get(nm));
      const v = ids.reduce((a, s) => a + Math.log(cs[s] / rv[symRole[s] * (A + 1) + val[s]]), 0) + Math.log(nseg[o.length] / N);
      if (v > bs) { bs = v; best = ids; }
    }
    return best;
  });
  const segsTE = w => w >= 0 ? segOf(w) : unseenSeg[-2 - w];
  let sum = 0, n = 0, ok = 0, okN = 0;
  for (let t = 0; t < TE.tok.length; t++) {
    const w = TE.tok[t]; if (w === -1) continue;
    const sg = segsTE(w); if (!sg) continue;
    if (TE.truth[t]) { okN++; ok += decode(sg) === TE.truth[t]; }
    const c = tc.get(tupleKey(sg)); if (!c) continue;
    sum += scoreAt(t, TE.tok, segsTE) + coin(sg) - Math.log(c / nseg[sg.length]); n++;
  }
  let trOk = 0, trN = 0, gsum = 0;
  for (let t = 0; t < TR.tok.length; t++) {
    const w = TR.tok[t]; if (w < 0) continue;
    const sg = segOf(w);
    gsum += ts[t] + coin(sg) - Math.log(tc.get(tupleKey(sg)) / nseg[sg.length]);
    if (TR.truth[t]) { trN++; trOk += decode(sg) === TR.truth[t]; }
  }
  return { train_gain: gsum / N / Math.LN2, heldout_gain: sum / n / Math.LN2, heldout_tokens: n,
    acc_train: trN ? trOk / trN : null, acc_test: okN ? ok / okN : null,
    null_share: q, seg_shares: [1, 2, 3].map(k => +(nseg[k] / N).toFixed(3)) };
}

const t0 = Date.now(); const restarts = []; let best = null;
for (let r = 0; r < RESTARTS; r++) {
  for (let w = 0; w < V; w++) an[w] = Math.floor(rand() * opts[w].length);
  for (let s = 0; s < S; s++) val[s] = sampleLetter();
  fullRecompute();
  for (let sw = 0; sw < SWEEPS; sw++) {
    const T = TG0 * Math.pow(TG1 / TG0, SWEEPS > 1 ? sw / (SWEEPS - 1) : 1);
    const allowNull = sw >= SWEEPS * NULLFROM;
    valueSweep(T, allowNull); readingSweep(T, allowNull);
    if (sw % 10 === 9) fullRecompute();                    // resynchronise cached scores
    if (argv.verbose && sw % 10 === 9) { const e = evaluate(); console.error(`  r${r} sweep ${sw} T=${T.toFixed(1)} J=${objective().toFixed(0)} acc=${e.acc_train} null=${e.null_share.toFixed(2)} segs=${e.seg_shares}`); }
  }
  for (let g = 0; g < 3; g++) { valueSweep(0, true); readingSweep(0, true); fullRecompute(); }
  const rec = { restart: r, J: objective(), ...evaluate() };
  restarts.push(rec); console.error(JSON.stringify(rec));
  if (!best || rec.J > best.J) best = { ...rec,
    symbols: symName.map((nm, s) => [nm, cs[s], val[s] === NUL ? '-' : ALPHA[val[s]]]).filter(x => x[1] > 0).sort((a, b) => b[1] - a[1]).slice(0, 400),
    readings: types.slice(0, 300).map((t, w) => [t, cnt[w], segOf(w).map(s => symName[s]).join(' + '), decode(segOf(w))]) };
}
const out = { params: { data: argv.data, lm: argv.lm, ALPHA, ORDER, SWEEPS, RESTARTS, TG0, TG1, G, KAPPA, seed: +(argv.seed ?? 1) }, types: V, symbols: S, seconds: (Date.now() - t0) / 1000, restarts, best };
if (argv.out) fs.writeFileSync(argv.out, JSON.stringify(out, null, 1));
console.log(JSON.stringify({ data: argv.data, lm: argv.lm, best_J: best.J, train_gain: best.train_gain, heldout: best.heldout_gain, acc_train: best.acc_train, acc_test: best.acc_test,
  null_share: best.null_share, seg_shares: best.seg_shares, all_heldout: restarts.map(r => +r.heldout_gain.toFixed(3)), seconds: out.seconds }));
