import json
import random
import time
import uuid

from core.message import Messaging, MessageLevel
from core.battle import Battle
from core.dungeon.dungeons import DungeonCell
from core.mdb import Persister
import core.strings as strings
from core.dice import Dice
import core.doodads as doodads

from definitions.model import Condition

class Expedition(Persister):

    PREP = 'pre'
    TRAVEL = 'trv'
    READY = 'rdy'
    EXPLORE = 'exp'
    ENCOUNTER = 'enc'
    BATTLE = 'bat'
    TRAP = 'trp'
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
        'trp': 2,
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
        self.battle = None
        self.id = str(uuid.uuid1())
        
        self.status = Expedition.PREP

        self.region_cursor = region.homebase
        self.dungeon_cursor = None

        self.outgoing = True

        self.steps = 0
        self.score = 0

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

    def prefix(self):
        return self.id[0:10]

    # explicitly for system logging, user facing text goes through emit
    def process_message(self, message):
        message = '{} - {}'.format(self.prefix(), message)
        for f in self.processors:
            f(message)

    def emit_cursor(self):
        Messaging.emit_coords('CURSOR', self._get_location(), [self, self.band])
        
    def emit_narrative(self, s, delver=None, level=MessageLevel.MINOR):
        if delver:
            objs = [self, delver]
        else:
            objs = [self, self.band]
        if self.indungeon:
            objs.append(self.dungeon)

        Messaging.emit_message(s, objs, level=level)

    def emit_new(self):
        Messaging.emit_basic('EXPEDITION-NEW', [self, self.band])

    def emit_delete(self):
        Messaging.emit_basic('EXPEDITION-DEL', [self, self.band])

    def emit_battle(self, start, roomNo):
        msg = {
            'room': roomNo,
        }
        if start:
            msg['type'] = 'BATTLE-START'
        else:
            msg['type'] = 'BATTLE-END'
        Messaging.emit_custom(msg, [self, self.band, self.dungeon])

    def emit_band(self):
        Messaging.emit_basic('BAND', [self.band])

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
            loc['dungeon'] = dc[0:2]
        rc = self.region_cursor
        if rc:
            loc['region'] = rc[0:2]

        return loc

    def data_format(self):
        return {
            'id': self.id,
            'name': 'PLACEHOLDER',
            'state': self.status,
            'complete': self.over(),
            'dungeon': self.dungeon.id,
            'band': self.band.id,
            'location': self._get_location(),
            'score': self.score
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
        self.history.append(self.dungeon_cursor)
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
                if self.dungeon_cursor not in self.history:
                    self.emit_narrative('The band has encountered an unexplored room. Get the lanterns ready.')
                    self._set_state(Expedition.ENCOUNTER)

                # TODO: move this to the encounter complete section?
                for cell in self.dungeon.roomBrethren(self.dungeon_cursor):
                    if cell not in self.history:
                        self.history.append(cell)
            elif self.dungeon_cursor in self.dungeon.traps.keys():
                self._set_state(Expedition.TRAP)
            else:
                self.history.append(self.dungeon_cursor)
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
                if any([d.canAct() for d in self.band.members]) :
                    self.emit_narrative('The band is victorious. Good job team.')

                    # clear out the dead monsters
                    self.dungeon.roomAt(self.dungeon_cursor).empty()
                    self.battle = None

                    self._set_state(Expedition.RECOVER)
                else:
                    self.emit_narrative('Sadly the band has been bested by the local miscreants.', None, MessageLevel.MAJOR)
                    self._set_state(Expedition.SCATTERED)
                self.emit_battle(False, room.num)
            else:
                r1 = self.battle.round()
                self.battle.next()
                r2 = self.battle.round()
                if r1 != r2:
                    return Expedition.TASK_DURATIONS['round_divider']

        else:
            self.battle = Battle(self.process_message, [self, self.dungeon])

            for m in room.locals:
                self.battle.addParticipant('monster', m)

            for d in self.band.members:
                self.battle.addParticipant('delver', d)

            self.emit_battle(True, room.num)
            self.battle.start()

    def runstate_trp(self, local):
        Messaging.cprint('*'*30)
        trap = self.dungeon.traps[self.dungeon_cursor]

        Messaging.cprint(trap)
        if trap.safe():
            # Test Safe - trap is no longer dangerous, move on
            Messaging.cprint('Safe')

            self.emit_narrative('The trap has been dealt with and the band moves on.')
            # finally mark the trap cell as explored
            self.history.append(self.dungeon_cursor)
            self._set_state(Expedition.EXPLORE)
        elif trap.spotted():
            # Test Spotted - trap is detected and still dangerous, select a resolution method       
            Messaging.cprint('Spotted')

            disabler = local.get('disabler')
            bypass = local.get('bypass')

            if disabler:
                Messaging.cprint('Disabler selected')
                v = disabler.calc_test_value(trap.model.avoid[0], trap.model.avoid[1])
                threshold = Dice.perform_test_100(v)
                if threshold > 0:
                    Messaging.cprint('Disarmed')
                    trap.disable()
                    self.emit_narrative('{} has successfully disabled the trap.')
                    disabler.apply_xp(1)

                else:
                    Messaging.cprint('Disarm failed')
                    s, d = self._apply_trap(trap, disabler)
                    self.emit_narrative(s)

            elif bypass:

                Messaging.cprint('Bypassing')
                if trap.model.bypass == 'AUTO':
                    trap.bypass()
                    self.emit_narrative('The band is able to easily bypass this trap.')
                else:
                    
                    for delver in self.band.members_by_health():
                        v = delver.calc_test_value(trap.model.bypass[0], trap.model.bypass[1])
                        threshold = Dice.perform_test_100(v)
                        if threshold > 0:
                            self.emit_narrative('{} has scooted past the trap safely.'.format(delver.name))
                            Messaging.cprint('{} by pass success'.format(delver.name))
                        else:
                            s, d = self._apply_trap(trap, delver)
                            self.emit_narrative(s)
                            
                        if trap.safe():
                            self.emit_narrative('The trap is spent and the remaining delvers may pass by.')
                            break

                    trap.bypass()
            
            else:
                # check for disable volunteers
                for delver in self.band.members_random():
                    
                    if delver.gauge_task(trap.model.disable[0], trap.model.disable[1]):
                        local['disabler'] = delver
                        self.emit_narrative('{} has volunteered to disable the trap.'.format(delver.name))
                        Messaging.cprint('Disabler selected')
                        break
                # if no one wants to disable the only option right now is bypass
                if not local.get('disabler'):
                    local['bypass'] = True
                    Messaging.cprint('Bypass selected')
                    self.emit_narrative('No one wishes to disable the trap so the band will attempt to bypass it.')

        else:
            # Trap Hidden - base state, test for spotting

            Messaging.cprint('They dont see it yet')

            spotter = None
            randos = self.band.members_random()
            for delver in randos:
                v = delver.calc_test_value('PERSPICACITY', trap.model.spot) 
                threshold = Dice.perform_test_100(v)
                if threshold > 0:
                    spotter = delver
                    break
            if spotter:
                # End Case - trap found, move on to solution next turn
                trap.spot()
                self.emit_narrative('The band is creeping along when suddenly {} spots a {} trap.'.format(spotter.name, trap.name))
            else:
                # End Case - trap fires, next turn its new state will be evaluated
                self.emit_narrative('The band have walked into a {} trap unaware.'.format(trap.name))
                hit = randos[0:trap.model.targets]
                for delver in hit:
                    v = delver.calc_test_value(trap.model.avoid[0], trap.model.avoid[1])
                    threshold = Dice.perform_test_100(v)
                    if threshold > 0:
                        self.emit_narrative('{} managed to scoot out of the way.'.format(delver.name))
                    else:
                        s, d = self._apply_trap(trap, delver)
                        self.emit_narrative(s)

    def _apply_trap(self, trap, delver):
        trap.spring()
        d = 0
        addendum = '.'
        if trap.model.effect.get('condition'):
            c = Condition.find(trap.model.effect['condition'])
            delver.apply_condition(trap.model.effect['condition'])
            addendum = ', and was affected by {}.'.format(c.name)
        if trap.model.effect.get('damage'):
            d = Dice.roll(trap.model.effect['damage'])
            delver.apply_damage(d)
        s = '{} was caught and received {} damage{}'.format(delver.name, d, addendum)
        return s, d

    def runstate_sct(self, local):
        self.process_message('Band is scattering')
        self.emit_narrative('Our intrepid band has been scattered to the five winds. Who knows what will become of them.', None, MessageLevel.MAJOR)
        self._set_state(Expedition.FAIL)

    def runstate_fai(self, local):
        self.process_message('Entering expedition failure state.')

    # Recover, general post-battle business
    def runstate_rec(self, local):
        self.emit_narrative('The band takes a little breather after a fight.')
        # for now we're just gonna heal the entire party so we don't die every other fight
        for delver in self.band.members:
            if delver.currenthp == 0:
                # being defeated gives a delver a random condition
                condition = Condition.random(lambda c: c.type in ['injury', 'mental'])
                print('<'*50)
                print('{} got condition {}'.format(delver.name, condition.name))
                delver.apply_condition(condition)
                self.emit_narrative('{} has recovered but has developed a {}'.format(delver.name, condition.name), delver, MessageLevel.MAJOR)

            delver.recuperate()
            delver.persist()

            # this is piggy backing off the battle update emit for now which is why it doesn't get a dedicated function
            body = {
                'type': 'BATTLE-UPDATE',
                'details': {
                    'source': delver.id,
                    'target': delver.id,
                    'dam': -1,
                    'newhp': delver.maxhp,
                    'maxhp': delver.maxhp,
                    'status': delver.status
                }
            }
            Messaging.emit_custom(body, [self, self.band, self.dungeon])
        
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

                    roll = random.uniform(1, 100)

                    if roll < 60:
                        item = doodads.Valuable.generate()
                    elif roll < 80:
                        item = doodads.Consumable.generate()
                    elif roll < 90:
                        item = doodads.Tool.generate()
                    else:
                        item = doodads.Equipable.generate()

                    if replace := delver.will_use(item):
                        if type(replace) == bool:
                            delver.wear(item)
                        else:
                            delver.wear(item, replace)
                        delver.persist()
                        self.emit_narrative('{} found {} and put it on.'.format(delver.name, item.name), delver)
                        self.emit_band()
                    elif item.useless() and delver.can_hold(item):
                        # for now only keep treasure items
                        delver.give(item)
                        delver.persist()
                        self.emit_narrative('{} found {}'.format(delver.name, item.name), delver)
                        self.emit_band()
                else:
                    self.emit_narrative('{} found {}, but it is worthless.'.format(delver.name, strings.StringTool.random('junk', indefinite=True)), delver, MessageLevel.TRANSIENT)    

                local['remaining'] = remaining - 1

            else:
                self.save_local({})
                self.emit_narrative('There is no more loot to find here.', None, MessageLevel.TRANSIENT)
                self._set_state(Expedition.EXPLORE)

        else:
            self.emit_narrative('Everyone starts turning the room over for treasure.')
            local['remaining'] = Dice.roll('2d3')
            local['order'] = random.shuffle(list(range(0, self.band.size())))
            

    # Complete
    def runstate_cmp(self, local):
        self.process_message('All done. Good hustle')
        self.process_message('Total Moves: {}'.format(self.steps))

        for mem in self.band.members:
            self.score += sum([item.value for item in mem.inventory])
        # we don't need to persist this change because it will get batched with later steps in the DM

        self.process_message('Expedition finished with a score of: {}'.format(self.score))

    def move(self):
        destination = self.path.pop()

        if self.location() == 'D':
            self.dungeon_cursor = destination
            self.process_message('Moving to D {}'.format(self.dungeon_cursor))
        else:
            self.region_cursor = destination
            self.process_message('Moving to R {}'.format(self.region_cursor))
    
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
                    elif cell in self.history:
                        display += '\033[94m' + cell.positiveSymbol() + '\033[0m'
                    else:
                        if cell in self.dungeon.traps.keys():
                            display += '*'
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
        easyDirections = [n for n in neighbors if n not in self.history]

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
            elif not target and lowest not in self.history:
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