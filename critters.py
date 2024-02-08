import uuid

import dice
import definitions.model as model

class Creature:

    def __init__(self, properties):
        raise NotImplementedError('Do not call the base class constructor please.')

    def generateInitiative(self):
        return dice.Dice.d(1,20)

    def __str__(self):
        return self.name + ', ' + self.stock + ' (' + str(self.currenthp) + '/' + str(self.maxhp) +')'

    def canAct(self):
        return self.currenthp > 0

    def getCombatAction(self, battle):
        # given the current battle state

        target_team = battle.randomTeam(exclude=self.type) # using self.type won't work in the long run

        x = {
            'action_type': 'melee attack',
            'target': target_team.randomMember(alive=True)
        }
        # print(' Me: {}, {}'.format(self.name, self.type))
        # print('Him: {}, {}'.format(x['target'].name, x['target'].type))
        return x

    def applyDamage(self, damage_count):
        old = self.currenthp
        self.currenthp = self.currenthp - damage_count
        if self.currenthp < 0:
            self.currenthp = 0
        print('  HP old - {}, new - {}'.format(old, self.currenthp))

    def status(self):
        if self.currenthp == 0:
            return 'dead'
        elif self.currenthp < self.currenthp / 2:
            return 'injured'
        else:
            return 'mostly ok'

    def rollStat(self, stat):
        target = getattr(self, stat)
        return dice.Dice.d(1,20) <= target

class Delver(Creature):
    @classmethod
    def random(self):
        from factory import NameFactory

        return Delver(NameFactory.generateRandom(), model.Stocks.random(), model.Classes.random())

    def __init__(self, name, stock, job):

        self.name = name
        # note that for the moment stock just contains a name string, this will need to be more involved later
        self.stock = stock.name
        self.job = job
        self.maxhp = job.hp
        self.currenthp = job.hp

    def __str__(self):
        return self.name + ', ' + self.stock + ', ' + self.job.name + ' (' + str(self.currenthp) + '/' + str(self.maxhp) +')'


class Monster(Creature):

    @classmethod
    def random(self):
        # return Monster(template=model.Monsters.random())
        return Monster(model.Monsters.random())

    def __init__(self, template):
        from factory import NameFactory

        self._template = template
        self.name = NameFactory.randomByType(template.category)
        self.stock  = template.name
        self.maxhp = template.hp
        self.currenthp = template.hp
