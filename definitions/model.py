import yaml
import random

from schema import Schema, SchemaError, And, Or, Optional

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
                try:
                    self._records.append(self(self._schema.validate(r)))
                except SchemaError as e:
                    e.add_note('Troublesome record: {}'.format(r))
                    raise
        else:
            raise ValueError('Model missing _source value - {}'.format(self.__name__))

    @classmethod
    def all(self):
        if len(self._records) == 0:
            self.load()
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
    def random(self, filter=None):
        if len(self._records) == 0:
            self.load()
        if callable(filter):
            return random.choice(self.filter(filter))
        else:
            return random.choice(self._records)

    @classmethod
    def filter(self, callback):
        if callable(callback):
            return [r for r in self._records if callback(r)]
        else:
            raise ValueError('Can not filter with non-callable argument.')

    def __init__(self, props):
        # TODO: maybe complain if we've got a duplicate ID/code/whatev
        self.raw = props
        for prop in props:
            setattr(self, prop, props[prop])

class Moves(Model):

    COMBAT = 'combat'
    PASSIVE = 'passive'
    REST = 'rest'
    DOWNTIME = 'downtime'
    CONSEQUENCE = 'consequence'

    _source = 'moves.yaml'

    _schema = Schema({
            'name': And(str, len),
            'code': And(str, len),
            'type': Or('combat', 'consequence', 'rest', 'downtime', 'passive', 'spellcasting'),
            'target': Or('any', 'melee', 'ranged', 'self', 'magic', 'friendly', 'none'),
            'test': Or('none', {
                'primary': And(str, len),
                Optional('secondary'): And(str, len)
            }),
            Optional('resist'): {
                'primary': And(str, len),
                Optional('aux'): And(str, len)
            },
            Optional('when'): And(str, len),
            Optional('effect'): {
                Optional('max targets'): And(int, lambda n: n > 0),
                Optional('status'): Or(str, [str]),
                Optional('damage'): Or(And(str, len), And(int, lambda n: n > 0)),
                Optional('duration'): And(int, lambda n: n > 0),
                Optional('healing'): And(str, len),
                Optional('special'): str                
            },
            Optional('consequence'): {
                Optional('max targets'): And(int, lambda n: n > 0),
                Optional('status'): Or(str, [str]),
                Optional('duration'): And(int, lambda n: n > 0),
                Optional('damage'): Or(And(str, len), And(int, lambda n: n > 0)),
                Optional('special'): str
            },
            Optional('failure'): {
                Optional('damage'): Or(And(str, len), And(int, lambda n: n > 0)),
            },
            Optional('summon'): {
                'type': And(str, len),
                'rank': Or(int, And([int], lambda l: len(l) == 2)) 
            },
            Optional('bonus'): [ [str, int] ] # this isn't right
        })

    def valid(self, fellah):
        # fellah is the local standard term for a monster or delver
        fun = getattr(self, '_' + self.when)
        return fun(fellah)

    def _follower_cap(self, fellah):
        return fellah.follower_cap() > 0

    def __str__(self):
        return 'Move ({})'.format(self.code)

    def __repr__(self):
        return 'Move ({})'.format(self.code)

class Spells(Model):
    _source = 'spells.yaml'

    _schema = Schema({
            'code': And(str, len),
            'name': And(str, len),
            'target': [Or('self', 'team', 'opponent')],
            'effect': {
                Optional('damage'): And(int, lambda n: n > 0),
                Optional('status'): Or(str, [str]),
                Optional('duration'): And(int, lambda n: n > 0)
            }
        })

class Critter(Model):
    pass

class Monsters(Critter):

    _source = 'monsters.yaml'

    _schema = Schema({
            'name': And(str, len),
            'code': And(str, len),
            'category': And(str, len),
            'hp': And(int, lambda h: h > 0),
            'traits': And(lambda t: len(t) == 3, [str]),
            # moves needs to be rejiggered to include weights, so lets not define anything specific yet
            'moves': [str]
        })

    def __repr__(self):
        return 'Monster Model ({})'.format(self.name)

class Classes(Model):
    _source = 'classes.yaml'

    _schema = Schema({
            'name': And(str, len),
            'code': And(str, len),
            'hp': And(int, lambda h: h > 0),
            'moves': [str],
            Optional('tool'): And(str, len),
            Optional('gear'): And(str, len),
            Optional('startingSpells'): [str],
            Optional('tools', default=2): And(int, lambda h: h > 0),
            Optional('followers', default=1): And(int, lambda h: h > 0),
        })

class Stocks(Model):
    _source = 'stocks.yaml'

    _schema = Schema({
            'code': And(str, len),
            'name': And(str, len)
        })

class Gear(Model):
    _source = 'gear.yaml'

    _schema = Schema({
            'name': And(str, len),
            'code': And(str, len),
            'slot': Or('head', 'torso', 'hands', 'feet', 'back', 'waist'),
            'rarity': And(int, lambda n: n >= 0),
            'value': And(int, lambda n: n >= 0),
            'effect': {
                Optional('pass'): 'pass', # placeholder value
                Optional('style'): And(int, lambda n: n > 0),
                Optional('armor'): And(int, lambda n: n > 0),
                Optional('encumberance'): And(int, lambda n: n > 0),
                Optional('attribute'): [ And(str, len), And(int, lambda n: n > 0) ]
            }
        })

class GearMod(Model):
    _source = 'gearmods.yaml'

    _schema = Schema({
            'code': And(str, len),
            'rarity': And(int, lambda n: n >= 0),
            'name': {
                Optional('prefix'): And(str, len),
                Optional('postfix'): And(str, len)
            },
            'effect': {
                Optional('pass'): 'pass', # placeholder value
                Optional('value'): int,
                Optional('value_mod'): int,
                Optional('armor'): int,
                Optional('armor_mod'): int,
                Optional('style'): int,
                Optional('style_mod'): int,
                Optional('rarity'): int,
            }

        })

class Consumable(Model):
    _source = 'consumables.yaml'

    _schema = Schema({
            'name': And(str, len),
            'code': And(str, len),
            'rarity': And(int, lambda n: n >= 0),
            'value': And(int, lambda n: n >= 0),
            'application': Or('fast', 'slow'),
            'effect': {
                Optional('healing'): And(str, len),
                Optional('bonus_hp'): And(int, lambda n: n > 0)
            }
        })

class Tool(Model):
    _source = 'tools.yaml'

    _schema = Schema({
            'name': And(str, len),
            'code': And(str, len), 
            'rarity': And(int, lambda n: n >= 0),
            'value': And(int, lambda n: n >= 0),
            'type': Or('melee', 'ranged', 'arcane', 'light', 'general'),
            'size': And(str, len), 
            Optional('tags', default=[]): [str],
            'grants': Or([str], str),
            'effect': {
                'power': And(int, lambda n: n >= 0),
                Optional('style'): And(int, lambda n: n > 0),
            }
        })

class ToolMod(Model):
    _source = 'toolmods.yaml'

    _schema = Schema({
            'code': And(str, len),
            'rarity': And(int, lambda n: n >= 0),
            'name': {
                Optional('prefix'): And(str, len),
                Optional('postfix'): And(str, len)
            },
            Optional('requires'): And(str, len),
            'effect': {
                Optional('pass'): 'pass', # placeholder value
                Optional('value'): int,
                Optional('value_mod'): int,
                Optional('power'): int,
                Optional('power_mod'): int,
                Optional('style'): int,
                Optional('style_mod'): int,
                Optional('rarity'): int,
            }
        })

    @classmethod
    def random_for(self, t: Tool, rarity: int):
        tags = [t.type, t.size] + t.tags
        return self.random(lambda tm: tm.rarity <= rarity and (not hasattr(tm, 'requires') or tm.requires in tags))

class Follower(Model):
    _source = 'follower.yaml'

    _schema = Schema({
            'name': And(str, len),
            'code': And(str, len),
            'type': Or('undead', 'beast', 'doll', 'hireling', 'arcane', 'devil'),
            'rank': And(int, lambda n: n >= 0),
            'health': And(int, lambda n: n >= 0),
            'power': And(int, lambda n: n >= 0),
            'grants': Or([str], str),
            Optional('salary'): And(str, len)
        })

if __name__ == "__main__":

    print('Moves')
    Moves.load()

    print('Spells')
    Spells.load()

    print('Monsters')
    Monsters.load()

    print('Delvers')
    Classes.load()

    print('Gear')
    Gear.load()

    print('GearMod')
    GearMod.load()

    print('Consumable')
    Consumable.load()

    print('Tools')
    Tool.load()
