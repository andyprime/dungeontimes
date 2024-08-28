import pytest

import core.dungeon.dungeons as dungeons
import core.critters
import definitions.model

class TestRoom:

    def test_init(self):
        with pytest.raises(ValueError):
            dungeons.Room((1,2), {})

    def test_contains(self):

        r = dungeons.Room((5,5), {'height': 6, 'width': 6})

        # contains wants a Cell object
        assert (6, 7) not in r

        # inside
        c1 = dungeons.Cell()
        c1.coords = (6, 7)
        assert c1 in r

        # outside
        c2 = dungeons.Cell()
        c2.coords = (2, 2)
        assert c2 not in r

        # borders
        c3 = dungeons.Cell()
        c3.coords = (5, 5)
        assert c3 in r
        c4 = dungeons.Cell()
        c4.coords = (6, 10)
        assert c4 in r

    def test_populate(self):

        r = dungeons.Room((5,5), {'height': 6, 'width': 6})

        with pytest.raises(ValueError):
            r.populate('Hello')

        assert type(r.locals) == list
        l1 = len(r.locals)
        m = core.critters.Monster(definitions.model.Monsters.random())
        r.populate(m)
        assert len(r.locals) == l1 + 1


class TestCell:


    def test_init(self):

        with pytest.raises(ValueError):
            dungeons.Cell(type='Hello')

        c1 = dungeons.Cell(type=dungeons.Cell.PASSAGE)
        assert c1.type == dungeons.Cell.PASSAGE

        c2 = dungeons.Cell()
        assert c2.type == dungeons.Cell.SOLID

    def test_coords(self):
        # not sure how much here really needs fussing with

        c1 = dungeons.Cell()
        c1.coords = (4, 5)
        assert c1.h == 4 and c1.w == 5

        assert c1.north() == (3, 5)
        assert c1.south() == (5, 5)
        assert c1.east() == (4, 6)
        assert c1.west() == (4, 4)

        assert c1.adjacent( (3, 5) )
        assert not c1.adjacent( (10, 12) )
