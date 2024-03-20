import random

import factory
import dice
import critters

from definitions.model import Moves

class Team:

    def __init__(self, name, no):
        self.name = name
        self.members = []
        self.teamNumber = no

    def add(self, c):
        self.members.append(c)

    def randomMember(self, alive=None):

        # TODO: this copy might get expensive but right now its convenient
        options = self.members.copy()

        if alive:
            for member in options:
                if not member.canAct():
                    options.remove(member)

        return random.choice(options)

    def remaining(self):
        # count of remaining active fighters
        a = len([x for x in self.members if x.canAct()])
        return a

    def teamPrint(self):
        print('Team #{}: {}'.format(self.teamNumber, self.name))
        for fellah in self.members:
            print('    {} - {}'.format( str(fellah), fellah.statusString() ))
        print()


class Battle:

    PAPERWORK = 1
    BATTAL = 2
    OVER = 3


    def __init__(self):
        self.teams = {}
        self.teamCount = 0
        self.conditions = []
        self.initiative = []
        self.state = Battle.PAPERWORK

    def start(self):
        print('Lets fight!')
        print()

        if len(self.teams) < 2:
            raise ValueError('Can not initiate battle with team count below two.')

        self.state = Battle.BATTAL

        round_count = 1
        while (self.state == Battle.BATTAL):
            print('=' * 50)
            print('ROUND {}'.format(round_count))

            for n, t in self.teams.items():
                t.teamPrint()
            print('=' * 50)


            # determine turn order
            self.resetInitiative()


            # everybody gets a turn
            while len(self.initiative) > 0:
                current = self.initiative.pop()
                # remember its a tuple
                fellah = current[1]
                teamName = current[2]

                fellah.tickStatus()

                if fellah.canAct():

                    # determine a course of action

                    action = self.selectCombatAction(fellah, teamName)

                    # execute it

                    self.processAction(action)
                else:
                    print('Skipping {}, they are having a rough day'.format(fellah.name))

                team_counts = [t.remaining() for t in self.teams.values()]
                if 0 in team_counts:
                    self.state = Battle.OVER
                    break

            round_count += 1

        print('!' * 10)
        print('All done')



    def selectCombatAction(self, fellah, team):
        # note that this lives in battle.py because it requires too much shared info to live on the creature itself

        # pick an enemy team
        targetTeam = self.randomTeam(exclude=team)

        # filter out moves that can not be performed
        validMoves = []

        for move in fellah.moves():
            # this is where the filtering should go but I think atm there's none of that

            if move.target == 'self':
                t = fellah
            else:
                t = targetTeam.randomMember()

            validMoves.append({
                    'actor': fellah,
                    'move': move,
                    'target': t
                })

        # add any special moves
        if fellah.hasStatus('CONFUSED'):
            validMoves.append({
                    'actor': fellah,
                    'move': Moves.find('CONFUSED'),
                    'target': fellah
                })


        # select a move
        # eventually this will be by weight, not round robin
        selectedMove = random.choice(validMoves)

        return selectedMove


    def processAction(self, action):
        fellah = action['actor']
        move = action['move']
        target = action['target']

        appliedDamage = None
        descriptor = 'Placeholder'

        if move.type == 'consequence':
            descriptor = '{act} performed a consequence move, right now those do nothing.'
        elif move.type == 'instant':

            # we're gonna generate a float between 1 and 100
            # if the result is above fullThreshold its a full success
            # otherwise if the result is above partialThreshold its a partial sucess
            # otherwise its a failure


            if move.test == 'none':
                partialThreshold = -1
                fullThreshold = 0
            else:
                partialThreshold, fullThreshold = fellah.testThresholds(move.test)

            assert(fullThreshold > partialThreshold)

            roll = random.uniform(1, 100)

            if roll >= fullThreshold:
                effect = move.effect

                if effect.get('status', None):
                    target.applyStatus(effect['status'])

                if effect.get('damage', None):
                    appliedDamage = effect['damage']
                    target.applyDamage(appliedDamage)

                descriptor = '{act} did a sick {move} on {trg}.'
                if appliedDamage:
                    descriptor += ' It did {dam} hp.'

            elif roll >= partialThreshold:
                effect = move.effect

                if effect.get('status', None):
                    target.applyStatus(effect['status'], half=True)

                if effect.get('damage', None):
                    appliedDamage = max(1, int(effect['damage'] / 2))
                    target.applyDamage(appliedDamage)

                descriptor = '{act} tried to do a {move} on {trg} and it kinda worked.'
                if appliedDamage:
                    descriptor += ' It did {dam} hp.'

            else:
                descriptor = '{act} tried to do a sweet {move} but it totally failed.'


        descriptor = descriptor.format(act=fellah.name, move=move.name, trg=target.name, dam=appliedDamage)

        print(descriptor)


    def resetInitiative(self):
        self.initiative = []

        for name, team in self.teams.items():
            for fellah in team.members:

                if fellah.canAct():
                    x = fellah.generateInitiative()

                    self.initiative.append( (x, fellah, name) )

        self.initiative.sort(key=lambda x: x[0])


    def addParticipant(self, side, creature):
        # TODO: handle state conditions
        if not self.teams.get(side, False):
            self.teams[side] = Team(side, self.teamCount)
            self.teamCount += 1

        self.teams[side].add(creature)

    def randomTeam(self, exclude=None):
        team_options = list(self.teams.keys())

        if exclude:
            team_options.remove(exclude)

        return self.teams[random.choice(team_options)]


if __name__ == "__main__":

    print(' - Battle Create')

    b = Battle()

    print(' - Add participants')

    for i in range(4):
        b.addParticipant('monster', critters.Monster.random())

    for i in range(4):
        b.addParticipant('adventurer', critters.Delver.random())

    print(' - Start battle')

    b.start()

    print('Ok, done.')
