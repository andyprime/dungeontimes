import json
import uuid

from core.dice import Dice
import definitions.model as model

class Creature:

    def __init__(self):
        self.status = []

    def generateInitiative(self):
        return Dice.d(1,20)

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

    def applyDamage(self, damage_count):
        old = self.currenthp
        self.currenthp = self.currenthp - damage_count
        if self.currenthp < 0:
            self.currenthp = 0
        print('  Apply Dam [{}] - HP old - {}, new - {}'.format(self.name, old, self.currenthp))

    def applyStatus(self, status, half=False):
        duration = Dice.d(1,4) + 2
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

    def rollStat(self, stat):
        target = getattr(self, stat)
        return Dice.d(1,20) <= target

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
    @classmethod
    def random(self):
        from core.names import NameFactory

        return Delver(NameFactory.generateRandom(), model.Stocks.random(), model.Classes.random())

    def __init__(self, name=None, stock=None, job=None, serialized=None):
        super().__init__()

        if serialized:
            if type(serialized) == str:
                serialized = json.loads(serialized)

            self.name = serialized['name']
            self.stock = serialized['stock']
            self.job = model.Classes.find(serialized['job'])
            self.maxhp = serialized['maxhp']
            self.currenthp = serialized['currenthp']
            self.id = serialized['id']
        else:
            self.name = name
            # note that for the moment stock just contains a name string, this will need to be more involved later
            self.stock = stock.name
            self.job = job
            self.maxhp = job.hp
            self.currenthp = job.hp
            self.id = str(uuid.uuid1())
        self.team = None # temp code for battles

    def __str__(self):
        return self.name + ', ' + self.stock + ', ' + self.job.name + ' (' + str(self.currenthp) + '/' + str(self.maxhp) +')'

    def __repr__(self):
        return self.name + ', ' + self.stock + ', ' + self.job.name + ' (' + str(self.currenthp) + '/' + str(self.maxhp) +')'

    def moves(self):
        moves = []
        for move in self.job.moves:
            moves.append(model.Moves.find(move))
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
        from core.names import NameFactory

        super().__init__()

        if serialized:
            self._template = model.Monsters.find(serialized['t'])
            self.name = serialized['n']
            self.stock = self._template.name
            self.maxhp = serialized['mhp']
            self.currenthp = serialized['chp']
        else:
            self._template = template
            self.name = NameFactory.randomByType(template.category)
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