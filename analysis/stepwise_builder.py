import math

import matplotlib.pyplot as plt
import numpy as np

'''
if x >= 0 & x < 20 [20] then f 1.75x + 0
if x >= 20 & x < 38 [18] then f 1.1x + 13.0
if x >= 38 & x < 53 [15] then f 0.7x + 28.200000000000006
if x >= 53 & x < 68 [15] then f 0.5x + 38.8
if x >= 68 & x < 80 [12] then f 0.4x + 45.599999999999994
if x >= 80 & x < 90 [10] then f 0.35x + 49.599999999999994
if x >= 90 & x < 100 [10] then f 0.3x + 54.099999999999994
if x >= 100 & x < 120 [20] then f 0.29500000000000026x + 54.599999999999966
if x >= 120 [0] then f 90
'''
source = {
    'scale': 100,
    'min': 0,
    'max': 90,
    'ranges': [(1.75, 0, 20), (1.1, 20, 38), (0.7, 38, 53), (0.5, 53, 68), (0.4, 68, 80), (0.35, 80, 90), (0.3, 90, 100), (0.08, 100, 120)]
}

'''
if x >= 0 & x < 4 [4] then f 1x + 0
if x >= 4 & x < 7 [3] then f 0.9x + 0.3999999999999999
if x >= 7 & x < 10 [3] then f 0.7x + 1.7999999999999998
if x >= 10 & x < 15 [5] then f 0.5x + 3.8000000000000007
if x >= 15 & x < 20 [5] then f 0.4x + 5.300000000000001
if x >= 20 & x < 30 [10] then f 0.4699999999999999x + 3.900000000000002
if x >= 30 [0] then f 18
'''
# source = {
#     'scale': 20,
#     'min': 0,
#     'max': 18,
#     'ranges': [(1, 0, 4), (0.9, 4, 7), (0.7, 7, 10), (0.5, 10, 15), (0.4, 15, 20), (0.1, 20, 30)]
# }

def identity(x):
    return x

def build_lammy(a, b):
    return lambda x: a*x + b

if __name__ == "__main__":

    if source['scale'] == 100:
        axis = np.arange(140, dtype=np.float64)
    elif source['scale'] == 20:
        axis = np.arange(40, dtype=np.float64)
    else:
        print('Not a supported axis')

    conditions = []
    cond_str = []
    lambdas = []
    lam_str = []

    for i in range(len(source['ranges'])):
        multiplier, start, stop = source['ranges'][i]
        
        # print(i, multiplier, start)

        if i == 0:
            c = (axis >= start) * (axis < stop)
            cs = f'x >= {start} & x < {stop}'

            b = 0
            if start * multiplier < source['min']:
                b = source['min'] - (start * multiplier)

            l = build_lammy(multiplier, b)
            ls = f'f {multiplier}x + {b}'

        elif i == len(source['ranges']) - 1:
            # last specified range will be forced to terminate on the specified max value
            c = (axis >= start) * (axis < stop)
            cs = f'x >= {start} & x < {stop}'

            last = lambdas[-1](start)
            next = source['max']

            slope = (next - last) / (stop - start)
            constant = last - (slope * start)

            l = build_lammy(slope, constant)
            ls = f'f {slope}x + {constant}'

        else:
            c = (axis >= start) * (axis < stop)
            cs = f'x >= {start} & x < {stop}'

            last = lambdas[-1](start)
            constant = last - start * multiplier
            l = build_lammy(multiplier, constant)
            ls = f'f {multiplier}x + {constant}'

        conditions.append(c)
        cond_str.append(cs)
        lambdas.append(l)
        lam_str.append(ls)

    # add static limit rule
    maxout = source['ranges'][-1][2]
    conditions.append(axis >= maxout)
    cond_str.append(f'x >= {maxout}')
    lambdas.append(build_lammy(0, source['max']))
    lam_str.append(f'f {source['max']}')


    fig, (ax1) = plt.subplots(1, 1, sharex=False, sharey=False)

    y100 = np.piecewise(axis, conditions, lambdas)
    ax1.plot(axis, identity(axis), label="x=y")
    ax1.plot(axis, np.full(axis.shape, source['scale']), label="max")
    ax1.plot(axis, y100, label="Ease 1")
    ax1.axhline(100, c='0.8')
    ax1.legend()

    for i in range(len(cond_str)):
        if i < len(source['ranges']):
            diff = source['ranges'][i][2] - source['ranges'][i][1]
        else:
            diff = 0
        print(f'if {cond_str[i]} [{diff}] then {lam_str[i]}')

    plt.show()

