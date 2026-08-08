import random

class Dice:

    EASE_MAP = {
        'low': 2,
        'high': 1
    }

    @classmethod
    def roll(self, s: str) -> int:
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
    def xroll(self, i: int | str) -> int:
        # a convenience function for parsing values that might either be a static number
        # or a die roll syntax string
        if type(i) == int:
            return i
        elif type(i) == str:
            return Dice.roll(i)
        else:
            return None

    @classmethod
    def boundedgamma(self, low, high, ease='low'):
        # this is all a little over-described in case I need to revisit
        # side note/todo, the larger the range requested the more likely the ceiling will 
        # inflate the occurence of the highest result
        shape = 1
        scale = Dice.EASE_MAP[ease]
        expected_mean = shape * scale
        variance = shape*(scale*scale) # variance is std-dev^2
        ceiling = expected_mean + 3*variance
        x = min(random.gammavariate(shape, scale), ceiling - 0.1)

        range_size = high - low + 1
        band_size = ceiling / range_size
        p = x / band_size
        band = int(p)
        result = low + band

        return result

    @classmethod
    def d(self, n, size=None):
        if size is None:
            return random.randint(1, n)
        else:
            total = 0
            for i in range(1, n + 1):
                total += random.randint(1, size)
            return total

    @classmethod
    def perform_test_100(self, undiminished_value):
        chance = Dice.diminish100(undiminished_value)

        success = 0
        total = 0

        while total < chance:
            total += Dice.roll('1d100')
            if total < chance:
                success += 1

        return success


    @classmethod
    def diminish100(self, x):
        if x < 0:
            return 0
        elif x >= 0 and x < 20:
            return 1.75*x
        elif x >= 20 and x < 38:
            return 1.1*x + 13.0
        elif x >= 38 and x < 53:
            return 0.7*x + 28.2
        elif x >= 53 and x < 68:
            return 0.5*x + 38.8
        elif x >= 68 and x < 80:
            return 0.4*x + 45.6
        elif x >= 80 and x < 90:
            return 0.35*x + 49.6
        elif x >= 90 and x < 100:
            return 0.3*x + 54.1
        elif x >= 100 and x < 120:
            return 0.295*x + 54.6
        elif x >= 120:
            return 90

if __name__ == "__main__":

    mean = 3
    nums = []
    total = 0
    runs = 10000
    for i in range(runs):
        x = Dice.boundedgamma(1, 3, 'high')
        nums.append(x)
        total += x

    print('Mean: {}'.format(total / len(nums)))
    print('Min: {}'.format(min(nums)))
    print('Max: {}'.format(max(nums)))

    breakdown = {}
    for n in nums:
        m = round(n)
        if(breakdown.get(m, False)):
            breakdown[m] += 1
        else:
            breakdown[m] = 1
    
    print('Base - ')
    for n, c in sorted(breakdown.items()):
        print('{}: {} - {}%'.format(n, c, round(c/runs * 100, 2)))

    print('')

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