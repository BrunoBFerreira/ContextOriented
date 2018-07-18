default_level_height = 3
space_index = 0

levels = dict({})
spaces = dict({})


def add_level(level, elevation):
    if elevation in levels:
        raise ValueError("Level already exists")
    else:
        levels[elevation] = level


def upper_level(level):
    global default_level_height
    new_height = level.elevation + default_level_height
    if new_height in levels:
        return levels[new_height]
    else:
        return Level(new_height)


def add_space(space, name):
    if name in spaces:
        raise ValueError("Space already exists")
    else:
        spaces[name] = space


class Level:
    def __init__(self, elevation, name="Level"):
        self.elevation = elevation
        if name == "Level":
            self.name = name + str(len(levels) + 1)
        else:
            self.name = name
        add_level(self, elevation)

    def add_space(self, space):
        self.spaces += space


class Space:
    def __init__(self, bounds, bottom_level=None, top_level=None, interior=True, name="Space"):
        assert len(bounds) >= 4
        self.bounds = bounds
        if name == "Space":
            global space_index
            self.name = name + str(space_index)
            space_index += 1
        else:
            self.name = name
        if bottom_level is None:
            global current_space
            self.lower_level = current_level
        else:
            self.lower_level = bottom_level
        if top_level is None:
            self.top_level = upper_level(self.lower_level)
        else:
            self.top_level = top_level
        self.interior = interior
        add_space(self, self.name)

levels[0] = Level(0, "Level 0")
current_level = levels[0]
current_space = None