import uuid

import dice

class Dungeon:

    rooms = []

    free_agents = []

    def __init__(self):
        pass


class Room: 

    def __init__(self, number):
        self.number = number
        self.entrance = False
        self.style = 'init'
        self.size = 'init'
        self.features = []
        self.inhabitants = []
        self.connections = []

    def __str__(self):
        line1 = 'Room {}. A {} room in the {} style.'.format(self.number, self.size, self.style)
        if len(self.inhabitants) > 0:
            line2 = 'Currently inhabited by some folks'
        else:
            line2 = 'Currently unoccupied'
        line3 = 'Connects to rooms {}'.format(', '.join(self.connections))
        return line1 + "\n" + line2 + "\n" + line3


    def addInhabitant(self, creature):
        # TODO: capacity limits?
        self.inhabitants.append(creature)


    def removeInhabitant(self, creature):
        new_inhabitants = [i for i in self.inhabitants if i.id != creature.id]
        self.inhabitants = new_inhabitants


class Creature:

    def __init__(self, properties):
        self.id = str(uuid.uuid1())
        self.name = properties.get('name', 'baddata')
        self.type = properties.get('type', 'baddata')
        self.job = properties.get('job', 'baddata')
        self.stock = properties.get('stock', 'baddata')

        self.str = properties.get('str', 'baddata')
        self.dex = properties.get('dex', 'baddata')
        self.con = properties.get('con', 'baddata')
        self.int = properties.get('int', 'baddata')
        self.wis = properties.get('wis', 'baddata')
        self.cha = properties.get('cha', 'baddata')

        self.maxhp = self.con
        self.currenthp = self.maxhp

    def generateInitiative(self):
        return dice.Dice.d(1,20)

    def __str__(self):
        return self.name + ', ' + self.stock + ' ' + self.job + '; S: ' + str(self.str) + ', D: ' + str(self.dex) + ', C: ' + str(self.con) + ', I: ' + str(self.int) + ', W: ' + str(self.wis) + ', C: ' + str(self.cha)

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
        
