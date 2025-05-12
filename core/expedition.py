import json
import random
import time

from core.battle import Battle

class Expedition:

    READY = 'rdy'
    MOVING = 'mov' #should probably be renamed to exploring
    ENCOUNTER = 'enc'
    BATTLE = 'bat'
    RECOVER = 'rec'
    EXITING = 'ext'
    SCATTERED = 'sct'
    COMPLETE = 'cmp'
    ERROR = 'err'

    DEFAULT_TURN_DELAY = 2

    # the abbreviated ones are just the default for any given stage, others need to be manually returned
    TASK_DURATIONS = {
        'rdy': 2,
        'mov': 1.5,
        'enc': 2,
        'bat': 0.1,
        'rec': 2,
        'ext': 2,
        'sct': 2,
        'cmp': 3,
        'round_divider': 2
    }

    # Only print the map every X moves
    PRINT_INTERVAL = 5

    def __init__(self, dungeon, party, cursor=None, id=None, mdb=None):

        self.dungeon = dungeon
        self.party = party
        self.battle = None
        self.id = id
        self.mdb = mdb

        self.entrance = dungeon.entrance()
        self.status = Expedition.READY

        if cursor:
            self.cursor = dungeon.getCell(*tuple(cursor))
        else:
            self.cursor = self.entrance

        self.steps = 0

        # if set it is the cells we are currently trying to navigate through
        self.path = []

        # Got to log which sections of the map have already been explored
        # So for now we're gonna keep the cell coords in an array to reference
        self.history = []
        self.history.append(self.cursor.coords)

        self.processors = []
        self.emitters = []

    def registerProcessor(self, callback):
        self.processors.append(callback)

    def registerEventEmitter(self, callback):
        self.emitters.append(callback)

    def processMessage(self, message, emit=False):
        for f in self.processors:
            f(message)
        if emit:
            self.emitNarrative(message)

    def emit(self, msg):
        for e in self.emitters:
            e(msg.encode('ASCII'))

    def identified_emit(self, code, msg):
        self.emit('{};{};{}'.format(code, self.id, msg))

    def emitCursorUpdate(self):
        c = self.cursor.coords
        if self.mdb:
            self.mdb.db.expeditions.update_one({'id': self.id}, {'$set': {'cursor': c}})
        self.emit('CURSOR;{};{},{}'.format(self.id, c[0], c[1]))
        
    def emitNarrative(self, s):
        self.emit('NARR;{};{}'.format(self.id, s))        

    def emitNew(self):
        self.emit('EXP-NEW;{}'.format(self.id))

    def emitDelete(self):
        self.emit('EXP-DEL;{}'.format(self.id))

    def emitBattle(self, start, roomNo):
        if start:
            self.emit('BTLS;{};{}'.format(self.id, roomNo))
        else:
            self.emit('BTLE;{};{}'.format(self.id, roomNo))

    def over(self):
        return self.status in [Expedition.COMPLETE, Expedition.ERROR]

    def begin(self):
        # this function is not exactly deprecated but it should only be used in the context
        # of making an expedition run itself
        while (self.status not in [Expedition.COMPLETE, Expedition.ERROR]):
            t = self.processTurn()
            if t:
                time.sleep(t)
            else:
                time.sleep(Expedition.DEFAULT_TURN_DELAY)

    def processTurn(self):
        self.steps += 1
        showOverride = False

        f = getattr(self, 'runstate_' + self.status)
        if f:
            delayOverride = f()

            if self.steps % Expedition.PRINT_INTERVAL == 0 or showOverride:
                self.historyMap()

            if delayOverride:
                return delayOverride
            else:
                return Expedition.TASK_DURATIONS[self.status]
        else:
            self.processMessage('Unknown expedition status: {}'.format(self.status))
            self.status = Expedition.ERROR
            return False

    # Ready
    def runstate_rdy(self):
        self.processMessage('The party enters the dungeon, prepared for peril and adventure.', True)

        # Nothing needs to go here just yet but we're gonna formalize it as a step for clarity and future use

        self.status = Expedition.MOVING

    # Moving
    def runstate_mov(self):
        if not self.path:
            self.path = self.navigate()

        if self.path is None:
            self.processMessage('The party declares there is nothing more to explore.', True)
            self.status = Expedition.EXITING
        elif len(self.path):
            
            self.move()

            if self.cursor.isRoom():
                if self.cursor.coords not in self.history:
                    self.processMessage('The party has encountered an unexplored room. Get the lanterns ready.', True)
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
            self.processMessage('This room is full of monsters! A battle ensues!', True)
            self.status = Expedition.BATTLE
        else:
            self.processMessage('This room is empty, oh well.', True)
            self.status = Expedition.MOVING

    # Exiting
    def runstate_ext(self):
        if self.path:
            self.move()
        else:

            if self.cursor == self.entrance:
                self.processMessage('The party has reached the entrance and left the dungeon.', True)
                self.status = Expedition.COMPLETE
                showOverride = True
            else:
                self.processMessage('Party is ready to leave and plotting a course back to the entrance.', True)
                self.path = self.generatePath(target=self.entrance)

    # Battle
    def runstate_bat(self):
        room = self.dungeon.roomAt(self.cursor)
        if self.battle:
            if self.battle.complete():
                if any([d.canAct() for d in self.party]) :
                    self.processMessage('The party is victorious. Good job team.', True)

                    # clear out the dead monsters
                    self.dungeon.roomAt(self.cursor).empty()
                    self.battle = None

                    self.status = Expedition.RECOVER
                else:
                    self.processMessage('Sadly the party has been slain by the local miscreants.', True)
                    self.status = Expedition.SCATTERED
                self.emitBattle(False, room.num)
            else:
                r1 = self.battle.round()
                self.battle.next()
                r2 = self.battle.round()
                if r1 != r2:
                    return Expedition.TASK_DURATIONS['round_divider']

        else:
            self.battle = Battle(self.processMessage, self.identified_emit)

            for m in room.locals:
                self.battle.addParticipant('monster', m)

            for d in self.party:
                self.battle.addParticipant('delver', d)

            self.emitBattle(True, room.num)
            self.battle.start()


    def runstate_sct(self):
        self.processMessage('Are there survivors? Who knows.')
        self.status = Expedition.COMPLETE

    # Recover
    def runstate_rec(self):
        self.processMessage('The party takes a little breather after a fight.', True)
        # for now we're just gonna heal the entire party so we don't die every other fight
        for p in self.party:
            p.recuperate()

            # this is piggy backing off the battle update emit for now
            body = {
                'source': p.id,
                'target': p.id,
                'dam': -1,
                'newhp': p.maxhp,
                'maxhp': p.maxhp,
                'status': p.status
            }
            self.emit('BTL-UPD;{}'.format(json.dumps(body)))

        self.status = Expedition.MOVING

    # Complete
    def runstate_cmp(self):
        self.processMessage('All done. Good hustle')
        self.processMessage('Total Moves: {}'.format(self.steps))

    def move(self):
        destination = self.path.pop()
        self.cursor = destination
        self.processMessage('Moving to {}'.format(self.cursor.coords))
        self.emitCursorUpdate()

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
        destination = None

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
                destination = lowest
                break
            elif lowest.coords not in self.history:
                # this is the standard exit scenario in which we've found the closest cell not already explored
                destination = lowest
                break

            neighbors = self.dungeon.getNeighbors(lowest)
            for neighbor in [n for n in neighbors if n in q]:
                newDistance = distance[lowest] + 1 if distance[lowest] else 1

                if newDistance < distance[neighbor]:
                    distance[neighbor] = newDistance
                    previous[neighbor] = lowest

        delta = time.perf_counter() - pathingStart

        self.processMessage('** Pathfinding run complete. Time: {}. Cells examined: {}, Cells remaining: {}'.format(str(delta), count, len(q)))

        if not destination:
            # this *shouldn't* be possible as long as mapgen has no significant bugs
            self.processMessage('Pathfinding did not produce a destination')
            return None
        
        path = [destination]
        while(previous.get(destination, False)):
            path.append(previous[destination])
            destination = previous[destination]

        return path