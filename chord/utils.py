import hashlib


def hash_function(data: str, m: int):
    return int(hashlib.sha1(data.encode()).hexdigest(), 16) % (2 ** m)


def _inbetween(k: int, start: int, end: int) -> bool:
    if start < end:
        return start < k <= end
    else:  # The interval wraps around 0
        return start < k or k <= end
