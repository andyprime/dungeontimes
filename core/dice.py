import random

class Dice:

    @classmethod
    def roll(self, s):
        # right now this just handles single die pools with one optional modifier
        # aka 3d6, or 3d6+1 are handled
        # this is really basic for expedience and does not handle bad input at all

        base = s
        plus = 0
        minus = 0
        if '+' in base:
            base, plus = base.split('+')
        if '-' in base:
            base, minus = base.split('-')

        num, size = base.split('d')

        roll = self.d(int(num), int(size))

        fin = roll + int(plus) - int(minus)

        return fin

    @classmethod
    def d(self, n, size=None):
        if size is None:
            return random.randint(1, n)
        else:
            total = 0
            for i in range(1, n + 1):
                total += random.randint(1, size)
            return total

if __name__ == "__main__":

    print('Test d6')
    for i in range(1,10):
        print(Dice.roll('1d6'))

    print('')
    print('Test 3d6')

    for i in range(1,10):
        print(Dice.roll('3d6'))

    print('')
    print('Test 2d6+6')

    for i in range(1,10):
        print(Dice.roll('2d6+6'))

    print('')
    print('Test 3d6-1')

    for i in range(1,10):
        print(Dice.roll('3d6-1'))