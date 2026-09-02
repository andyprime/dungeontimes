import json
import random
import uuid

from enum import Enum

import core.strings as strings
from core.dice import Dice
from core.doodads import Tool
from core.mdb import Persister
import definitions.model as model

class Creature(Persister):

    CATEGORIES = ['MUSCULARITY', 'AGILITY', 'FACULTY', 'WISDOM', 'WILLPOWER', 'GUILE', 'TOUGHNESS', 'PIZAZZ']
    ATTRIBUTE_MAP = {
        'MUSCULARITY': ['BEEFINESS', 'ATHLETICISM', 'PUISSANCE', 'PLACEHOLDER'],
        'AGILITY': ['PROWESS', 'ADROITNESS', 'ELASTICITY', 'SPRYNESS'],
        'FACULTY': ['PEDANTRY', 'MENTALITY', 'PERSPICACITY', 'ERUDITION'],
        'DILIGENCE': ['RECTITUDE', 'GRAVITAS', 'MOXIE', 'GRACE'],
        'WILLPOWER': ['COOL', 'MANDATE', 'BRAVADO', 'WEIRD'],
        'GUILE': ['CRAFTINESS', 'DISSIMULATION', 'CROOKERY', 'CONFIDENTIALITY'],
        'TOUGHNESS': ['OBDURACY', 'IMMUNITY', 'PONDEROSITY', 'DISAFFECTION'],
        'PIZAZZ': ['GLAMOUR', 'MAGNETISM', 'PULCHRITUDE', 'STAGEPRESENCE']
    }
    SECONDARIES = ['ARMOR', 'EVADE', 'STYLE']

    ATTRIBUTE_NAMES = {
        'MUSCULARITY': 'Muscularity', 
        'BEEFINESS': 'Beefiness', 
        'ATHLETICISM': 'Athleticism', 
        'PUISSANCE': 'Puissance', 
        'PLACEHOLDER': 'Placeholder',
        'AGILITY': 'Agility',
        'PROWESS': 'Prowess', 
        'ADROITNESS': 'Adroitness', 
        'ELASTICITY': 'Elasticity', 
        'SPRYNESS': 'Spryness',
        'FACULTY': 'Faculty',
        'PEDANTRY': 'Pedantry', 
        'MENTALITY': 'Mentality', 
        'PERSPICACITY': 'Perspicacity', 
        'ERUDITION': 'Erudition',
        'DILIGENCE': 'Diligence',
        'RECTITUDE': 'Rectitude', 
        'GRAVITAS': 'Gravitas', 
        'MOXIE': 'Moxie', 
        'GRACE': 'Grace',
        'WILLPOWER': 'Willpower',
        'COOL': 'Cool', 
        'MANDATE': 'Mandate', 
        'BRAVADO': 'Bravado', 
        'DISAFFECTION': 'Disaffection',
        'GUILE': 'Guile',
        'CRAFTINESS': 'Craftiness', 
        'DISSIMULATION': 'Dissimulation', 
        'CROOKERY': 'Crookery', 
        'CONFIDENTIALITY': 'Confidentiality',
        'TOUGHNESS': 'Toughness',
        'OBDURACY': 'Obduracy', 
        'IMMUNITY': 'Immunity', 
        'PONDEROSITY': 'Ponderosity', 
        'WEIRD': 'Weird',
        'PIZAZZ': 'Pizazz',
        'GLAMOUR': 'Glamour', 
        'MAGNETISM': 'Magnetism', 
        'PULCHRITUDE': 'Pulchritude', 
        'STAGEPRESENCE': 'Stage Presence'
    }

    STATIC_ATTR_VALUE = 10

    @classmethod
    def _build_full_attr(self, method='random'):
        at = {}
        for parent, attrs in Creature.ATTRIBUTE_MAP.items():
            for attr in attrs:
                if method == 'random':
                    at[attr] = Dice.roll('3d6')
                elif method == 'static':
                    at[attr] = self.STATIC_ATTR_VALUE
        return at

    @classmethod
    def _build_limited_attr(self, method='random'):
        at = {}
        for attr in Creature.CATEGORIES:
            if method == 'random':
                at[attr] = Dice.roll('3d6')
            elif method == 'static':
                at[attr] = self.STATIC_ATTR_VALUE
        return at

    def __init__(self):
        self.status = []
        self.conditions = []

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

    def apply_condition(self, condition):
        if type(condition) == str:
            condition = model.Condition.find(condition)
        if condition not in self.conditions:
            self.conditions.append(condition)

    def heal_condition(self, method, count=999):
        nix = []
        for c in self.conditions:
            print(f'{method} vs {c.heal}')
            if method in c.heal or method == 'any':
                nix.append(c)
                if len(nix) >= count:
                    break
        self.conditions = [c for c in self.conditions if c not in nix]
        return nix
        
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

    def get_prop(self, name):
        if name in Creature.CATEGORIES:
            return self.calc_parent(name)
        elif name in Creature.SECONDARIES:
            return self.calc_secondary(name)
        else:
            return self.calc_attr(name)

    def parent_attr(self, name):
        for parent, attrs in Creature.ATTRIBUTE_MAP.items():
            if name.upper() in attrs:
                return parent
        raise ValueError(f'Trying to find parent attribute for unrecognized attribute: {name}')

    def calc_parent(self, name):
        # non delvers default all attributes to the parent value
        return self.attr.get(name.upper(), None)

    def calc_attr(self, name):
        # non delvers currently do no have any bonuses
        return self.calc_parent(self.parent_attr(name.upper()))

    def set_attr(self, name, value):
        self.attr[name] = value

    def calc_secondary(self, name):
        # non delvers will have their secondaries stored as attributes
        return self.attr.get(name.upper(), None)

    def moves(self):
        pass

    def valid_moves(self, types):
        if type(types) == str:
            types = [types]
        return [move for move in self.moves() if move.type in types]

    def calc_test_value(self, primary, secondary, auxiliaries=[]):

        print(f'PERFORM TEST - {primary}-{self.get_prop(primary)}, {secondary}-{self.get_prop(secondary)}')

        full_value = self.get_prop(primary) + int(self.get_prop(secondary) / 2)
        for aux in auxiliaries:
            full_value += self.get_prop(aux)

        return full_value

    def apply_xp(self, amount:int):
        # non delvers don't account xp
        pass

    def can_advance(self):
        return False

    def statusString(self):
        t = '['
        x = []
        for s in self.status:
            x.append('({} {})'.format(s['code'], str(s['duration'])))
        t += ','.join(x)
        t += ']'
        return t

class DelverStatus(Enum):
    FINE = 'fine'
    MISSING = 'missing'
    RETIRED = 'retired'
    DECEASED = 'deceased'

class Delver(Creature):

    @classmethod
    def random(self, c=None):
        if c:
            c = model.Classes.find(c)
        else:
            c = model.Classes.random()

        return Delver(strings.StringTool.random('regular_names'), model.Stocks.random(), c)

    @classmethod
    def random_hobbies(self):
        hobbies = [strings.StringTool.random('hobbies')]
        if Dice.roll('1d2') == 2:
            hobbies.append(strings.StringTool.random('hobbies'))
        if Dice.roll('1d2') == 2:
            hobbies.append(strings.StringTool.random('hobbies'))
        return list(set(hobbies))

    @classmethod
    def test_delver(self):
        s = model.Stocks.find('HUMAN')
        c = model.Classes.find('SWORDLORD')
        return Delver('The Test Delver', s, c, method='static')

    def __init__(self, name=None, stock=None, job=None, **kwargs):
        super().__init__()

        self.name = name
        self.state = DelverStatus.FINE
        self.gear_priority = random.choice(['armor', 'style'])
        self.stock = stock.name
        self.job = job
        self.level = 1
        self.maxhp = job.hp
        self.currenthp = job.hp
        self.id = str(uuid.uuid1())
        self.encumberence = 10
        self.inventory = []
        self.followers = []
        self.learned_moves = []
        self.wealth = 0
        self.lifetime_wealth = 0
        if kwargs.get('method') == 'static':
            self.attr = Delver._build_full_attr('static')
        else:
            self.attr = Delver._build_full_attr()
        self.gear = {}
        self.tools = []
        self.minutia = {
            'hobbies': Delver.random_hobbies(),
            'sign': strings.StringTool.random('astrology')
        }

        self.advancement = {
            'xp': 0,
            'treasure': 0
        }

        if hasattr(self.job, 'tool'):
            try:
                self.tools.append(Tool.generate(1, 0, self.job.tool))
            except IndexError:
                raise ValueError(f'No valid starting gear for tool type: {self.job.tool}')

        self.team = None # temp code for battles

    def __str__(self):
        return self.name + ', ' + self.stock + ', ' + self.job.name + ' (' + str(self.currenthp) + '/' + str(self.maxhp) +')'

    def __repr__(self):
        return self.name + ', ' + self.stock + ', ' + self.job.name + ' (' + str(self.currenthp) + '/' + str(self.maxhp) +')'

    def moves(self):
        moves = []
        for move in self.job.moves:
            moves.append(model.Moves.find(move))

        for move in self.learned_moves:
            moves.append(model.Moves.find(move))

        for tool in self.tools:
            moves.append(model.Moves.find(tool.grants))
        
        for fol in self.followers:
            moves.append(model.Moves.find(fol.grants))

        return moves

    def add_move(self, move):
        if type(move) == model.Moves:
            move = move.code
        self.learned_moves.append(move)

    def filter_moves(self, **kwargs):
        valid = []

        type = kwargs.get('type')

        for move in self.moves():
            if type and move.type != type:
                continue

            valid.append(move)

        return valid

    def valid_moves(self, types):
        moves = super().valid_moves(types)

        # combat moves might eventually have cooldowns or something 
        # downtime moves have conditions

        for move in moves:
            if hasattr(move, 'when') and not move.valid(self):
                moves.remove(move)

        return moves

    def calc_attr(self, name):
        running = self.attr[name.upper()]

        parent = self.parent_attr(name)
        for move in self.filter_moves(type=model.Moves.PASSIVE):
            if hasattr(move, 'bonus'):
                for bonus in move.bonus:
                    if bonus[0] in [name, parent]:
                        running += bonus[1]

        for item in self.tools + list(self.gear.values()):
            # items have attr bonuses like this
            # effect:
            #   attribute: ['muscularity', 1]
            attr = item.effect.get('attribute', None)
            if attr and attr[0] in [name, parent]:
                running += attr[1]

        for condition in self.conditions:
            if condition.effect.get('all'):
                running += condition.effect['all']
            elif name.lower() in condition.effect.keys():
                running += condition.effect[name.lower()]
        
        return running

    def calc_parent(self, name):
        # this shouldn't get used much but we're just averaging all the related attributes
        total = 0
        for attr in Creature.ATTRIBUTE_MAP[name]:
            total += self.calc_attr(attr)

        return int(total / len(Creature.ATTRIBUTE_MAP[name]))

    def calc_secondary(self, name):
        running = 0

        if name == 'armor':
            pass
        elif name == 'style':
            pass
        elif name == 'evade':
            pass

        return running

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

        self.advancement['treasure'] += amt
        if self.advancement['treasure'] > 100:
            self.advancement['treasure'] = 0
            self.apply_xp(1)

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
            same_type = [t for t in self.tools if t.type == item.type]
            consider = []
            has_room = len(self.tools) < self.job.tools
            has_type = bool(same_type)

            if has_room and not has_type:
                return True
            elif has_type:
                consider = same_type
            else:
                consider = self.tools

            x = self.evaluate_gear(item)
            # for the moment we're going to return the tool itself so that later steps can know which tool to replace
            for t in consider:
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

    def spend(self, value):
        self.wealth = int(self.wealth - value)

    def purchase(self, item, replace=None):
        if item.value > self.wealth:
            raise ValueError('Delver {} spent more money then they had.'.format(self.name))

        self.spend(item.value)
        if item.consumable():
            self.give(item)
        elif item.wearable() or item.tool():
            self.wear(item, replace)

    def will_hire(self, fol):
        return fol.salary < self.wealth and Dice.roll('1d100') < 5

    def follower_cap(self):
        return self.job.followers - len(self.followers)

    def acquire_follower(self, follower):
        self.spend(follower.salary)
        self.followers.append(follower)

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

    def apply_xp(self, amount:int):
        self.advancement['xp'] += amount

    def can_advance(self):
        return self.advancement['xp'] >= 10 + self.level * 10

    def advance(self):
        self.advancement['xp'] = 0
        self.advancement['treasure'] = 0

        self.level += 1

        # for now we're just giving a +1d6 bonus to two random attributes
        previous = []
        info = []
        for i in range(2):
            attr = random.choice([a for a in self.attr.keys() if a not in previous])
            previous.append(attr)

            amt = Dice.roll('1d6')
            self.attr[attr] += amt
            info.append((attr, amt))

            print('/'*50)
            print(f'Delver {self.name} adding {amt} to {attr}')
            print('/'*50)
        return info

    def data_format(self):
        return {
            'id': self.id,
            'name': self.name,
            'state': self.state.value,
            'status': self.status,
            'conditions': [c.name for c in self.conditions],
            'stock': self.stock,
            'job': self.job.code,
            'maxhp': self.maxhp,
            'currenthp': self.currenthp,
            'attributes': self.attr,
            'tools': [t.data_format() for t in self.tools],
            'gear': [i.data_format() for i in self.gear.values()],
            'inventory': [i.data_format() for i in self.inventory],
            'followers': [f.data_format() for f in self.followers],
            'minutia': self.minutia,
            'level': self.level,
            'advancement': self.advancement
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

class Follower(Creature):

    NAME_SOURCES = {
        'undead': '', 
        'beast': 'friendly_animal_names', 
        'doll': '', 
        'hireling': 'regular_names', 
        'arcane': '', 
        'devil': ''
    }

    @classmethod
    def generate(self, ftype, ranks):
        if type(ranks) == int:
            ranks = [ranks]
        fol = model.Follower.random(lambda f: f.type == ftype and f.rank in ranks)
        return Follower(fol)

    def __init__(self, model):
        super().__init__()

        self.id = str(uuid.uuid1())
        
        self.model = model
        self.type = model.type
        self.rank = model.rank
        self.currenthp = model.health
        self.maxhp = model.health
        self.power = model.power
        self.grants = model.grants

        self.name = strings.StringTool.random(Follower.NAME_SOURCES[self.type])

        if self.type == 'hireling':
            self.salary = Dice.roll(model.salary)
        else:
            self.salary = 0

    def data_format(self):
        return {
            'id': self.id,
            'type': self.type,
            'name': self.name,
            'desc': self.model.name,
            'salary': self.salary
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
            self.attr = Monster._build_limited_attr()
        self.id = Monster.idgen()

    def moves(self):
        moves = []
        for move in self._template.moves:
            moves.append(model.Moves.find(move))
        return moves

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
        self.last_downtime = 0
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

    def wants_downtime(self, current_time):
        # this can be tuned to the band later
        return current_time - self.last_downtime > 500

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