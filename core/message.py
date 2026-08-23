import json
import pika
from enum import Enum

import core.mdb


class MessageLevel(str, Enum):
    MINOR = 'minor'
    MAJOR = 'major'
    TRANSIENT = 'transient'

class Messaging:

    connection = None
    channel = None

    @classmethod
    def setup(self, host, user, passwd):
        creds = pika.PlainCredentials(user, passwd)
        parameters = (pika.ConnectionParameters(host=host, credentials=creds))
        
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        self.channel.exchange_declare('dungeon', exchange_type='fanout', durable=True)

    @classmethod
    def publish(self, message):
        self.channel.basic_publish(exchange='dungeon', routing_key='*', body=message)

    @classmethod
    def emit(self, msg):
        package = json.dumps(msg)
        self.publish(package.encode('ASCII'))

    @classmethod
    def _build_context(self, objs):
        try:
            iterator = iter(objs)
        except TypeError:
            objs = [objs]

        try:
            return {type(o).__name__.lower(): o.id for o in objs}
        except KeyError as e:
            e.add_note('Problem children: {}'.format(objs))
            raise

    @classmethod
    def emit_message(self, message, context_objects, level=MessageLevel.MINOR):
        try:
            iterator = iter(context_objects)
        except TypeError:
            context_objects = [context_objects]

        shared = {
            'level': level,
            'message': message,
            'context': self._build_context(context_objects),
            'names': {o.id: o.name for o in context_objects if hasattr(o, 'name')}
        }

        self.emit({'type': 'NARRATIVE'} | shared)
        core.mdb.MongoService.save_event('general', [o.id for o in context_objects], shared)

    @classmethod
    def emit_basic(self, type, context_objects):
        msg = {
            'type': type.upper(),
            'context': self._build_context(context_objects)
        }
        self.emit(msg)

    @classmethod
    def emit_coords(self, type, coords, context_objects):
        msg = {
            'type': type.upper(),
            'coords': coords,
            'context': self._build_context(context_objects)
        }
        self.emit(msg)

    @classmethod
    def emit_custom(self, message, context_objects):
        message['context'] = self._build_context(context_objects)
        self.emit(message)