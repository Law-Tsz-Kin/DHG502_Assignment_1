import jieba
from collections import Counter

with open("明史.txt", encoding="utf-8") as f:
    text = f.read()

words = [w for w in jieba.cut(text) if w.strip() and len(w) > 1]
top10 = Counter(words).most_common(10)

with open("top10_words.txt", "w", encoding="utf-8") as f:
    for word, count in top10:
        f.write(f"{word}\t{count}\n")

for word, count in top10:
    print(f"{word}\t{count}")
