from collections import defaultdict
from operator import itemgetter

import pandas as pd
import matplotlib.pyplot as plt


def cmp(a, b):
    if a > b:
        return 1
    if a < b:
        return -1
    return 0


def bucketize(data, key_name, step=0.01):
    buckets = defaultdict(list)
    for _, row in data.iterrows():
        x = row[key_name]
        bucket = x / step
        buckets[bucket].append((x, row))
    return buckets


def get_min_data(filename='min_interval.res', header=('instrument', 'n', 'd', 'freq_1', 'freq_2', 'answer')):
    data = pd.read_csv(
        filename,
        header=None,
        names=header
    )
    gr = pd.DataFrame()
    gr["delta"] = data.apply(lambda r: abs(1 - r["n"]/r["d"]), axis=1)
    gr["correct"] = data.apply(lambda r: int(cmp(r["n"], r["d"]) == r["answer"]), axis=1)
    gr["n"] = data["n"]
    gr["d"] = data["d"]
    gr["freq"] = data["freq_1"]
    r = []
    for k, values in bucketize(gr, "delta").items():
        r.append((k, sum(v[1]["correct"] for v in values)/len(values)))
    return pd.DataFrame(r, columns=("ratio", "result")).sort_values(by="ratio")

def get_max_data(filename='max_interval.res', header=('instrument', 'n', 'd', 'freq_1', 'answer')):
    data = pd.read_csv(
        filename,
        header=None,
        names=header
    )
    gr = pd.DataFrame()
    gr["delta"] = data.apply(lambda r: abs(1 - r["n"]/r["d"]), axis=1)
    gr["is_interval"] = data.apply(lambda r: int(r["answer"]<0), axis=1)
    gr["n"] = data["n"]
    gr["d"] = data["d"]
    gr["freq"] = data["freq_1"]
    r = []
    for k, values in bucketize(gr, "delta").items():
        r.append((k, sum(v[1]["is_interval"] for v in values)/len(values)))
    return pd.DataFrame(r, columns=("ratio", "is_interval")).sort_values(by="ratio")


def into_buckets(data, step, x_getter, y_getter):
    buckets = defaultdict(list)
    for row in data:
        x = x_getter(row)
        y = y_getter(row)
        bucket = x // step
        buckets[bucket].append((x, y))
    return buckets


if __name__ == "__main__":
    df = get_max_data()
    plt.close('all')
    df.plot("ratio", "is_interval")
    plt.show()
