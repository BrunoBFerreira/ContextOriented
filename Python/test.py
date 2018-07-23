from Trilobite import *

delete_all_shapes()

b1 = Bound(xyz(0,0,0), xyz(10, 0, 0))
b2 = Bound(xyz(10, 0, 0), xyz(10, 5, 0))
b3 = Bound(xyz(10, 5, 0), xyz(0, 5, 0))
b4 = Bound(xyz(0, 5, 0), xyz(0, 0, 0))

bt = Bound(xyz(10, 5, 0), xyz(0, 0, 0))

b5 = Bound(xyz(15,0,0), xyz(30, 0, 0))
b6 = Bound(xyz(30, 0, 0), xyz(30, 15, 0))
b7 = Bound(xyz(30, 15, 0), xyz(15, 15, 0))
b8 = Bound(xyz(15, 15, 0), xyz(15, 0, 0))

s1 = Space([b1, b2, b3, b4])

s2 = Space([b5, b6, b7, b8])

w1 = Wall(xyz(0, 0, 0), xyz(10, 0, 0), lvls=[current_level], spcs=[s1])

w2 = Wall(xyz(0, 5, 0), xyz(10, 5, 0), lvls=[current_level], spcs=[s1])

w3 = Wall(xyz(16, 5, 0), xyz(16, 10, 0), lvls=[current_level], spcs=[s2])

set_current_space(s1)

with activelayers(layer_analysis, layer_space):
    generate()

