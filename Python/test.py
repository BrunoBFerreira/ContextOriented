from Trilobite import *

delete_all_shapes()

lvl1 = upper_level(current_level)

s1 = Space([1, 2, 3, 4])

s2 = Space([5, 6, 7, 8])

w1 = Wall(xyz(0, 0, 0), xyz(10, 0, 0), lvls=[current_level], spcs=[s1])

w2 = Wall(xyz(0, 10, 0), xyz(10, 10, 0), lvls=[current_level], spcs=[s1, s2])

w3 = Wall(xyz(0, 20, 0), xyz(10, 20, 0), lvls=[current_level], spcs=[s2])

set_current_space(s2)

with activelayers(layer_analysis, layer_space):
    generate()

