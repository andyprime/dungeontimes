import random
import time

from core.battle import Battle

class Expedition:

    READY = 'rdy'
    MOVING = 'mov'
    ENCOUNTER = 'enc'
    BATTLE = 'bat'
    RECOVER = 'rec'
    EXITING = 'ext'
    SCATTERED = 'sct'
    COMPLETE = 'cmp'
    ERROR = 'err'

    DEFAULT_TURN_DELAY = 2

    # Only print the map every X moves
    PRINT_INTERVAL = 5

    def __init__(self, dungeon, party):

        self.dungeon = dungeon
        self.party = party
        self.battle = None

        self.entrance = dungeon.entrance()
        self.cursor = self.entrance
        self.status = Expedition.READY

        self.steps = 0

        # if set it is the cells we are currently trying to navigate through
        self.path = []

        # Got to log which sections of the map have already been explored
        # So for now we're gonna keep the cell coords in an array to reference
        self.history = []
        self.history.append(self.cursor.coords)

        self.processors = []

    def registerProcessor(self, callback):
        self.processors.append(callback)

    def processMessage(self, message):
        for f in self.processors:
            f(message)

    def begin(self):
        while (self.status not in [Expedition.COMPLETE, Expedition.ERROR]):
            self.processTurn()
            time.sleep(Expedition.DEFAULT_TURN_DELAY)

    def processTurn(self):
        self.steps += 1
        showOverride = False

        f = getattr(self, 'runstate_' + self.status)
        if f:
            f()

            if self.steps % Expedition.PRINT_INTERVAL == 0 or showOverride:
                self.historyMap()
        else:
            self.processMessage('Unknown expedition status: {}'.format(self.status))
            self.status = Expedition.ERROR

    # Ready
    def runstate_rdy(self):
        self.processMessage('The party enters the dungeon, prepared for peril and adventure.')

        # Nothing needs to go here just yet but we're gonna formalize it as a step for clarity and future use

        self.status = Expedition.MOVING

    # Moving
    def runstate_mov(self):
        if not self.path:
            self.path = self.navigate()

        if self.path is None:
            self.processMessage('The dungeon is completely explored.')
            self.status = Expedition.EXITING
        elif len(self.path):
            destination = self.path.pop()
            self.cursor = destination
            self.processMessage('Moving to {}'.format(self.cursor.coords))

            if self.cursor.isRoom():
                if self.cursor.coords not in self.history:
                    self.processMessage('Party has encountered an unexplored room. Get the lanterns ready.')
                    self.status = Expedition.ENCOUNTER

                # TODO: move this to the encounter complete section?
                for cell in self.dungeon.roomBrethren(self.cursor):
                    if cell not in self.history:
                        self.history.append(cell.coords)

            else:
                self.history.append(self.cursor.coords)
        else:
            self.processMessage('Moving algorithm did not produce a destination')
            self.status = Expedition.ERROR

    # Encounter
    def runstate_enc(self):

        if self.dungeon.roomAt(self.cursor).occupied():
            self.processMessage('This room is full of monsters! A battle ensues!')
            self.status = Expedition.BATTLE
        else:
            self.processMessage('This room is unoccupied. Maybe there is some treasure? (That doesnt exist yet)')
            self.status = Expedition.MOVING

    # Exiting
    def runstate_ext(self):
        if self.path:
            self.cursor = self.path.pop()
        else:

            if self.cursor == self.entrance:
                self.processMessage('Party has reached the entrance and left the dungeon.')
                self.status = Expedition.COMPLETE
                showOverride = True
            else:
                self.processMessage('Party is ready to leave and plotting a course back to the entrance.')
                self.path = self.generatePath(target=self.entrance)

    # Battle
    def runstate_bat(self):
        if self.battle:

            if self.battle.complete():
                if any([d.canAct() for d in self.party]) :
                    self.processMessage('The party is victorious. Good job team.')

                    # clear out the dead monsters
                    self.dungeon.roomAt(self.cursor).empty()
                    self.battle = None

                    self.status = Expedition.RECOVER
                else:
                    self.processMessage('Sadly the part has been slain my the local miscreants.')
                    self.status = Expedition.SCATTERED
            else:
                self.battle.round()

        else:

            self.battle = Battle()

            for m in self.dungeon.roomAt(self.cursor).locals:
                self.battle.addParticipant('monster', m)

            for d in self.party:
                self.battle.addParticipant('delver', d)

    def runstate_sct(self):
        self.processMessage('Are there survivors? Who knows.')
        self.status = Expedition.COMPLETE

    # Recover
    def runstate_rec(self):
        self.processMessage('The party takes a little breather after a fight.')
        self.status = Expedition.MOVING

    # Complete
    def runstate_cmp(self):
        self.processMessage('All done. Good hustle')
        self.processMessage('Total Moves: {}'.format(self.steps))

    def historyMap(self):
        for index, row in enumerate(self.dungeon.grid):
            display = '{}: '.format(str(index).rjust(4, ' '))

            for cell in row:
                if cell == self.cursor:
                    display += 'P'
                elif self.path and cell in self.path:
                    display += '\033[93m' + cell.positiveSymbol() + '\033[0m'
                elif cell.coords in self.history:
                    display += '\033[94m' + cell.positiveSymbol() + '\033[0m'
                else:
                    display += cell.symbol()
            print(display)
        print('\n')

    def navigate(self):
        # this is broken out to support future plans to provide different navigation approaches

        # just going to implement a real basic navigation system for now
        # if there are unexplored cells adjacent to our current location just pick one at random and go there
        # otherwise find the closest unexplored cell and chart a course to there

        neighbors = self.dungeon.getNeighbors(self.cursor)
        easyDirections = [n for n in neighbors if n.coords not in self.history]

        if easyDirections:
            return [random.choice(easyDirections)]
        else:
            # time to Dijkstra
            return self.generatePath()

    def generatePath(self, target=None):
        # just a basic dijkstra implementation that stops once it finds an unexplored cell

        pathingStart = time.perf_counter()

        distance = {}
        previous = {}
        q = []

        for cell in self.dungeon.allCells(navigable=True):
            distance[cell] = 1000000
            previous[cell] = None
            q.append(cell)

        distance[self.cursor] = 0

        count = 0
        while len(q) > 0:
            count += 1
            lowest = q[0]
            for cell in q:
                if distance[cell] < distance[lowest]:
                    lowest = cell
            q.remove(lowest)

            # default break point is finding the first unexplored
            if target and lowest == target:
                break
            elif lowest.coords not in self.history:
                break

            neighbors = self.dungeon.getNeighbors(lowest)
            for neighbor in [n for n in neighbors if n in q]:
                newDistance = distance[lowest] + 1 if distance[lowest] else 1

                if newDistance < distance[neighbor]:
                    distance[neighbor] = newDistance
                    previous[neighbor] = lowest

        delta = time.perf_counter() - pathingStart

        self.processMessage('** Pathfinding run complete. Time: {}. Cells examined: {}, Cells remaining: {}'.format(str(delta), count, len(q)))

        if len(q) == 0:
            return None

        c = lowest
        path = [c]
        while(previous.get(c, False)):
            path.append(previous[c])
            c = previous[c]

        return path