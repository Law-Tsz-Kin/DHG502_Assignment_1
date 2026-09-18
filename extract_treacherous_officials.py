"""Extract the names of all 奸臣 (treacherous officials) recorded in 明史.txt.

明史 卷三百〇八 is 《奸臣傳》. Main biographies open with "姓名，字X" or
"姓名，籍貫人。" at the start of a paragraph; attached brief biographies open
with the given name only (the full name appears in the preceding biography,
usually in a name list such as 「如紀綱、馬麟、丁玨、秦政學、趙緯、李芳」).
jieba is used for segmentation, POS tagging and name verification.
"""
import re

import jieba
import jieba.posseg as pseg

SOURCE = "明史.txt"
OUTPUT = "奸臣名單.txt"

HAN = "\u4e00-\u9fff"                                   # bare range for composing classes
KIN = set("子父兄弟孫")                                  # 其子世蕃 → main head's surname
NUM = set("一二三四五六七八九十百千萬零兩")
CONT = {"初", "先是", "未幾", "明年", "尋", "會", "已而", "頃之", "至是"}
STOP = set(  # characters that cannot end a surname when gluing X+given name
    "其與及並而為以謂之於是時會言劾問愛稱諭用起皆坐誅殺在帝王公侯至自到從由當歲"
    "年月日先後若乃夫蓋故遂既未幾臨奉詔敕令賜貶斥罷逐執逮繫獄論罪郎都督將軍伯卿"
)
BAD_FLAGS = {"t", "m", "ns", "s", "nt"}                 # time / numeral / place words
WINDOW = 5


def load_section():
    lines = open(SOURCE, encoding="utf-8").read().splitlines()
    start = next(i for i, l in enumerate(lines) if "作《奸臣傳》" in l)
    end = next(i for i in range(start + 1, len(lines)) if re.match(r"^卷", lines[i]))
    return [l for l in lines[start:end] if l.strip()]


def full_head(line):
    m = re.match(rf"^([{HAN}]{{2,3}})，(?:字[{HAN}]{{1,3}}[，。]|[{HAN}]{{1,4}}人。)", line)
    return m.group(1) if m else None


def resolve_short(t, window, last_main, text):
    """Resolve an attached short name (e.g. 麟 / 世蕃) to its full name."""
    for p in window:  # list rule: 「如紀綱、馬麟、丁玨、秦政學、趙緯、李芳，皆以傾險聞」
        for m in re.finditer(rf"如([^。；]{{1,40}}?)[，。]", p):
            for item in re.split("[、]", m.group(1)):
                if re.fullmatch(rf"[{HAN}]{{2,3}}", item) and item.endswith(t):
                    return item
    if len(t) >= 2:  # mention rule: 「與懷寧阮大鋮同中進士」
        for p in window:
            for m in re.finditer(rf"([{HAN}])" + re.escape(t), p):
                pre = m.group(1)
                if pre not in STOP | KIN | NUM and text.count(pre + t) >= 2:
                    return pre + t
        if last_main and re.search(rf"[{''.join(KIN)}]" + re.escape(t), "".join(window)):
            return last_main[0] + t  # 其子世蕃 inside 嚴嵩's bio → 嚴世蕃
    return None


def extract(section):
    text = "".join(section)
    flags = {w: f for w, f in pseg.cut(text)}
    heads = {h for l in section if (h := full_head(l))}
    roster, last_main = [], None

    def add(name, status):
        nonlocal last_main
        for j, (n, s) in enumerate(roster):
            if n == name:
                if status == "本傳" and s == "附傳":  # own head paragraph found later
                    roster[j] = (name, "本傳")
                    last_main = name
                return False
        roster.append((name, status))
        if status == "本傳":
            last_main = name
        return True

    for i, line in enumerate(section):
        window = section[max(0, i - WINDOW):i]
        head = full_head(line)
        if head:
            if len(head) == 2:  # 2-char attached entry such as 昌時
                longer = resolve_short(head, window, None, text)
                if longer and not any(n.endswith(head) and n != head for n, _ in roster):
                    add(longer, "附傳")
                    continue
            add(head, "本傳")
            continue
        for t in (line[:2], line[:1]):
            if not re.fullmatch(rf"[{HAN}]{{{len(t)}}}", t):
                continue
            if any(n.endswith(t) for n, _ in roster) or t in heads:
                break
            if t[0] in set("一二三四五六七八九十百千萬零兩") or t in CONT or flags.get(t, "x") in BAD_FLAGS:
                break
            full = resolve_short(t, window, last_main, text)
            if full and add(full, "附傳"):
                break

    if re.search(r"[塗涂]節", text):  # named only inside 胡惟庸/陳寧's biographies
        roster = [r for r in roster if r != ("塗節", "附傳")]
        roster.insert(2, ("塗節", "附傳"))
    return roster, flags


def main():
    section = load_section()
    text = "".join(section)
    roster, flags = extract(section)
    nr_names = {w for w, f in flags.items() if f.startswith("nr")}

    report = [f"明史·奸臣傳（卷三百〇八）共得 {len(roster)} 人", "", "姓名\t身分\t原文次數\tjieba人名標記"]
    for name, status in roster:
        report.append(f"{name}\t{status}\t{text.count(name)}\t{'是' if name in nr_names else '否'}")
    print("\n".join(report))
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write("\n".join(report) + "\n")


if __name__ == "__main__":
    main()
