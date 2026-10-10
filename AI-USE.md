# AI Use Declaration

**Course:** DHG 502 Digital Approaches in Historical Research
**Assignment:** Collocation analysis of 倭 in the *Ming Shi* 明史
**AI tool:** GitHub Copilot (agent mode, Z.ai GLM) in VS Code — 2026-10-08

## What the AI did

1. **Environment setup** — documented the Python packages required by the analysis in `requirements.txt`.
2. **Corpus inspection** — located the 328 卷 header lines and their Chinese-numeral formats (e.g. 卷一百〇一, 卷二百十一), paragraph/separator conventions, inline citation markers `[n]`, table-of-contents lines (prefixed ○), and the location of the Japan chapter (卷 322).
3. **Scripting and reports** — combined corpus preparation and analysis into `analysis.py`. The script performs OpenCC t2s conversion; sentence splitting on 。！？； with closing-quote attachment; whitespace and citation-marker stripping; per-line 卷 indexing; jieba tokenization with the custom dictionary; and a ≥5-word filter. It then runs qhchina collocation analyses for 倭 using 5- and 10-token windows and sentence context; removes simplified classical Chinese stopwords; calculates log-likelihood and logDice; includes results with raw p-value <0.05; writes full results and separate top-20-by-logDice files (`output/top20_collocates_倭_window_h5.csv`, `output/top20_collocates_倭_window_h10.csv`, and `output/top20_collocates_倭_sentence.csv`); and generates `output/results.html`, a standalone interactive five-page English report with sortable result tables. Pages 2–4 show each run's top 20 collocates by logDice; page 5 compares all qualifying collocates in a vertically scrollable list and lets readers select multiple measures at once. Collocate is the fixed row label, with local/global counts, ratios, significance values, log-likelihood, and logDice available as selectable measures.
   - Console output omits collocates found in all three methods; the three per-method CSV files retain all results with raw p-value <0.05.
4. **KWIC concordance** — uses `qhchina.analytics.collocations.kwic` to find up to 10 distinct passages for each of 王京 and 新 alongside 倭 in a 10-word context. In the HTML report, 倭 and the selected collocate are highlighted in separate colors throughout the context and passage; the CSV retains plain text. Each row includes left/node/right context, the complete sentence, and the sentence counts of 倭 and the selected collocate. `output/kwic.html` presents the concordance, and `output/kwic.csv` contains the same passages as structured data. If `data/index.csv` is available, both outputs include 卷 number and title.
5. **Collocation summary tables** — creates `output/table1_significance_vs_strength_5word.png` with the top 10 5-word collocates ranked separately by log-likelihood and logDice, and `output/table2_top_collocates_comparison.png` with the union of each method's top 10 collocates ranked by logDice. The PNGs are generated separately and are not embedded in `output/results.html`. Matplotlib renders the tables; `mplfonts` provides the CJK font.
6. **Reference files** — `requirements.txt`, `data/userdict.txt`, and this declaration.

## Human decisions and verification

- **Target word list** (`data/userdict.txt`, 86 entries: 倭 plus related personal names, Japanese titles/terms, and Ming coastal-defense official titles). Candidate words were frequency-checked against the source text; the final selection and its rationale remain the author's responsibility.
- **Segmentation check** — `analysis.py` prints 20 random 倭-containing tokenized sentences using fixed seed 42; `MIN_WORDS`, `SEED`, and `SAMPLE_TARGET` are configurable near the top of the script.
- **KWIC scope** — up to 10 distinct sentences are shown for each of 王京 and 新 in the 10-word window. The collocate must fall within ten tokens to either side of 倭. Row counts are literal character counts in the complete sentence, not corpus-wide frequency or an inferential statistic.
- **Measure ranking** — page 5 ranks each selected measure within each method; lower p-values rank ahead of higher p-values, while other measures rank in descending order. Adjusted p-values are displayed but are not used to filter results.
- **Summary table ranking** — Table 1 ranks 5-word results by descending log-likelihood and logDice. Table 2 compares the union of each method's top 10 by logDice; cells show logDice and observed local frequency.
- **Conversion fidelity** — OpenCC `t2s` spot-checked on target words (e.g. 禦倭→御倭, 良懷→良怀, 源義滿→源义满, 宗設→宗设).
- **Known limitations** — paragraphs without sentence-final punctuation (chapter TOCs, numerical tables in the 志 chapters, copyright notice) are excluded; a small number of numerical table fragments may remain; quotation-final punctuation is treated as sentence-final; "≥5 words" is counted after jieba tokenization. Stopwords are filtered from the reported collocates.

## Data provenance

- Source: mcjkurz/qh-starter `明史.txt` (Zhang Tingyu 張廷玉 et al., public-domain text), commit 5d67025.
- All derived files (`data/data.txt`, `data/index.csv`, `data/segmented.txt`) are generated deterministically by `analysis.py` from that source and can be regenerated by running `python analysis.py`.