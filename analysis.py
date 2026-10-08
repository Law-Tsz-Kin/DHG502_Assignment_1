#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analysis.py — 《明史》「倭」字搭配（collocation）分析
執行本腳本即可預處理語料、分析搭配詞並產生互動報告：
    python analysis.py

搭配詞結果輸出（output/）：
    collocates_倭_window_h5.csv  — 前後各 5 詞的窗口
    collocates_倭_window_h10.csv — 前後各 10 詞的窗口
    collocates_倭_sentence.csv   — 同句搭配
    kwic.csv                    — 五詞窗口 KWIC concordance
    results.html                — 可互動的五頁英文分析報告
    kwic.html                   — 五詞窗口 KWIC concordance
    table1_significance_vs_strength_5word.png
    table2_top_collocates_comparison.png
"""

import csv
import html
import json
import os
import random
import re
import unicodedata

import jieba
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.ft2font import FT2Font
import mplfonts
import opencc
import pandas as pd
from qhchina import LineSentenceFile, load_stopwords
from qhchina.analytics.collocations import find_collocates, kwic

SRC = 'data/明史.txt'
DATA_TXT = 'data/data.txt'
INDEX_CSV = 'data/index.csv'
CORPUS = 'data/segmented.txt'
USERDICT = 'data/userdict.txt'
OUTDIR = 'output'
TARGET = '倭'
MIN_WORDS = 5
N_SAMPLES = 20
SEED = 42
SAMPLE_TARGET = '倭'
MIN_WORD_LENGTH = 1
P_VALUE_THRESHOLD = 0.05
MAX_COLLOCATES = 20
HTML_OUT = os.path.join(OUTDIR, 'results.html')
KWIC_HTML_OUT = os.path.join(OUTDIR, 'kwic.html')
KWIC_CSV_OUT = os.path.join(OUTDIR, 'kwic.csv')
TABLE1_OUT = os.path.join(OUTDIR, 'table1_significance_vs_strength_5word.png')
TABLE2_OUT = os.path.join(OUTDIR, 'table2_top_collocates_comparison.png')
KWIC_COLLOCATES = ['海上', '入寇', '朝鲜', '新']
KWIC_LIMIT = 10
TABLE_TOP_N = 10
MISSING_TABLE_GLYPHS = set()

SENT_END = re.compile(r'([。！？；]」?)')
JUAN_RE = re.compile(r'^卷[一二三四五六七八九十百〇零]+$')
CITE_RE = re.compile(r'\[\d+\]')

CN_DIGITS = {'零': 0, '〇': 0, '一': 1, '二': 2, '三': 3, '四': 4,
             '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}

RUNS = [
    {
        'method': 'window',
        'horizon': 5,
        'label': '5-Word Analysis',
        'key': 'window_h5',
        'filename': f'collocates_{TARGET}_window_h5.csv',
    },
    {
        'method': 'window',
        'horizon': 10,
        'label': '10-Word Analysis',
        'key': 'window_h10',
        'filename': f'collocates_{TARGET}_window_h10.csv',
    },
    {
        'method': 'sentence',
        'horizon': None,
        'label': 'Sentence Analysis',
        'key': 'sentence',
        'filename': f'collocates_{TARGET}_sentence.csv',
    },
]


def cn2num(s: str) -> int:
    """Convert Chinese numerals used in juan headings to Arabic numbers."""
    s = s.replace('零', '〇')
    total = 0
    if '百' in s:
        head, rest = s.split('百', 1)
        total += CN_DIGITS[head] * 100
    else:
        rest = s
    if not rest:
        return total
    if '十' in rest:
        tens, ones = rest.split('十', 1)
        total += (CN_DIGITS[tens] if tens else 1) * 10
        if ones:
            total += CN_DIGITS[ones]
    else:
        total += int(''.join(str(CN_DIGITS[c]) for c in rest))
    return total


def is_punct(ch: str) -> bool:
    return unicodedata.category(ch).startswith(('P', 'Z', 'S'))


def tokenize(sent: str) -> list[str]:
    """Tokenize a sentence and remove punctuation-only tokens."""
    out = []
    for word in jieba.lcut(sent):
        word = word.strip()
        while word and is_punct(word[0]):
            word = word[1:]
        while word and is_punct(word[-1]):
            word = word[:-1]
        if word and not all(is_punct(char) for char in word):
            out.append(word)
    return out


def prepare_corpus():
    converter = opencc.OpenCC('t2s')
    with open(SRC, encoding='utf-8') as source_file:
        text = source_file.read()

    records = []
    current_no, current_title = None, None
    for line in text.split('\n'):
        sentence = line.strip()
        if JUAN_RE.match(sentence):
            current_no, current_title = cn2num(sentence[1:]), sentence
            continue
        if (current_no is None or not sentence
                or set(sentence) <= {'=', '-'}
                or sentence.startswith('○')
                or '公有領域' in sentence):
            continue
        sentence = CITE_RE.sub('', sentence)
        sentence = re.sub(r'\s+', '', sentence)
        sentence = converter.convert(sentence)
        if not SENT_END.search(sentence):
            continue
        parts = SENT_END.split(sentence)
        for index in range(1, len(parts), 2):
            records.append((current_no, current_title, parts[index - 1] + parts[index]))
        if len(parts) % 2 == 1 and parts[-1]:
            no, title, last = records[-1]
            records[-1] = (no, title, last + parts[-1])

    jieba.load_userdict(USERDICT)
    with open(USERDICT, encoding='utf-8') as userdict_file:
        targets = [word.strip() for word in userdict_file if word.strip()]

    kept = []
    for number, (no, title, sentence) in enumerate(records, 1):
        words = tokenize(sentence)
        if len(words) >= MIN_WORDS:
            kept.append((no, title, sentence, words))
        if number % 50000 == 0:
            print(f'  已分詞 {number}/{len(records)} 句 …')

    with open(DATA_TXT, 'w', encoding='utf-8') as data_file:
        for _, _, sentence, _ in kept:
            data_file.write(sentence + '\n')

    with open(INDEX_CSV, 'w', encoding='utf-8-sig', newline='') as index_file:
        writer = csv.writer(index_file)
        writer.writerow(['line_no', 'juan_no', 'juan_title'])
        for index, (no, title, _, _) in enumerate(kept, 1):
            writer.writerow([index, no, title])

    with open(CORPUS, 'w', encoding='utf-8') as corpus_file:
        for _, _, _, words in kept:
            corpus_file.write(' '.join(words) + '\n')

    if SAMPLE_TARGET:
        sample_pool = [row for row in kept if SAMPLE_TARGET in row[2]]
    else:
        sample_pool = [row for row in kept if any(word in row[2] for word in targets)]
    target_count = sum(1 for row in kept if TARGET in row[2])
    print(f'\n語料統計：切出 {len(records)} 句，保留（≥{MIN_WORDS} 詞）{len(kept)} 句，'
          f'含「{TARGET}」{target_count} 句')

    random.seed(SEED)
    sample = random.sample(sample_pool, min(N_SAMPLES, len(sample_pool)))
    print(f'\n=== {len(sample)} 句含「{SAMPLE_TARGET or "目標詞"}」的隨機分詞例句'
          f'（seed={SEED}）===\n')
    for no, _, _, words in sample:
        print(f'[卷{no:>3}] {"/".join(words)}')


def build_results_html():
    datasets = {}
    significant_counts = {}
    for run in RUNS:
        input_path = os.path.join(OUTDIR, run['filename'])
        full_df = pd.read_csv(input_path, encoding='utf-8-sig')
        significant_counts[run['key']] = len(full_df)
        df = full_df.head(MAX_COLLOCATES)
        datasets[run['key']] = [
            {
                key: None if value != value else value.item() if hasattr(value, 'item') else value
                for key, value in row.items()
            }
            for row in df.to_dict(orient='records')
        ]
    datasets['significant_counts'] = significant_counts

    data_json = json.dumps(datasets, ensure_ascii=False, allow_nan=False)
    data_json = data_json.replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    with open(HTML_OUT, 'w', encoding='utf-8') as html_file:
        html_file.write(HTML_TEMPLATE.replace('__DATA_JSON__', data_json))
    print(f'Interactive report → {HTML_OUT}')


def configure_table_font(datasets):
    """Use the bundled Simplified Chinese font and verify required glyph coverage."""
    global MISSING_TABLE_GLYPHS
    required_chars = set('倭显著性强度搭配词校正方法排名分数')
    for df in datasets.values():
        if 'collocate' in df:
            required_chars.update(''.join(df['collocate'].astype(str)))

    font_path = os.path.join(
        os.path.dirname(mplfonts.__file__),
        'fonts',
        'NotoSansCJKsc-Regular.otf',
    )
    charmap = FT2Font(font_path).get_charmap()
    missing_chars = sorted(char for char in required_chars if ord(char) not in charmap)
    if missing_chars:
        MISSING_TABLE_GLYPHS = set(missing_chars)
        missing_codes = ', '.join(f'U+{ord(char):04X}' for char in missing_chars)
        print(
            'Warning: the bundled CJK font lacks glyphs '
            f'{missing_codes}; PNG tables will show their Unicode codes. '
            'CSV and HTML retain the original characters.'
        )
    font_manager.fontManager.addfont(font_path)
    matplotlib.rcParams['font.family'] = font_manager.FontProperties(
        fname=font_path,
    ).get_name()


def render_table_image(title, subtitle, columns, rows, output_path, *, row_height=0.42):
    """Render a titled, styled table as a standalone PNG."""
    def display_text(value):
        text = str(value)
        for char in MISSING_TABLE_GLYPHS:
            text = text.replace(char, f'[U+{ord(char):04X}]')
        return text

    columns = [display_text(column) for column in columns]
    rows = [[display_text(value) for value in row] for row in rows]
    width = max(11, len(columns) * 1.7)
    height = 1.8 + max(1, len(rows)) * row_height
    figure, axis = plt.subplots(figsize=(width, height))
    figure.patch.set_facecolor('#f3f5f5')
    axis.set_facecolor('#f3f5f5')
    axis.axis('off')
    axis.text(
        0.01, 1.04, title, transform=axis.transAxes,
        fontsize=17, color='#173f5f', va='bottom',
    )
    axis.text(
        0.01, 1.005, subtitle, transform=axis.transAxes,
        fontsize=10, color='#5c6c78', va='bottom',
    )
    table = axis.table(
        cellText=rows,
        colLabels=columns,
        cellLoc='center',
        colLoc='center',
        loc='upper center',
        bbox=[0, 0, 1, 0.94],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    for (row_index, _), cell in table.get_celld().items():
        cell.set_edgecolor('#dce3e5')
        if row_index == 0:
            cell.set_facecolor('#173f5f')
            cell.set_text_props(color='white')
        else:
            cell.set_facecolor('#ffffff' if row_index % 2 else '#edf3f4')
            cell.set_text_props(color='#17232e')
    figure.savefig(output_path, dpi=220, bbox_inches='tight', facecolor=figure.get_facecolor())
    plt.close(figure)
    print(f'PNG table → {output_path}')


def build_collocation_tables(datasets):
    """Create summary tables for the 5-word window and cross-method collocates."""
    configure_table_font(datasets)
    five_word = datasets['window_h5']
    significance = five_word.sort_values(
        ['log_likelihood', 'collocate'],
        ascending=[False, True],
        kind='mergesort',
    ).head(TABLE_TOP_N).reset_index(drop=True)
    strength = five_word.sort_values(
        ['log_dice', 'collocate'],
        ascending=[False, True],
        kind='mergesort',
    ).head(TABLE_TOP_N).reset_index(drop=True)

    comparison = []
    for rank in range(TABLE_TOP_N):
        significant_row = significance.iloc[rank] if rank < len(significance) else None
        strength_row = strength.iloc[rank] if rank < len(strength) else None
        comparison.append([
            rank + 1 if significant_row is not None else '—',
            significant_row['collocate'] if significant_row is not None else '—',
            f"{significant_row['log_likelihood']:.3f}" if significant_row is not None else '—',
            f"{significant_row['adjusted_p_value']:.2e}" if significant_row is not None else '—',
            rank + 1 if strength_row is not None else '—',
            strength_row['collocate'] if strength_row is not None else '—',
            f"{strength_row['log_dice']:.3f}" if strength_row is not None else '—',
        ])
    render_table_image(
        'Table 1. Top 10 Collocates in the 5-Word Window',
        'Significance ranked by log-likelihood (FDR-adjusted p shown); strength ranked by logDice.',
        [
            'Significance rank', 'Collocate', 'Log-likelihood', 'Adjusted p',
            'Strength rank', 'Collocate', 'logDice',
        ],
        comparison,
        TABLE1_OUT,
    )

    run_keys = ('window_h5', 'window_h10', 'sentence')
    run_labels = ('5-Word', '10-Word', 'Sentence')
    ranked_runs = {
        key: datasets[key].sort_values(
            ['log_dice', 'collocate'],
            ascending=[False, True],
            kind='mergesort',
        ).reset_index(drop=True)
        for key in run_keys
    }
    ranked_top_runs = {
        key: frame.head(TABLE_TOP_N)
        for key, frame in ranked_runs.items()
    }
    union = {}
    for key in run_keys:
        for rank, row in ranked_top_runs[key].iterrows():
            entry = union.setdefault(row['collocate'], {})
            entry[key] = rank + 1
    ordered_collocates = sorted(
        union,
        key=lambda word: (
            min(union[word].values()),
            sum(union[word].values()),
            word,
        ),
    )
    cross_method_rows = []
    for word in ordered_collocates:
        row = [word]
        for key in run_keys:
            method_rows = ranked_runs[key]
            matches = method_rows.index[method_rows['collocate'] == word]
            if matches.empty:
                row.extend(['—', '—', '—'])
            else:
                rank = int(matches[0]) + 1
                method_row = method_rows.iloc[rank - 1]
                row.extend([
                    rank,
                    f"{method_row['log_dice']:.3f}",
                    f"{method_row['log_likelihood']:.3f}",
                ])
        cross_method_rows.append(row)
    render_table_image(
        'Table 2. Top 10 Collocates Across Methods',
        'Union of each method’s top 10 ranked by logDice; ranks and scores are shown wherever the collocate occurs.',
        [
            'Collocate',
            '5-Word rank', '5-Word logDice', '5-Word log-likelihood',
            '10-Word rank', '10-Word logDice', '10-Word log-likelihood',
            'Sentence rank', 'Sentence logDice', 'Sentence log-likelihood',
        ],
        cross_method_rows,
        TABLE2_OUT,
    )


def build_kwic_html():
    corpus = LineSentenceFile(CORPUS)
    with open(DATA_TXT, encoding='utf-8') as data_file:
        passages = [line.rstrip('\n') for line in data_file]

    index_by_line = {}
    if os.path.exists(INDEX_CSV):
        index_df = pd.read_csv(INDEX_CSV, encoding='utf-8-sig')
        required = {'line_no', 'juan_no', 'juan_title'}
        missing = required.difference(index_df.columns)
        if missing:
            raise ValueError(f'{INDEX_CSV} is missing columns: {", ".join(sorted(missing))}')
        index_by_line = index_df.set_index('line_no')[['juan_no', 'juan_title']].to_dict('index')

    methods = [('5-Word', 5)]
    sections = []
    csv_rows = []
    for method, horizon in methods:
        matches = kwic(
            sentences=corpus,
            target=TARGET,
            horizon=horizon,
            sort_by='position',
            separator='',
            return_type='dataframe',
            max_sentence_length=None,
        )
        for collocate in KWIC_COLLOCATES:
            rows = []
            seen_passages = set()
            for result in matches.to_dict(orient='records'):
                doc_index = int(result['doc_index'])
                context_tokens = result['left_tokens'] + result['right_tokens']
                if collocate not in context_tokens or doc_index in seen_passages:
                    continue
                seen_passages.add(doc_index)
                passage = passages[doc_index]
                metadata = index_by_line.get(doc_index + 1, {})
                rows.append({
                    'collocate': collocate,
                    'juan_no': metadata.get('juan_no'),
                    'juan_title': metadata.get('juan_title'),
                    'left': result['left'],
                    'node': result['node'],
                    'right': result['right'],
                    'passage': passage,
                    'target_count': passage.count(TARGET),
                    'collocate_count': passage.count(collocate),
                })
                if len(rows) >= KWIC_LIMIT:
                    break
            csv_rows.extend(rows)

            table_rows = []
            for row in rows:
                volume_cells = ''
                if index_by_line:
                    volume = '' if pd.isna(row['juan_no']) else f"卷{int(row['juan_no'])}"
                    title = '' if pd.isna(row['juan_title']) else row['juan_title']
                    volume_cells = (
                        f'<td>{html.escape(volume)}</td>'
                        f'<td>{html.escape(str(title))}</td>'
                    )
                table_rows.append(
                    '<tr>'
                    f'{volume_cells}'
                    f'<td class="context">{html.escape(row["left"])}</td>'
                    f'<td class="node">{html.escape(row["node"])}</td>'
                    f'<td class="context">{html.escape(row["right"])}</td>'
                    f'<td class="passage">{html.escape(row["passage"])}</td>'
                    f'<td>{row["target_count"]}</td>'
                    f'<td>{row["collocate_count"]}</td>'
                    '</tr>'
                )

            volume_headers = '<th>卷</th><th>Title</th>' if index_by_line else ''
            if table_rows:
                table = (
                    '<div class="table-wrap"><table><thead><tr>'
                    f'{volume_headers}<th>Left context</th><th>Node</th><th>Right context</th>'
                    '<th>Passage</th><th>倭 count</th><th>Collocate count</th>'
                    '</tr></thead><tbody>'
                    + ''.join(table_rows)
                    + '</tbody></table></div>'
                )
            else:
                table = '<p class="empty">No passages contain both 倭 and this collocate in this context.</p>'
            sections.append(
                f'<section class="collocate"><h3>{html.escape(collocate)}</h3>'
                f'<p class="muted">{len(rows)} passage(s), up to {KWIC_LIMIT}; '
                'counts refer to the complete sentence.</p>'
                f'{table}</section>'
            )

    index_metadata = (
        'Volume number and title are taken from data/index.csv.'
        if index_by_line else
        'data/index.csv was not found; volume metadata is omitted.'
    )
    html_document = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>KWIC: Collocation Analysis of “倭” Represent throughout Ming Shi 明史</title>
<style>
:root{{--ink:#17232e;--muted:#5c6c78;--blue:#173f5f;--teal:#207c78;--paper:#f3f5f5;--line:#dce3e5}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}}
header{{min-height:65vh;padding:clamp(28px,8vw,100px);display:flex;flex-direction:column;justify-content:center;background:linear-gradient(145deg,#fff 35%,#e5f1ef)}}
.eyebrow{{color:var(--teal);font-weight:700;text-transform:uppercase;letter-spacing:.12em}}
h1,h2,h3{{font-family:Georgia,"Noto Serif",serif}}
h1{{font-size:clamp(2.2rem,5.6vw,4.8rem);line-height:1.08;max-width:1000px}}
h2{{font-size:2rem;border-bottom:2px solid var(--teal);padding-bottom:8px}}
h3{{font-size:1.5rem;color:var(--blue)}}
main{{max-width:1500px;margin:24px auto;padding:0 24px 50px}}
.method,.collocate{{background:white;border:1px solid var(--line);border-radius:10px;padding:24px;margin:20px 0}}
.table-wrap{{overflow:auto;border:1px solid var(--line);border-radius:7px}}
table{{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}}
th,td{{padding:9px 11px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}
th{{background:#eef3f4;white-space:nowrap}}
.context{{white-space:nowrap;max-width:300px;overflow-wrap:anywhere}}
.node{{font-weight:700;color:#9c3f2b}}
.passage{{min-width:300px;white-space:normal}}
.muted,.empty{{color:var(--muted)}}
@media print{{body{{background:white}}main{{max-width:none;margin:0}}header{{min-height:0;page-break-after:always}}.method{{page-break-before:always}}}}
</style>
</head>
<body>
<header>
<div class="eyebrow">Keywords in Context · 明史</div>
<h1>KWIC: Collocation Analysis of “倭” Represent throughout Ming Shi 明史</h1>
<p>5-word-window concordance passages for 倭 and 朝鲜, 新, 移西, 沈惟敬, 秀吉.</p>
<p class="muted">{html.escape(index_metadata)} Each row reports the counts of 倭 and the selected collocate in its full sentence.</p>
</header>
<main>{''.join(sections)}</main>
</body>
</html>
"""
    csv_columns = [
        'collocate', 'juan_no', 'juan_title', 'left', 'node', 'right',
        'passage', 'target_count', 'collocate_count',
    ]
    pd.DataFrame(csv_rows, columns=csv_columns).to_csv(
        KWIC_CSV_OUT, index=False, encoding='utf-8-sig',
    )
    print(f'KWIC CSV → {KWIC_CSV_OUT} ({len(csv_rows)} passages)')
    with open(KWIC_HTML_OUT, 'w', encoding='utf-8') as html_file:
        html_file.write(html_document)
    print(f'KWIC report → {KWIC_HTML_OUT}')


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    prepare_corpus()
    corpus = LineSentenceFile(CORPUS)   # 可重啟迭代器（find_collocates 需迭代兩次）
    print(f'語料：{corpus.sentence_count:,} 句，{corpus.token_count:,} 詞\n')

    stopwords = load_stopwords('zh_cl_sim')
    table_datasets = {}
    printed_datasets = {}
    for run in RUNS:
        method, horizon, label = run['method'], run['horizon'], run['key']
        df = find_collocates(
            sentences=corpus,
            target_words=[TARGET],
            method=method,
            horizon=horizon,
            measures=['log_likelihood', 'logDice'],
            filters={
                'stopwords': stopwords,
                'min_word_length': MIN_WORD_LENGTH,
            },
            correction='fdr_bh',
            sort_by='log_dice',
            ascending=False,
            return_type='dataframe',
        )
        df = df.loc[df['p_value'] < P_VALUE_THRESHOLD]
        df = df.sort_values(
            ['log_dice', 'collocate'],
            ascending=[False, True],
            kind='mergesort',
        )
        table_datasets[run['key']] = df.copy()
        printed_datasets[run['key']] = df.head(MAX_COLLOCATES).copy()

        output_path = os.path.join(OUTDIR, f'collocates_{TARGET}_{label}.csv')
        df.to_csv(output_path, index=False, encoding='utf-8-sig')

    shared_collocates = set.intersection(
        *(set(dataset['collocate']) for dataset in table_datasets.values())
    )
    if shared_collocates:
        print(
            'Console output excludes collocates present in all three methods: '
            + ', '.join(sorted(shared_collocates))
        )
    for run in RUNS:
        label = run['key']
        output_path = os.path.join(OUTDIR, run['filename'])
        printed_df = printed_datasets[label]
        printed_df = printed_df.loc[
            ~printed_df['collocate'].isin(shared_collocates)
        ]
        print(
            f'搭配詞結果（{label}）→ {output_path}'
            f'（CSV {len(table_datasets[label])} 列；列印 {len(printed_df)} 列）'
        )
        print(printed_df.to_string(index=False))
        print()

    build_collocation_tables(table_datasets)
    build_results_html()
    build_kwic_html()


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Collocation Analysis of “倭” — Ming Shi 明史</title>
<style>
:root{color-scheme:light;--ink:#17232e;--muted:#5c6c78;--blue:#173f5f;--teal:#207c78;--paper:#f3f5f5;--line:#dce3e5;--white:#fff}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}
.topbar{position:sticky;top:0;z-index:5;background:var(--blue);color:white;box-shadow:0 3px 12px #10253630}
.topbar-inner{max-width:1440px;margin:auto;padding:12px 24px;display:flex;align-items:center;gap:18px}
.brand{font-weight:700;white-space:nowrap;margin-right:auto}
.nav{display:flex;gap:7px;flex-wrap:wrap}
button,select,input{font:inherit}
.nav button,.pager button{border:1px solid #ffffff66;background:transparent;color:white;border-radius:6px;padding:8px 11px;cursor:pointer}
.nav button:hover,.nav button.active{background:white;color:var(--blue)}
main{max-width:1440px;margin:28px auto;padding:0 24px 36px}
.page{display:none;min-height:70vh;background:var(--white);border:1px solid var(--line);border-radius:12px;padding:clamp(24px,5vw,64px);box-shadow:0 8px 30px #1025360b}
.page.active{display:block}
.cover{min-height:70vh;display:flex;flex-direction:column;justify-content:center;background:linear-gradient(145deg,#fff 35%,#e5f1ef)}
.eyebrow{color:var(--teal);font-weight:700;text-transform:uppercase;letter-spacing:.12em;font-size:.82rem}
h1{font-family:Georgia,"Noto Serif",serif;font-size:clamp(2.2rem,5.6vw,4.8rem);line-height:1.08;max-width:1000px;margin:.5em 0}
h2{font-family:Georgia,"Noto Serif",serif;font-size:clamp(1.7rem,3vw,2.5rem);margin:0 0 8px}
h3{margin:.3em 0}
.subtitle,.muted{color:var(--muted)}
.lead{font-size:1.2rem;max-width:760px;color:#40535f}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:14px;margin:26px 0}
.card{border:1px solid var(--line);border-radius:9px;padding:16px;background:#fbfcfc}
.card strong{display:block;color:var(--blue);font-size:1.2rem;margin-top:5px}
.table-wrap{overflow:auto;border:1px solid var(--line);border-radius:8px;margin-top:22px}
table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}
th,td{padding:10px 12px;text-align:right;border-bottom:1px solid var(--line);white-space:nowrap}
th{background:#eef3f4;color:#273d4b;position:sticky;top:0}
th:first-child,td:first-child{text-align:left}
th button{border:0;background:transparent;color:inherit;font-weight:700;padding:2px;cursor:pointer}
th button:hover{color:var(--teal);text-decoration:underline}
tbody tr:hover{background:#f0f8f7}
.toolbar{display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin:20px 0 4px}
.toolbar label{font-weight:650}
select,input{border:1px solid #b9c6cb;border-radius:6px;padding:9px 11px;background:white;color:var(--ink)}
input{min-width:min(300px,100%)}
.pager{display:flex;justify-content:space-between;gap:12px;margin-top:18px}
.pager button{background:var(--blue)}
.pager button:disabled{opacity:.45;cursor:not-allowed}
.note{padding:14px 17px;border-radius:7px;background:#edf5f4;color:#28434b}
.page-number{color:var(--muted);margin-top:14px;font-size:.9rem}
@media(max-width:850px){.topbar-inner{align-items:flex-start;flex-direction:column;gap:10px}.brand{margin:0}.nav{max-height:130px;overflow:auto}}
@media print{.topbar,.pager{display:none!important}body{background:white}main{max-width:none;margin:0;padding:0}.page{display:block!important;min-height:0;box-shadow:none;border:0;page-break-after:always;padding:24px}.table-wrap{overflow:visible}th{position:static}}
</style>
</head>
<body>
<header class="topbar"><div class="topbar-inner">
<div class="brand">Ming Shi 明史 · Collocation Study</div>
<nav class="nav" aria-label="Report pages">
<button data-page="0">1 · Cover</button><button data-page="1">2 · 5-Word</button>
<button data-page="2">3 · 10-Word</button><button data-page="3">4 · Sentence</button>
<button data-page="4">5 · Compare</button>
</nav></div></header>
<main>
<section class="page cover" id="page-1">
<div class="eyebrow">Historical Corpus Linguistics · Interactive Report</div>
<h1>Collocation Analysis of “倭” Represent throughout Ming Shi 明史</h1>
<p class="lead">A comparison of words associated with 倭 in the Ming Shi, using two word-window sizes and whole-sentence context.</p>
<div class="cards" id="overview-cards"></div>
<p class="note">Pages 2–4 show the top 20 collocates in each method. Page 5 compares the methods.</p>
<div class="page-number">Page 1 of 5</div>
</section>
<section class="page" id="page-2">
<div class="eyebrow">Window method · horizon = 5</div><h2>5-Word Analysis</h2>
<p class="subtitle">Top 20 collocates by logDice from all collocates with p-value &lt; 0.05, within five tokens to either side of 倭. Adjusted p-values are reported but are not used as an inclusion filter.</p>
<div class="cards" id="stats-window_h5"></div><div class="table-wrap" id="table-window_h5"></div><div class="page-number">Page 2 of 5</div>
</section>
<section class="page" id="page-3">
<div class="eyebrow">Window method · horizon = 10</div><h2>10-Word Analysis</h2>
<p class="subtitle">Top 20 collocates by logDice from all collocates with p-value &lt; 0.05, within ten tokens to either side of 倭. Adjusted p-values are reported but are not used as an inclusion filter.</p>
<div class="cards" id="stats-window_h10"></div><div class="table-wrap" id="table-window_h10"></div><div class="page-number">Page 3 of 5</div>
</section>
<section class="page" id="page-4">
<div class="eyebrow">Sentence method</div><h2>Sentence Analysis</h2>
<p class="subtitle">Top 20 collocates by logDice from all collocates with p-value &lt; 0.05, occurring in the same sentence as 倭. Adjusted p-values are reported but are not used as an inclusion filter.</p>
<div class="cards" id="stats-sentence"></div><div class="table-wrap" id="table-sentence"></div><div class="page-number">Page 4 of 5</div>
</section>
<section class="page" id="page-5">
<div class="eyebrow">Cross-method comparison</div><h2>Compare the Three Analyses</h2>
<p class="subtitle">Choose a measure to compare its score and within-run rank for every collocate across 5-word, 10-word, and sentence contexts.</p>
<div class="toolbar"><label for="metric-choice">Measure</label><select id="metric-choice"><option value="log_dice">logDice</option><option value="log_likelihood">Log-likelihood</option></select>
<label for="compare-search">Find a collocate</label><input id="compare-search" type="search" placeholder="Type a word to filter"></div>
<div class="table-wrap" id="comparison-table"></div>
<div class="page-number">Page 5 of 5</div>
</section>
<div class="pager"><button id="previous-page">← Previous page</button><button id="next-page">Next page →</button></div>
</main>
<script id="analysis-data" type="application/json">__DATA_JSON__</script>
<script>
const datasets=JSON.parse(document.getElementById('analysis-data').textContent);
const runInfo=[
  {key:'window_h5',label:'5-Word Analysis'},
  {key:'window_h10',label:'10-Word Analysis'},
  {key:'sentence',label:'Sentence Analysis'}
];
const columns=[
  ['collocate','Collocate','text'],['obs_local','Observed local','number'],
  ['exp_local','Expected local','number'],['obs_global','Observed global','number'],
  ['ratio_local','Local ratio','number'],['log_likelihood','Log-likelihood','number'],
  ['log_dice','logDice','number'],['p_value','p-value','number'],
  ['adjusted_p_value','Adjusted p-value','number']
];
const pageButtons=[...document.querySelectorAll('.nav button')];
let activePage=0;
function setPage(index,updateHash=true){
  activePage=Math.max(0,Math.min(4,index));
  document.querySelectorAll('.page').forEach((page,i)=>page.classList.toggle('active',i===activePage));
  pageButtons.forEach((button,i)=>button.classList.toggle('active',i===activePage));
  document.getElementById('previous-page').disabled=activePage===0;
  document.getElementById('next-page').disabled=activePage===4;
  if(updateHash)history.replaceState(null,'','#page-'+(activePage+1));
  window.scrollTo({top:0,behavior:'smooth'});
}
pageButtons.forEach((button)=>button.addEventListener('click',()=>setPage(Number(button.dataset.page))));
document.getElementById('previous-page').addEventListener('click',()=>setPage(activePage-1));
document.getElementById('next-page').addEventListener('click',()=>setPage(activePage+1));
function formatValue(value,key){
  if(value===null||value===undefined)return '—';
  if(key==='p_value'||key==='adjusted_p_value')return value===0?'< 1e-300':value<.001?value.toExponential(3):value.toFixed(4);
  if(typeof value==='number')return Number(value.toFixed(4)).toString();
  return String(value);
}
function cell(row,key){const td=document.createElement('td');td.textContent=formatValue(row[key],key);return td}
function makeSortableTable(container,rows,tableColumns,initialKey,initialAscending,onSort=null){
  let sortKey=initialKey,ascending=initialAscending;
  const draw=()=>{
    const sorted=[...rows].sort((a,b)=>{
      const left=a[sortKey],right=b[sortKey];
      if((left===null||left===undefined)&&(right===null||right===undefined))return 0;
      if(left===null||left===undefined)return 1;
      if(right===null||right===undefined)return -1;
      const comparison=typeof left==='string'?left.localeCompare(right):left-right;
      return comparison===0?0:(ascending?comparison:-comparison);
    });
    const table=document.createElement('table'),thead=table.createTHead(),header=thead.insertRow();
    tableColumns.forEach(([key,label])=>{
      const th=document.createElement('th'),button=document.createElement('button');
      button.type='button';button.textContent=label+(key===sortKey?(ascending?' ↑':' ↓'):'');
      button.addEventListener('click',()=>{
        if(onSort){onSort(key);return}
        if(sortKey===key)ascending=!ascending;else{sortKey=key;ascending=key==='collocate'}draw()
      });
      th.append(button);header.append(th);
    });
    const body=table.createTBody();
    sorted.forEach(row=>{const tr=body.insertRow();tableColumns.forEach(([key])=>tr.append(cell(row,key)))});
    container.replaceChildren(table);
  };
  draw();
}
function renderRun(key){
  const rows=datasets[key];
  const ranked=[...rows].sort((a,b)=>b.log_dice-a.log_dice);
  const best=ranked[0];
  const cards=[
    ['Collocates with p-value < 0.05',datasets.significant_counts[key].toLocaleString()],
    ['Shown in this table',rows.length+' (top 20)'],
    ['Highest logDice',best?best.collocate+' · '+formatValue(best.log_dice,'log_dice'):'—'],
  ];
  const container=document.getElementById('stats-'+key);
  container.replaceChildren(...cards.map(([label,value])=>{
    const card=document.createElement('div'),heading=document.createElement('strong');
    card.className='card';card.append(document.createTextNode(label));heading.textContent=value;card.append(heading);return card;
  }));
  makeSortableTable(document.getElementById('table-'+key),rows,columns,'log_dice',false);
}
runInfo.forEach(run=>renderRun(run.key));
document.getElementById('overview-cards').innerHTML=runInfo.map(run=>
  '<div class="card">'+run.label+'<strong>'+datasets.significant_counts[run.key].toLocaleString()+' collocates (p < 0.05)</strong></div>'
).join('');
const metricChoice=document.getElementById('metric-choice'),searchInput=document.getElementById('compare-search');
let comparisonSortKey='rank-window_h5',comparisonAscending=true;
function renderComparison(){
  const metric=metricChoice.value;
  const indexed=runInfo.map(run=>{
    const ranked=[...datasets[run.key]].sort((a,b)=>b[metric]-a[metric]);
    const map=new Map(ranked.map((row,index)=>[row.collocate,{score:row[metric],rank:index+1}]));
    return {run,map};
  });
  const words=[...new Set(indexed.flatMap(item=>[...item.map.keys()]))];
  const query=searchInput.value.trim().toLocaleLowerCase();
  const rows=words.filter(word=>word.toLocaleLowerCase().includes(query)).map(word=>{
    const row={collocate:word};
    indexed.forEach(({run,map})=>{
      const entry=map.get(word);
      row['score-'+run.key]=entry?entry.score:null;
      row['rank-'+run.key]=entry?entry.rank:null;
    });
    return row;
  });
  const compareColumns=[['collocate','Collocate','text']];
  runInfo.forEach(run=>{
    compareColumns.push(['score-'+run.key,run.label+' score ('+(metric==='log_dice'?'logDice':'log-likelihood')+')','number']);
    compareColumns.push(['rank-'+run.key,run.label+' rank','number']);
  });
  makeSortableTable(document.getElementById('comparison-table'),rows,compareColumns,comparisonSortKey,comparisonAscending,key=>{
    if(comparisonSortKey===key)comparisonAscending=!comparisonAscending;
    else{comparisonSortKey=key;comparisonAscending=key==='collocate'}
    renderComparison();
  });
}
metricChoice.addEventListener('change',()=>{comparisonSortKey='rank-window_h5';comparisonAscending=true;renderComparison()});
searchInput.addEventListener('input',renderComparison);
renderComparison();
const hashMatch=location.hash.match(/^#page-([1-5])$/);
setPage(hashMatch?Number(hashMatch[1])-1:0,false);
</script>
</body>
</html>
"""


if __name__ == '__main__':
    main()