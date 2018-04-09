#lang racket

(require rosetta/autocad)
(require "contextRacket.rkt")

(provide (all-defined-out))
(provide with-layers deflayered define-layered define-layer)

(define-layer 3D)
(define-layer 2D)
(define-layer analysis)

(define (rotated-v v alpha)
  (vpol (pol-rho v) (+ (pol-phi v) alpha) v))

(define-layered wall)
(define-layered slab)
(define-layered door)
(define-layered slab-with-opening)

(deflayered (wall 3D)
  (lambda (p1 p2 width height)
    (let* ((v0 (p-p p2 p1))
           (v1 (rotated-v v0 pi/2))
           (c (loc-from-o-vx-vy p1 v0 v1)))
      (box (p+v c (vy (/ width -2) c)) (distance p1 p2) width height))))
           

(deflayered (wall 2D)
  (lambda (p1 p2 width height)
    (let* ((v0 (p-p p2 p1))
           (v1 (rotated-v v0 pi/2))
           (c (loc-from-o-vx-vy p1 v0 v1)))
      (rectangle (p+v c (vy (/ width -2) c)) (distance p1 p2) width))))

(deflayered (wall analysis)
  (lambda (p1 p2 width height)
    (let* ((v0 (p-p p2 p1))
           (v1 (rotated-v v0 pi/2))
           (c (loc-from-o-vx-vy p1 v0 v1))
           (p3 (p+v c (vx (distance p1 p2) c)))
           (p4 (p+v p3 (vz height)))
           (p5 (p+v p4 (vx (- (distance p1 p2)) c))))
      (surface (line c p3 p4 p5 c)))))

(deflayered (slab 3D)
  (lambda(path thickness)
    (extrusion (surface path) thickness)))

(deflayered (slab 2D)
  (lambda (path thickness)
    path))

(deflayered (slab analysis)
  (lambda (path thickness)
    (surface path)))

(deflayered (door 3D)
  (lambda (w p1 p2 wth h)
    (let* ((v0 (p-p p2 p1))
           (v1 (rotated-v v0 pi/2))
           (c (loc-from-o-vx-vy p1 v0 v1)))
      (subtraction w (box (p+v c (-vy (+ (/ wth 2) 0.01) c)) (distance p1 p2) (+ wth 0.01) h)))))

(deflayered (door 2D)
  (lambda(w p1 p2 wth h)
    (list)))


(deflayered (door analysis)
  (lambda (w p1 p2 wth h)
    (let* ((v0 (p-p p2 p1))
           (v1 (rotated-v v0 pi/2))
           (c (loc-from-o-vx-vy p1 v0 v1))
           (p3 (p+v c (vx (distance p1 p2) c)))
           (p4 (p+v p3 (vz h)))
           (p5 (p+v p4 (vx (- (distance p1 p2)) c))))
      (subtraction w (surface (line c p3 p4 p5 c))))))

(deflayered (slab-with-opening 3D)
  (lambda (path openings thickness)
    (define (openings-recursive list-op res)
      (if (null? list-op)
          res
          (begin
          (openings-recursive (cdr list-op)
                              (subtraction res (extrusion (surface (closed-line (car list-op))) (+ thickness 1)))))))
    (let ((res (extrusion (surface path) thickness)))
      (openings-recursive openings res))))
      

(deflayered (slab-with-opening 2D)
  (lambda (path openings thickness)
    path))

(deflayered (slab-with-opening analysis)
  (lambda (path openings thickness)
    (define (openings-recursive list-op res)
      (if (null? list-op)
          res
          (openings-recursive (cdr list-op) (subtraction res (surface (closed-line (car list-op)))))))
    (let ((res (surface path)))
      (openings-recursive openings res))))



#|
(delete-all-shapes)
(with-layers (analysis)
  ((door) ((wall) (xyz 0 0 0) (xyz 20 0 0) 1 3) (xyz 5 0 0) (xyz 7 0 0) 1 2))

|#