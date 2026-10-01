from enum import Enum

# note that some of these states are functionally identically but have record keeping value
class TrapStatus(str, Enum):
    HIDDEN = 'hidden'       # starting state
    DETECTED = 'detected'   # delvers have found it before tripping it
    SPRUNG = 'sprung'       # trap has gone off but is still live
    SPENT = 'spent'         # trap has gone off and is no longer dangerous
    DISABLED = 'disabled'   # trap has been disabled by delvers
    BYPASSED = 'bypassed'   # still live but the delvers know how to avoid it

class Trap:

    def __init__(self, model):
        self.name = model.name
        self.code = model.code
        self.model = model

        self.charges = model.charges
        self.state = TrapStatus.HIDDEN

    def live(self):
        return self.state in [TrapStatus.HIDDEN, TrapStatus.DETECTED, TrapStatus.SPRUNG]

    def safe(self):
        return not self.live()

    def spotted(self):
        return self.state != TrapStatus.HIDDEN

    def spot(self):
        if self.state == TrapStatus.HIDDEN:
            self.state = TrapStatus.DETECTED
        else:
            raise ValueError('Attempt to spot unhidden trap in invalid state: {}'.format(self))

    def disable(self):
        if self.state in [TrapStatus.DETECTED, TrapStatus.SPRUNG]:
            self.state = TrapStatus.DISABLED
        else:
            raise ValueError('Attempt to disable trap in invalid state: {}'.format(self))

    def bypass(self):
        if self.state in [TrapStatus.DETECTED, TrapStatus.SPRUNG]:
            self.state = TrapStatus.BYPASSED
        else:
            raise ValueError('Attempt to bypass trap in invalid state: {}'.format(self))

    def spring(self):
        if self.live():
            self.state = TrapStatus.SPRUNG
        else:
            raise ValueError('Attempt to spring unhidden trap in invalid state: {}'.format(self))

    def spend(self):
        if self.live() and self.charges > 0:
            self.charges -= 1
        else:
            raise ValueError('Attempt to spend on trap in invalid state: {}'.format(self))

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return 'Trap: {} - {} - {}'.format(self.code, self.state, self.charges)