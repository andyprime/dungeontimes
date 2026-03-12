import json
import random
import time
import uuid

from core.battle import Battle
from core.dungeon.dungeons import Cell
from core.mdb import Persister
import core.strings as strings
from core.dice import Dice
import core.doodads as doodads

class Expedition(Persister):

    PREP = 'pre'
    TRAVEL = 'trv'
    READY = 'rdy'
    EXPLORE = 'exp'
    ENCOUNTER = 'enc'
    BATTLE = 'bat'
    RECOVER = 'rec'
    SEARCH = 'src'
    EXITING = 'ext'
    SCATTERED = 'sct'
    COMPLETE = 'cmp'
    ERROR = 'err'
    FAIL = 'fai'

    DEFAULT_TURN_DELAY = 2

    OVERLAND_STATES = ['pre', 'trv', 'sct', 'cmp']
    DUNGEON_STATES = ['rdy', 'exp', 'enc', 'bat', 'rec', 'ext']

    # the abbreviated ones are just the default for any given stage, others need to be manually returned
    TASK_DURATIONS = {
        'pre': 10,
        'trv': 1,
        'rdy': 2,
        'exp': 1.5,
        'enc': 2,
        'bat': 0.1,
        'rec': 2,
        'ext': 2,
        'sct': 2,
        'cmp': 3,
        'src': 3,
        'fai': 3,
        'round_divider': 2
    }

    # Only print the map every X moves
    PRINT_INTERVAL = 5

    def __init__(self, region, dungeon, band, cursor=None, id=None):

        self.region = region
        self.dungeon = dungeon
        self.band = band
        self.party = band.members
        self.battle = None
        self.id = str(uuid.uuid1())
        
        self.status = Expedition.PREP

        self.region_cursor = region.homebase
        self.dungeon_cursor = None

        self.outgoing = True

        self.steps = 0

        # if set it is the cells we are currently trying to navigate through
        self.path = []

        # general data holder for individual steps that doesn't require making top level properties
        self.localstate = {}

        # Got to log which sections of the map have already been explored
        # So for now we're gonna keep the cell coords in an array to reference
        self.history = []
        # self.history.append(self.cursor)

        self.processors = []
        self.emitters = []
        self.event_saver = None

    def __str__(self):
        return 'Expedition object status: {}. Band: {}, Dungeon:  ({})'.format(self.status, self.band.id, self.dungeon.id)

    def __repr__(self):
        return 'Expedition object status: {}. Band: {}, Dungeon:  ({})'.format(self.status, self.band.id, self.dungeon.id)

    def register_processor(self, callback):
        self.processors.append(callback)

    def register_emitter(self, callback):
        self.emitters.append(callback)

    def register_event(self, callback):
        self.event_saver = callback

    def save_event(self, type, objects, msg):
        if callable(self.event_saver):
            self.event_saver(type, objects, msg)

    def prefix(self):
        return self.id[0:10]

    # explicitly for system logging, user facing text goes through emit
    def process_message(self, message):
        message = '{} - {}'.format(self.prefix(), message)
        for f in self.processors:
            f(message)
       
    def _build_context(self):
        context = {
            'expedition': self.id,
            'band': self.band.id
        }
        if self.indungeon:
            context['dungeon'] = self.dungeon.id
        return context

    def emit(self, msg):
        if not msg.get('context', False):
            msg['context'] = self._build_context()
        package = json.dumps(msg)
        for e in self.emitters:
            e(package.encode('ASCII'))

    def emit_cursor(self):
        msg = {
            'type': 'CURSOR',
            'coords': self._get_location(),
        }
        self.emit(msg)

    def emit_narrative(self, s, targets=[]):
        msg = {
            'type': 'NARRATIVE',
            'message': s,
        }

        event_refs = [self.band.id]
        if targets:
            event_refs += targets
        self.save_event('expedition', [self.band.id], s)
        self.emit(msg)

    def emit_new(self):
        msg = {
            'type': 'EXPEDITION-NEW',
        }
        self.emit(msg)

    def emit_delete(self):
        msg = {
            'type': 'EXPEDITION-DEL',
        }
        self.emit(msg)
        
    def emit_battle(self, start, roomNo):
        msg = {
            'room': roomNo,
        }
        if start:
            msg['type'] = 'BATTLE-START'
        else:
            msg['type'] = 'BATTLE-END'
        self.emit(msg)

    def emit_band(self):
        msg = {
            'type': 'BAND',
        }
        self.emit(msg)

    def overland(self):
        return self.status in Expedition.OVERLAND_STATES

    def indungeon(self):
        return self.status in Expedition.DUNGEON_STATES

    def over(self):
        return self.status in [Expedition.COMPLETE, Expedition.ERROR, Expedition.FAIL]

    def failed(self):
        return self.over() and self.status == Expedition.FAIL

    def location(self):
        if self.indungeon():
            return 'D'
        else:
            return 'O'

    def _get_location(self):
        loc = {}
        # can't fix the cell/tuple problem here so just detect it
        dc = self.dungeon_cursor
        if dc:
            if type(dc) != tuple:
                dc = dc.coords
            loc['dungeon'] = dc
        rc = self.region_cursor
        if rc:
            if type(rc) != tuple:
                rc = rc.coords
            loc['region'] = rc

        return loc

    def data_format(self):
        return {
            'id': self.id,
            'name': 'PLACEHOLDER',
            'state': self.status,
            'complete': self.over(),
            'dungeon': self.dungeon.id,
            'band': self.band.id,
            'location': self._get_location()
        }

    def _set_state(self, new_state):
        self.status = new_state
        self.persist()

    def _get_local(self, step):
        if step not in self.localstate:
            self.localstate[step] = {}
        return self.localstate[step]

    def save_local(self, state):
        self.localstate[self.status] = state

    def process_turn(self):
        self.steps += 1
        showOverride = False

        f = getattr(self, 'runstate_' + self.status)
        if f:
            delayOverride = f(self._get_local(self.status))

            if self.steps % Expedition.PRINT_INTERVAL == 0 or showOverride:
                self.history_map()

            if delayOverride:
                return delayOverride
            else:
                return Expedition.TASK_DURATIONS[self.status]
        else:
            self.process_message('Unknown expedition status: {}'.format(self.status))
            self._set_state(Expedition.ERROR)
            return False

    # Home base starting status
    def runstate_pre(self, local):
        self.emit_narrative('{} does some last minute shopping in town. Always pack a spare {}.'.format(self.band.name, strings.StringTool.random('useful_item')))
        self._set_state(Expedition.TRAVEL)

    # overland travel
    def runstate_trv(self, local):
        if self.outgoing:
            target = self.region.find_dungeon(self.dungeon.id)
        else:
            target = self.region.getCell(*self.region.homebase)

        if self.region_cursor == target:
            if self.outgoing:
                self.emit_narrative('{} has located the entrance to the dungeon.'.format(self.band.name))
                self._set_state(Expedition.READY)
            else:
                self.emit_narrative('{} has returned home for some well deserved rest.'.format(self.band.name))
                self._set_state(Expedition.COMPLETE)
        elif self.path:
            self.move()
        else:
            self.process_message('Pathing to {}'.format(target))
            self.path = self.generate_path(self.region_cursor, self.region, target)

    # Ready
    def runstate_rdy(self, local):
        self.emit_narrative('The band enters the dungeon, adjusting to the dim light.')
        self.dungeon_cursor = self.dungeon.entrance()
        self.history.append(self.dungeon_cursor.coords)
        self.path = []
        self._set_state(Expedition.EXPLORE)

    # Moving
    def runstate_exp(self, local):
        if not self.path:
            self.path = self.navigate()

        if self.path is None:
            self.process_message('Dungeon fully explored.')
            self.emit_narrative('The band thinks there is no more to explore down here, time to navigate back home.')
            self._set_state(Expedition.EXITING)
        elif len(self.path):
            
            self.process_message('Standard dungeon move')

            self.move()

            if self.dungeon_cursor.isRoom():
                if self.dungeon_cursor.coords not in self.history:
                    self.emit_narrative('The band has encountered an unexplored room. Get the lanterns ready.')
                    self._set_state(Expedition.ENCOUNTER)

                # TODO: move this to the encounter complete section?
                for cell in self.dungeon.roomBrethren(self.dungeon_cursor):
                    if cell not in self.history:
                        self.history.append(cell.coords)

            else:
                self.history.append(self.dungeon_cursor.coords)
        else:
            self.process_message('Moving algorithm did not produce a destination')
            self._set_state(Expedition.ERROR)

    # Encounter
    def runstate_enc(self, local):

        if self.dungeon.roomAt(self.dungeon_cursor).occupied():
            self.emit_narrative('This room is full of jerks! Draw your blades!')
            self._set_state(Expedition.BATTLE)
        else:
            self.emit_narrative('This room is empty, oh well.')
            self._set_state(Expedition.EXPLORE)

    # Exiting
    def runstate_ext(self, local):
        if self.path:
            self.move()
        else:

            if self.dungeon_cursor == self.dungeon.entrance():
                self.emit_narrative('{} has emerged from the depths of {}.'.format(self.band.name, self.dungeon.name))
                self._set_state(Expedition.TRAVEL)
                # this may no longer be necessary
                # self.region_cursor = self.region.find_dungeon(self.dungeon.id)
                self.path = []
                self.outgoing = False
                showOverride = True
            else:
                self.process_message('Party is ready to leave and plotting a course back to the entrance.')
                self.path = self.generate_path(self.dungeon_cursor, self.dungeon, target=self.dungeon.entrance())

    # Battle
    def runstate_bat(self, local):
        room = self.dungeon.roomAt(self.dungeon_cursor)
        if self.battle:
            if self.battle.complete():
                if any([d.canAct() for d in self.party]) :
                    self.emit_narrative('The band is victorious. Good job team.')

                    # clear out the dead monsters
                    self.dungeon.roomAt(self.dungeon_cursor).empty()
                    self.battle = None

                    self._set_state(Expedition.RECOVER)
                else:
                    self.emit_narrative('Sadly the band has been bested by the local miscreants.')
                    self._set_state(Expedition.SCATTERED)
                self.emit_battle(False, room.num)
            else:
                r1 = self.battle.round()
                self.battle.next()
                r2 = self.battle.round()
                if r1 != r2:
                    return Expedition.TASK_DURATIONS['round_divider']

        else:
            self.battle = Battle(self.process_message, self.emit)

            for m in room.locals:
                self.battle.addParticipant('monster', m)

            for d in self.party:
                self.battle.addParticipant('delver', d)

            self.emit_battle(True, room.num)
            self.battle.start()


    def runstate_sct(self, local):
        self.process_message('Band is scattering')
        self.emit_narrative('Our intrepid band has been scattered to the five winds. Who knows what will become of them.')
        self._set_state(Expedition.FAIL)

    def runstate_fai(self, local):
        self.process_message('Entering expeditoin failure state.')

    # Recover, general post-battle business
    def runstate_rec(self, local):
        self.emit_narrative('The band takes a little breather after a fight.')
        # for now we're just gonna heal the entire party so we don't die every other fight
        for p in self.party:
            p.recuperate()

            # this is piggy backing off the battle update emit for now which is why it doesn't get a dedicated function
            body = {
                'type': 'BATTLE-UPDATE',
                'context': {
                    'expedition': self.id,
                    'band': self.band.id,
                    'dungeon': self.dungeon.id
                },
                'details': {
                    'source': p.id,
                    'target': p.id,
                    'dam': -1,
                    'newhp': p.maxhp,
                    'maxhp': p.maxhp,
                    'status': p.status
                }
            }
            self.emit(body)
        
        self._set_state(Expedition.SEARCH)

    # room search
    def runstate_src(self, local):

        remaining = local.get('remaining', None)
        if remaining != None:

            if remaining > 0:

                pos = remaining % self.band.size()
                delver = self.band.members[pos]

                success = random.uniform(1, 100) > 50

                if success:

                    type = random.uniform(1, 100)

                    if type < 70:
                        item = doodads.Valuable.generate()
                    elif type < 90:
                        item = doodads.Consumable.generate()
                    else:
                        item = doodads.Equipable.generate()

                    if delver.will_wear(item):
                        delver.wear(item)
                        delver.persist()
                        self.emit_narrative('{} found {} and put it on.'.format(delver.name, item.name), [delver.id])
                        self.emit_band()
                    elif delver.can_hold(item):
                        delver.give(item)
                        delver.persist()
                        self.emit_narrative('{} found {}'.format(delver.name, item.name), [delver.id])
                        self.emit_band()
                else:
                    self.emit_narrative('{} found {}, but it is worthless.'.format(delver.name, strings.StringTool.random('junk', indefinite=True)), [delver.id])    

                local['remaining'] = remaining - 1

            else:
                self.save_local({})
                self.emit_narrative('There is no more loot to find here.')
                self._set_state(Expedition.EXPLORE)

        else:
            self.emit_narrative('Everyone starts turning the room over for treasure.')
            local['remaining'] = Dice.roll('2d3')
            local['order'] = random.shuffle(list(range(0, self.band.size())))
            

    # Complete
    def runstate_cmp(self):
        self.process_message('All done. Good hustle')
        self.process_message('Total Moves: {}'.format(self.steps))

    def move(self):
        destination = self.path.pop()

        if self.location() == 'D':
            self.dungeon_cursor = destination
            self.process_message('Moving to D {}'.format(self.dungeon_cursor.coords))
        else:
            self.region_cursor = destination
            self.process_message('Moving to R {}'.format(self.region_cursor.coords))
    
        self.emit_cursor()
        self.persist()

    def history_map(self):
        if self.indungeon():
            for index, row in enumerate(self.dungeon.grid):
                display = '{}: '.format(str(index).rjust(4, ' '))

                for cell in row:
                    if cell == self.dungeon_cursor:
                        display += 'P'
                    elif self.path and cell in self.path:
                        display += '\033[93m' + cell.positiveSymbol() + '\033[0m'
                    elif cell.coords in self.history:
                        display += '\033[94m' + cell.positiveSymbol() + '\033[0m'
                    else:
                        display += cell.symbol()
                print(display)
        else:
            self.region.prettyPrint(self.region_cursor, self.path)
        print('\n')

    def navigate(self):
        # this is broken out to support future plans to provide different navigation approaches

        # just going to implement a real basic navigation system for now
        # if there are unexplored cells adjacent to our current location just pick one at random and go there
        # otherwise find the closest unexplored cell and chart a course to there

        neighbors = self.dungeon.getNeighbors(self.dungeon_cursor)
        easyDirections = [n for n in neighbors if n.coords not in self.history]

        if easyDirections:
            return [random.choice(easyDirections)]
        else:
            # time to Dijkstra
            return self.generate_path(self.dungeon_cursor, self.dungeon)

    def generate_path(self, start, grid, target=None):
        # just a basic dijkstra implementation that stops once it finds an unexplored cell

        if type(start) == tuple:
            start = grid.getCell(*start)

        if type(target) == tuple:
            target = grid.getCell(*target)

        pathingStart = time.perf_counter()

        distance = {}
        previous = {}
        q = []
        destination = None

        for cell in grid.allCells(navigable=True):
            distance[cell] = 1000000
            previous[cell] = None
            q.append(cell)

        distance[start] = 0

        count = 0
        while len(q) > 0:
            count += 1
            lowest = q[0]
            for cell in q:
                if distance[cell] < distance[lowest]:
                    lowest = cell
            q.remove(lowest)

            # Our break points are finding the optionally provided target cell, or otherwise the closest unexplored cell
            if target and lowest == target:
                destination = lowest
                break
            elif not target and lowest.coords not in self.history:
                destination = lowest
                break

            neighbors = grid.getNeighbors(lowest)
            for neighbor in [n for n in neighbors if n in q]:
                weight = grid.getWeight(neighbor)
                newDistance = distance[lowest] + weight if distance[lowest] else weight

                if newDistance < distance[neighbor]:
                    distance[neighbor] = newDistance
                    previous[neighbor] = lowest

        delta = time.perf_counter() - pathingStart

        self.process_message('** Pathfinding run complete. Time: {}. Cells examined: {}, Cells remaining: {}'.format(str(delta), count, len(q)))

        if not destination:
            # this *shouldn't* be possible as long as mapgen has no significant bugs
            self.process_message('Pathfinding did not produce a destination')
            return None
        
        path = [destination]
        while(previous.get(destination, False)):
            path.append(previous[destination])
            destination = previous[destination]

        return path