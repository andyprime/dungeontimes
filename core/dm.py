import random
import time

import core.time as Time

from core.dice import Dice
from core.message import Messaging, MessageLevel
import core.dungeon.generate
import core.expedition
import core.region
import core.critters

# def finisher(func):
#     def inner(*args):
#         func(*args)
#         args[1].finish()
#     return inner

class DungeonMaster:

    def __init__(self, options):
        self.outputfn = options.get('output')
        self.band_count = options.get('bands')
        self.dungeon_count = options.get('dungeons')
    
    def setup(self):
        # build region
        self.region = core.region.RegionGenerate.generate_region()
        self.region.save()
        
        # build bands
        self.bands = {}
        for i in range(0, self.band_count):
            b = self.build_party()
            self.bands[b.id] = b
        self.mia = []

        self.dungeons = {}
        self.expeditions = {}

        # seed initial dungeons
        while len(self.dungeons) < self.dungeon_count:
            d = self.build_dungeon()
            self.dungeons[d.id] = d
            self.region.place_dungeon(d)
        
        self.region.persist()
        self.region.emit_dungeon_locales()

        self.todo = []
        
        # setup initial recurring todos
        for venue in self.region.city.venues:
            self.todo.append(Time.Todo('restock', venue))

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

    def band_for(self, delver):
        for band in self.bands.values():
            if delver in band.members:
                return band
        return False

    def available_dungeons(self):
        occupied_dungeons = [e.dungeon.id for e in self.expeditions.values()]
        return [d for d in self.dungeons.values() if d.id not in occupied_dungeons]        

    def run(self):
        # setup longrunning checks
        self.todo.append(Time.Todo('band_homework'))
        
        while True:
            print('New loop, time: {}'.format(Time.clock.now))
            # dungeon_changes = False

            self.todo = [t for t in self.todo if not t.done]

            # Check to see if any bands don't have anything to do
            for band_id, band in self.bands.items():
                options = ['downtime']

                if not band.is_busy():
                    print('Generating todos for {}'.format(band))
                    d = self.available_dungeons()
                    band.generate_todos(d, len(d) / self.dungeon_count)

            todos = []
            for band in self.bands.values():
                x = band.all_todos()
                print(band.name, x)
                todos += x
            print('Final', len(todos))
            if len(todos) > 30:
                pizza.ham()
            todos += self.todo

            # Find the soonest action
            todos.sort(key=lambda a: a.end)
            do = todos.pop(0)
            print('We chose: {}'.format(do))
            time.sleep(do.end - Time.clock.now)
            Time.clock.advance(int(do.end))

            f = getattr(self, 'action_' + do.action)
            if callable(f):
                f(do)
            do.finish()

    def action_band_homework(self, do):
        # 1. Check to see if we lost a band and create a replacement
        if len(self.bands) < self.band_count:
            print('Making new band')
            b = self.build_party()
            self.bands[b.id] = b
            Messaging.emit_message('Aspiring delvers have formed a new band, {}.'.format(b.name), b, level=MessageLevel.MAJOR)
            Messaging.emit_basic('bands', [self.region])
        elif len(self.mia):
            survivor = self.mia.pop()
            state = random.choice([core.critters.DelverStatus.RETIRED, core.critters.DelverStatus.DECEASED])
            survivor.condition = state
            survivor.persist()
            if state == core.critters.DelverStatus.RETIRED:
                Messaging.emit_message('The missing delver {} has escaped the failed expedition but has retired.'.format(survivor.name), [self.region, survivor], level=MessageLevel.MAJOR)
            else:
                Messaging.emit_message('The missing delver {} has not been found and is presumed dead.'.format(survivor.name), [self.region, survivor], level=MessageLevel.MAJOR)

        self.todo.append(Time.Todo('band_homework'))

    def action_exp(self, do):
        band = do.doer
        exp = self.expeditions[band.id]

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

            del self.expeditions[band.id]
            del self.dungeons[exp.dungeon.id]

            if exp.failed():
                Messaging.emit_message('{} have been defeated within the dungeon, who knows if any survive.'.format(band.name), [self.region, band, exp], level=MessageLevel.MAJOR)
                del self.bands[band.id]
                band.active = False
                
                for member in band.members:
                    member.condition = core.critters.DelverStatus.MISSING
                    self.mia.append(member)
                band.persist()
            else:
                band.last_exp = Time.clock.now
                Messaging.emit_message('{} have returned from their daring dungeon expedition.'.format(band.name), [self.region, band, exp], level=MessageLevel.MAJOR)

        else:
            delay = exp.process_turn()
            band.todo.append(Time.Todo('exp', band, schedule=delay))

    def action_plan(self, do):
        band = do.doer
        available_dungeons = self.available_dungeons()

        if len(available_dungeons) > 0:
            dungeon = random.choice(available_dungeons)

            exp = core.expedition.Expedition(self.region, dungeon, band, None)
            exp.save()

            exp.register_processor(self.outputfn)
            exp.emit_new()

            Messaging.emit_message('{} have planned an expedition to {}.'.format(band.name, dungeon.name), [self.region, exp, band, dungeon], level=MessageLevel.MAJOR)

            self.expeditions[band.id] = exp

            next = Time.Todo('exp', band)
            
            band.todo.append(next)
            
        else:
            Messaging.emit_message('{} were going to plan an expedition to the last dungeon but someone beat them to it.'.format(band.name), [self.region, band])

    def action_research(self, do):
        band = do.doer

        d = self.build_dungeon()
        self.dungeons[d.id] = d
        self.region.place_dungeon(d)
        
        Messaging.emit_message('{} have been asking around and heard rumors about the location of {}.'.format(band.name, d.name), [self.region, band, d])
        self.region.emit_new_dungeon(d)
        self.region.persist()

        # adding a little extra chance to keep the dungeon count topped up
        if random.choice([True, False]):
            band.todo.append(Time.Todo('research', band))

    def action_offload(self, do):
        # sell a random loot item from one of the band
        
        if type(do.doer) == core.critters.Band:
            band = do.doer
            participants = band.members()
        else:
            # single delver
            participants = [do.doer]
            band = self.band_for(do.doer)

        # make sure to search the members in a random order so this process isn't deterministic
        order = list(range(0, len(participants)))
        random.shuffle(order)

        for i in order:
            delver = participants[i]

            loot = [i for i in delver.inventory if i.useless()]

            if len(loot) > 0:
                item = random.choice(loot)
                delver.inventory.remove(item)
                delver.add_wealth(item.value)
                delver.persist()
                Messaging.emit_message('{} sold {} for {} coins.'.format(delver.name, item.name, item.value), [self.region, delver])
                band.add_wealth(item.value)
                band.persist()
                Messaging.emit_basic('band', [self.region, band])

                break

    def action_advance(self, do):
        delver = do.doer

        if delver.can_advance():
            increase = delver.advance()
            
            delver.persist()
            
            name1 = core.critters.Creature.ATTRIBUTE_NAMES[increase[0][0]]
            name2 = core.critters.Creature.ATTRIBUTE_NAMES[increase[1][0]]

            Messaging.emit_message('{} has advanced to level {}.'.format(delver.name, delver.level), [self.region, delver], level=MessageLevel.MAJOR)
            Messaging.emit_message('{} has increased {} by {} and {} by {}.'.format(delver.name, name1, increase[0][1], name2, increase[1][1]), [self.region, delver])
            Messaging.emit_basic('band', [self.region, band])
        else:
            raise ValueError('Somehow tried to advance someone that can not: {} {}'.format(delver.name, delver.id))

    def action_medicate(self, do):
        delver = do.doer

        # for the moment just heal 1 condition regardless of type
        removed = delver.heal_condition('any', 1)
        if removed:
            delver.persist()
            Messaging.emit_message('{} visit the local temple and has been cured of their {}.'.format(delver.name, removed[0].name), [self.region, delver])
        else:
            raise ValueError('Delver with no conditions just tried to medicate: {}'.format(delver.name))


    def action_downtime_move(self, do):
        delver = do.doer
        band = self.band_for(delver)
        move = do.extras['move']

        if hasattr(move, 'summon'):
            follower = core.critters.Follower.generate(move.summon['type'], move.summon['rank'])
            delver.acquire_follower(follower)

            delver.persist()
            Messaging.emit_basic('band', [self.region, band])

            Messaging.emit_message('{} did a downtime move {}.'.format(delver.name, move.name), [self.region, delver])
        else:
            raise ValueError('Tried to process a downtime move with no known handling: {}'.format(move))

    def action_carouse(self, do):
        delver = do.doer
        delver.spend_wealth(min(delver.wealth, Dice.roll('3d20')))

        msg = '{} is going on a long bender.'.format(delver.name)
        Messaging.emit_message(msg, [self.region, delver] )
        
    def action_shop(self, do):
        delver = do.doer
        band = self.band_for(delver)

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
                Messaging.emit_message('{} went shopping at {} but nothing looked good.'.format(delver.name, shop.name), [self.region, delver], level=MessageLevel.TRANSIENT)
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

            Messaging.emit_message('{} went to {} but decided against hiring anyone.'.format(delver.name, shop.name), [self.region, delver], level=MessageLevel.TRANSIENT)
    
    def action_idle(self, do):
        delver = do.doer

        Messaging.emit_message('{} spends their free time mostly farting around.'.format(delver.name), [self.region, delver])

    def action_train(self, do):
        delver = do.doer

        Messaging.emit_message('{} went on a training montage.'.format(delver.name), [self.region, delver])

    def action_restock(self, do):
        venue = do.doer
        venue.restock()
        self.region.city.persist()
        self.region.emit_self()

        self.todo.append(Time.Todo('restock', venue))
