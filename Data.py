currentLevel = 0
currentSpace = 0

class Building:
    def __init__(self):
        self.levels = [Level(0)]

    def addLevel(self, level):
        self.levels += level

    def getLevels(self):
        return self.levels

class Level:
    def __init__(self, elevation, name="Level", spaces=[]):
        self.elevation = elevation
        global currentLevel
        self.name = name + str(currentLevel)
        currentLevel += 1
        self.spaces=spaces

    def addSpace(self, space):
        self.spaces+=space

class Space:
    def __init__(self, bounds, elevation, level, interior, name="Space", connected=None):
        assert len(bounds) >= 4
        self.bounds = bounds
        global currentSpace
        self.name = name + str(currentSpace)
        currentSpace += 1
        self.elevation = elevation
        self.level = level
        self.interior + interior
        self.connected = connected






