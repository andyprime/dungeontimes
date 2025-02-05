import random
import uuid

import core.dice
import core.critters

from definitions.model import Moves

class Team:

    def __init__(self, name, no):
        self.name = name
        self.members = []
        self.teamNumber = no

    def add(self, c):
        self.members.append(c)


    def validMembers(self, alive=None, exclude=None):
        options = []

        for member in self.members:
            if alive and not member.canAct():
                continue
            if exclude and member == exclude:
                continue
            options.append(member)

        return options

    # def randomMember(self, alive=None):

    #     # TODO: this copy might get expensive but right now its convenient
    #     options = self.members.copy()

    #     if alive:
    #         for member in options:
    #             if not member.canAct():
    #                 options.remove(member)

    #     return random.choice(options)

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

    # Set to True if you want to skip combat for speed
    SKIP_BATTLE = False

    PAPERWORK = 1
    BATTAL = 2
    OVER = 3


    def __init__(self, processCallback):
        self.teams = {}
        self.teamCount = 0
        self.conditions = []
        self.initiative = []
        self.state = Battle.PAPERWORK
        self.roundCount = 0
        self.processCallback = processCallback

    def start(self):
        self.processMessage('Lets fight!')
        self.processMessage('')

        if len(self.teams) < 2:
            raise ValueError('Can not initiate battle with team count below two.')

        self.state = Battle.BATTAL

        self.round()

    def processMessage(self, message, emit=False):
        if callable(self.processCallback):
            self.processCallback(message, emit)

    def round(self):
        self.processMessage('=' * 50)
        self.processMessage('ROUND {}'.format(self.roundCount))

        for n, t in self.teams.items():
            t.teamPrint()
        self.processMessage('=' * 50)

        # determine turn order
        self.resetInitiative()

        # everybody gets a turn
        while len(self.initiative) > 0:
            current = self.initiative.pop()
            # remember its a tuple
            fellah = current[1]
            teamName = current[2]

            self.processMessage('Starting {}s turn '.format(fellah.name))

            fellah.tickStatus()

            if fellah.canAct():

                # determine a course of action

                action = self.selectCombatAction(fellah, teamName)

                # execute it

                self.processAction(action)
            else:
                self.processMessage('Skipping {}, they are having a rough day'.format(fellah.name))

            team_counts = [t.remaining() for t in self.teams.values()]
            if 0 in team_counts:
                self.state = Battle.OVER
                break

        self.roundCount += 1

        # print('!' * 10)
        # print('Combat loop over')

    def complete(self):
        if Battle.SKIP_BATTLE:
            return True
        else:
            return self.state == Battle.OVER

    # def victor(self):
    #     if self.state != Battle.OVER:
    #         return None

    def selectCombatAction(self, fellah, team):
        # note that this lives in battle.py because it requires too much shared info to live on the creature itself

        # # pick an enemy team
        # targetTeam = self.randomTeam(exclude=team)

        # filter out moves that can not be performed
        validMoves = []

        for move in fellah.moves():
            # this is where the filtering should go but I think atm there's none of that

            if move.target == 'self':
                t = fellah
            else:
                t = self.randomTarget(fellah, 'opponent')

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

            # TODO - remove this once proper external testing is done
            assert(fullThreshold > partialThreshold)

            roll = random.uniform(1, 100)

            if roll >= fullThreshold:
                effect = move.effect

                appliedDamage = self.applyEffect(target, effect)

                descriptor = '{act} did a sick {move} on {trg}.'
                if appliedDamage:
                    descriptor += ' It did {dam} hp.'

            elif roll >= partialThreshold:
                effect = move.effect

                appliedDamage = self.applyEffect(target, effect, True)

                descriptor = '{act} tried to do a {move} on {trg} and it kinda worked.'
                if appliedDamage:
                    descriptor += ' It did {dam} hp.'

            else:
                descriptor = '{act} tried to do a sweet {move} but it totally failed.'
        elif move.type == 'spellcasting':
            spells = fellah.getSpells()

            assert(len(spells) > 0)

            spell = random.choice(spells)

            targetTypes = spell.target
            target = self.randomTarget(fellah, targetTypes)

            self.applyEffect(target, spell.effect)


            descriptor = '{act} cast a cool spell but unfortunately for them its not implemented yet.'


        else:
            descriptor = 'Invalid move type: {}'.format(move)


        descriptor = descriptor.format(act=fellah.name, move=move.name, trg=target.name, dam=appliedDamage)

        self.processMessage(descriptor, True)

    def applyEffect(self, target, effect, partial=False):

        appliedDamage = 0

        if effect.get('status', None):
            target.applyStatus(effect['status'])

        if effect.get('damage', None):
            if partial:
                appliedDamage = max(1, int(effect['damage'] / 2))
            else:
                appliedDamage = effect['damage']
            target.applyDamage(appliedDamage)

        return appliedDamage

    def randomTarget(self, fellah, types):

        potentials = []

        if 'self' in types:
            potentials.append(fellah)
        if 'team' in types:
            potentials.extend(self.getTeam(fellah.team).validMembers(True, fellah))
        if 'opponent' in types:
            potentials.extend(self.getOppositeTeam(fellah.team).validMembers(True))

        return random.choice(potentials)

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

        creature.team = side
        self.teams[side].add(creature)

    def getTeam(self, teamCode):
        return self.teams[teamCode]

    def getOppositeTeam(self, teamCode):
        teams = list(self.teams.keys())
        teams.remove(teamCode)
        return self.teams[teams[0]]

if __name__ == "__main__":

    seed = str(uuid.uuid1())
    # seed = '89739eaa-0d70-11ef-899a-3b62a91e32e4'

    random.seed(seed)
    print('Seed : {}'.format(seed))


    print(' - Battle Create')

    b = Battle()

    print(' - Add participants')

    for i in range(4):
        b.addParticipant('monster', core.critters.Monster.random())

    for i in range(4):
        b.addParticipant('adventurer', core.critters.Delver.random())

    print(' - Start battle')

    b.start()

    while b.state != Battle.OVER:
        b.round()

    print('Testing complete.')
    print('Seed : {}'.format(seed))
