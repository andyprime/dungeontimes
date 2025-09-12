import uuid

from pymongo import MongoClient

class MongoService:

    client = None
    db = None

    COLLECTION_MAP= {
        '<class \'core.dungeon.dungeons.Dungeon\'>': 'dungeons',
        '<class \'core.critters.Delver\'>': 'delvers',
        '<class \'core.region.Region\'>': 'regions',
        '<class \'core.expedition.Expedition\'>': 'expeditions',
        '<class \'core.critters.Band\'>': 'bands'
    }

    @classmethod
    def setup(self, host):
        try:
            self.client = MongoClient(host)
            self.db = self.client.dungeondb
        except Exception as e:
            # this is probably a ConnectionFailure exception but lets wait and see how the connection pooling plays out
            print('Exception during mongo connection')
            print(e)

    @classmethod
    def get_collection(self, obj):
        flat_type = str(type(obj))
        return MongoService.COLLECTION_MAP.get(flat_type, False)

    @classmethod
    def save(self, object):
        collection = self.get_collection(object)

        if collection:
            c = getattr(self.db, collection)

            # Note: Mongo collections don't implement a basic truthiness function so you gotta compare it
            if c != None:
                c.insert_one(object.data_format())
            else: 
                raise ValueError('No collection object found for: {}'.format(collection))
        else:
            raise ValueError('Did not find collection map for type "{}"'.format(collection))

    @classmethod
    def persist(self, object):
        collection = self.get_collection(object)

        if collection:
            c = getattr(self.db, collection)

            if c != None:
                c.replace_one({'id': object.id}, object.data_format())
            else: 
                raise ValueError('No collection object found for: {}'.format(collection))
        else:
            raise ValueError('Did not find collection map for type "{}"'.format(collection))

    @classmethod
    def persist_prop(self, object, prop, value):
        collection = self.get_collection(object)

        if collection:
            c = getattr(self.db, collection)

            if c != None:
                values = {}
                values[prop] = value
                c.update_one({'id': object.id}, {'$set': values})
            else: 
                raise ValueError('No collection object found for: {}'.format(collection))
        else:
            raise ValueError('Did not find collection map for type "{}"'.format(collection))        

class Persister:

    def __init__(self):
        pass

    def data_format(self):
        raise ValueError('You must override the data_format method.')

    def save(self):
        MongoService.save(self)
        return self.id

    def persist(self):
        MongoService.persist(self)
        return self.id

    def persist_prop(self, prop, value):
        MongoService.persist_prop(self, prop, value)
        return self.id