# point2_driver.py - Driver de prueba del Punto 2 para la gramática CRUD.g4
# Instrucciones:
# 1. Instalar ANTLR4 y su runtime para Python:
#    pip install antlr4-python3-runtime
# 2. Generar el parser con:
#    antlr4 -Dlanguage=Python3 CRUD.g4 -o antlr_out
# 3. Ejecutar:
#    python3 point2_driver.py tests.sql

import sys
from antlr4 import FileStream, CommonTokenStream, ParseTreeWalker

from antlr_out.CRUDLexer import CRUDLexer
from antlr_out.CRUDParser import CRUDParser

def main(input_file):
    input_stream = FileStream(input_file, encoding='utf-8')
    lexer = CRUDLexer(input_stream)
    tokens = CommonTokenStream(lexer)
    parser = CRUDParser(tokens)
    tree = parser.program()
    print(tree.toStringTree(recog=parser))

if __name__ == "__main__":
    file_path = sys.argv[1] if len(sys.argv) > 1 else "tests.sql"
    main(file_path)
