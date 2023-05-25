import random

import factory
import dice

class Team:

    def __init__(self, name):
        self.name = name
        self.members = []

    def add(self, c):
        self.members.append(c)

    def randomMember(self, alive=None):

        # TODO: this copy might get expensive but right now its convenient
        options = self.members.copy()

        c1 = len(options)
        if alive:
            for member in options:
                if not member.canAct():
                    options.remove(member)

        c2 = len(options)
        print(' member filtering - {} - {}'.format(c1, c2))

        # TODO: should this raise an error or something if the filters remove all possible options?
        return random.choice(options)

    def remaining(self):
        # count of remaining active fighters
        a = len([x for x in self.members if x.canAct()])
        print('R: {}'.format(a))
        return a


class Battle:

    PAPERWORK = 1
    BATTAL = 2
    OVER = 3


    def __init__(self):
        self.teams = {}
        self.conditions = []
        self.initiative = []
        self.state = Battle.PAPERWORK

    def start(self):
        print('Lets fight!')
        print()

        count = 1
        for name, team in self.teams.items():
            print('Team #{}: {}'.format(count, name))
            for fellah in team.members:
                print('    {}'.format(str(fellah)))
            print()
            count += 1


        self.state = Battle.BATTAL


        round_count = 1
        while (self.state == Battle.BATTAL):
            print('ROUND {}'.format(round_count))

            # determine turn order
            self.resetInitiative()


            # everybody gets a turn
            while len(self.initiative) > 0:
                current = self.initiative.pop()
                # remember its a tuple
                fellah = current[1]


                if fellah.canAct():

                    # determine a course of action

                    action = fellah.getCombatAction(self)


                    # execute it

                    self.processAction(fellah, action)
                else:
                    print('Skipping {}, they are having a rough day'.format(fellah.name))


                team_counts = [t.remaining() for t in self.teams.values()]
                print('Counts: {}'.format(team_counts))
                if 0 in team_counts:
                    self.state = Battle.OVER
                    break

            round_count += 1

        print('All done')


        # TODO: I think the isAlive filtering in random member is destroying the member lists
        print('hmmm')
        print([len(x.members) for x in self.teams.values()])



    def processAction(self, actor, action):
        # for now we'll just do basic ass dex checks
        target = action['target']
        success = actor.rollStat('dex')
        if success:

            damage = dice.Dice.d(1,6)
            target.applyDamage(damage)

            descriptor = '{} attacked {} with a sword or something, dealing {} damage. They are now {}'.format(actor.name, target.name, damage, target.status())
        else:
            descriptor = '{} attacked {} with a sword or something, but missed'.format(actor.name, target.name)

        print(descriptor)


    def resetInitiative(self):
        self.initiative = []

        for name, team in self.teams.items():
            for fellah in team.members:

                if fellah.canAct():
                    x = fellah.generateInitiative()

                    self.initiative.append( (x, fellah) )

        self.initiative.sort(key=lambda x: x[0])


    def addParticipant(self, side, creature):
        # TODO: handle state conditions
        if not self.teams.get(side, False):
            self.teams[side] = Team(side)

        self.teams[side].add(creature)

    def randomTeam(self, exclude=None):
        team_options = list(self.teams.keys())

        if exclude:
            team_options.remove(exclude)

        return self.teams[random.choice(team_options)]


if __name__ == "__main__":

    b = Battle()


    for i in range(4):
        b.addParticipant('monster', factory.CreatureFactory.randomMonster())

    for i in range(4):
        b.addParticipant('adventurer', factory.CreatureFactory.randomAdventurer())

    b.start()

    print('Ok, done.')
