#lang racket

(require (except-in rosetta/autocad wall slab door))
(require "TrilobiteCOP.rkt")

(delete-all-shapes)

(define wall-height 4000)
(define door-height 3000)
(define wall-thickness 100)
(define  floor-thickness 300)

(define wall-door-start 0.1)
(define wall-door-end 0.3)

(define (shop p v l w)
  (let* ((v1 (rotated-v v pi/2))
         (c (loc-from-o-vx-vy p v v1)))
    (begin
      ((wall) (p+v c (vy (/ w 2) c)) (p+v c (vy (/ w -2) c)) wall-thickness wall-height)
      ((wall) (p+v c (vy (/ w -2) c)) (p+v c (vxy l (/ w -2) c)) wall-thickness wall-height)
      ((wall) (p+v c (vxy l (/ w -2) c)) (p+v c (vxy l (/ w 2) c)) wall-thickness wall-height)
      ((door) ((wall) (p+v c (vxy  l (/ w 2) c)) (p+v c (vy (/ w 2) c)) wall-thickness wall-height)
              (p+v c (vxy (* wall-door-start l) (/ w 2) c))
              (p+v c (vxy (* wall-door-end l) (/ w 2) c))
              wall-thickness door-height))))

(define (line-shops p0 p1 l w)
  (let* ((d (distance p0 p1))
         (v (unitize (p-p p1 p0)))
         (n (floor (/ d l))))
    (if (equal? (exact-ceiling n) 0)
        (list)
        (let ((l (/ d n)))
          (for/list ([r (division 0 (exact-ceiling d) (exact-ceiling n) #f)])
            (shop (p+v p0 (v*r v r)) v l w))))))

(define (polygonal-shapes ps l w shape)
  (if (eq? (length ps) 2)
      (list (shape (car ps) (car (cdr ps)) l w))
      (let* ((p0 (car ps))
             (p1 (car (cdr ps)))
             (p2 (car (cddr ps)))
             (v01 (v*r (unitize (p-p p1 p0)) (/ w 2)))
             (v12 (v*r (unitize (p-p p2 p1)) (/ w 2)))
             (p1e (p+v p1 v01))
             (p2s (p+v p1 v12)))
        (cons (shape p0 p1e l w)
              (polygonal-shapes (cons p2s (cddr ps)) l w shape)))))

(define (polygonal-shops ps l w)
  (polygonal-shapes ps l w line-shops))

(define (v-in-v v0 v1)
  (let ((v (v+v v0 v1)))
    (v/r (v*r v (v.v v0 v0)) (v.v v v0))))

(define (offset-line ps d)
  (let* ((vs (for/list ([p0 (reverse (cdr (reverse ps)))]
                        [p1 (cdr ps)])
               (rotated-v (v*r (unitize (p-p p1 p0)) d) pi/2)))
         (vss (append (cons (car vs)
                          (for/list ([v0 (reverse (cdr (reverse vs)))]
                                     [v1 (cdr vs)])
                            (v-in-v v0 v1)))
                    (list (car (reverse vs))))))
    (for/list ([p ps]
               [v vss])
      (p+v p v))))

(define (single-sided-shops ps l w)
  (polygonal-shops (offset-line ps (/ w 2)) l w))

(define (double-sided-shops ps l w)
  (begin
    (polygonal-shops (offset-line ps (/ w 2)) l w)
    (polygonal-shops (offset-line (reverse ps) (/ w 2)) l w)))

(define (veli a b phi)
  (vxy (* a (cos phi)) (* b (sin phi))))

(define (l-points c la lb alpha dalpha)
  (list (p+v c (veli la lb alpha))
        (p+v c (veli (* la (sqrt 2)) (* lb (sqrt 2)) (+ alpha (/ dalpha 2))))
        (p+v c (veli la lb (+ alpha dalpha)))))

(define (u-points c l alpha dalpha)
  (list (p+v c (vpol l alpha))
        (p+v c (vpol (* l (sqrt 2)) (+ alpha (/ dalpha 2))))
        (p+v c (vpol l (+ alpha dalpha)))))

(define (single-sided-circular-shops p r l w ex ey)
  (for/list ([fi (division 0 (* 2 pi) 4 #f)])
    (single-sided-shops (l-points (p+v p (veli (* (/ ex 2) (sqrt 2))
                                               (* (/ ey 2) (sqrt 2))
                                               (+ fi pi/4)))
                                  (- r (/ ex 2))
                                  (- r (/ ey 2))
                                  fi
                                  pi/2)
                        l w)))

(define (double-sided-circular-shops p r l w ex ey)
  (for/list ([fi (division 0 (* 2 pi) 4 #f)])
    (double-sided-shops (l-points (p+v p (veli (* (/ ex 2) (sqrt 2))
                                               (* (/ ey 2) (sqrt 2))
                                               (+ fi pi/4)))
                                  (- r (/ ex 2))
                                  (- r (/ ey 2))
                                  fi
                                  pi/2)
                        l w)))

(define (double-sided-n-circular-shops p r l w ex ey e n)
  (if (eq? n 0)
      (list)
      (begin
        (double-sided-circular-shops p r l w ex ey)
        (double-sided-n-circular-shops p (- (- r (* 2 w)) e) l w ex ey e (- n 1)))))

(define (colombo p r l w ex ey n)
  (let ((e (max ex ey))
        (p0 (p+v p (vxy (* -1 r) (* -1 r)))))
    (begin
      (single-sided-circular-shops p r l w ex ey)
      (double-sided-n-circular-shops p (- (- r (* 2 w)) e) l w ex ey e (- n 1))
      ((slab)(line p0
                  (p+v p0 (vx (* 2 r)))
                  (p+v p0 (vxy (* 2 r) (* 2 r)))
                  (p+v p0 (vy (* 2 r)))
                  p0)
            (* -1 floor-thickness)))))

(define (colombo-atrio p r l a ex ey n)
  (let* ((e (max ex ey))
         (w (/ (- r a (* (- n 1) e)) (- (* 2 n) 1))))
    (colombo p r l w ex ey n)))

(with-layers (2D)
 (colombo-atrio (xy 0 0) 100000 12000 25000 7000 7000 4))
  #;(shop (xyz 0 0 0 ) (vx 1) 10 10)