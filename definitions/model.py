import yaml
from schema import Schema, And, Or, Optional

class Model:

    _records = []

    _schema = {}

    # Source yaml file for this model
    _source = ''

    @classmethod
    def load(self):
        # gotta reset this so we don't "borrow" the parent class's copy
        self._records = []
        if self._source != '':
            handle = open(self._source, 'r')
            for r in yaml.safe_load_all(handle):
                self._records.append(self(self._schema.validate(r)))

    @classmethod
    def all(self):
        return self._records

    @classmethod
    def find(self, id):
        for r in self._records:
            if r.get('code', None) == id:
                return r
        return None

    def __init__(self, props):
        # TODO: maybe complain if we've got a duplicate ID/code/whatev
        for prop in props:
            setattr(self, prop, props[prop])


class Moves(Model):

    _source = 'moves.yaml'

    _schema = Schema({
            'name': And(str, len),
            'code': And(str, len),
            'type': Or('consequence', 'instant', 'persist'),
            'target': Or('any', 'melee', 'ranged', 'self'),
            Optional('effect'): {
                Optional('max targets'): And(int, lambda n: n > 0),
                Optional('status'): Or(str, [str]),
                Optional('damage'): And(int, lambda n: n > 0),
                Optional('duration'): And(int, lambda n: n > 0)
            },
            Optional('consequence'): {
                Optional('max targets'): And(int, lambda n: n > 0),
                Optional('status'): Or(str, [str]),
                Optional('damage'): And(int, lambda n: n > 0)
            }
        })

    def __str__(self):
        return 'Move ({})'.format(self.code)

    def __repr__(self):
        return 'Move ({})'.format(self.code)


class Monsters(Model):

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


if __name__ == "__main__":

    print('Moves')
    Moves.load()

    # print(Moves.all())


    print('Monsters')
    print(Monsters.all())

    Monsters.load()

    print(Monsters.all())

    print(Moves.all())