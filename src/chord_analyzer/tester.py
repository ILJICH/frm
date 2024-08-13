import csv
from enum import Enum
from gen import gen_interval, scale
from random import shuffle, randint
import math
from functools import partial


class Choice(Enum):
    left = -1
    equal = 0
    right = 1


def read_input():
    match input('# z: left is more dissonant; x: unison; c: right is more dissonant: \n'):
        case 'z':
            return Choice.left
        case 'x':
            return Choice.equal
        case 'c':
            return Choice.right
        case _:
            return None


def read_custom_input(mapping, prompt):
    return mapping.get(input(prompt))


def midi_g(program):
    print("a a0 0 200")
    print("a a1 1 a0:3/2")
    print(f"program {program} a0 a1")
    while True:
        inp = yield
        if inp is None:
            break
        freq, n, den = inp
        print("as")
        print(f"c a0 {freq}")
        print(f"c a1 a0:{n}/{den}")
        print("ap")
    print("as")


def midi_g_sep(program):
    print("a a0 0 200")
    print("a a1 1 a0:3/2")
    print(f"program {program} a0 a1")
    while True:
        inp = yield
        if inp is None:
            break
        freq, n, den = inp
        print("as")
        print(f"c a0 {freq}")
        print(f"c a1 a0:{n}/{den}")
        print("as")
        print("p a0")
        print("sleep 2")
        print("as")
        print("p a1")
        print("sleep 2")
        print("as")
    print("as")


def output(filename):
    with open(filename, 'a+') as f:
        writer = csv.writer(f)
        while True:
            inp = yield
            if inp is None:
                break
            writer.writerow(inp)


def run_compare_intervals(instrument=82, freq=220, nums=(2, 3, 4, 5), scales=3):
    candidates_1 = scale(nums, scales)
    candidates_2 = scale(nums, scales)
    shuffle(candidates_1)
    shuffle(candidates_2)
    g = midi_g(82)
    next(g)
    o = output('1.res')
    next(o)
    for c1, c2 in zip(candidates_1, candidates_2):
        freq_1, freq_2 = randint(freq//2, freq*2), randint(freq//2, freq*2)
        while True:
            g.send((freq_1, *c1))
            print('sleep 1')
            g.send((freq_2, *c2))
            inp = read_input()
            print(f'# {inp}')
            if inp is not None:
                o.send([
                    instrument,
                    c1[0], c1[1], 1.0*c1[0]/c1[1]*freq,
                    c2[0], c2[1], 1.0*c2[0]/c2[1]*freq,
                    inp
                ])
                break
    print('# All done!')


def run_min_interval(
    instrument=82, min_freq=110, max_freq=440,
    d_nums=(1, 2, 3, 4, -1, -2, -3, -4), dens=(128, ),
    cutoff_min=0.5, cutoff_max=1.5
):
    candidates = [(d+d_n, d) for d_n in d_nums for d in dens]
    shuffle(candidates)
    g = midi_g_sep(instrument)
    next(g)
    o = output('min_interval.res')
    next(o)
    rd = partial(
        read_custom_input,
        {
            'z': Choice.left,
            'x': Choice.equal,
            'c': Choice.right
        },
        '# z: first tone higer; x: unison; c: second tone higher\n'
    )

    running = True
    for candidate in candidates:
        if not running:
            try:
                g.send(None)
            except StopIteration:
                pass
            break
        freq = randint(min_freq, max_freq)
        n, d = candidate
        if randint(0, 1):
            n, d = d, n
        if not (cutoff_min <= n/d <= cutoff_max):
            if not (cutoff_min <= d/n <= cutoff_max):
                print(f'# Skipping {n}/{d} because false {cutoff_min} <= {n/d} <= {cutoff_max}')
                continue
            n, d = d, n
        while True:
            g.send((freq, n, d))
            try:
                inp = rd()
            except KeyboardInterrupt:
                print('# exiting')
                running = False
                break
            if inp is not None:
                o.send([
                    instrument,
                    n, d, freq, 1.0*n/d*freq,
                    inp.value
                ])
                break
    print('# All done!')


def run_max_interval(
    instrument=82, min_freq=110, max_freq=440,
    nums=range(17, 63), dens=(16, )
):
    candidates = [(n, d) for n in nums for d in dens]
    shuffle(candidates)
    g = midi_g(instrument)
    next(g)
    o = output('max_interval.res')
    next(o)
    rd = partial(
        read_custom_input,
        {
            'z': Choice.left,
            'c': Choice.right
        },
        '# z: sounds like an interval; c: sounds like two notes\n'
    )

    running = True
    for n, d in candidates:
        if not running:
            try:
                g.send(None)
            except StopIteration:
                pass
            break
        freq = randint(min_freq, max_freq)
        while True:
            g.send((freq, n, d))
            try:
                inp = rd()
            except KeyboardInterrupt:
                print('# exiting')
                running = False
                break
            if inp is not None:
                o.send([
                    instrument,
                    n, d, freq, 1.0*n/d*freq,
                    inp.value
                ])
                break
    print('# All done!')


if __name__ == "__main__":
    run_max_interval()
