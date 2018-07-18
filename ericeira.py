from khepri.autocad import *
from TrilobiteCOPtest import *

##PROBLEMAS A RESOLVER
#1 riscado das paredes opacas sempre para fora
#3 colocar riscado das paredes opacas a acompanhar o wall level
#4 criar paredes com os riscado subtraido

#

def media(a, b):
    return (a + b)/2.0

def media_pontos(p0, p1):
    return xyz(media(p0.x, p1.x), media(p0.y, p1.y), media(p0.z, p1.z))

def centro_quadrangulo(p0, p1, p2, p3):
    return media_pontos(media_pontos(p0, p2), media_pontos(p1, p3))

def normal_poligono(vs):
    return unitize(produtos_cruzados(vs + [vs[0]]))

def produtos_cruzados(vs):
    if len(vs) == 1:
        return vxyz(0, 0, 0)
    else:
        return produto_cruzado(vs[0], vs[1]) + produtos_cruzados(vs[1:])
def produto_cruzado(v0, v1):
    return v0.cross(v1)

def normal_quadrangulo(p0, p1, p2, p3):
    return normal_poligono([p0, p1, p2, p3])

def itera_quads(f, ptss):
    return [[f(p0,
               p1,
               p2,
               p3) for p0, p1, p2, p3 in zip(pts0,
                                             pts1,
                                             pts1[1:],
                                             pts0[1:])] for pts0, pts1 in zip(ptss,
                                                                              ptss[1:])]

def laje(z, e, pts):
    return Slab(closed_spline(pts), e).generate()

def parede(e, pts, ti, tf):
    decision_lst = [ti if n%2 == 0 else tf for n in range(0, len(pts))]
    for pt0, pt1, is_start_on in zip(pts, pts[1:], decision_lst):
        if is_start_on:
            Wall(pt0, pt1).generate()

#function --> cria stripes ao longo duma lista de pts

'''
(define (xpto pts ti tf)
  (for/list ((pt0 pts)
             (pt1 (cdr pts))
             (start-on? (in-cycle (list ti tf))))
    (when start-on?
      (let* ((n (unitize (p-p pt0 pt1))) #stripes deviam estar sempre para fora!!!
             (v (vxy (* e-wall (cy n)) (* e-wall (cx n))))
             (p0 (p+v pt0 v))
             (p1 (p+v pt1 v)))
        (itera-quads wall-pattern (grid-creation p0 p1))))))
'''

#function --> lista com os PTS extremidades duma malha
def grid_extremes(ptss):
    p0 = ptss[0][0]
    p1 = ptss[0][-1]
    p2 = ptss[-1][-1]
    p3 = ptss[-1][0]
    return [p0, p1, p2, p3]

#function --> cria malha PTS entre os dois pontos da base
def grid_creation(p0, p1):
    x = distance(p0, p1)
    n = unitize(p1 - p0)
    return map_division(lambda i, j: p0 + vxyz(i*n.x, i*n.y, j),
                        0,
                        x,
                        1,
                        0,
                        z_floor0,
                        m_cells)

#function -->grid striped pattern
def stripe(p1, p2, p3, p4):
    n = normal_quadrangulo(p1, p2, p3, p4)
    p = centro_quadrangulo(p1, p2, p3, p4)
    return extrusion(surface_polygon(p1, p2, p3, p4), e_grid)

def multi_stripes(p0, p1, p2, p3):
    d = distance(p0, p1)
    h = distance(p0, p3)
    return stripes(p0, p1, p2, p3, 0.05, 0.2, 0.05, 0.2) #0.10 0.30 0.10

def stripes(p0, p1, p2, p3, min_c, max_c, d_c, max_d_stripes):
    l_stripe = random_range(min_c, max_c + d_c)
    f_initial = random(0.15)
    p0_initial = intermediate_loc(p0, p1, f_initial)
    p3_initial = intermediate_loc(p3, p2, f_initial)
    if distance(p0_initial, p1) < l_stripe or p0_initial.x > p1.x or p0_initial.y > p1.y:
        return empty_shape()
    else:
        d_stripes = random_range(0, max_d_stripes)
        d_total = distance(p0, p1)
        p1_s = intermediate_loc(p0_initial, p1, l_stripe/d_total)
        p2_s = intermediate_loc(p3_initial, p2, l_stripe/d_total)
        new_p0 = intermediate_loc(p0_initial, p1, (l_stripe + d_stripes)/d_total)
        new_p3 = intermediate_loc(p3_initial, p2, (l_stripe + d_stripes)/d_total)
        return union(stripe(p0_initial, p1_s, p2_s, p3_initial),
                     stripes(new_p0, p1, p2, new_p3, min_c, max_c, d_c, max_d_stripes))

#function --> window profile
def metal_profile(pts, ang):
    return sweep(polygon(pts),
                 rotate(surface_rectangle(xy(-0.02, -0.005), 0.04, 0.01), ang)) #nos YY --> perfil mal!!! ---> transformacoes coordenadas

#function --> wall striped pattern
def wall_pattern(p0, p1, p3, p4):
    return right_cuboid(p0, 0.01, 0.01, p1)

#»»»»»»»»»»»»»»»»»»»»»»»»»»»»»»»»»»  Ericeira House  ««««««««««««««««««««««««««««««««««««««««««««««««««««
#Pts
##ceiling
t0 = u0()
t1 = t0 + vx(9.6)
t2 = t1 + vy(-8.7)
t3 = t2 + vx(5.8)
t4 = t3 + vy(13.8)
t5 = t4 + vx(-15.4)
##slab
l0 = t0 + vy(-5.85)
l1 = l0 + vx(5)
l2 = l1 + vy(5.85)
l3 = t1
l4 = t2
l5 = t3
l6 = t4
l7 = t5
c1 = t0 + vx(1.5)
c2 = t1
c3 = c2 + vy(-5.77)
c4 = c3 + vx(1.4)
c5 = t2 + vx(1.4)
c6 = t3
c7 = c6 + vy(4.7)
c8 = c7 + vx(-1.3)
c9 = c8 + vy(5.6)
c10 = c9 + vx(1.3)
c11 = t4
c12 = t5
c13 = c12 + vx(2.7)
c14 = c13 + vy(-5.2)
##janelas piso 0
w0 = c1 + vx(1.9)
w1 = w0 + vx(1.6)
w2 = w1 + vx(2.0)
w3 = w2 + vx(1.6)
w4 = t1 + vy(-1)
w5 = w4 + vy(-1.9)
w6 = t3 + vy(0.8)
w7 = w6 + vy(1.9)
w8 = c8
w9 = w8 + vy(3.9)
w10 = c9 + vy(-0.8)
w11 = w10 + vy(0.6)
w12 = c13
w13 = c14 + vy(1)
##walls int piso0
ci0 = t4 + vxy(-5.2, -1.13)
ci1 = ci0 + vy(-2.23)
ci2 = t4 + vxy(-2.95, -2)
ci22 = t4 + vy(-2)
ci3 = c10 + vx(-2.95)
ci4 = c10 + vx(-4.2)
ci5 = w9 + vx(-2.9)
ci6 = w8
ci7 = c7 + vx(-5.8)

#FLOOR 1
##walls piso1
p0 = t0 + vx(1.5)
p1 = p0 + vx(1.9)
p2 = p1 + vx(1.6)
p3 = p2 + vx(2.0)
p4 = p3 + vx(1.6)
p5 = p4 + vx(1.3)
p6 = t2
p7 = p6 + vx(4.4)
p8 = p7 + vy(4)
p9 = p8 + vx(1.4)
p10 = p9 + vy(9.8)
p11 = t5
p12 = p11 + vx(1.5)
p13 = p12 + vy(-4.2)
p14 = p13 + vx(8.1)
##paredes int. piso1
pi0 = t5 + vx(5.1)
pi1 = pi0 + vy(-3.1)
pi2 = pi0 + vx(2.35)
pi3 = pi2 + vy(-2.9)
pi4 = t1 + vy(5.1)
pi5 = pi4 + vy(-4.2)
pi6 = t4 + vy(-2)
pi7 = pi6 + vx(-3.4)
pi8 = pi7 + vy(-3.1)
pi9 = pi8 + vx(3.4)
pi10 = t1
pi11 = pi8 + vy(-4.7)
pi12 = pi11 + vx(3.4)
pi13 = t2 + vy(4)
##janelas piso1
j0 = p12
j1 = p13
j2 = p13 + vx(1.7)
j3 = j2 + vx(1.8)
j4 = j3 + vx(1.8)
j5 = j4 + vx(1.8)
j6 = t1 + vy(-4.7)
j7 = j6 + vy(-1)
j8 = p7 + vy(0.9)
j9 = p8 + vy(1.6)
j10 = p9 + vy(0.88)
j11 = j10 + vy(1.6)
j12 = j11 + vy(3)
j13 = j12 + vy(0.6)
j14 = t4 + vx(-3.6)
j15 = j14 + vx(-0.9)
##claraboias
###claraboia 1
cl10 = t5 + vxy(5.9, -1.53)
cl11 = cl10 + vx(0.6)
cl12 = cl10 + vy(-0.6)
cl13 = cl10 + vxy(0.6, -0.6)
###claraboia 2
cl20 = t5 + vxy(8.9, -1.53)
cl21 = cl20 + vx(0.6)
cl22 = cl20 + vy(-0.6)
cl23 = cl20 + vxy(0.6, -0.6)
###claraboia 3
cl30 = t4 + vxy(-1.6, -0.86)
cl31 = cl30 + vx(0.6)
cl32 = cl30 + vy(-0.6)
cl33 = cl30 + vxy(0.6, -0.6)

#Conjuntos Pts
##Piso0 Paredes
pts_walls_floor0 = [c1, w0, w13, c14, w1, w2, w3, t1, t1, w4, w5, c3, c4, c5, c5, c6, c6, w6, w7, c7, w9, w10, c9, c10, c10, c11, c11, c12]
pts_inside_walls_floor0 = [ci0, ci1, ci22, ci2, ci2, ci3, ci3, ci4, ci4, ci5, ci5, w9, ci6, ci7]
##Piso1 Paredes
pts_walls_floor1 = [p13, j2, j3, j4, j5, p14, t1, j6, j7, p6, p6, p7, p7, j8, j9, p8, p9, j10, j11, j12, j13, p10, p10, p11]
pts_outter_walls_floor1 = [p0, p1, p2, p3, p4, p5]
pts_inside_walls_floor1 = [pi0, pi1, pi2, pi3, pi4, pi5, pi6, pi7, pi7, pi8, pi9, pi10, pi8, pi11, pi12, pi13]
##Piso0&1 Janelas
pts_winds_floor0 = [w0, w1, w2, w3, w4, w5, w6, w7, w8, w9, w10, w11, w12, w13]
pts_winds_floor1 = [j0, j1, j2, j3, j4, j5, j6, j7, j8, j9, j10, j11, j12, j13, j14, j15]
##Claraboias
pts_cl_1 = [cl10, cl11, cl13, cl12, cl10]
pts_cl_2 = [cl20, cl21, cl23, cl22, cl20]
pts_cl_3 = [cl30, cl31, cl33, cl32, cl30]
##Lajes
pts_laje_0 = [t0, l3, l4, l5, l6, l7, t0]
pts_laje_1 = [l0, l1, l2, l3, l4, l5, l6, l7, l0]
##Cobertura
pts_teto = [t0, t1, t2, t3, t4, t5, t0]

#»»»»»»»»»»»»»»»»»»»»»»»»»»»»»»»»»»»»»»»»» House parameters ««««««««««««««««««««««««««««««««««««««««««««««
n_panels_w1 = 4
n_panels_w0 = 3
e_stripe = 0.062
m_cells = 35 #h_stripe=6.2cm
e_grid = 0.04
e_wall = 0.15
e_slab = 0.3
len_panel_w0 = distance(w13, w12)/n_panels_w0
len_panel_w1 = (distance(t0, t5) - e_grid - e_wall)/n_panels_w1
floors_height = 2.2
z_floor0 = 0 + floors_height
z_floor1 = z_floor0 + 2.5

#»»»»»»»»»»»»»»»»»»»»»»»»»»»»»»»»»»»»»» Surface Grids ««««««««««««««««««««««««««««««««««««««««««««««
##South grid floor0 s1=1.6m s2=1.6m
def wall_f0_s1():
    return map_division(lambda i, j: w0 + vxyz(i, 0, j),
                        0,
                        1.6,
                        1,
                        0,
                        z_floor0,
                        m_cells)
def wall_f0_s2():
    return map_division(lambda i, j: w2 + vxyz(i, 0, j),
                        0,
                        1.6,
                        1,
                        0,
                        z_floor0,
                        m_cells)

##South grid floor1 s0=1.5m s1=1.6m s2=1.6m
def wall_f1_s0():
    return map_division(lambda i, j: t0 + vxyz(i, 0, j),
                        0,
                        1.5,
                        1,
                        z_floor0 + e_slab,
                        z_floor1,
                        m_cells)
def wall_f1_s1():
    return map_division(lambda i, j: p1 + vxyz(i, 0, j),
                        0,
                        1.6,
                        1,
                        z_floor0 + e_slab,
                        z_floor1,
                        m_cells)
def wall_f1_s2():
    return map_division(lambda i, j: p3 + vxyz(i, 0, j),
                        0,
                        1.6,
                        1,
                        z_floor0 + e_slab,
                        z_floor1,
                        m_cells)

##West grid floor1
def wall_f1_w1():
    return map_division(lambda i, j: t0 + vxyz(0, i, j),
                        e_grid,
                        len_panel_w1 + e_grid,
                        1,
                        z_floor0 + e_slab,
                        z_floor1,
                        m_cells)
def wall_f1_w2():
    return map_division(lambda i, j: t0 + vxyz(0, i, j),
                        len_panel_w1 + e_grid,
                        2*len_panel_w1 + e_grid,
                        1,
                        z_floor0 + e_slab,
                        z_floor1,
                        m_cells)
def wall_f1_w3():
    return map_division(lambda i, j: t0 + vxyz(0, i, j),
                        2*len_panel_w1 + e_grid,
                        3*len_panel_w1 + e_grid,
                        1,
                        z_floor0 + e_slab,
                        z_floor1,
                        m_cells)
def wall_f1_w4():
    return map_division(lambda i, j: t0 + vxyz(0, i, j),
                        3*len_panel_w1 + e_grid,
                        4*len_panel_w1 + e_grid,
                        1,
                        z_floor0 + e_slab,
                        z_floor1,
                        m_cells)

##west grid floor0
def wall_f0_w1():
    return map_division(lambda i, j: w13 + vxyz(0, i, j),
                        0,
                        len_panel_w0,
                        1,
                        0,
                        z_floor0,
                        m_cells)
def wall_f0_w2():
    return map_division(lambda i, j: w13 + vxyz(0, i, j),
                        len_panel_w0,
                        2*len_panel_w0,
                        1,
                        0,
                        z_floor0,
                        m_cells)
def wall_f0_w3():
    return map_division(lambda i, j: w13 + vxyz(0, i, j),
                        2*len_panel_w0,
                        3*len_panel_w0,
                        1,
                        0,
                        z_floor0,
                        m_cells)

#»»»»»»»»»»»»»»»»»»»»»»»»»»»»»» function --> house volume «««««««««««««««««««««««««««««««««««««««««««««««

''' 
def house():
    delete_all_shapes()
    al = activelayer(myAnalysisLayer)
    with al:
        if al._getActiveLayers().__contains__(myAnalysisLayer):
            # piso1
            # current_level(upper_level())
            Slab(line([pt + vz(3) for pt in pts_laje_1])).generate()
            parede(0.12, [pt + vz(3) for pt in pts_walls_floor1], True, False)
            # problema do nivel!!!
            parede(0.12, [pt + vz(3) for pt in pts_outter_walls_floor1], True, False)
            # problema do nivel!!!
            parede(0, [pt + vz(3) for pt in pts_inside_walls_floor1], True, False)
            parede(0, [pt + vz(3) for pt in pts_winds_floor1], True, False)
            # windows f1
            # roof
            # current_level(upper_level())
            # sobe de nivel de acordo com o default
            Slab_With_Opening(line([pt + vz(6) for pt in pts_teto]),
                              [[pt + vz(6) for pt in pts_cl_1],
                               [pt + vz(6) for pt in pts_cl_2],
                               [pt + vz(6) for pt in pts_cl_3]]).generate()
        else:
            #piso0
            Slab(line(pts_laje_0)).generate()
            #pts da laje + nivel da laje (definido anteriormente)
            parede(0.12, pts_walls_floor0, True, False)
            #xpto(pts_walls_floor0, True, False)
            parede(0, pts_winds_floor0, True, False)
            #windows f0
            parede(0, pts_inside_walls_floor0, True, False)
            #piso1
            #current_level(upper_level())
            Slab(line([pt + vz(3) for pt in pts_laje_1])).generate()
            parede(0.12, [pt + vz(3) for pt in pts_walls_floor1], True, False)
            #problema do nivel!!!
            parede(0.12, [pt + vz(3) for pt in pts_outter_walls_floor1], True, False)
            #problema do nivel!!!
            parede(0, [pt + vz(3) for pt in pts_inside_walls_floor1], True, False)
            parede(0, [pt + vz(3) for pt in pts_winds_floor1], True, False)
            #windows f1
            #roof
            #current_level(upper_level())
            #sobe de nivel de acordo com o default
            Slab_With_Opening(line([pt + vz(6) for pt in pts_teto]),
                              [[pt + vz(6) for pt in pts_cl_1],
                              [pt + vz(6) for pt in pts_cl_2],
                              [pt + vz(6) for pt in pts_cl_3]]).generate()
            #Slab(line([pt + vz(6) for pt in pts_teto])).generate()
'''

floorAnalysisLayer = layer("floor")
fullModelLayer = layer("full")

@around(floorAnalysisLayer)
def house():
    with activelayer(myAnalysisLayer):
        # piso1
        # current_level(upper_level())
        Slab(line([pt + vz(3) for pt in pts_laje_1])).generate()
        parede(0.12, [pt + vz(3) for pt in pts_walls_floor1], True, False)
        # problema do nivel!!!
        parede(0.12, [pt + vz(3) for pt in pts_outter_walls_floor1], True, False)
        # problema do nivel!!!
        parede(0, [pt + vz(3) for pt in pts_inside_walls_floor1], True, False)
        parede(0, [pt + vz(3) for pt in pts_winds_floor1], True, False)
        # windows f1
        # roof
        # current_level(upper_level())
        # sobe de nivel de acordo com o default
        Slab_With_Opening(line([pt + vz(6) for pt in pts_teto]),
                          [[pt + vz(6) for pt in pts_cl_1],
                           [pt + vz(6) for pt in pts_cl_2],
                           [pt + vz(6) for pt in pts_cl_3]]).generate()

@around(fullModelLayer)
def house():
    with activelayer(my3DLayer):
        # piso0
        Slab(line(pts_laje_0)).generate()
        # pts da laje + nivel da laje (definido anteriormente)
        parede(0.12, pts_walls_floor0, True, False)
        # xpto(pts_walls_floor0, True, False)
        parede(0, pts_winds_floor0, True, False)
        # windows f0
        parede(0, pts_inside_walls_floor0, True, False)
        # piso1
        # current_level(upper_level())
        Slab(line([pt + vz(3) for pt in pts_laje_1])).generate()
        parede(0.12, [pt + vz(3) for pt in pts_walls_floor1], True, False)
        # problema do nivel!!!
        parede(0.12, [pt + vz(3) for pt in pts_outter_walls_floor1], True, False)
        # problema do nivel!!!
        parede(0, [pt + vz(3) for pt in pts_inside_walls_floor1], True, False)
        parede(0, [pt + vz(3) for pt in pts_winds_floor1], True, False)
        # windows f1
        # roof
        # current_level(upper_level())
        # sobe de nivel de acordo com o default
        Slab_With_Opening(line([pt + vz(6) for pt in pts_teto]),
                          [[pt + vz(6) for pt in pts_cl_1],
                           [pt + vz(6) for pt in pts_cl_2],
                           [pt + vz(6) for pt in pts_cl_3]]).generate()
        # Slab(line([pt + vz(6) for pt in pts_teto])).generate()
'''
for pts, ang in zip([wall_f0_w1(), wall_f0_w2(), wall_f0_w3(), wall_f0_s1(), wall_f0_s2(), wall_f1_w1(), wall_f1_w2(), wall_f1_w3(), wall_f1_w4(), wall_f1_s0(), wall_f1_s1(), wall_f1_s2()], [pi/2, pi/2, pi/2, 0, 0, pi/2, pi/2, pi/2, pi/2, 0, 0, 0]):
    union(itera_quads_chess(stripe, multi_stripes, pts),
          metal_profile(grid_extremes(pts), ang))
'''

delete_all_shapes()

with activelayer(floorAnalysisLayer):
    house()
