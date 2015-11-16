from itertools import chain


def voxify(sentence):
    def d(num):
        n = int(num)
        if n < 20:
            return str(num)
        elif n < 100:
            return str(((n // 10) * 10)) + ' ' + (d(n % 10) if n % 10 else '')
        elif n < 5000:
            return d(n // 100) + ' hundred ' + (d(n % 100) if n % 100 else '')
        elif n < 1000000:
            return d(n // 1000) + ' thousand ' + (d(n %
                                                    1000) if n %
                                                  1000 else '')

    words = chain.from_iterable(
        d(w).split()if w.isdigit() and w != '0'
        else [w]
        for w in sentence.split()
    )
    return ["vox/{}.wav".format(w) for w in words]
