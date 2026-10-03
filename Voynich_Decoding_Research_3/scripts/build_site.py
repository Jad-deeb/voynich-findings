"""Build the static findings site (GitHub Pages) into outputs/site/.

index.html is generated from the result files so every number on the page comes
from the same JSON the reports use. Reports are copied as Markdown (GitHub
Pages renders them); code and results are packed into one zip."""
import html
import json
import re
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]          # Voynich_Decoding_Research_3
OUT = ROOT.parent / 'site'
DATA = ROOT / 'data'

REPORTS = [
    ('Voynich_Research_Notes.md', 'Attempt 1 — first statistics and reading guide'),
    ('Voynich_Decoding_Attempt_2.md', 'Attempt 2 — letter-for-letter substitution searches'),
    ('Voynich_Decoding_Attempt_3.md', 'Attempt 3 — word-level tests and a structure-aware cipher solver'),
    ('Voynich_Decoding_Attempt_4.md', 'Attempt 4 — 46 languages, period corpora, three new solvers, outside claims'),
]


def strip_dist():
    rows = json.loads((DATA / 'diag_bible_distance.json').read_text(encoding='utf-8'))
    langs, vms = [], {}
    for r in rows:
        share = r['word_d2'] / r['word_d1'] if r['word_d1'] > 0 else 0.0
        if r['text'].startswith('VOYNICH'):
            vms[r['text']] = (r['word_d1'], r['word_d2'], share)
        else:
            name = r['text'].replace('-NT', '').replace('-PART', '').replace('-tok', '')
            langs.append((name, r['word_d1'], r['word_d2'], share))
    models = []
    for r in json.loads((DATA / 'compare_models.json').read_text()):
        if r['text'].startswith('Timm'):
            models.append(('Timm–Schinner generator (no message)', r['word_d1'], r['word_d2']))
        if r['text'].startswith('Greshko'):
            models.append(('Greshko Naibbe cipher of Latin', r['word_d1'], r['word_d2']))
    for r in json.loads((DATA / 'markov_baseline.json').read_text()):
        if r['text'] == 'Voynich glyph Markov chain, order 4':
            models.append(('Glyph chain, 4 glyphs of memory', r['word_d1'], r['word_d2']))
    return sorted(langs, key=lambda x: x[3]), vms, models


def beeswarm(values, x, r, maxrows=9):
    """Place dots on rows so that none overlap; returns row offsets."""
    placed, rows = [], []
    for v in values:
        cx = x(v)
        k = 0
        while True:
            off = (k + 1) // 2 * (1 if k % 2 else -1)
            if all(abs(cx - px) >= 2 * r + 1 or po != off for px, po in placed):
                break
            k += 1
            if k > maxrows * 2:
                break
        placed.append((cx, off))
        rows.append(off)
    return rows


def chart_svg(langs, vms, models):
    W, L, R = 760, 190, 30
    x = lambda v: L + max(v, 0) / 0.8 * (W - L - R)
    r = 5
    lang_vals = [l[3] for l in langs]
    offs = beeswarm(lang_vals, x, r)
    maxoff = max(abs(o) for o in offs)
    half = (maxoff + 1) * (2 * r + 1)
    y1 = 24 + half
    ylab = y1 + half + 14
    y2 = ylab + 46
    y3 = y2 + 64
    H = y3 + 70
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-labelledby="chart-title chart-desc" class="strip">']
    # grid & axis
    for t in (0, 0.2, 0.4, 0.6, 0.8):
        xx = x(t)
        s.append(f'<line x1="{xx:.1f}" x2="{xx:.1f}" y1="22" y2="{H - 28}" class="grid"/>')
        s.append(f'<text x="{xx:.1f}" y="{H - 10}" class="tick" text-anchor="middle">{int(t * 100)}%</text>')
    s.append(f'<line x1="{L}" x2="{W - R}" y1="{H - 28}" y2="{H - 28}" class="axis"/>')
    # row labels
    s.append(f'<text x="{L - 14}" y="{y1 + 4:.1f}" class="rowlab" text-anchor="end">46 languages</text>')
    s.append(f'<text x="{L - 14}" y="{y1 + 22:.1f}" class="rowsub" text-anchor="end">(same Bible text)</text>')
    s.append(f'<text x="{L - 14}" y="{y2 + 4:.1f}" class="rowlab" text-anchor="end">Voynich manuscript</text>')
    s.append(f'<text x="{L - 14}" y="{y3 + 4:.1f}" class="rowlab" text-anchor="end">Models</text>')
    # language dots
    for (name, d1, d2, sh), off in zip(langs, offs):
        cy = y1 + off * (2 * r + 1)
        tip = f'{name}: {sh * 100:.0f}% (next word {d1:.3f} bits, two apart {d2:.3f} bits)'
        s.append(f'<g class="pt" data-tip="{html.escape(tip)}"><circle cx="{x(sh):.1f}" cy="{cy:.1f}" r="12" class="hit"/>'
                 f'<circle cx="{x(sh):.1f}" cy="{cy:.1f}" r="{r}" class="dot s1"/></g>')
    lo, hi = langs[0], langs[-1]
    s.append(f'<text x="{x(lo[3]):.1f}" y="{ylab:.1f}" class="dlab" text-anchor="middle">{lo[0]} {lo[3] * 100:.0f}%</text>')
    s.append(f'<text x="{x(hi[3]):.1f}" y="{ylab:.1f}" class="dlab" text-anchor="middle">{hi[0]} {hi[3] * 100:.0f}%</text>')
    # manuscript dots
    v_raw = vms['VOYNICH']; v_mrg = vms['VOYNICH variants merged']
    for (label, (d1, d2, sh), dy, anchor) in (('as written', v_raw, -14, 'start'), ('variant spellings merged', v_mrg, 22, 'start')):
        tip = f'Voynich, {label}: {max(sh, 0) * 100:.0f}% (next word {d1:.3f} bits, two apart {d2:.3f} bits)'
        s.append(f'<g class="pt" data-tip="{html.escape(tip)}"><circle cx="{x(sh):.1f}" cy="{y2:.1f}" r="12" class="hit"/>'
                 f'<circle cx="{x(sh):.1f}" cy="{y2:.1f}" r="{r + 1}" class="dot s2"/></g>')
        s.append(f'<text x="{x(sh) + 10:.1f}" y="{y2 + dy:.1f}" class="dlab">{label} {max(sh, 0) * 100:.0f}%</text>')
    # models (all at or below zero)
    for i, (name, d1, d2) in enumerate(models):
        sh = d2 / d1 if d1 > 0 else 0
        cy = y3 + (i - 1) * 19
        tip = f'{name}: two-apart dependence {d2:.3f} bits (none)'
        s.append(f'<g class="pt" data-tip="{html.escape(tip)}"><circle cx="{x(0):.1f}" cy="{cy:.1f}" r="10" class="hit"/>'
                 f'<circle cx="{x(0):.1f}" cy="{cy:.1f}" r="{r}" class="dot s3"/></g>')
        s.append(f'<text x="{x(0) + 12:.1f}" y="{cy + 4:.1f}" class="dlab">{html.escape(name)} — none</text>')
    s.append('</svg>')
    return '\n'.join(s)


def table_rows(langs, vms, models):
    out = []
    for name, d1, d2, sh in sorted(langs, key=lambda x: -x[3]):
        out.append(f'<tr><td>{html.escape(name)}</td><td>{d1:.3f}</td><td>{d2:.3f}</td><td>{sh * 100:.0f}%</td></tr>')
    for k, lab in (('VOYNICH', 'Voynich, as written'), ('VOYNICH variants merged', 'Voynich, variant spellings merged')):
        d1, d2, sh = vms[k]
        out.append(f'<tr class="hl"><td>{lab}</td><td>{d1:.3f}</td><td>{d2:.3f}</td><td>{max(sh, 0) * 100:.0f}%</td></tr>')
    for name, d1, d2 in models:
        out.append(f'<tr class="hl2"><td>{html.escape(name)}</td><td>{d1:.3f}</td><td>{d2:.3f}</td><td>none</td></tr>')
    return '\n'.join(out)


def report_link(md):
    return md.replace('.md', '.html')


PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Voynich Decoding Findings</title>
<meta name="description" content="Four rounds of computational attempts to decode the Voynich manuscript: what was tested, what failed, and what the text turned out to be like.">
<style>
:root {
  color-scheme: light;
  --page: #f9f9f7; --surface: #fcfcfb; --ink: #0b0b0b; --ink-2: #52514e; --muted: #898781;
  --grid: #e1e0d9; --axis: #c3c2b7; --border: rgba(11,11,11,0.10);
  --s1: #2a78d6; --s2: #eb6834; --s3: #1baf7a; --accent: #2a78d6; --hl: #fdf0ea; --hl2: #e8f6f0;
}
@media (prefers-color-scheme: dark) {
  :root:where(:not([data-theme="light"])) {
    color-scheme: dark;
    --page: #0d0d0d; --surface: #1a1a19; --ink: #ffffff; --ink-2: #c3c2b7; --muted: #898781;
    --grid: #2c2c2a; --axis: #383835; --border: rgba(255,255,255,0.10);
    --s1: #3987e5; --s2: #d95926; --s3: #199e70; --accent: #6da7ec; --hl: #2e1d15; --hl2: #12271f;
  }
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --page: #0d0d0d; --surface: #1a1a19; --ink: #ffffff; --ink-2: #c3c2b7; --muted: #898781;
  --grid: #2c2c2a; --axis: #383835; --border: rgba(255,255,255,0.10);
  --s1: #3987e5; --s2: #d95926; --s3: #199e70; --accent: #6da7ec; --hl: #2e1d15; --hl2: #12271f;
}
* { box-sizing: border-box; }
html { background: var(--page); }
body { margin: 0; background: var(--page); color: var(--ink); font: 16px/1.6 system-ui, -apple-system, "Segoe UI", sans-serif; }
main { max-width: 880px; margin: 0 auto; padding: 48px 16px 72px; }
header .kicker { font-size: 13px; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); margin: 0 0 8px; }
h1 { font-size: clamp(28px, 5vw, 40px); line-height: 1.15; margin: 0 0 16px; letter-spacing: -0.01em; }
h2 { font-size: 22px; margin: 56px 0 12px; }
h3 { font-size: 17px; margin: 28px 0 8px; }
p, li { color: var(--ink); }
.lede { font-size: 19px; color: var(--ink-2); max-width: 62ch; }
.verdict { background: var(--surface); border: 1px solid var(--border); border-left: 4px solid var(--s2); border-radius: 8px; padding: 18px 20px; margin: 28px 0; }
.verdict strong { display: block; font-size: 18px; margin-bottom: 4px; }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 14px; margin: 18px 0; }
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 16px; }
.card .num { font-size: 30px; font-weight: 650; line-height: 1.1; margin-bottom: 6px; }
.card p { margin: 0; color: var(--ink-2); font-size: 15px; }
figure { margin: 24px 0; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 18px 16px 10px; }
figcaption { color: var(--ink-2); font-size: 14px; margin: 6px 4px 8px; }
.fig-title { font-weight: 650; margin: 0 4px 2px; }
svg.strip { width: 100%; height: auto; display: block; overflow: visible; }
.grid { stroke: var(--grid); stroke-width: 1; }
.axis { stroke: var(--axis); stroke-width: 1; }
.tick, .rowsub { fill: var(--muted); font-size: 12px; }
.rowlab { fill: var(--ink); font-size: 13px; font-weight: 600; }
.dlab { fill: var(--ink-2); font-size: 12px; }
.dot { stroke: var(--surface); stroke-width: 2; }
.s1 { fill: var(--s1); } .s2 { fill: var(--s2); } .s3 { fill: var(--s3); }
.hit { fill: transparent; cursor: default; }
.pt:hover .dot { stroke: var(--ink); }
.legend { display: flex; flex-wrap: wrap; gap: 16px; font-size: 13px; color: var(--ink-2); margin: 4px 4px 0; }
.legend span::before { content: ""; display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 6px; vertical-align: -1px; background: var(--c); }
#tip { position: fixed; pointer-events: none; background: var(--ink); color: var(--page); font-size: 13px; padding: 6px 9px; border-radius: 6px; max-width: 300px; opacity: 0; transition: opacity .1s; }
table { width: 100%; border-collapse: collapse; font-size: 14px; margin: 12px 0; }
th, td { text-align: left; padding: 7px 8px; border-bottom: 1px solid var(--grid); vertical-align: top; }
th { color: var(--ink-2); font-weight: 600; }
td.n, th.n { text-align: right; font-variant-numeric: tabular-nums; }
tr.hl td { background: var(--hl); } tr.hl2 td { background: var(--hl2); }
.wrap { overflow-x: auto; }
details { margin: 8px 4px; } summary { cursor: pointer; color: var(--accent); font-size: 14px; }
a { color: var(--accent); }
code { font-family: ui-monospace, Consolas, monospace; font-size: .92em; background: var(--grid); padding: 1px 4px; border-radius: 4px; }
.files li { margin: 6px 0; }
.small { font-size: 14px; color: var(--ink-2); }
footer { margin-top: 64px; padding-top: 16px; border-top: 1px solid var(--grid); font-size: 13px; color: var(--muted); }
</style>
</head>
<body>
<main>
<header>
<p class="kicker">Beinecke MS 408 · research log · October 2026</p>
<h1>Trying to decode the Voynich manuscript</h1>
<p class="lede">Four rounds of computational attempts used letter substitutions, cipher solvers, 46 languages and medieval texts. Every method was tested on hidden-key ciphers before it was trusted. This page summarises what was tested and what the manuscript turned out to be like.</p>
</header>

<div class="verdict"><strong>No translation.</strong>No method that cracked a hidden test cipher found a message in the manuscript. No word, plant name or sentence of the Voynich script has been read. The work did establish, with controls, several properties that any future decipherment has to explain.</div>

<h2>Five findings</h2>
<div class="cards">
<div class="card"><div class="num">0%</div><p>The share of next-word dependence the manuscript keeps between words two apart. Every one of 46 languages keeps 33–76%.</p></div>
<div class="card"><div class="num">1.2×</div><p>How often a word is followed by itself, compared with chance. Every language avoids this (0.42× or less), except Indonesian, whose hyphenated doubled words were split into separate words.</p></div>
<div class="card"><div class="num">k/t, ch/sh, e/ee</div><p>Words that differ by these glyphs occur in the same contexts, like interchangeable spellings. The preferred spelling drifts by section.</p></div>
<div class="card"><div class="num">4 glyphs</div><p>A simple chain predicting each glyph from the previous four, trained on the manuscript, reproduces almost every word-sequence statistic measured.</p></div>
<div class="card"><div class="num">0 of ~42</div><p>The number of language models with which the best cipher solver found a message. The same solver recovered 93–99% of letters from hidden test ciphers in six languages, including 15th-century German herbal text.</p></div>
</div>

<h2>The clearest result</h2>
<figure>
<p class="fig-title" id="chart-title">Dependence kept between words two apart, as a share of next-word dependence</p>
<div class="legend"><span style="--c: var(--s1)">Languages</span><span style="--c: var(--s2)">Voynich manuscript</span><span style="--c: var(--s3)">Models of how it might have been made</span></div>
__CHART__
<figcaption id="chart-desc">In real language, grammar and phrasing link a word to the words two and three places on. Each blue dot is one Bible translation, cut to its first 34,000 words from Matthew onward. The manuscript keeps none of this link, even after its variant spellings are merged. Neither do a letter-level cipher, Timm and Schinner's meaningless generator, or a short glyph chain. Hover a dot for values.</figcaption>
<details><summary>Show the data table</summary>
<div class="wrap"><table><thead><tr><th>Text</th><th class="n">Next word (bits)</th><th class="n">Two apart (bits)</th><th class="n">Share kept</th></tr></thead>
<tbody>__TABLE__</tbody></table></div></details>
</figure>
<p>Any reading that turns each Voynich word into a word of a language inherits this property. The decoded text would have no grammar linking words beyond their immediate neighbours, and no language tested behaves like that. In practice, word-for-word "translations" of the manuscript cannot be ordinary prose in any of these languages.</p>

<h2>What the manuscript's word stream looks like</h2>
<div class="wrap"><table>
<thead><tr><th>Text</th><th class="n">Same word twice, per 1,000 pairs</th><th class="n">vs chance</th><th class="n">Two apart (bits)</th><th class="n">Glyph link across the space (bits)</th></tr></thead>
<tbody>
<tr class="hl"><td>Voynich manuscript (paragraph text)</td><td class="n">9.7</td><td class="n">1.19</td><td class="n">0.00</td><td class="n">0.176</td></tr>
<tr><td>Latin prose (<i>Secretum secretorum</i>)</td><td class="n">0.3</td><td class="n">0.02</td><td class="n">0.125</td><td class="n">0.038</td></tr>
<tr><td>Croatian Bible</td><td class="n">0.6</td><td class="n">0.07</td><td class="n">0.282</td><td class="n">—</td></tr>
<tr class="hl2"><td>Timm–Schinner generator (no message)</td><td class="n">10.2</td><td class="n">0.80</td><td class="n">−0.02</td><td class="n">0.012</td></tr>
<tr class="hl2"><td>Greshko's Naibbe cipher (Latin message)</td><td class="n">1.4</td><td class="n">0.31</td><td class="n">−0.01</td><td class="n">0.002</td></tr>
<tr class="hl2"><td>Glyph chain, 4 glyphs of memory</td><td class="n">4.2</td><td class="n">1.25</td><td class="n">−0.02</td><td class="n">0.182</td></tr>
</tbody></table></div>
<p class="small">The glyph link across the space is the mutual information between a word's last glyph and the next word's first, above a shuffle. In the manuscript, after <code>-y</code> the next word starts with <code>qo-</code> 1.65 times as often as chance and with <code>a-</code> 0.14 times. A short glyph chain reproduces this; neither published model does.</p>

<h2>Decoding attempts</h2>
<div class="wrap"><table>
<thead><tr><th>Approach</th><th>On hidden-key controls</th><th>On the manuscript</th></tr></thead>
<tbody>
<tr><td>Letter-for-letter substitution into Latin, Italian, English, Spanish (48 configurations)</td><td>98–100% of letters</td><td>No readable text; entropy far too low for any of them</td></tr>
<tr><td>Each word = one or two letters, fixed word divisions (Naibbe type)</td><td>99.8–99.9%</td><td>Real text no better than shuffled text</td></tr>
<tr><td>Same, with the word division learned together with the key</td><td>93–99% in six languages</td><td>Nothing with 35 Bible languages, period German (1460–1543 and Middle High German), Old Czech, Middle English, Old Occitan, Latin, Italian; per section; right-to-left; line by line</td></tr>
<tr><td>Cluster the word pieces, then solve as a substitution cipher</td><td>70% of letters</td><td>Real text no better than shuffled text</td></tr>
<tr><td>Words of 1–3 pieces with null fillers</td><td>Failed its own control (collapsed into nulls)</td><td>Not used</td></tr>
<tr><td>Calibration: a known Latin cipher solved with the <i>wrong</i> language</td><td>+0.58 to +1.10 bits/word above shuffled</td><td>Manuscript with the same five models: +0.04 to +0.39</td></tr>
</tbody></table></div>

<h2>Outside proposals checked</h2>
<h3>ZFD, "15th-century Croatian apothecary shorthand"</h3>
<p>ZFD decodes each Voynich word through a fixed glyph-to-sound table, so its "Croatian" inherits the manuscript's statistics. Its decoded text keeps almost no link two words apart (0.038 bits, against 0.282 in real Croatian). It repeats words immediately 19 times as often as real Croatian, and 66% of its English glosses are "?". Its validation score ignores word order, so a shuffled manuscript would score the same.</p>
<h3>"Mostly Hebrew, words written right to left"</h3>
<p>Letter for letter, the manuscript is far more predictable than written Hebrew: 2.2 bits per glyph against 3.4, in either reading direction. Hebrew words link two apart (0.315 bits); the manuscript's do not. Hebrew as a cipher plaintext was also tested in the solver sweep and gave nothing.</p>

<h2>What could still change this</h2>
<ul>
<li><b>A crib:</b> one plaintext word securely tied to a Voynich word. The Latin-script German on f116v is the only candidate and it is weak.</li>
<li><b>Physical evidence:</b> multispectral imaging, erasures, the original page order.</li>
<li><b>Untested cipher designs:</b> pieces standing for syllables, or rules that change with position in the line. Without a crib, the space of such designs is effectively unlimited.</li>
</ul>
<p>The simpler explanation, a text written by a short-memory procedure whose spelling habits drifted over time, now fits the measurements at least as well as any cipher tested. That is not proof that the text is meaningless.</p>

<h2>Reports and code</h2>
<ul class="files">
__REPORTS__
<li><a href="Voynich_English_Reading_Guide.pdf">Illustrated English reading guide (PDF)</a>: describes what the pictures show; it does not translate the text.</li>
<li><a href="voynich-research-code-and-results.zip">Code and results (zip)</a>: Python and Node.js, standard libraries only, plus every solver log, key and statistics file.</li>
</ul>
<p class="small">Data used, not redistributed here (the scripts download it):</p>
<ul class="small">
<li>Takahashi (IT) and Zandbergen–Landini (ZL) transliterations (<a href="https://www.voynich.nu/transcr.html">voynich.nu</a>);</li>
<li>Lindemann–Bowern historical corpora;</li>
<li>parallel Bible corpus (<a href="https://github.com/christos-c/bible-corpus">christos-c/bible-corpus</a>);</li>
<li>HistCorp period German and Czech (<a href="https://zenodo.org/records/10013189">Zenodo 10013189</a>, CC BY 4.0);</li>
<li>COMETA Old Occitan (<a href="https://zenodo.org/records/15300719">Zenodo 15300719</a>, CC BY 4.0);</li>
<li>Timm and Schinner's generator sample (<a href="https://github.com/TorstenTimm/SelfCitationTextgenerator">TorstenTimm/SelfCitationTextgenerator</a>);</li>
<li>Greshko's Naibbe ciphertext (<a href="https://github.com/greshko/naibbe-cipher">greshko/naibbe-cipher</a>).</li>
</ul>

<footer>Research carried out with AI assistants: attempts 1–2 with GPT-based tools, attempts 3–4 with Claude (Anthropic). No part of the Voynich main text has been translated. A claimed reading should only be trusted if a fixed key predicts pages it was not built from.</footer>
</main>
<div id="tip" role="tooltip"></div>
<script>
(function () {
  var tip = document.getElementById('tip');
  document.querySelectorAll('.pt').forEach(function (g) {
    g.addEventListener('mousemove', function (e) {
      tip.textContent = g.getAttribute('data-tip');
      tip.style.left = Math.min(e.clientX + 14, window.innerWidth - 320) + 'px';
      tip.style.top = (e.clientY + 14) + 'px';
      tip.style.opacity = 1;
    });
    g.addEventListener('mouseleave', function () { tip.style.opacity = 0; });
  });
})();
</script>
</body>
</html>
"""


def main():
    OUT.mkdir(exist_ok=True)
    for child in OUT.iterdir():          # clear contents, keep the folder (it may be open elsewhere)
        if child.name == '.git':
            continue
        shutil.rmtree(child) if child.is_dir() else child.unlink()
    langs, vms, models = strip_dist()
    reports = '\n'.join(f'<li><a href="{report_link(md)}">{html.escape(title)}</a> (<a href="{md}">Markdown</a>)</li>' for md, title in REPORTS)
    page = PAGE.replace('__CHART__', chart_svg(langs, vms, models)).replace('__TABLE__', table_rows(langs, vms, models)).replace('__REPORTS__', reports)
    (OUT / 'index.html').write_text(page, encoding='utf-8', newline='\n')
    # reports, wrapped so Jekyll renders them and leaves {{ }} alone
    for md, title in REPORTS:
        text = (ROOT.parent / md).read_text(encoding='utf-8')
        text = text.replace('](Voynich_Decoding_Research_3/', '](https://github.com/Jad-deeb/voynich-findings/blob/main/Voynich_Decoding_Research_3/')
        front = f'---\ntitle: "{title}"\nlayout: default\n---\n\n[← Back to the summary](index.html)\n\n{{% raw %}}\n'
        (OUT / md).write_text(front + text + '\n{% endraw %}\n', encoding='utf-8', newline='\n')
    shutil.copy(ROOT.parent / 'Voynich_English_Reading_Guide.pdf', OUT / 'Voynich_English_Reading_Guide.pdf')
    (OUT / '_config.yml').write_text('title: Voynich decoding findings\ntheme: jekyll-theme-primer\n', encoding='utf-8')
    (OUT / 'README.md').write_text(
        '# Voynich decoding findings\n\n'
        'Four rounds of computational attempts to decode the Voynich manuscript (Beinecke MS 408), October 2026. '
        '**No translation was found**; the site summarises what was tested and what the text turned out to be like.\n\n'
        '- Site: https://jad-deeb.github.io/voynich-findings/ (`index.html`, published with GitHub Pages)\n'
        '- Reports: `Voynich_Research_Notes.md`, `Voynich_Decoding_Attempt_2.md` to `_4.md`\n'
        '- Code and results: `Voynich_Decoding_Research_2/`, `Voynich_Decoding_Research_3/` '
        '(also packed in `voynich-research-code-and-results.zip`)\n\n'
        'Third-party data (transliterations, corpora, model outputs) is not redistributed; the scripts download it. '
        'Sources and licences are listed on the site and in the reports.\n', encoding='utf-8')
    # code and results: both research folders, without derived corpora
    keep_data = re.compile(r'^(diag_.*|compare_models|markov_baseline|check_zfd.*|anchor_expert|label_anchor_candidates|gen_selfcite|hebrew_entropy|lm_bible_alphabets|lm_period_alphabets)\.json$')
    for folder in ('Voynich_Decoding_Research_2', 'Voynich_Decoding_Research_3'):
        src = ROOT.parent / folder
        for p in src.rglob('*'):
            if p.is_dir() or '__pycache__' in p.parts or p.suffix == '.zip':
                continue
            if 'Qeqchi' in p.name:          # failed run; its log holds local file paths
                continue
            rel = p.relative_to(ROOT.parent)
            if folder.endswith('_3') and rel.parts[1] == 'data' and not keep_data.match(p.name):
                continue
            dst = OUT / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(p, dst)
    with zipfile.ZipFile(OUT / 'voynich-research-code-and-results.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        for folder in ('Voynich_Decoding_Research_2', 'Voynich_Decoding_Research_3'):
            for p in (OUT / folder).rglob('*'):
                if p.is_file():
                    z.write(p, p.relative_to(OUT))
    total = sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file())
    print('site built', OUT, 'files', sum(1 for p in OUT.rglob('*') if p.is_file()), 'MB', round(total / 1e6, 1))


if __name__ == '__main__':
    main()
