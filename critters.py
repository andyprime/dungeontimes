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
        print('  HP old - {}, new - {}'.format(old, self.currenthp))

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

    def testThresholds(self, test):
        pass

    def statusString(self):
        t = '['
        x = []
        for s in self.status:
            x.append('({} {})'.format(s['code'][0], str(s['duration'])))
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