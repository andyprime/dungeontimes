import random

from core.dice import Dice

short_circuit = {
    'exp': 1,
    'plan': 1,
    'research': 1,
    'carouse': 1,
    'medicate': 1,
    'shop': 1,
    'train': 1,
    'idle': 1,
    'advance': 1,
    'offload': 1,
    'restock': (1000, 1200),
    'downtime': 50,
    'downtime_end': 100,
    'downtime_move': (20, 30),
    'band_homework': (100, 200),
    'exp_delay': 50 # time after an expedition before a band can start another to allow downtime        
}

normal_time = {
    'exp': 20,
    'plan': 20,
    'research': 20,
    'carouse': 60,
    'medicate': 60,
    'shop': (20,30),
    'train': (60.80),
    'idle': (60, 80),
    'advance': 20,
    'offload': 20,
    'restock': (5000, 8000),
    'downtime': 50,
    'downtime_end': 100,
    'downtime_move': (20, 30),
    'band_homework': (100, 200),
    'exp_delay': 500 # time after an expedition before a band can start another to allow downtime        
}

TIME_MAP = normal_time

INTERRUPTIBLE = ['train', 'idle', 'carouse']

class _Clock:

    def __init__(self):
        self.now = 1

    def advance(self, newtime):
        if newtime >= self.now:
            self.now = newtime
        else:
            raise ValueError('Time advance failure. {} is less than the current time of {}'.format(newtime, self.now))

clock = _Clock()

class Todo:
    def __init__(self, action, doer=None, **kwargs):
        self.action = action
        self.doer = doer
        self.done = False
        self.trivial = action in INTERRUPTIBLE
        if kwargs.get('extras'):
            self.extras = kwargs['extras']
        else:
            self.extras = None
        if kwargs.get('start'):
            self.start = kwargs.get('start')
        else:
            self.start = clock.now
        if kwargs.get('schedule'):
            self.end = self.start + kwargs.get('schedule')
        else:
            duration = TIME_MAP[action]
            if type(duration) == tuple:
                t = random.uniform(duration[0], duration[1])
            elif type(duration) == str:
                t = Dice.roll(duration)
            else:
                t = duration
            self.end = self.start + t

    def between(self, now):
        return now >= self.start and now <= self.end

    def finish(self):
        self.done = True

    def __repr__(self):
        return 'Todo {}- {} - {}'.format('(X)' if self.done else '', self.action, self.doer.name if self.doer else '')
