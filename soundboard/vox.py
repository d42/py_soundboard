import re
from itertools import chain


def _separate_decimal(words):
    replacements = {}
    for i, w in enumerate(words[1:], start=1):
        if w.isdigit() and words[i - 1] == ".":
            replacements[i] = w

    for pos, d in sorted(replacements.items(), reverse=True):
        words[pos:pos + 1] = list(d)

    return words


def voxify(sentence):
    special_replace = {".": "point"}

    def d(num):
        n = int(num)
        if n == 0:
            return "0"
        if n < 20:
            return str(num)
        elif n < 100:
            return str((n // 10) * 10) + " " + (d(n % 10) if n % 10 else "")
        elif n < 5000:
            return d(n // 100) + " hundred " + (d(n % 100) if n % 100 else "")
        elif n < 1000000:
            return d(n // 1000) + " thousand " + (d(n % 1000) if n % 1000 else "")
        elif n < 100000000:
            return (
                d(n // 1000000) + " million " + (d(n % 1000000) if n % 1000000 else "")
            )
        else:
            raise ValueError("THE VALUE IS TOO DAMN HIGH")

    words = [w for w in re.split(r"([ ]+|\.)", sentence) if w.strip()]
    words = _separate_decimal(words)
    words = [special_replace.get(w, w) for w in words]
    words = chain.from_iterable(d(w).split() if w.isdigit() else [w] for w in words)

    return [f"vox/{w}.wav".lower() for w in words]
