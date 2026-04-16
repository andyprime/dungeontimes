import pytest

import core.dungeon.dungeons as dungeons
import core.critters
import definitions.model


class TestDungeon:

    basic_grid = [
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    ]

    def convert_grid(self, ngrid):

        grid = []
        for i in range(len(ngrid)):
            grid.append([])
            for j in range(len(ngrid[0])):
                ntype = ngrid[i][j]
                grid[i].append(dungeons.DungeonCell(i, j, dungeons.Tiles(ntype)))

        return grid

    def test_create(self):
        dungeon = dungeons.Dungeon()
        dungeon.initialize(20, 30)

        assert dungeon.height() == 20
        assert dungeon.width() == 30

        c = dungeon.getCell(1, 1)
        assert type(c) == dungeons.DungeonCell
        assert c.type == dungeons.Tiles.SOLID

    def test_carving(self):

        dungeon = dungeons.Dungeon()
        dungeon.grid = self.convert_grid(TestDungeon.basic_grid)
        # dungeon.prettyPrint()

        c = dungeon.carvePassage(dungeon.getCell(2, 5))
        assert c.type == dungeons.Tiles.PASSAGE

        options = dungeon.getPossibleCarves(c)
        assert len(options) == 4

        c2 = dungeon.getCell(1, 1)
        options2 = dungeon.getPossibleCarves(c2)
        assert len(options2) == 2
        assert dungeons.Directions.NORTH not in options2
        assert dungeons.Directions.WEST not in options2

        c3 = dungeon.getCell(2, 4)
        options3 = dungeon.getPossibleCarves(c3)
        assert len(options3) == 3
        assert dungeons.Directions.EAST not in options3


class TestRoom:

    def test_init(self):
        with pytest.raises(ValueError):
            dungeons.Room((1,2), {})

    def test_contains(self):

        r = dungeons.Room((5,5), {'height': 6, 'width': 6})

        # contains wants a DungeonCell object
        assert (6, 7) not in r

        # inside
        c1 = dungeons.DungeonCell(6, 7)
        assert c1 in r

        # outside
        c2 = dungeons.DungeonCell(2, 2)
        assert c2 not in r

        # borders
        c3 = dungeons.DungeonCell(5, 5)
        assert c3 in r
        c4 = dungeons.DungeonCell(6, 10)
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

        with pytest.raises(TypeError):
            dungeons.DungeonCell()

        c1 = dungeons.DungeonCell(1, 2, dungeons.Tiles.PASSAGE)
        assert c1.type == dungeons.Tiles.PASSAGE

        c2 = dungeons.DungeonCell(1, 2)
        assert c2.type == dungeons.Tiles.SOLID

    def test_coords(self):
        # not sure how much here really needs fussing with

        c1 = dungeons.DungeonCell(4, 5)
        assert c1.h == 4 and c1.w == 5
        assert c1[0] == 4 and c1[1] == 5

        assert c1.north() == (3, 5)
        assert c1.south() == (5, 5)
        assert c1.east() == (4, 6)
        assert c1.west() == (4, 4)

        assert c1.adjacent( (3, 5) )
        assert not c1.adjacent( (10, 12) )
