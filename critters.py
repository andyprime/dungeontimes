import uuid

import dice
import definitions.model as model

class Creature:

    def __init__(self):
        self.status = []

    def generateInitiative(self):
        return dice.Dice.d(1,20)

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

    def applyDamage(self, damage_count):
        old = self.currenthp
        self.currenthp = self.currenthp - damage_count
        if self.currenthp < 0:
            self.currenthp = 0
        print('  Apply Dam [{}] - HP old - {}, new - {}'.format(self.name, old, self.currenthp))

    def applyStatus(self, status, half=False):
        duration = dice.Dice.d(1,4) + 2
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

    def rollStat(self, stat):
        target = getattr(self, stat)
        return dice.Dice.d(1,20) <= target

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
        from factory import NameFactory

        return Delver(NameFactory.generateRandom(), model.Stocks.random(), model.Classes.random())

    def __init__(self, name, stock, job):
        super().__init__()

        self.name = name
        # note that for the moment stock just contains a name string, this will need to be more involved later
        self.stock = stock.name
        self.job = job
        self.maxhp = job.hp
        self.currenthp = job.hp
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

class Monster(Creature):

    @classmethod
    def random(self):
        # return Monster(template=model.Monsters.random())
        return Monster(model.Monsters.random())

    def __init__(self, template):
        from factory import NameFactory

        super().__init__()

        self._template = template
        self.name = NameFactory.randomByType(template.category)
        self.stock  = template.name
        self.maxhp = template.hp
        self.currenthp = template.hp

    def moves(self):
        moves = []
        for move in self._template.moves:
            moves.append(model.Moves.find(move))
        return moves

    def testThresholds(self, test):
        return (60, 80)

    def __str__(self):
        return self.name + ', ' + self.stock + ', ' + ' (' + str(self.currenthp) + '/' + str(self.maxhp) +')'

    def __repr__(self):
        return self.name + ', ' + self.stock + ', ' + ' (' + str(self.currenthp) + '/' + str(self.maxhp) +')'