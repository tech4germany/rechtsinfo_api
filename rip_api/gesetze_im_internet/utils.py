import itertools


# From: https://docs.python.org/3/library/itertools.html?highlight=itertools#itertools-recipes
def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return itertools.zip_longest(*args, fillvalue=fillvalue)


def chunk_string(string, length):
    return ["".join(chunk) for chunk in grouper(string, length)]
