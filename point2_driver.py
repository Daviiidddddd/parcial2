# codigo de python

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
