import numpy as np
import csv
import os
import os.path

# filename='data/bigfile.csv'
# rows = 1000000
# cols = 30

def generate_random_csv(filename, rows, cols, seed=1234):
    if os.path.exists(filename):
        return filename
    try:
        with open(filename, 'w') as csvfile:
            writer = csv.writer(csvfile)
            np.random.seed(seed=seed)
            for _ in range(0,rows):
                row=list(np.random.normal(loc=0.5, scale=0.8, size=cols))
                writer.writerow(row)
    except (KeyboardInterrupt, SystemExit):
        os.remove(filename)
        raise
    return filename



def generate_random_multivariate_normal_csv(filename, rows, seed=1234, header=None, reset=False):
    """
    Adapted from: https://github.com/e-/PANENE/blob/master/examples/kernel_density/online.py
    Author: Jaemin Jo
    Date: February 2019
    """
    if isinstance(filename, str) and os.path.exists(filename) and not reset:
        return filename
    def mv(n, mean, cov):
        return np.random.multivariate_normal(mean, cov, size=(n)).astype(np.float32)
    N = rows//3
    X = np.concatenate((
        mv(N, [0.1, 0.3], [[0.01, 0], [0, 0.09]]),
        mv(N, [0.7, 0.5], [[0.04, 0], [0, 0.01]]),
        mv(N, [-0.4, -0.3], [[0.09, 0.04], [0.04, 0.02]])
        ), axis=0)
    np.random.shuffle(X)
    kw = {} if header is None else dict(header=header, comments='')
    np.savetxt(filename, X, delimiter=',', **kw)
    return filename
    
