# Punto 3 — Transformación a LL(1), FIRST/FOLLOW y conjuntos PRED

Este archivo resume la transformación de la gramática aritmética clásica a una forma LL(1)
y contiene los conjuntos FIRST, FOLLOW y los conjuntos de predicción (PRED).

## Gramática original (ambigua / con recursión izquierda)
E -> E + T | T
T -> T * F | F
F -> ( E ) | id

## Eliminación de recursión izquierda (transformación a forma equivalente LL)
E  -> T E'
E' -> '+' T E' | '-' T E' | ε
T  -> F T'
T' -> '*' F T' | '/' F T' | ε
F  -> '(' E ')' | id

## FIRST sets
FIRST(E)  = FIRST(T) = FIRST(F) = { '(', id }
FIRST(E') = { '+', '-', ε }
FIRST(T') = { '*', '/', ε }
FIRST(F)  = { '(', id }

## FOLLOW sets (suponiendo S = E y $ = EOF)
FOLLOW(E)  = { ')', $ }
FOLLOW(E') = { ')', $ }
FOLLOW(T)  = { '+', '-', ')', $ }
FOLLOW(T') = { '+', '-', ')', $ }
FOLLOW(F)  = { '*', '/', '+', '-', ')', $ }

## Predicción (PRED) para cada producción
PRED(E -> T E')     = FIRST(T) = { '(', id }
PRED(E' -> + T E')  = { '+' }
PRED(E' -> - T E')  = { '-' }
PRED(E' -> ε)       = FOLLOW(E') = { ')', $ }
PRED(T -> F T')     = FIRST(F) = { '(', id }
PRED(T' -> * F T')  = { '*' }
PRED(T' -> / F T')  = { '/' }
PRED(T' -> ε)       = FOLLOW(T') = { '+', '-', ')', $ }
PRED(F -> ( E ))    = { '(' }
PRED(F -> id)       = { id }

## Comentarios
- La gramática resultante es LL(1) y puede implementarse con un parser recursivo-descendente predictivo.
- A continuación se incluye un parser en Python `rd_parser_ll1.py` que implementa las funciones E, E', T, T', F y
  una función `match()` que consume tokens. El parser reporta errores con posición y realiza comprobación completa.
