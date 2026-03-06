import random
import time

from core.dice import Dice
import core.dungeon.generate
import core.expedition
import core.region


class DungeonMaster:

    TIME_MAP = {
        'exp': 20,
        'plan': 20,
        'research': 20,
        'carouse': 60,
        'shop': 20,
        'offload': 20,
        'restock': (5000, 8000),
        'exp_delay': 500 # time after an expedition before a band can start another to allow downtime
    }

    def __init__(self, options):
        self.db = options.get('db')
        self.emitfn = options.get('rabbit')
        self.outputfn = options.get('output')
        self.band_count = options.get('bands')
        self.dungeon_count = options.get('dungeons')
    
    def eventsaver(self, type, object, msg, transient=False):
        self.db.save_event(type, object, msg, transient)

    def setup(self):
        # build region
        self.region = core.region.RegionGenerate.generate_region()
        self.region.save()
        self.region.register_emitter(self.emitfn)
        self.region.register_event(self.eventsaver)

        # build bands
        self.bands = {}
        for i in range(0, self.band_count):
            b = self.build_party()
            self.bands[b.id] = b

        self.dungeons = {}
        self.expeditions = {}

        # seed initial dungeons
        while len(self.dungeons) < self.dungeon_count:
            d = self.build_dungeon()
            self.dungeons[d.id] = d
            self.region.place_dungeon(d)
        
        self.region.persist()
        self.region.emit_dungeon_locales()

        self.to_do = []
        self.current_time = 1

        # setup initial recurring todos
        for venue in self.region.city.venues:
            self.new_task('restock', venue.id)
            
    def new_task(self, action, item, **kwargs):
        task = {
            'action': action,
            'id': item,
            }
        if kwargs.get('extras', False):
            task['extras'] = kwargs['extras']
        if kwargs.get('schedule', False):
            task['schedule'] = self.current_time + kwargs.get('schedule')
        else:
            duration = DungeonMaster.TIME_MAP[action]
            if type(duration) == tuple:
                time = random.uniform(duration[0], duration[1])
            elif type(duration) == str:
                time = Dice.roll(duration)
            else:
                time = duration
            task['schedule'] = self.current_time + time

        self.to_do.append(task)

    def build_dungeon(self):
        dungeon = core.dungeon.generate.DungeonFactoryAlpha.generateDungeon({
                'DEFAULT_HEIGHT': 10,
                'DEFAULT_WIDTH': 30,
                'ROOM_HEIGHT_RANGE': (3,4),
                'ROOM_WIDTH_RANGE': (3,8),
                'MAX_SPARENESS_RUNS': 5,
                'MAX_ROOM_ATTEMPTS': 100
            })

        for room in dungeon.rooms:
            for i in range(4):
                room.populate(core.critters.Monster.random())

        dungeon.save()
        return dungeon

    def build_party(self):
        # create party
        delvers = []
        ids = []
        for i in range(4):
            d = core.critters.Delver.random()
            delvers.append(d)
            ids.append(d.save())

        band = core.critters.Band()
        band.members = delvers
        band.save()

        return band

    def run(self):
        while True:
            print('New loop, time: {}'.format(self.current_time))
            dungeon_changes = False

            # 1. Check to see if we lost a band and create a replacement
            if len(self.bands) < self.band_count:
                print('Making new band')
                b = self.build_party()
                self.bands[b.id] = b
                self.region.emit_narrative('Aspiring delvers have formed a new band, {}.'.format(b.name), b.id)
                self.region.emit_bands()

            # 2. Check to see if any bands don't have anything to do
            for band_id, band in self.bands.items():
                if not any(t.get('id') == band_id for t in self.to_do):
                    print('Band {} has nothing to do'.format(band.name))

                    # possible actions
                    #   - offload loot, takes precedence
                    #   - plan expedition
                    #   - carouse
                    #   - shop
                    #   - research dungeons

                    if band.has_loot():
                        selected = 'offload'
                    else:
                        options = []

                        if band.can_carouse():
                            options.append('carouse')
                        if band.can_shop():
                            options.append('shop')

                        occupied_dungeons = [e.dungeon.id for e in self.expeditions.values()]
                        available_dungeons = [d for d in self.dungeons.values() if d.id not in occupied_dungeons]
                        if len(available_dungeons) > 0 and (band.last_exp == None or band.last_exp + DungeonMaster.TIME_MAP['exp_delay'] < self.current_time):
                            options.append('plan')
                        if len(available_dungeons) < int(self.dungeon_count/2):
                            options.append('research')

                        selected = random.choice(options)

                    self.new_task(selected, band_id)
                    
            # 3. Find the soonest action

            self.to_do.sort(key=lambda a: a['schedule'])
            do = self.to_do.pop(0)
            time.sleep(do['schedule'] - self.current_time)
            self.current_time = do['schedule']

            f = getattr(self, 'action_' + do['action'])
            if callable(f):
                f(do)

            # we batch the emission of the dungeon entrance message
            if dungeon_changes:
                region.emit_dungeon_locales()


    def action_exp(self, do):
        band = self.bands[do['id']]
        exp = self.expeditions[do['id']]

        if exp.over():

            self.region.remove_dungeon(exp.dungeon)
            self.region.emit_del_dungeon(exp.dungeon.id)
            self.region.persist()

            exp.dungeon.complete = True
            exp.dungeon.persist()

            exp.emit_delete()
            exp.persist()
            dungeon_changes = True

            del self.expeditions[band.id]
            del self.dungeons[exp.dungeon.id]

            if exp.failed():
                self.region.emit_narrative('{} have been defeated with the dungeon, who knows if any survive.'.format(band.name), band.id)
                del self.bands[band.id]
                band.active = False
                band.persist()
            else:
                band.last_exp = self.current_time
                self.region.emit_narrative('{} have returned from their daring dungeon expedition.'.format(band.name), band.id)

        else:
            delay = exp.process_turn()
            self.new_task('exp', band.id, schedule=delay)

    def action_plan(self, do):
        band = self.bands[do['id']]

        occupied_dungeons = [e.dungeon.id for e in self.expeditions.values()]
        available_dungeons = [d for d in self.dungeons.values() if d.id not in occupied_dungeons]

        if len(available_dungeons) > 0:
            dungeon = random.choice(available_dungeons)

            exp = core.expedition.Expedition(self.region, dungeon, band, None)
            exp.save()

            exp.register_emitter(self.emitfn)
            exp.register_processor(self.outputfn)
            exp.emit_new()
            self.region.emit_narrative('{} have planned an expedition to {}.'.format(band.name, dungeon.name), band.id)

            self.expeditions[band.id] = exp

            self.new_task('exp', band.id)

        else:
            self.region.emit_narrative('{} were going to plan an expedition to the last dungeon but someone beat them to it.')

    def action_research(self, do):
        band = self.bands[do['id']]

        d = self.build_dungeon()
        self.dungeons[d.id] = d
        self.region.place_dungeon(d)
        self.dungeon_changes = True

        self.region.emit_narrative('{} have been asking around and heard rumors about the location of {}.'.format(band.name, d.name), band.id)
        self.region.emit_new_dungeon(d)
        self.region.persist()

        # adding a little extra chance to keep the dungeon count topped up
        if random.choice([True, False]):
            self.new_task('research', band.id)

    def action_offload(self, do):
        # sell a random loot item from one of the band
        band = self.bands[do['id']]

        # make sure to search the members in a random order so this process isn't deterministic
        order = list(range(0, len(band.members)))
        random.shuffle(order)

        for i in order:
            delver = band.members[i]
            if len(delver.inventory) > 0:
                item = delver.inventory.pop()
                print('Selling item: {} at {}'.format(item.name, item.value))
                delver.add_wealth(item.value)
                delver.persist()
                self.region.emit_narrative('{} sold {} for {} coins.'.format(delver.name, item.name, item.value), band.id)
                band.add_wealth(item.value)
                band.persist()
                self.region.emit_band(band)
                break

    def action_carouse(self, do):
        band = self.bands[do['id']]
        self.region.emit_narrative('{} are going on a long bender.'.format(band.name), band.id)
        
    def action_shop(self, do):
        band = self.bands[do['id']]

        # for the moment we're gonna do a little hack to approximate delver specific actions
        order = do.get('extras', {}).get('order', None)
        if not order:
            order = list(range(0, len(band.members)))
            random.shuffle(order)

        delver = band.members[order.pop()]

        shop = random.choice([v for v in self.region.city.venues if v.type == core.region.Venue.SHOP])

        options = [i for i in shop.stock if delver.will_buy(i)]
        
        if len(options):
            item = random.choice(options)

            delver.purchase(item)
            shop.remove_item(item)

            delver.persist()
            self.region.city.persist()
            self.region.emit_band(band)
            self.region.emit_self()
            self.region.emit_narrative('{} bought a brand new {} at {}.'.format(delver.name, item.name, shop.name), band.id)
        else:
            self.region.emit_narrative('{} went shopping at {} but nothing looked good.'.format(delver.name, shop.name), band.id)

        # every one gets a turn before we move on
        if order:
            self.new_task('shop', band.id, extras={'order': order})
                
    def action_restock(self, do):
        for i in range(5):
            print('!'*50)

        venue = next(v for v in region.city.venues if v.id == do['venue'])
        venue.restock()
        region.city.persist()
        region.emit_self()

        to_do.append({'action': 'restock', 'venue': venue.id, 'schedule': current_time + TIME_MAP['restock'] + Dice.roll('1d3') * 1000})
