# rd_parser_ll1.py - Parser recursivo-descendente (LL(1)) para la gramática transformada
# Gramática usada:
# E  -> T E'
# E' -> ('+' | '-') T E' | ε
# T  -> F T'
# T' -> ('*' | '/') F T' | ε
# F  -> '(' E ')' | id | number

import re, sys
from pprint import pprint

TOKENS = [
    ('NUMBER',   r'\d+'),
    ('ID',       r'[a-zA-Z_][a-zA-Z0-9_]*'),
    ('PLUS',     r'\+'),
    ('MINUS',    r'-'),
    ('TIMES',    r'\*'),
    ('DIV',      r'/'),
    ('LPAREN',   r'\('),
    ('RPAREN',   r'\)'),
    ('WS',       r'[ \t\r\n]+'),
    ('MISMATCH', r'.'),
]

TOK_REGEX = re.compile('|'.join('(?P<%s>%s)' % pair for pair in TOKENS))

class Token:
    def __init__(self, type_, value, pos):
        self.type = type_
        self.value = value
        self.pos = pos
    def __repr__(self):
        return f"Token({self.type},{self.value!r},{self.pos})"

def tokenize(s):
    for m in TOK_REGEX.finditer(s):
        kind = m.lastgroup; val = m.group()
        if kind == 'WS': continue
        if kind == 'MISMATCH':
            raise SyntaxError(f'Unexpected char {val!r} at {m.start()}')
        yield Token(kind, val, m.start())
    yield Token('EOF','', len(s))

class ParserLL1:
    def __init__(self, tokens):
        self.tokens = list(tokens)
        self.i = 0
        self.curr = self.tokens[self.i]
    def next(self):
        self.i += 1
        if self.i < len(self.tokens):
            self.curr = self.tokens[self.i]
        else:
            self.curr = Token('EOF','', self.curr.pos if self.curr else 0)
    def match(self, expected):
        # expected: token type string or tuple/list of types
        if isinstance(expected, str):
            expected = (expected,)
        if self.curr.type in expected:
            val = self.curr.value
            self.next()
            return val
        raise SyntaxError(f"Expected {expected} at pos {self.curr.pos}, got {self.curr.type} ('{self.curr.value}')")
    # Grammar functions
    def parse_E(self):
        t = self.parse_T()
        ep = self.parse_Ep()
        return ('E', t, ep)
    def parse_Ep(self):
        if self.curr.type in ('PLUS','MINUS'):
            op = self.curr.type; self.next()
            t = self.parse_T()
            ep = self.parse_Ep()
            return ('Ep', op, t, ep)
        # epsilon
        return ('Ep', 'ε')
    def parse_T(self):
        f = self.parse_F()
        tp = self.parse_Tp()
        return ('T', f, tp)
    def parse_Tp(self):
        if self.curr.type in ('TIMES','DIV'):
            op = self.curr.type; self.next()
            f = self.parse_F()
            tp = self.parse_Tp()
            return ('Tp', op, f, tp)
        return ('Tp', 'ε')
    def parse_F(self):
        if self.curr.type == 'LPAREN':
            self.match('LPAREN')
            e = self.parse_E()
            self.match('RPAREN')
            return ('F', '(', e, ')')
        if self.curr.type == 'ID':
            v = self.match('ID'); return ('F', ('id', v))
        if self.curr.type == 'NUMBER':
            v = self.match('NUMBER'); return ('F', ('num', v))
        raise SyntaxError(f"Unexpected token in F at pos {self.curr.pos}: {self.curr}")

def parse_expression(s):
    toks = tokenize(s)
    p = ParserLL1(toks)
    ast = p.parse_E()
    if p.curr.type != 'EOF':
        raise SyntaxError(f"Extra input after valid expression at pos {p.curr.pos}: {p.curr}")
    return ast

if __name__ == '__main__':
    samples = [
        "id + id * id",
        "( id + id ) * id",
        "id + - id",
        "(1 + 2) * 3",
    ]
    for s in samples:
        try:
            print('\nInput:', s)
            ast = parse_expression(s)
            pprint(ast)
        except Exception as e:
            print('Error:', e)
