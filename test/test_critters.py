import core.critters


# delver stuff

class TestDelver:

    def test_delver(self):
        d = core.critters.Delver.random()
        assert type(d) == core.critters.Delver