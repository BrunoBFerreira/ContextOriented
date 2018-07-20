from khepri.autocad import *

delete_all_shapes()

def rotated_v(v, alpha):
    return vpol(pol_rho(v), pol_phi(v) + alpha)

def centered_rectangle(p0, w, p1):
    v0 = p1 - p0
    v1 = rotated_v(v0, pi/2)
    c = loc_from_o_vx_vy(p0, v0, v1)
    return rectangle(c-vy(w/2, c.cs), distance(p0, p1), w)

#centered_rectangle(xy(1,2), 1, xy(10,20))

layer_doors = create_layer("Doors", rgb(255,0,0))
layer_walls = create_layer("Walls", rgb(240,240,240))
layer_front = create_layer("Front", rgb(255,255,200))
layer_floor = create_layer("Floor", rgb(200,200,200))

wall_door_start = 0.1
wall_door_end = 0.3

def shop2d(p, v, l, w):
    v1 = rotated_v(v, pi/2)
    c = loc_from_o_vx_vy(p, v, v1)
    with current_layer(layer_walls):
        rectangle(c-vy(w/2, c.cs), l, w)
    with current_layer(layer_doors):
        line(c+vxy(wall_door_start*l, w/2), c+vxy(wall_door_end*l, w/2))

wall_height = 4000
door_height = 3000
wall_thickness = 100
floor_thickness = 300

def shop3d(p, v, l, w):
    v1 = rotated_v(v, pi/2)
    c = loc_from_o_vx_vy(p, v, v1)
#    with current_layer(layer_floor):
#        box(c-vy(w/2), l, w, -floor_thickness)
    cc = c+vz(wall_height/2)
    with current_layer(layer_walls):
        polygonal_shapes([cc+vy(w/2), cc+vy(-w/2), cc+vxy(l,-w/2), cc+vxy(l,w/2)],
                         l, wall_thickness,
                         lambda p0,p1,l,w: right_cuboid(p0,
                                                        wall_thickness,
                                                        wall_height,
                                                        p1))
    cd = c+vz(door_height/2)
    with current_layer(layer_front):
        subtraction(right_cuboid(cc+vy(w/2),
                                 wall_thickness/4,
                                 wall_height,
                                 cc+vxy(l, w/2)),
                    right_cuboid(cd+vxy(wall_door_start*l, w/2),
                                 wall_thickness/2,
                                 door_height,
                                 cd+vxy(wall_door_end*l, w/2)))         

#there is a line of shops

def line_shops(p0, p1, l, w):
    d = distance(p0, p1)
    v = unitize(p1 - p0)
    n = floor(d/l)
    if n == 0:
        raise Exception("Insuficient space!") 
    l = d/n
    return [shop(p0 + v*r, v, l, w) for r in division(0, d, n, False)]

#line_shops(xy(1,2), xy(10,20), 3, 1)

def polygonal_shapes(ps, l, w, shape):
    if len(ps) == 2:
        return [shape(ps[0], ps[1], l, w)]
    else:
        p0 = ps[0]
        p1 = ps[1]
        p2 = ps[2]
        v01 = unitize(p1 - p0) * w/2
        v12 = unitize(p2 - p1) * w/2
        p1e = p1 + v01
        p2s = p1 + v12
        return [shape(p0, p1e, l, w)] + polygonal_shapes([p2s] + ps[2:], l, w, shape)


def polygonal_shops(ps, l, w):
    return polygonal_shapes(ps, l, w, line_shops)

#polygonal_shops([xy(1,2), xy(10,20), xy(-5, 30)], 3, 1)

def v_in_v(v0, v1):
    v = v0 + v1
    return v*(v0.dot(v0))/(v.dot(v0))

def offset_line(ps, d):
    vs = [rotated_v(unitize(p1 - p0)*d, pi/2) for p0, p1 in zip(ps[:-1], ps[1:])]
    vs = [vs[0]] + [v_in_v(v0, v1) for v0, v1 in zip(vs[:-1], vs[1:])] + [vs[-1]]
    return [p + v for p, v in zip(ps, vs)]

#ps = [xy(1,2), xy(10,20), xy(-5, 30), xy(-10, 40)]

#line(ps)
#for i in range(1, 5):
#    line(offset_line(ps, i))

ps = [xy(10000,20000), xy(-5000, 20000), xy(-5000, 40000)]
#line(ps)
#polygonal_shops(ps, 8000, 3000)
#polygonal_shops(offset_line(list(reversed(ps)), 1), 5, 1)
#polygonal_shops(offset_line(ps, 1), 5, 1)

def single_sided_shops(ps, l, w):
    #line(ps)
    polygonal_shops(offset_line(ps, w/2), l, w)
    #polygonal_shops(offset_line(list(reversed(ps)), w/2), l, w)

def double_sided_shops(ps, l, w):
    polygonal_shops(offset_line(ps, w/2), l, w)
    polygonal_shops(offset_line(list(reversed(ps)), w/2), l, w)

#single_sided_shops(ps, 8000, 3000)
#double_sided_shops(ps, 8000, 3000)
#double_sided_shops(L_points(x(10), 30, 0, pi/2), 10, 6)
#double_sided_shops(L_points(x(10), 30, 0, -pi/2), 10, 6)

# circular shops

#eliptical coordinates
def veli(a, b, phi):
    return vxy(a*cos(phi), b*sin(phi))

def L_points(c, la, lb, alpha, dalpha):
    return [c+veli(la, lb, alpha), c+veli(la*sqrt(2), lb*sqrt(2), alpha+dalpha/2), c+veli(la, lb, alpha+dalpha)]

def U_points(c, l, alpha, dalpha):
    return [c+vpol(l, alpha), c+vpol(l*sqrt(2), alpha+dalpha/2), c+vpol(l, alpha+dalpha)]

def single_sided_circular_shops(p, r, l, w, ex, ey):
    #rectangle(p+vxy(-r,-r),2*r, 2*r)
    for fi in division(0, 2*pi, 4, False):
        single_sided_shops(L_points(p+veli(ex/2*sqrt(2), ey/2*sqrt(2), fi+pi/4), r-ex/2, r-ey/2, fi, pi/2), l, w)
    for fi in division(0, 2*pi, 4, False):
        mall_exit_door(p+vpol(r, fi + pi/2), veli(ex, ey, fi))

exit_door_wall_fraction = make_parameter(1)

def mall_exit_door(c, v):
    fraction = exit_door_wall_fraction()
    if fraction < 1:
        subtraction(right_cuboid(c-v/2+vz(wall_height/2),
                                 wall_thickness,
                                 wall_height,
                                 c+v/2+vz(wall_height/2)),
                    right_cuboid(c-v*fraction/2+vz(door_height/2),
                                 wall_thickness,
                                 door_height,
                                 c+v*fraction/2+vz(door_height/2)))
                 
#single_sided_circular_shops(xy(0,0), 8000, 3000, 1000, 1000, 0)

def double_sided_circular_shops(p, r, l, w, ex, ey):
    #rectangle(p+vxy(-r,-r),2*r, 2*r)
    for fi in division(0, 2*pi, 4, False):
        double_sided_shops(L_points(p+veli(ex/2*sqrt(2), ey/2*sqrt(2), fi+pi/4), r-ex/2, r-ey/2, fi, pi/2), l, w)
    
def double_sided_n_circular_shops(p, r, l, w, ex, ey, e, n):
    if n == 0:
        pass
    else:
        double_sided_circular_shops(p, r, l, w, ex, ey)
        double_sided_n_circular_shops(p, r - 2*w - e, l, w, ex, ey, e, n - 1)

#double_sided_n_circular_shops(xy(0,0), 8000, 1000, 600, 800, 800, 4)

def colombo(p, r, l, w, ex, ey, n):
    e = max(ex, ey)
    single_sided_circular_shops(p, r, l, w, ex, ey)
    double_sided_n_circular_shops(p, r - 2*w - e, l, w, ex, ey, e, n - 1)
    with current_layer(layer_floor):
        pass
        box(p+vxy(-r, -r), 2*r, 2*r, -floor_thickness)
        #box(p+vxyz(-r, -r, wall_height), 2*r, 2*r, floor_thickness)

def mall(p, r, l, w, e, n):
    double_sided_n_circular_shops(p, r, l, w, e, e, e, n)
    with current_layer(layer_floor):
        box(p-vxyz(l,l,floor_thickness), p+vxy(l,l))

#shop = shop2d
shop = shop3d
#mall(centro, raio, comprimento_loja, largura_loja, largura_corredor, aneis)
#mall(xy(0,0), 80000, 12000, 10000, 6000, 3)

#colombo(xy(0,0), 30000, 12000, 10000, 6000, 3)
#colombo(xy(0,0), 100000, 12000, 8000, 7000, 000, 4)

def colombo_atrio(p, r, l, a, ex, ey, n):
    e = max(ex, ey)
    w = (r - a - (n - 1)*e)/(2*n - 1)
    colombo(p, r, l, w, ex, ey, n)

#Variacoes atrio
#colombo_atrio(xy(0,0), 100000, 12000, 20000, 7000, 7000, 4)
#colombo_atrio(xy(0,0), 100000, 12000, 25000, 7000, 7000, 4)
#colombo_atrio(xy(0,0), 100000, 12000, 30000, 7000, 7000, 4)
#colombo_atrio(xy(0,0), 100000, 12000, 35000, 7000, 7000, 4)

#Variacoes aneis
#colombo_atrio(xy(0,0), 100000, 12000, 20000, 7000, 7000, 2) #133
#colombo_atrio(xy(0,0), 100000, 12000, 20000, 7000, 7000, 3) #120.5
#colombo_atrio(xy(0,0), 100000, 12000, 20000, 7000, 7000, 4) #
#colombo_atrio(xy(0,0), 100000, 12000, 20000, 7000, 7000, 5) #

#Variacoes largura corredores
#colombo_atrio(xy(0,0), 100000, 12000, 20000, 3000, 3000, 4)
#colombo_atrio(xy(0,0), 100000, 12000, 20000, 3500, 3500, 4)
#colombo_atrio(xy(0,0), 100000, 12000, 20000, 4000, 4000, 4)
#colombo_atrio(xy(0,0), 100000, 12000, 20000, 4500, 4500, 4)
#colombo_atrio(xy(0,0), 100000, 12000, 20000, 5000, 5000, 4)
#colombo_atrio(xy(0,0), 100000, 12000, 20000, 7000, 7000, 4)
#colombo_atrio(xy(0,0), 100000, 12000, 20000, 9000, 9000, 4)

#Variacoes largura portas
#with exit_door_wall_fraction(0.4): colombo_atrio(xy(0,0), 100000, 12000, 20000, 6000, 6000, 4)
#with exit_door_wall_fraction(0.5): colombo_atrio(xy(0,0), 100000, 12000, 20000, 6000, 6000, 4)
#with exit_door_wall_fraction(0.6): colombo_atrio(xy(0,0), 100000, 12000, 20000, 6000, 6000, 4)
#with exit_door_wall_fraction(0.7): colombo_atrio(xy(0,0), 100000, 12000, 20000, 6000, 6000, 4)
#with exit_door_wall_fraction(0.8): colombo_atrio(xy(0,0), 100000, 12000, 20000, 6000, 6000, 4)
#with exit_door_wall_fraction(0.9): colombo_atrio(xy(0,0), 100000, 12000, 20000, 6000, 6000, 4)
#with exit_door_wall_fraction(1.0): colombo_atrio(xy(0,0), 100000, 12000, 20000, 6000, 6000, 4)




#with exit_door_wall_fraction(2/2)colombo_atrio(xy(0,0), 56000, 10000, 12000, 2000, 2000, 3)
#with exit_door_wall_fraction(2/2.5): colombo_atrio(xy(0,0), 56000, 10000, 12000, 2500, 2500, 3)
#with exit_door_wall_fraction(2/3): colombo_atrio(xy(0,0), 56000, 10000, 12000, 3000, 3000, 3)
#with exit_door_wall_fraction(2/3.5): colombo_atrio(xy(0,0), 56000, 10000, 12000, 3500, 3500, 3)
#with exit_door_wall_fraction(2/4): colombo_atrio(xy(0,0), 56000, 9999, 12000, 4000, 4000, 3)

#with exit_door_wall_fraction(2.1/3.1): colombo_atrio(xy(0,0), 56000, 10000, 12000, 3100, 3100, 3) #OldA
#with exit_door_wall_fraction(2.1/3.2): colombo_atrio(xy(0,0), 56000, 10000, 12000, 3200, 3200, 3) #OldB
#with exit_door_wall_fraction(2.1/3.3): colombo_atrio(xy(0,0), 56000, 10000, 12000, 3300, 3300, 3) #OldC
#with exit_door_wall_fraction(2.1/3.4): colombo_atrio(xy(0,0), 56000, 10000, 12000, 3400, 3400, 3) #OldD
#with exit_door_wall_fraction(2.1/3.5): colombo_atrio(xy(0,0), 56000, 10000, 12000, 3500, 3500, 3) #OldE
with exit_door_wall_fraction(2.1/3.6): colombo_atrio(xy(0,0), 56000, 10000, 12000, 3600, 3600, 3) #OldF

#view(xyz(100,-94,15), xyz(10,-9,-15), 18)
#view(xyz(96,-93,11), xyz(-11,14,-96), 18)
#view(xyz(3026,9907,939), xyz(533,8002,-784), 18)

#render_size(1920, 1080)
#render_view("mall")

from subprocess import check_output

pathfinder_path = "C:/Program Files/Pathfinder 2017/"
dos_pathfinder_path = "C:/PROGRA~1/PATHFI~1/"
automate_path = "C:/Users/aml/Dropbox/AML/Projects/Pathfinder/"
#pathfinder_path = "C:/Users/aml/Dropbox/AML/Projects/Pathfinder/"
#dos_pathfinder_path = pathfinder_path

jar_folders = ["", "lib/", "lib/pyrosim-lite/", "lib/rlm/", "lib/vtk-6.3.0/"]
java_path = ["", "lib/", "lib/rlm/"]

def test():
    str = dos_pathfinder_path + "jre/bin/java"
    str += " -cp "
    str += '"' + pathfinder_path + '";'
    for f in jar_folders:
        str += '"' + pathfinder_path + f + '*";'
    str += '"' + automate_path + '";'
    str += '"' + automate_path + '*";'
    str = str[0:-1]
    str += " -Djava.library.path="
    for f in java_path:
        str += '"' + pathfinder_path + f + '";'
    str = str[0:-1]
    str += " -Dsun.java2d.noddraw=true"
    str += " Automate"
    #str += " inferno/TestSim"
    str += " merlin.Run"
    print(str)
    check_output(str, shell=True)

