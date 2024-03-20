import yaml
import random

from schema import Schema, And, Or, Optional

'''
  Just a reminder that these are just definitions not the entities themselves

  There might be a better name than model because of that but its not coming to me atm
'''


class Model:

    _records = []

    _schema = {}

    # Source yaml file for this model
    _source = ''

    @classmethod
    def load(self):
        # print('--- Model Load - ' + self._source)
        # gotta reset this so we don't "borrow" the parent class's copy
        self._records = []
        if self._source != '':
            handle = open('definitions/' + self._source, 'r')
            for r in yaml.safe_load_all(handle):
                self._records.append(self(self._schema.validate(r)))
        else:
            raise ValueError('Model missing _source value - {}'.format(self.__name__))

    @classmethod
    def all(self):
        return self._records

    @classmethod
    def find(self, id):
        if len(self._records) == 0:
            self.load()
        for r in self._records:
            if r.code == id:
                return r
        raise ValueError('Asked for missing {} with id: {}'.format(self._source, id))

    @classmethod
    def random(self):
        if len(self._records) == 0:
            self.load()
        return random.choice(self._records)

    def __init__(self, props):
        # TODO: maybe complain if we've got a duplicate ID/code/whatev
        for prop in props:
            setattr(self, prop, props[prop])


class Moves(Model):

    _source = 'moves.yaml'

    _schema = Schema({
            'name': And(str, len),
            'code': And(str, len),
            'type': Or('consequence', 'instant', 'onesy'),
            'target': Or('any', 'melee', 'ranged', 'self', 'magic'),
            'test': And(str, len),
            Optional('effect'): {
                Optional('max targets'): And(int, lambda n: n > 0),
                Optional('status'): Or(str, [str]),
                Optional('damage'): And(int, lambda n: n > 0),
                Optional('duration'): And(int, lambda n: n > 0),
                Optional('special'): str
            },
            Optional('consequence'): {
                Optional('max targets'): And(int, lambda n: n > 0),
                Optional('status'): Or(str, [str]),
                Optional('duration'): And(int, lambda n: n > 0),
                Optional('damage'): And(int, lambda n: n > 0),
                Optional('special'): str
            }
        })

    def __str__(self):
        return 'Move ({})'.format(self.code)

    def __repr__(self):
        return 'Move ({})'.format(self.code)


class Critter(Model):
    pass


class Delver(Critter):
    pass


class Monsters(Critter):

    _source = 'monsters.yaml'

    _schema = Schema({
            'name': And(str, len),
            'category': And(str, len),
            'hp': And(int, lambda h: h > 0),
            'traits': And(lambda t: len(t) == 3, [str]),
            # moves needs to be rejiggered to include weights, so lets not define anything specific yet
            'moves': [str]
        })

    def __repr__(self):
        return 'Monster ({})'.format(self.name)

class Classes(Model):
    _source = 'classes.yaml'

    _schema = Schema({
            'name': And(str, len),
            'hp': And(int, lambda h: h > 0),
            'moves': [str]
        })

class Stocks(Model):
    _source = 'stocks.yaml'

    _schema = Schema({
            'name': And(str, len)
        })


if __name__ == "__main__":

    print('Moves')
    Moves.load()

    print('Monsters')
    Monsters.load()

    for monster in Monsters.all():
        for move in monster.moves:
            Moves.find(move)

    allStatus = []
    for move in Moves.all():
        examine = {}
        if move.type == 'consequence':
            examine = move.consequence
        elif move.type == 'instant':
            examine = move.effect
        else:
            continue

        x = examine.get('status', False)
        if type(x) == str:
            allStatus.append(x)
        elif type(x) == list:
            allStatus = allStatus + x
        else:
            pass

    print('All recorded statuses: {}'.format(set(allStatus)))

    print(' --- ')


    print(Monsters.all())
    print(Moves.all())