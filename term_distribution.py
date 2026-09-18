"""Analyse how often 嚴嵩, 南京 and 尚書 appear in 明史.txt and how their
distribution changes across the text.

The text is split into 20 equal segments (by character position); jieba
tokenises each segment and the three terms are counted per segment as exact
tokens (cross-checked against raw substring counts). Results are written to
詞頻分佈.txt and printed.
"""
import jieba

SOURCE = "明史.txt"
OUTPUT = "詞頻分佈.txt"
TERMS = ["嚴嵩", "南京", "尚書"]
SEGMENTS = 20


def main():
    text = open(SOURCE, encoding="utf-8").read()
    n = len(text)
    size = n // SEGMENTS

    rows = []  # (seg_no, start%, end%, token counts, substring counts)
    for s in range(SEGMENTS):
        chunk = text[s * size:(s + 1) * size if s < SEGMENTS - 1 else n]
        tokens = jieba.lcut(chunk)
        tok_counts = {t: tokens.count(t) for t in TERMS}
        sub_counts = {t: chunk.count(t) for t in TERMS}
        rows.append((s + 1, s * 100 // SEGMENTS, (s + 1) * 100 // SEGMENTS, tok_counts, sub_counts))

    total_tokens = {t: sum(r[3][t] for r in rows) for t in TERMS}
    total_subs = {t: sum(r[4][t] for r in rows) for t in TERMS}

    lines = [
        f"明史.txt 詞頻分佈分析：{'、'.join(TERMS)}",
        f"全文長度：{n:,} 字，切成 {SEGMENTS} 段（每段約 {size:,} 字）",
        "",
        "詞\t字符出現次數\tjieba分詞次數",
    ]
    lines += [f"{t}\t{total_subs[t]}\t{total_tokens[t]}" for t in TERMS]

    lines += ["", f"各段分佈（第{SEGMENTS}段至文末）：", "段\t位置\t" + "\t".join(TERMS)]
    for seg, a, b, tok, sub in rows:
        lines.append(f"{seg}\t{a}%–{b}%\t" + "\t".join(str(tok[t]) for t in TERMS))

    report = "\n".join(lines)
    print(report)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(report + "\n")


if __name__ == "__main__":
    main()
