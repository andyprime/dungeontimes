import matplotlib.pyplot as plt
import numpy as np


def basic_diminish(x, n):
    return x / (x + n)

def adv_diminish(x, n, m):
    return (m * x) / (x + n)

def tiered_dimish(x):
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

if __name__ == "__main__":

    fig, (ax, ax2) = plt.subplots(2, 1, sharex=True)

    xs = np.arange(40, dtype=np.float64)

    #  doesn't taper off enough, quickly exceeds 20
    cond = [xs < 10, (xs < 16) * (xs >= 10), (xs >= 16)]
    yt = np.piecewise(xs, cond, [t1, t2, t3])

    ys1 = 20 * xs / (xs + 10)

    control = 20 * xs / (xs + 5)

    yc = np.piecewise(xs, [xs < 15, xs >= 15], [t1, lambda x: 20 * x / (x + 5)])

    ax.plot(xs, yt, label='Tiered')
    ax.axhline(20, c='0.8')
    ax.legend()

    ax2.axhline(20, c='0.8')
    ax2.plot(xs, ys1, label='Scaled 1')
    ax2.plot(xs, control, label="+5 Control")
    ax2.plot(xs, yc, label='Combo')
    ax2.legend()    

    # plt.plot(xs, ys)
    plt.show()