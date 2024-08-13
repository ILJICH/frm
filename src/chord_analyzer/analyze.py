from collections import defaultdict
import math
import numpy as np
from tabulate import tabulate


def simplify(ratio):
    n, d = ratio
    gcd = math.gcd(n, d)
    while gcd > 1:
        n //= gcd
        d //= gcd
        gcd = math.gcd(n, d)
    return n, d


def reduce(*harmonics):
    stack_a = sorted(harmonics)
    stack_b = []
    needs_run = True
    while needs_run:
        needs_run = False
        while stack_a:
            v = stack_a.pop()
            if len(stack_a) and v % 2 == 0 and stack_a[-1] == v - 1:
                _ = stack_a.pop()
                stack_b.append(v // 2)
                needs_run = True
            else:
                stack_b.append(v)
        stack_b.sort()
        stack_a, stack_b = stack_b, stack_a
    return stack_a 


def get_harmonics(n, d):
    return reduce(*list(range(d+1, n+1)))


def analyze(*ratios):
    a_n, a_d = zip(*ratios)
    input_nums = np.array(a_n)
    input_dens = np.array(a_d)
    output_nums = input_nums * input_dens.reshape(input_dens.size, 1)
    output_dens = input_dens * input_nums.reshape(input_nums.size, 1)
    func = np.vectorize(lambda x, y: simplify((x, y)))
    return func(output_nums, output_dens)


def sum_table(size=12, mode='ratio'):
    match mode:
        case 'ratio': func = lambda n, d: simplify((n, d))
        case 'harmonics': func = lambda n, d: ','.join(map(str, get_harmonics(*simplify((n, d)))))
    result = list(['-' for _ in range(size)] for _ in range(size))
    for i in range(size):
        for j in range(size):
            if j == 0:
                result[i][j] = func(i+1, max(1, i))
            elif i == 0:
                result[i][j] = func(j+1, max(1, j))
            else:
                r = func((i+1)*(j+1), i*j)
                result[i][j] = r if len(r) < 2 else '.'
    return result


def resolutions(size=12):
    result = defaultdict(list)
    for i in range(1, size+1):
        for j in range(i, size+1):
            n, d = i * j, (i - 1) * (j - 1)
            h = get_harmonics(*simplify((n, d)))
            if len(h) == 1:
                result[h[0]].append((i, j))
    return result


def print_sum_table(mode='harmonics'):
    print(tabulate(sum_table(mode)))


def print_resolutions(size):
    r = resolutions(size)
    for i in range(2, 17):
        print(f'{i}: {r[i]}')


def negative(h):
    return [-2] + get_harmonics(*simplify((2*(h-1), h)))


def print_negatives(size):
    for i in range(3, size+1):
        harmonics = ','.join(map(str, negative(i)))
        print(f'-{i} = {harmonics}')


print_resolutions(64)
print('\n', '*' * 64, '\n')
print(tabulate(sum_table(size=32, mode='harmonics')))
print('\n', '*' * 64, '\n')
print_negatives(16)
