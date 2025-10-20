# Punto 2 — Implementación práctica del lenguaje CRUD

Este punto implementa la gramática del lenguaje CRUD (del punto 1) en ANTLR4 y ejecuta pruebas sobre ella.

## Contenido
- CRUD.g4 — gramática ANTLR4 del lenguaje CRUD
- point2_driver.py — script Python para ejecutar el parser generado
- tests.sql — ejemplos válidos de comandos CRUD

## Instrucciones de uso

1. Instalar ANTLR4 y el runtime de Python:

```bash
pip install antlr4-python3-runtime
```

2. Generar el parser:

```bash
antlr4 -Dlanguage=Python3 CRUD.g4 -o antlr_out
```

3. Ejecutar el driver:

```bash
python3 point2_driver.py tests.sql
```

El resultado será el árbol de análisis sintáctico de cada sentencia CRUD.

## Ejemplo de salida esperada
```
(program (stmt (create_stmt CREATE TABLE users ( (column_list (column_def id INT) , (column_def name VARCHAR ( 100 )) , (column_def active BOOLEAN)) )) ;))
...
```
