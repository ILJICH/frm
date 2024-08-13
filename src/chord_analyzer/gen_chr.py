import math


def simplify(ratio):
    n, d = ratio
    gcd = math.gcd(n, d)
    while gcd > 1:
        n //= gcd
        d //= gcd
        gcd = math.gcd(n, d)
    return n, d


def gen_interval(program, freq, items):
    print("a a0 0 200")
    print("a a1 1 a0:3/2")
    print(f"program {program} a0 a1")
    print("p a0")
    print("sleep 2")
    prev = 0
    for n, den in items:
        print("s a1")
        print(f"c a1 a0:{n}/{den}")
        freq_mul = n/den
        if prev != 0:
            print(f"# freq_total: {freq_mul*freq} freq_mul: {freq_mul} delta: {math.log2(freq_mul/prev)}")
        prev = freq
        print("ap")
        print("sleep 2")
    print("as")


def same_den(den, start=1, end=0):
    if end == 0:
        end = 4*den+start
    return ((n, den) for n in range(start, end))


def scale(dens=(2, 5, 7, 9), limit=4):
    all_intervals = []
    seen = set()
    for den in dens:
        for item in same_den(den, 1, limit*den+1):
            if item is None:
                continue
            n, d = simplify(item)
            if (n, d) not in seen:
                all_intervals.append((n, d))
                seen.add((n, d))

    all_intervals.sort(key=lambda x: x[0]/x[1])
    return all_intervals

if __name__ == "__main__":
    gen_interval(82, 220, scale((2, 3, 4, 5), 3))
