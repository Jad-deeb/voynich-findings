// Distributional clustering of cipher symbols (exchange algorithm, Kneser and
// Ney 1993; Martin, Liermann and Ney 1998): assign every symbol type to one of K
// classes so that the class-bigram likelihood of the symbol stream is maximal.
// If symbols are homophones of plaintext letters, the classes should recover
// the letters; the class stream is then an ordinary substitution cipher.
//
// input JSON: { streams: [[sym, ...], ...] (null = break), truth?: [[letter,...]] }
// usage: node cluster_parts.mjs in=x.json K=22 iters=30 seed=1 out=y.json
import fs from 'fs';
const argv = Object.fromEntries(process.argv.slice(2).map(a => { const i = a.indexOf('='); return [a.slice(0, i), a.slice(i + 1)]; }));
const K = +(argv.K ?? 22), ITERS = +(argv.iters ?? 30), MINC = +(argv.mincount ?? 1);
let seed = (+(argv.seed ?? 1)) >>> 0;
function rand() { seed = (seed + 0x6D2B79F5) >>> 0; let t = seed; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }
const D = JSON.parse(fs.readFileSync(argv.in, 'utf8'));
const cnt = new Map();
for (const s of D.streams) for (const x of s) if (x !== null) cnt.set(x, (cnt.get(x) || 0) + 1);
const types = [...cnt.keys()].filter(t => cnt.get(t) >= MINC).sort((a, b) => cnt.get(b) - cnt.get(a));
const id = new Map(types.map((t, i) => [t, i])); const V = types.length;
// bigram counts between types (within streams, no break crossing)
const right = Array.from({ length: V }, () => new Map()), left = Array.from({ length: V }, () => new Map());
const uni = new Float64Array(V);
for (const s of D.streams) for (let i = 0; i < s.length; i++) {
  const a = s[i] === null ? -1 : (id.has(s[i]) ? id.get(s[i]) : -1);
  if (a >= 0) uni[a]++;
  if (i + 1 < s.length) {
    const b = s[i + 1] === null ? -1 : (id.has(s[i + 1]) ? id.get(s[i + 1]) : -1);
    if (a >= 0 && b >= 0) { right[a].set(b, (right[a].get(b) || 0) + 1); left[b].set(a, (left[b].get(a) || 0) + 1); }
  }
}
const f = x => x > 0 ? x * Math.log(x) : 0;
const cls = new Int32Array(V);
// initialise: frequent types round-robin, which spreads the mass
for (let w = 0; w < V; w++) cls[w] = w < K ? w : Math.floor(rand() * K);
const nc = new Float64Array(K), nb = new Float64Array(K * K), nl = new Float64Array(K), nr = new Float64Array(K);
function rebuild() {
  nc.fill(0); nb.fill(0); nl.fill(0); nr.fill(0);
  for (let a = 0; a < V; a++) { nc[cls[a]] += uni[a]; for (const [b, n] of right[a]) { nb[cls[a] * K + cls[b]] += n; nl[cls[a]] += n; nr[cls[b]] += n; } }
}
// objective: sum f(n(c1,c2)) - sum f(n_left(c)) - sum f(n_right(c))  (bigram class log-likelihood up to constants)
function objective() { let x = 0; for (let i = 0; i < K * K; i++) x += f(nb[i]); for (let c = 0; c < K; c++) x -= f(nl[c]) + f(nr[c]); return x; }
rebuild();
const tmpR = new Float64Array(K), tmpL = new Float64Array(K);
for (let it = 0; it < ITERS; it++) {
  let moved = 0;
  for (let w = 0; w < V; w++) {
    const old = cls[w];
    // counts of w's neighbours by class (excluding self-loops handled separately)
    tmpR.fill(0); tmpL.fill(0); let self = 0, outW = 0, inW = 0;
    for (const [b, n] of right[w]) { if (b === w) self += n; else tmpR[cls[b]] += n; outW += n; }
    for (const [a, n] of left[w]) { if (a !== w) tmpL[cls[a]] += n; inW += n; }
    // remove w from old class
    const rem = (c, sign) => {
      for (let d = 0; d < K; d++) { if (tmpR[d]) nb[c * K + d] += sign * tmpR[d]; if (tmpL[d]) nb[d * K + c] += sign * tmpL[d]; }
      nb[c * K + c] += sign * self; nl[c] += sign * outW; nr[c] += sign * inW;
    };
    rem(old, -1);
    let best = old, bestD = -Infinity;
    for (let c = 0; c < K; c++) {
      // delta of adding w to class c
      let d = 0;
      for (let e = 0; e < K; e++) {
        if (tmpR[e]) d += f(nb[c * K + e] + tmpR[e]) - f(nb[c * K + e]);
        if (tmpL[e] && e !== c) d += f(nb[e * K + c] + tmpL[e]) - f(nb[e * K + c]);
      }
      // the (c,c) cell gets tmpL[c] (left neighbours already in c) + self; tmpR[c] handled above
      if (tmpL[c] || self) {
        const base = nb[c * K + c] + tmpR[c];
        d += f(base + tmpL[c] + self) - f(base);
      }
      d -= f(nl[c] + outW) - f(nl[c]) + f(nr[c] + inW) - f(nr[c]);
      if (d > bestD) { bestD = d; best = c; }
    }
    rem(best, +1); cls[w] = best; if (best !== old) moved++;
  }
  rebuild();
  if (argv.verbose) console.error(`iter ${it} moved ${moved} obj ${objective().toFixed(1)}`);
  if (moved === 0) break;
}
// purity against truth (controls): for each class, majority true letter
let purity = null;
if (D.truth) {
  const m = Array.from({ length: K }, () => new Map()); let n = 0;
  D.streams.forEach((s, si) => s.forEach((x, i) => { if (x === null || !id.has(x)) return; const L = D.truth[si][i]; if (!L) return; const c = cls[id.get(x)]; m[c].set(L, (m[c].get(L) || 0) + 1); n++; }));
  let ok = 0; for (const mm of m) { let b = 0; for (const v of mm.values()) if (v > b) b = v; ok += b; }
  purity = ok / n;
}
const classStreams = D.streams.map(s => s.map(x => x === null || !id.has(x) ? null : cls[id.get(x)]));
const out = { K, types: V, objective: objective(), purity, classStreams, members: Array.from({ length: K }, (_, c) => types.filter((t, w) => cls[w] === c).slice(0, 25)) };
if (argv.out) fs.writeFileSync(argv.out, JSON.stringify(out));
console.log(JSON.stringify({ in: argv.in, K, types: V, objective: out.objective, purity }));
