import math

import matplotlib.pyplot as plt
import numpy as np


def identity(x):
    return x

def basic_diminish(x, n):
    return x / (x + n)

def adv_diminish(x, n, m):
    return (m * x) / (x + n)

def tiered_diminish(x):
    if x < 10:
        return basic_diminish(x, 2)
    else:
        return basic_diminish(x, 5)

def t1(x):
    return x

def t2(x):
    return .75*x + 2.5

def t3(x):
    return .5*x +6.5

def dostuff(x):
    return 2 * x

def build_lammy(a, b):
    return lambda x: a*x + b

def build_piecewise(axis, max, ease=1.0):

    # steps = int(len(axis) ** .5) * 2
    steps = 8
    spacing = int(len(axis) / steps)

    conditions = []
    cond_str = []
    lambdas = []
    lam_str = []

    for i in range(steps):
        start = spacing * i
        stop = spacing * (i + 1)

        if i == 0:
            c = axis < spacing
            cs = f'x < {spacing}'
            # l = build_lammy(1, 0)
            # ls = f'f 1x + 0'
            l = build_lammy(ease, 0)
            ls = f'f {ease}x + 0'

        elif i == steps - 1:
            c = axis >= start
            cs = f'x >= {start}'

            last = lambdas[-1](start)
            l = build_lammy(0, last)
            ls = f'f 0x + {last}'
            # l = build_lammy(0, max)
            # ls = f'f 0x + {max}'
        else:
            c = (axis >= start) * (axis < stop)
            cs = f'x >= {start} & x < {stop}'

            multiplier = ease / (i + 1)
            # multiplier = ease / i 

            print(f' {ease} / ({i} + 1) =', multiplier)

            last = lambdas[-1](start)
            constant = last - start * multiplier

            l = build_lammy(multiplier, constant)
            ls = f'f {multiplier}x + {constant}'

        conditions.append(c)
        cond_str.append(cs)
        lambdas.append(l)
        lam_str.append(ls)

        # either of these two methods exist to create a static binding for the current value of start
        # lambdas.append(lambda x, i=start: i)
        # lambdas.append(build_lammy(0, start))

    print(len(cond_str), cond_str)
    print(len(lam_str), lam_str)
    print('Max value - ', lambdas[-1](100))

    return (conditions, lambdas)


if __name__ == "__main__":

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, sharex=False, sharey=False)

    # xs = np.arange(40, dtype=np.float64)

    # cond20 = [xs < 10, (xs >= 10) * (xs < 20), (xs >= 20) * (xs < 30), (xs >= 30) * (xs < 55), xs >= 55]
    # yt20 = np.piecewise(xs, cond20, [lambda x: x, lambda x: .5*x + 5, lambda x: .25*x + 10, lambda x: .1*x + 14.5, 20])

    # ax.plot(xs, identity(xs), label="x=y")
    # ax.plot(xs, yt20, label='Manual')
    # ax.axhline(20, c='0.8')
    # # subplots seem to have locked graph limits
    # ax.set_xlim([0, 55])
    # ax.legend()

    # cond100 = [x100 < 16, (x100 >= 16) * (x100 < 35), (x100 >= 35) * (x100 < 70), (x100 >= 70) * (x100 < 90), (x100 >= 90) * (x100 < 110), x100 >= 110]
    # fn100   = [
    #     lambda x: 1.5*x,            # < 16      (24)
    #     lambda x: x + 8,            # 16 - 35   (43)
    #     lambda x: 0.8*x + 15,       # 35 - 70   (71)
    #     lambda x: 0.7*x + 22,       # 70 - 90   (85)
    #     lambda x: 0.5*x + 40,       # 90 - 110  (95)
    #     lambda x: 95
    # ]

    x100 = np.arange(120, dtype=np.float64)
    

    (cond100, fn100) = build_piecewise(x100, 98, 1)
    y100 = np.piecewise(x100, cond100, fn100)
    ax1.plot(x100, identity(x100), label="x=y")
    ax1.plot(x100, y100, label="Ease 1")
    ax1.axhline(100, c='0.8')
    ax1.legend()
    

    (condb, fnb) = build_piecewise(x100, 98, 2)
    y100b = np.piecewise(x100, condb, fnb)
    ax2.plot(x100, identity(x100), label="x=y")
    ax2.plot(x100, y100b, label="Ease 2")
    ax2.axhline(100, c='0.8')
    ax2.legend()


    (condc, fnc) = build_piecewise(x100, 98, 3)
    y100c = np.piecewise(x100, condc, fnc)
    ax3.plot(x100, identity(x100), label="x=y")
    ax3.plot(x100, y100c, label="Ease 3")
    ax3.axhline(100, c='0.8')
    ax3.legend()


    plt.show()