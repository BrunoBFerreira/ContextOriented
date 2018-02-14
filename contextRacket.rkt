#lang racket

(require rnrs/mutable-pairs-6)
#|
ContextScheme v0.1
Copyright (c) 2009 Pascal Costanza

Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without
restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or
sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
|#

#|
Workarounds for potentially missing Scheme features.

Multiple values:

(define (call-with-values vals cont)
  (apply cont (vals)))

(define values list)


Dynamic wind:

(define (dynamic-wind pre main post)
  (pre)
  (let ((result (main)))
    (post)
    result))
|#

(define set-car! set-mcar!)

(define set-cdr! set-mcdr!)


(define (remove element list)
  (cond ((null? list) '())
	((eqv? element (car list)) (cdr list))
	(else (cons (car list) (remove element (cdr list))))))

(define (adjoin-front element list)
  (cons element (remove element list)))

(define current-context-stack '())

(define (call-with-context context thunk)
  (let ((old-context-stack '()))
    (dynamic-wind
	(lambda () 
	  (set! old-context-stack current-context-stack)
	  (set! current-context-stack (cons context current-context-stack)))
	(lambda () 
	  (context thunk))
	(lambda () 
	  (set! current-context-stack old-context-stack)))))

(define (call-with-context-reset thunk)
  (let ((old-context-stack '()))
    (dynamic-wind
	(lambda ()
	  (set! old-context-stack current-context-stack)
	  (set! current-context-stack '()))
	thunk
	(lambda ()
	  (set! current-context-stack old-context-stack)))))

(define (call-with-context-stack context-stack thunk)
  (cond ((null? context-stack) (thunk))
	(else (call-with-context
	       (car context-stack)
	       (lambda () (call-with-context-stack (cdr context-stack) thunk))))))

(define current-layers '())

(define (call-with-layer layer thunk)
  (call-with-context (lambda (thunk)
		       (let ((old-layers '()))
			 (dynamic-wind
			     (lambda () 
			       (set! old-layers current-layers)
			       (set! current-layers (adjoin-front layer current-layers)))
			     thunk
			     (lambda () 
			       (set! current-layers old-layers)))))
		     thunk))

(define (call-without-layer layer thunk)
  (call-with-context (lambda (thunk)
		       (let ((old-layers '()))
			 (dynamic-wind
			     (lambda ()
			       (set! old-layers current-layers)
			       (set! current-layers (remove layer current-layers)))
			     thunk
			     (lambda ()
			       (set! current-layers old-layers)))))
		     thunk))

(define (lookup name)
  (define (find-value layers)
    (cond ((null? layers) (values #f #f))
	  (else (let ((binding (assv name (car layers))))
		  (cond (binding (values (cdr binding) (cdr layers)))
			(else (find-value (cdr layers))))))))
  (define (lookup-in-context context-stack layers)
    (call-with-values
	(lambda () (find-value layers))
      (lambda (value remaining-layers)
	(if value
	    (let ((proceed 
		   (lambda ()
		     (let ((proceed-context-stack 
			    (append context-stack (reverse current-context-stack))))
		       (call-with-context-reset
			(lambda ()
			  (call-with-context-stack
			   proceed-context-stack
			   (lambda () (lookup-in-context proceed-context-stack remaining-layers)))))))))
	      (value proceed))
	    #f))))
  (lookup-in-context (reverse current-context-stack) current-layers))

(define (add-layered-definition name layer definition)
  (let ((binding (assv name layer)))
    (if binding (begin
		  (set-cdr! binding definition)
		  layer)
	(cons (cons name definition) layer))))

(define-syntax with-layers
  (syntax-rules ()
    ((with-layers () body ...)
     (let () body ...))
    ((with-layers (first-layer other-layers ...) body ...)
     (call-with-layer 
      first-layer
      (lambda ()
	(with-layers (other-layers ...) body ...))))))

(define-syntax without-layers
  (syntax-rules ()
    ((without-layers () body ...)
     (let () body ...))
    ((without-layers (first-layer other-layers ...) body ...)
     (call-without-layer
      first-layer
      (lambda ()
	(without-layers (other-layers ...) body ...))))))

(define-syntax define-layer
  (syntax-rules ()
    ((define-layer name)
     (define name '()))))

(define-syntax define-layered
  (syntax-rules ()
    ((define-layered name)
     (define (name) (lookup 'name)))))

(define-syntax deflayered
  (syntax-rules ()
    ((deflayered (name layer) definition)
     (set! layer (add-layered-definition 'name layer (lambda (proceed) definition))))
    ((deflayered (name layer proceed) definition)
     (set! layer (add-layered-definition 'name layer (lambda (proceed) definition))))))

#|
Alternative ("traditional") macro definitions:

(define-macro with-layers
  (lambda (layers . body)
    (if (null? layers)
      `(let () ,@body)
      `(call-with-layer ,(car layers)
         (lambda ()
           (with-layers ,(cdr layers) ,@body))))))

(define-macro without-layers
  (lambda (layers . body)
    (if (null? layers)
      `(let () ,@body)
      `(call-without-layer ,(car layers)
         (lambda ()
           (with-layers ,(cdr layers) ,@body))))))

(define-macro define-layer
  (lambda (name) `(define ,name '())))

(define-macro define-layered
  (lambda (name) `(define (,name) (lookup ',name))))

(define-macro deflayered
  (lambda (spec definition)
    (let ((name (car spec))
          (layer (cadr spec))
          (proceed (if (null? (cddr spec))
		       '%%%proceed
		       (caddr spec))))
      `(set! ,layer (add-layered-definition ',name ,layer (lambda (,proceed) ,definition))))))
|#

(define (out msg) (display msg) (newline))

(define (test1)
  (define l1 (list (cons 'p (lambda (proceed) 10))))
  (define l2 (list (cons 'p (lambda (proceed) (+ (proceed) 5)))))
  (out "The following yields 18.")
  (with-layers (l1 l2) (+ (lookup 'p) 3)))

(define (test1a)
  (define-layer l1)
  (define-layer l2)
  (define-layered p)
  (deflayered (p l1) 10)
  (deflayered (p l2 proceed) (+ (proceed) 5))
  (out "The following yields 18.")
  (with-layers (l1 l2) (+ (p) 3)))

(define (test2)
  (define l1 (list (cons 'p (lambda (proceed) (lambda (x) 1)))))
  (define l2 (list (cons 'p (lambda (proceed) (lambda (x) ((proceed) x))))))
  (define l3 (list (cons 'p (lambda (proceed) (lambda (x) 3)))))
  (out "The following yields 1.")
  ((lambda (f) (with-layers (l3) (f 10)))
   (with-layers (l1 l2) (lookup 'p))))

(define (test2a)
  (define-layer l1)
  (define-layer l2)
  (define-layer l3)
  (define-layered p)
  (deflayered (p l1) (lambda (x) 1))
  (deflayered (p l2 proceed) (lambda (x) ((proceed) x)))
  (deflayered (p l3) (lambda (x) 3))
  (out "The following yields 1.")
  ((lambda (f) (with-layers (l3) (f 10)))
   (with-layers (l1 l2) (p))))

(define (test3)
  (define l1 (list (cons 'p (lambda (proceed) (lookup 'q)))
		   (cons 'q (lambda (proceed) (lambda (x) 4)))))
  (define l2 (list (cons 'p (lambda (proceed) (lambda (x) ((proceed) x))))))
  (define l3 (list (cons 'p (lambda (proceed) (lambda (x) 3)))
		   (cons 'q (lambda (proceed) (lambda (x) 5)))))
  (out "The following yields 5.")
  ((lambda (f) (with-layers (l3) (f 10)))
   (with-layers (l1 l2) (lookup 'p))))

(define (test3a)
  (define-layer l1)
  (define-layer l2)
  (define-layer l3)
  (define-layered p)
  (define-layered q)
  (deflayered (p l1) (q))
  (deflayered (q l1) (lambda (x) 4))
  (deflayered (p l2 proceed) (lambda (x) ((proceed) x)))
  (deflayered (p l3) (lambda (x) 3))
  (deflayered (q l3) (lambda (x) 5))
  (out "The following yields 5.")
  ((lambda (f) (with-layers (l3) (f 10)))
   (with-layers (l1 l2) (p))))

(define (example)
  (define-layer root)
  (define-layer employment)
  (define-layer info)

  (define-layered print)

  (deflayered (print root) 
    (lambda (person)
      (out (cadr (assq 'name person)))))

  (deflayered (print employment proceed)
    (lambda (person)
      ((proceed) person)
      (out (cadr (assq 'employer person)))))

  (deflayered (print info proceed)
    (lambda (person)
      ((proceed) person)
      (out (cadr (assq 'address person)))))

  (with-layers (root)
   (define pascal '((name "Pascal") (employer "VUB") (address "Brussels")))

   (out "Only name:")
   ((print) pascal)
   (newline)

   (with-layers (employment)
     (out "Name + employer:")
     ((print) pascal))
   (newline)

   (with-layers (info)
     (out "Name + address:")
     ((print) pascal))
   (newline)

   (with-layers (employment info)
     (out "Name + employer + address:")
     ((print) pascal))))