import pytest

from core.dice import Dice


def test_roll():
    threedee6 = [Dice.roll('3d6') for i in range(100)]
    assert(max(threedee6) <= 18)
    assert(min(threedee6) >= 3)

    deeeightplustwo = [Dice.roll('1d8+2') for i in range(100)]
    assert(max(deeeightplustwo) <= 10)
    assert(min(deeeightplustwo) >= 3)

def test_xroll():

    assert(Dice.xroll(1) == 1)
    assert(Dice.xroll(10) == 10)
    assert(Dice.xroll(True) == None)

    threedee6 = [Dice.xroll('3d6') for i in range(100)]
    assert(max(threedee6) <= 18)
    assert(min(threedee6) >= 3)