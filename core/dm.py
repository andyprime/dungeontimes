import random
import time

from core.dice import Dice
from core.message import Messaging
import core.dungeon.generate
import core.expedition
import core.region
import core.critters


class DungeonMaster:

    TIME_MAP = {
        'exp': 20,
        'plan': 20,
        'research': 20,
        'carouse': 60,
        'shop': (20,30),
        'train': (60.80),
        'idle': (60, 80),
        'advance': 20,
        'offload': 20,
        'restock': (5000, 8000),
        'downtime': 50,
        'downtime_end': 100,
        'downtime_move': (20, 30),
        'exp_delay': 500 # time after an expedition before a band can start another to allow downtime
    }

    def __init__(self, options):
        self.outputfn = options.get('output')
        self.band_count = options.get('bands')
        self.dungeon_count = options.get('dungeons')
    
    def eventsaver(self, type, object, msg, transient=False):
        self.db.save_event(type, object, msg, transient)

    def setup(self):
        # build region
        self.region = core.region.RegionGenerate.generate_region()
        self.region.save()
        
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
                Messaging.emit_message('Aspiring delvers have formed a new band, {}.'.format(b.name), b)
                Messaging.emit_basic('bands', [self.region])
                
            # 2. Check to see if any bands don't have anything to do
            for band_id, band in self.bands.items():
                if not any(t.get('id') == band_id for t in self.to_do):
                    print('Band {} has nothing to do'.format(band.name))

                    # possible actions
                    #   - offload loot, takes precedence
                    #   - plan expedition
                    #   - downtime
                    #   - research dungeons

                    if band.has_loot():
                        selected = 'offload'
                    elif band.wants_downtime(self.current_time):
                        selected = 'downtime'
                    else:
                        options = ['downtime']

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
            self.current_time = int(do['schedule'])

            f = getattr(self, 'action_' + do['action'])
            if callable(f):
                f(do)

            # we batch the emission of the dungeon entrance message
            if dungeon_changes:
                self.region.emit_dungeon_locales()


    def action_exp(self, do):
        band = self.bands[do['id']]
        exp = self.expeditions[do['id']]

        if exp.over():
            # process the turn so we don't skip tasks in the final step
            exp.process_turn()

            self.region.remove_dungeon(exp.dungeon)
            self.region.emit_del_dungeon(exp.dungeon)
            self.region.persist()

            exp.dungeon.complete = True
            exp.dungeon.persist()

            exp.emit_delete()
            exp.persist()
            dungeon_changes = True

            del self.expeditions[band.id]
            del self.dungeons[exp.dungeon.id]

            if exp.failed():
                Messaging.emit_message('{} have been defeated with the dungeon, who knows if any survive.'.format(band.name), [self.region, band, exp])
                del self.bands[band.id]
                band.active = False
                band.persist()
            else:
                band.last_exp = self.current_time
                Messaging.emit_message('{} have returned from their daring dungeon expedition.'.format(band.name), [self.region, band, exp])

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

            exp.register_processor(self.outputfn)
            exp.emit_new()

            Messaging.emit_message('{} have planned an expedition to {}.'.format(band.name, dungeon.name), [self.region, exp, band, dungeon])

            self.expeditions[band.id] = exp

            self.new_task('exp', band.id)

        else:
            Messaging.emit_message('{} were going to plan an expedition to the last dungeon but someone beat them to it.'.format(band.name), [self.region, band])

    def action_research(self, do):
        band = self.bands[do['id']]

        d = self.build_dungeon()
        self.dungeons[d.id] = d
        self.region.place_dungeon(d)
        self.dungeon_changes = True

        Messaging.emit_message('{} have been asking around and heard rumors about the location of {}.'.format(band.name, d.name), [self.region, band, d])
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

            loot = [i for i in delver.inventory if i.useless()]

            if len(loot) > 0:
                item = random.choice(loot)
                delver.inventory.remove(item)
                print('Selling item: {} at {}'.format(item.name, item.value))
                delver.add_wealth(item.value)
                delver.persist()
                Messaging.emit_message('{} sold {} for {} coins.'.format(delver.name, item.name, item.value), [self.region, delver])
                band.add_wealth(item.value)
                band.persist()
                Messaging.emit_basic('band', [self.region, band])

                break

    def action_downtime(self, do):
        band = self.bands[do['id']]

        band.last_downtime = self.current_time
        Messaging.emit_message('{} split up to get some things done.'.format(band.name), [band, self.region])
        
        partiers = []
        for delver in band.members:
            if delver.can_advance():
                options = ['advance']
            else:
                options = ['train', 'idle']
                if delver.will_carouse():
                    options.append('carouse')
                if delver.will_shop():
                    options.append('shop')

                options += delver.valid_moves('downtime')

            selection = random.choice(options)
            if selection == 'carouse':
                partiers.append(delver)
            else:

                if type(selection) == str:
                    self.new_task(selection, band.id, extras=delver.id)
                else:
                    self.new_task('downtime_move', band.id, extras = {'delver': delver.id, 'move': selection})

        if len(partiers):
            self.new_task('carouse', band.id, extras=[d.id for d in partiers])

        self.new_task('downtime_end', band.id)

    def action_downtime_end(self, do):
        # we don't really do anything here, this just gets put into the to dos so the band has an active task
        band = self.bands[do['id']]
        Messaging.emit_message('{} are done with their downtime.'.format(band.name), [self.region, band])

    def action_advance(self, do):
        band = self.bands[do['id']]
        delver = band.get(do['extras'])

        if delver.can_advance():
            increase = delver.advance()
            
            delver.persist()
            
            name1 = core.critters.Creature.ATTRIBUTE_NAMES[increase[0][0]]
            name2 = core.critters.Creature.ATTRIBUTE_NAMES[increase[1][0]]

            Messaging.emit_message('{} has advanced to level {}.'.format(delver.name, delver.level), [self.region, delver])
            Messaging.emit_message('{} has increased {} by {} and {} by {}.'.format(delver.name, name1, increase[0][1], name2, increase[1][1]), [self.region, delver])
            Messaging.emit_basic('band', [self.region, band])
        else:
            raise ValueError('Somehow tried to advance someone that can not: {} {}'.format(delver.name, delver.id))

    def action_downtime_move(self, do):
        band = self.bands[do['id']]
        delver = band.get(do['extras']['delver'])
        move = do['extras']['move']

        if hasattr(move, 'summon'):
            follower = core.critters.Follower.generate(move.summon['type'], move.summon['rank'])
            delver.acquire_follower(follower)

            delver.persist()
            Messaging.emit_basic('band', [self.region, band])

            Messaging.emit_message('{} did a downtime move {}.'.format(delver.name, move.name), [self.region, delver])
        else:
            raise ValueError('Tried to process a downtime move with no known handling: {}'.format(move))

    def action_carouse(self, do):
        band = self.bands[do['id']]
        delvers = [band.get(d) for d in do['extras']]

        for delver in delvers:
            delver.spend_wealth(min(delver.wealth, Dice.roll('3d20')))

        if len(delvers) == 1:
            msg = '{} is going on a long bender.'.format(delvers[0].name)
        else:
            first = ', '.join(d.name for d in delvers[0:len(delvers)-1])
            msg = '{}, and {} are going on a long bender. '.format(first, delvers[-1].name)

        Messaging.emit_message(msg, [self.region, band] + delvers)
        
    def action_shop(self, do):
        band = self.bands[do['id']]
        delver = band.get(do['extras'])

        shops = [v for v in self.region.city.venues if v.type == core.region.Venue.SHOP]
        guilds = [v for v in self.region.city.venues if v.type == core.region.Venue.GUILD]

        if delver.follower_cap() > 0:
            options = shops + guilds
            weights = [2]*len(shops) + [1]*len(guilds)
            shop = random.choices(options, weights)[0]
        else:
            shop = random.choice(shops)

        if shop.type == core.region.Venue.SHOP:
            # will_buy is (intentionally) not deterministic so we must preserve the answer
            thoughts = {i: delver.will_buy(i) for i in shop.stock}
            options = {i: j for i, j in thoughts.items() if j}
            
            if len(options):    
                item = random.choice(list(options.keys()))

                if type(options[item]) != bool:
                    delver.purchase(item, options[item])
                else:
                    delver.purchase(item)
                shop.remove_item(item)

                delver.persist()
                self.region.city.persist()
                Messaging.emit_basic('band', [self.region, band])
                self.region.emit_self()
                Messaging.emit_message('{} bought a brand new {} at {}.'.format(delver.name, item.name, shop.name), [self.region, delver])
            else:
                Messaging.emit_message('{} went shopping at {} but nothing looked good.'.format(delver.name, shop.name), [self.region, delver])
        else:
            for fol in shop.stock:
                if delver.will_hire(fol):

                    delver.acquire_follower(fol)
                    delver.persist()
                    shop.remove_item(fol)

                    self.region.city.persist()
                    Messaging.emit_basic('band', [self.region, band])
                    self.region.emit_self()
                    Messaging.emit_message('{} hired {} the {} at {}.'.format(delver.name, fol.name, fol.model.name, shop.name), [self.region, delver])
                    break

            Messaging.emit_message('{} went to {} but decided against hiring anyone.'.format(delver.name, shop.name), [self.region, delver])
    
    def action_idle(self, do):
        band = self.bands[do['id']]
        delver = band.get(do['extras'])

        Messaging.emit_message('{} spends their free time mostly farting around.'.format(delver.name), [self.region, delver])

    def action_train(self, do):
        band = self.bands[do['id']]
        delver = band.get(do['extras'])

        Messaging.emit_message('{} went on a training montage.'.format(delver.name), [self.region, delver])

    def action_restock(self, do):
        for i in range(5):
            print('!'*50)

        venue = next(v for v in self.region.city.venues if v.id == do['id'])
        venue.restock()
        self.region.city.persist()
        self.region.emit_self()

        self.new_task('restock', venue.id)
