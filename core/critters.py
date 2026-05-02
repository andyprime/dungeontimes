import json
import random
import uuid

import core.strings as strings
from core.dice import Dice
from core.mdb import Persister
import definitions.model as model

class Creature(Persister):

    ATTRIBUTES = []

    @classmethod
    def _build_attr(self):
        return {attr: Dice.roll('3d6') for attr in self.ATTRIBUTES}

    def __init__(self):
        self.status = []

    def generateInitiative(self):
        return Dice.roll('1d20')

    def __str__(self):
        return self.name + ', ' + self.stock + ' (' + str(self.currenthp) + '/' + str(self.maxhp) +')'

    def canAct(self):
        return self.currenthp > 0

    def hasStatus(self, statusCode):
        for status in self.status:
            if status.get('code') == statusCode:
                return True
        return False

    def tickStatus(self):
        for status in self.status:
            if status['duration'] == 1:
                self.status.remove(status)
            else:
                status['duration'] -= 1

    def clearStatus(self):
        self.status = []

    def apply_damage(self, damage_count: int):
        old = self.currenthp
        self.currenthp = self.currenthp - damage_count
        if self.currenthp < 0:
            self.currenthp = 0

    def apply_healing(self, healing: int):
        self.currenthp = min(self.maxhp, self.currenthp + healing)

    def applyStatus(self, status, half=False):
        duration = Dice.roll('1d4+2')
        if half:
            duration = max(1, int(duration / 2))
        for s in self.status:
            if s['code'] == status:
                s['duration'] += duration
                return
        self.status.append({
                'code': status,
                'duration': duration
            })

    def healthCheck(self):
        if self.currenthp == 0:
            return 'dead'
        elif self.currenthp < self.currenthp / 2:
            return 'injured'
        else:
            return 'mostly ok'

    def recuperate(self):
        self.currenthp = self.maxhp
        self.clearStatus()

    def attribute(self, name):
        return {
            'base': self.attr[name],
            'current': self.calc_attr(name)
        }

    def attributes(self):
        return { name: self.attribute(name) for name in type(self).ATTRIBUTES}

    def calc_attr(self, name):
        # currently we're not modifying these but we will soon
        return self.attr[name]

    def moves(self):
        pass

    # To be implemented by children. Return a 2-tuple of ints 0-100 that indicate the partial and full success thresholds for the given test.
    # The roll is d100 (1-100) trying to roll above or equal to the threshold numbers.
    # The first number is the partial threshold, it will always be lower than the full threshold
    # The second tuple element is the full threshold
    # Example: if the tuple is (45, 75) a failure is a roll of 1-44, a partial success is 45-74 and a full is 75-100
    def testThresholds(self, test):
        pass

    def statusString(self):
        t = '['
        x = []
        for s in self.status:
            x.append('({} {})'.format(s['code'], str(s['duration'])))
        t += ','.join(x)
        t += ']'
        return t

class Delver(Creature):

    MAX_TOOLS = 2
    ATTRIBUTES = ['muscularity', 'prowess', 'pendantry', 'diligence', 'cool', 'guile', 'obduracy', 'pizazz']

    @classmethod
    def random(self):
        return Delver(strings.StringTool.random('regular_names'), model.Stocks.random(), model.Classes.random())

    @classmethod
    def random_hobbies(self):
        hobbies = [strings.StringTool.random('hobbies')]
        if Dice.roll('1d2') == 2:
            hobbies.append(strings.StringTool.random('hobbies'))
        if Dice.roll('1d2') == 2:
            hobbies.append(strings.StringTool.random('hobbies'))
        return list(set(hobbies))


    def __init__(self, name=None, stock=None, job=None):
        super().__init__()

        self.name = name
        self.gear_priority = random.choice(['armor', 'style'])
        self.stock = stock.name
        self.job = job
        self.maxhp = job.hp
        self.currenthp = job.hp
        self.id = str(uuid.uuid1())
        self.encumberence = 10
        self.inventory = []
        self.wealth = 0
        self.lifetime_wealth = 0
        self.attr = Delver._build_attr()
        self.gear = {}
        self.tools = []
        self.minutia = {
            'hobbies': Delver.random_hobbies(),
            'sign': strings.StringTool.random('astrology')
        }

        self.team = None # temp code for battles

    def __str__(self):
        return self.name + ', ' + self.stock + ', ' + self.job.name + ' (' + str(self.currenthp) + '/' + str(self.maxhp) +')'

    def __repr__(self):
        return self.name + ', ' + self.stock + ', ' + self.job.name + ' (' + str(self.currenthp) + '/' + str(self.maxhp) +')'

    def moves(self):
        moves = []
        for move in self.job.moves:
            moves.append(model.Moves.find(move))

        for tool in self.tools:
            moves.append(model.Moves.find(tool.grants))
            
        return moves

    def testThresholds(self, test):
        return (33, 66)
        
    def getSpells(self):

        spellIds = []
        if self.job.startingSpells:
            spellIds = self.job.startingSpells

        # TODO - include any learned spells

        spells = []

        for id in spellIds:
            spells.append(model.Spells.find(id))

        return spells

    def has_loot(self):
        return any([ True for item in self.inventory if item.useless() ])

    def will_carouse(self):
        return self.wealth > 0

    def will_shop(self):
        return self.wealth > 0

    def add_wealth(self, amt):
        self.wealth += amt
        self.lifetime_wealth += amt

    def spend_wealth(self, amt):
        if amt <= self.wealth:
            self.wealth -= amt
        else:
            raise ValueError('Attempt to spend {} wealth when only {} is present.'.format(amt, self.wealth))

    def can_hold(self, item):
        return sum([i.weight for i in self.inventory]) + item.weight <= self.encumberence

    def will_use(self, item):
        if item.wearable():
            slot = item.slot
            # for now, if we don't have any gear in that slot, go for it
            if not self.gear.get(slot, False):
                return True
            x = self.evaluate_gear(item)
            y = self.evaluate_gear(self.gear[slot])
            if x > y:
                return True

        if item.tool():
            if len(self.tools) < Delver.MAX_TOOLS:
                return True
            x = self.evaluate_gear(item)

            # for the moment we're going to return the tool itself so that later steps can know which tool to replace
            for t in self.tools:
                y = self.evaluate_gear(t)
                if x > y:
                    return t

        return False

    def will_buy(self, item):
        if item.value > self.wealth:
            return False

        if item.consumable():
            # consumables
            return self.can_hold(item) and sum([i.weight for i in self.inventory if i.consumable()]) < self.encumberence / 2
        elif item.wearable() or item.tool():
            return self.will_use(item)
        else:
            # this shouldn't happen but just in case
            return False

    def purchase(self, item, replace=None):
        if item.value > self.wealth:
            raise ValueError('Delver {} spent more money then they had.'.format(self.name))

        self.wealth = int(self.wealth - item.value)
        if item.consumable():
            self.give(item)
        elif item.wearable() or item.tool():
            self.wear(item, replace)

    # this returns a numeric value that indicates how good this delver considers this item
    # note that this function is not intended to be consistent, as in there is no garuantee
    # that the same item will always return the same number
    def evaluate_gear(self, item):
        value = 0
        if item.wearable():
            props = ['armor', 'style']
        else:
            props = ['power', 'style']
        # currently we're only deciding between armor and style
        for prop in props:
            if prop == self.gear_priority:
                value += item.effect[prop] * random.uniform(1.5, 1.8)
            else:
                value += item.effect[prop] * random.uniform(0.6, 0.75)

        return value

    def wear(self, item, replace=None):
        if item.wearable():
            self.gear[item.slot] = item
        elif item.tool():
            print('Tool equip, replace: ', replace)
            if replace:
                self.tools.remove(replace)
            self.tools.append(item)

    def give(self, item):
        self.inventory.append(item)

    def data_format(self):
        return {
            'id': self.id,
            'name': self.name,
            'stock': self.stock,
            'job': self.job.code,
            'maxhp': self.maxhp,
            'currenthp': self.currenthp,
            'attributes': self.attributes(),
            'tools': [t.data_format() for t in self.tools],
            'gear': [i.data_format() for i in self.gear.values()],
            'inventory': [i.data_format() for i in self.inventory],
            'minutia': self.minutia
        }

    def serialize(self, stringify=False):
        c = {
            'id': self.id,
            'name': self.name,
            'stock': self.stock,
            'job': self.job.code,
            'maxhp': self.maxhp,
            'currenthp': self.currenthp
        }

        if stringify:
            return json.dumps(c)
        else:
            return c

class Hireling(Creature):

    @classmethod
    def generate(self, maxquality):
        return Hireling()

    def __init__(self):
        super().__init__()

        self.id = str(uuid.uuid1())
        self.name = strings.StringTool.random('regular_names')
        self.stock = model.Stocks.random().name
        self.maxhp = 10
        self.currenthp = 10
        self.encumberence = 10
        self.inventory = []

    def data_format(self):
        return {
            'id': self.id,
            'name': self.name,
            'profession': 'hireling'
        }

class Monster(Creature):

    # monsters don't need proper UUIDs so they can just have an internally incrementer
    _id = 0
    @classmethod
    def idgen(self):
        self._id += 1
        return 'm{}'.format(self._id)

    @classmethod
    def idreset(self):
        self._id = 0

    @classmethod
    def random(self):
        # return Monster(template=model.Monsters.random())
        return Monster(model.Monsters.random())

    def __init__(self, template=None, serialized=None):
        super().__init__()

        if serialized:
            self._template = model.Monsters.find(serialized['t'])
            self.name = serialized['n']
            self.stock = self._template.name
            self.maxhp = serialized['mhp']
            self.currenthp = serialized['chp']
        else:
            self._template = template
            self.name = strings.StringTool.random('monster_' + template.category)
            self.stock  = template.name
            self.maxhp = template.hp
            self.currenthp = template.hp
        self.id = Monster.idgen()

    def moves(self):
        moves = []
        for move in self._template.moves:
            moves.append(model.Moves.find(move))
        return moves

    def testThresholds(self, test):
        return (60, 80)

    def serialize(self, stringify=False):
        c = {
            'id': self.id,
            'n': self.name,
            't': self._template.code,
            'mhp': self.maxhp,
            'chp': self.currenthp
        }
        if stringify:
            return json.dumps(c)
        else:
            return c

    def __str__(self):
        return self.name + ', ' + self.stock + ', ' + ' (' + str(self.currenthp) + '/' + str(self.maxhp) +')'

    def __repr__(self):
        return self.name + ', ' + self.stock + ', ' + ' (' + str(self.currenthp) + '/' + str(self.maxhp) +')'


class Band(Persister):

    def __init__(self):
        self.id = str(uuid.uuid1())
        self.name = strings.StringTool.random('band_names')
        self.members = []
        self.completed = 0
        # wealth and lifetime wealth are the same thing until band level acquisitions become a thing
        self.wealth = 0
        self.lifetime_wealth = 0
        self.active = True
        self.last_exp = None

    def has_money(self):
        return [d for d in self.members if d.wealth > 0]

    def data_format(self):
        return {
            'id': self.id,
            'name': self.name,
            'members': [m.id for m in self.members],
            'wealth': self.wealth,
            'lifetime_wealth': self.lifetime_wealth,
            'active': self.active
        }

    def add_wealth(self, amt):
        self.wealth += amt
        self.lifetime_wealth += amt

    def spend_wealth(self, amt):
        if amt < self.wealth:
            self.wealth -= amt
        else:
            raise ValueError('Attempt to spend {} wealth when only {} is present.'.format(amt, self.wealth))

    def has_loot(self):
        return any([True for mem in self.members if mem.has_loot()])

    def size(self):
        return len(self.members)

    def get(self, id):
        return next(m for m in self.members if m.id == id)

    def random_member(self, skip=[]):
        real = [member for member in self.members if member not in skip]
        return random.choice(real)

    def __str__(self):
        return '{} ({})'.format(self.name, self.id)

    def __repr__(self):
        return '{} ({})'.format(self.name, self.id)