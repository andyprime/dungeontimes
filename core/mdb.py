import uuid

from pymongo import MongoClient

class MongoService:

    PERSIST_MAP= {
        '<class \'core.dungeon.dungeons.Dungeon\'>': 'dungeon',
        '<class \'core.critters.Delver\'>': 'delver',
        '<class \'core.region.Region\'>': 'region'
    }

    def __init__(self, host):
        try:
            self.client = MongoClient(host)
            self.db = self.client.dungeondb
        except Exception as e:
            # this is probably a ConnectionFailure exception but lets wait and see how the connection pooling plays out
            print('Exception during mongo connection')
            print(e)

    def persist(self, object):
        flat_type = str(type(object))
        suffix = MongoService.PERSIST_MAP.get(flat_type, False)

        if suffix:
            f = getattr(self, '_persist_' + suffix)
            if f:
                return f(object)
            else: 
                raise ValueError('Found persist map but no callable for type {}'.format(flat_type))
        else:
            raise ValueError('Did not find persist map for type "{}"'.format(flat_type))
            
    def _persist_dungeon(self, dungeon):
        b = dungeon.serialize()
        dungeon_id = str(uuid.uuid1())
        d = {
            'id': dungeon_id,
            'name': dungeon.name,
            'body': b
        }
        self.db.dungeons.insert_one(d)
        return dungeon_id

    def _persist_delver(self, delver):
        d = delver.serialize()
        self.db.delvers.insert_one(d)
        return d['id']

    def _persist_region(self, region):
        self.db.regions.insert_one(region.serialize(False))
        return region.id

    # expedition is in a funny place right now, so we'll skip the mapping shenanigans for now
    def persist_expedition(self, dungeon_id, delver_ids, entrance_cell):
        e = {
            'id': str(uuid.uuid1()),
            'name': 'PLACEHOLDER',
            'complete': False,
            'dungeon': dungeon_id,
            'party': delver_ids,
            'cursor': entrance_cell
        }
        self.db.expeditions.insert_one(e)
        return e['id']
