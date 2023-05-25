import random

class Dice:

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
    def between(self, low, high):
        return random.randint(low, high)

if __name__ == "__main__":


    print('Test d6')
    for i in range(1,10):
        print(Dice.d(6))

    print('')
    print('Test 3d6')

    print(range(1, 6))
    for i in range(1,10):
        print(Dice.d(3, 6))