"""Build report.html (English) from the three analysis outputs:
top10_words.txt, 奸臣名單.txt and 詞頻分佈.txt.

Sections appear in this order: Top 10 words, Treacherous officials,
Term distribution (嚴嵩 / 南京 / 尚書 across the text).
"""
import html

TOP10_FILE = "top10_words.txt"
OFFICIALS_FILE = "奸臣名單.txt"
DISTRIBUTION_FILE = "詞頻分佈.txt"
OUTPUT = "report.html"


def read_top10():
    rows = []
    for line in open(TOP10_FILE, encoding="utf-8"):
        parts = line.strip().split("\t")
        if len(parts) == 2 and parts[1].isdigit():
            rows.append((parts[0], int(parts[1])))
    return rows


def read_officials():
    rows = []
    for line in open(OFFICIALS_FILE, encoding="utf-8"):
        parts = line.strip().split("\t")
        if len(parts) == 4 and parts[0] != "姓名" and not parts[0].startswith("明史"):
            rows.append((parts[0], parts[1], int(parts[2]), parts[3]))
    return rows


def read_distribution():
    totals, dist = [], []
    in_totals = in_dist = False
    for line in open(DISTRIBUTION_FILE, encoding="utf-8"):
        parts = line.strip().split("\t")
        if parts[0] == "詞":
            in_totals, in_dist = True, False
            continue
        if parts[0] == "段":
            in_totals, in_dist = False, True
            continue
        if in_totals and len(parts) == 3:
            totals.append((parts[0], int(parts[1]), int(parts[2])))
        elif in_dist and len(parts) == 5:
            dist.append((int(parts[0]), parts[1], *(int(x) for x in parts[2:])))
    return totals, dist


def bar_chart_top10(rows):
    peak = rows[0][1]
    cells = "".join(
        f"<tr><td class='term'>{w}</td>"
        f"<td class='bar'><div class='fill' style='width:{c / peak * 100:.1f}%'>{c:,}</div></td></tr>"
        for w, c in rows)
    return f"<table class='bars'>{cells}</table>"


def bar_chart_distribution(dist):
    terms = ["嚴嵩", "南京", "尚書"]
    colors = {"嚴嵩": "#c0392b", "南京": "#2980b9", "尚書": "#27ae60"}
    maxima = {i: max(r[2 + i] for r in dist) for i in range(3)}
    cols = ""
    for seg, pos, *counts in dist:
        bars = "".join(
            f"<div class='vbar' style='height:{max(c / maxima[i] * 100, 0.5):.1f}%;background:{colors[t]}' "
            f"title='Segment {seg} ({pos}) {t}: {c}'>{c if c else ''}</div>"
            for i, (t, c) in enumerate(zip(terms, counts)))
        cols += f"<div class='seg'><div class='stack'>{bars}</div><div class='lbl'>{seg}</div></div>"
    legend = "".join(f"<span class='lg'><i style='background:{colors[t]}'></i>{t} ({['Yan Song','Nanjing','Shangshu (Minister)'][i]})</span>"
                     for i, t in enumerate(terms))
    return f"<div class='chart'>{cols}</div><p class='legend'>{legend}</p>"


def page(top10, officials, totals, dist):
    t10 = bar_chart_top10(top10)
    off_rows = "".join(
        f"<tr><td>{n}</td><td>{'Main biography' if s == '本傳' else 'Attached biography'}</td>"
        f"<td>{c}</td><td>{'Yes' if f == '是' else 'No'}</td></tr>"
        for n, s, c, f in officials)
    tot_rows = "".join(
        f"<tr><td>{t}</td><td>{['Yan Song (Jiajing-era Grand Secretary)','Nanjing (southern capital)','Shangshu (Minister, head of a ministry)'][i]}</td>"
        f"<td>{s:,}</td><td>{j:,}</td></tr>"
        for i, (t, s, j) in enumerate(totals))
    dist_chart = bar_chart_distribution(dist)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Analysis of the History of Ming (明史)</title>
<style>
body{{font-family:Georgia,'Times New Roman',serif;max-width:900px;margin:2rem auto;padding:0 1rem;color:#222;line-height:1.55}}
h1{{border-bottom:3px double #666}} h2{{border-bottom:1px solid #bbb;margin-top:2.2rem}}
table{{border-collapse:collapse;margin:1rem 0;width:100%}}
th,td{{border:1px solid #ccc;padding:.35rem .6rem;text-align:left}}
th{{background:#f0ede6}}
table.bars td{{border:none;padding:.2rem 0}}
td.term{{width:5rem;font-size:1.05rem}}
td.bar{{width:100%}}
.fill{{background:#4a6fa5;color:#fff;padding:.15rem .5rem;min-width:2.5rem;text-align:right;border-radius:2px}}
.chart{{display:flex;align-items:flex-end;height:260px;gap:6px;margin:1.5rem 0 .5rem}}
.seg{{flex:1;display:flex;flex-direction:column;height:100%;justify-content:flex-end}}
.stack{{display:flex;flex-direction:column-reverse;align-items:stretch;height:100%}}
.vbar{{width:100%;font-size:.62rem;color:#fff;text-align:center}}
.lbl{{text-align:center;font-size:.72rem;color:#555;margin-top:3px}}
.legend .lg{{margin-right:1rem}} .legend i{{display:inline-block;width:12px;height:12px;margin-right:4px;vertical-align:-1px}}
.note{{color:#555;font-size:.9rem}}
</style>
</head>
<body>
<h1>Text Analysis of the <i>History of Ming</i> (明史.txt)</h1>
<p class="note">Source: 明史.txt ({len(open('明史.txt', encoding='utf-8').read()):,} characters), segmented with <b>jieba</b>.</p>

<h2>1. Top 10 Most Frequent Words</h2>
{t10}
<p class="note">Words of length ≥ 2 after jieba segmentation. The list is dominated by institutional vocabulary —
<b>御史</b> (censors), <b>尚書</b> (ministers), <b>巡撫</b> (grand coordinators), <b>進士</b> (jinshi graduates) —
and by era names (<b>洪武</b>, <b>元年</b>, <b>三年</b>, <b>明年</b>) and places (<b>南京</b>), reflecting the annals-and-biographies structure of the history.</p>

<h2>2. Treacherous Officials Recorded in 明史 (奸臣傳, Chapter 308)</h2>
<table>
<tr><th>Name</th><th>Status</th><th>Mentions in chapter</th><th>Tagged as person name by jieba</th></tr>
{off_rows}
</table>
<p class="note">{len(officials)} officials in total. Main biographies (本傳) open the entry; attached biographies (附傳) are
resolved from name lists such as 「如紀綱、馬麟、丁玨、秦政學、趙緯、李芳」. The lineup spans the whole dynasty:
<b>胡惟庸</b> and <b>陳寧</b> under the founding emperor, <b>陳瑛</b> under Yongle, <b>嚴嵩</b> and his son <b>嚴世蕃</b>
under Jiajing, and <b>周延儒</b>, <b>溫體仁</b>, <b>馬士英</b>, <b>阮大鋮</b> at the dynasty's end.</p>

<h2>3. Term Distribution: 嚴嵩, 南京, 尚書 across the Text</h2>
<table>
<tr><th>Term</th><th>Meaning</th><th>Substring occurrences</th><th>jieba token occurrences</th></tr>
{tot_rows}
</table>
<p class="note">The text was cut into {len(dist)} equal segments (0–5%, 5–10%, … of all characters). Bars below are scaled
per term to its segment maximum; hover for exact counts.</p>
{dist_chart}
<p class="note"><b>Reading the chart:</b> <b>嚴嵩</b> (Yan Song) spikes sharply in segments 11–13 (50–65% of the text) —
the Jiajing-reign annals and biographies that recount his two decades of dominance — and is nearly absent elsewhere.
<b>南京</b> (Nanjing) keeps a steady presence throughout (the secondary capital and southern administration), with a
broad peak in segments 10–13 and a collapse in the final segments, after the court's fall. <b>尚書</b> (minister) is the
most evenly distributed, since it is a routine official title, peaking wherever annal chapters pile up appointments.</p>
</body>
</html>
"""


def main():
    top10 = read_top10()
    officials = read_officials()
    totals, dist = read_distribution()
    doc = page(top10, officials, totals, dist)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(doc)
    print(f"Wrote {OUTPUT} ({len(doc):,} chars)")


if __name__ == "__main__":
    main()
