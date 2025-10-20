# rd_parser_match.py, codigo del punto5
# Parser descendente recursivo con implementación sólida de 'match' y recuperación de errores (modo pánico).
# Usa la gramática transformada para expresiones y también reconoce las sentencias CRUD básicas para demo.
#
# Funcionalidades:
# - función match(expected) que consume tokens o registra error y trata de recuperarse.
# - recuperación por pánico: al encontrar un error, el parser salta tokens hasta encontrar uno en el conjunto de sincronización.
# - reportes de errores con posición y mensaje claro.
# - ejemplos de uso en __main__ con sentencias válidas e inválidas.

import re
from pprint import pprint

# Tokenizer (similar al usado en Punto 1)
TOKEN_SPEC = [
    ('NUMBER',   r'\d+'),
    ('STRING',   r"'([^'\\]|\\.)*'"),
    ('COMMA',    r','),
    ('SEMI',     r';'),
    ('LPAREN',   r'\('),
    ('RPAREN',   r'\)'),
    ('STAR',     r'\*'),
    ('EQ',       r'=='),
    ('NEQ',      r'!='),
    ('LE',       r'<='),
    ('GE',       r'>='),
    ('LT',       r'<'),
    ('GT',       r'>'),
    ('ASSIGN',   r'='),
    ('PLUS',     r'\+'),
    ('MINUS',    r'-'),
    ('TIMES',    r'\*'),
    ('DIV',      r'/'),
    ('DOT',      r'\.'),
    ('ID',       r'[A-Za-z_][A-Za-z0-9_]*'),
    ('WS',       r'[ \t\r\n]+'),
    ('MISMATCH', r'.'),
]

MASTER_RE = re.compile('|'.join('(?P<%s>%s)' % pair for pair in TOKEN_SPEC), re.DOTALL | re.IGNORECASE)

KEYWORDS = {'CREATE','TABLE','INSERT','INTO','VALUES','SELECT','FROM','WHERE','UPDATE','SET','DELETE','AS','TRUE','FALSE','NULL','INT','VARCHAR','TEXT','BOOLEAN','AND','OR'}

class Token:
    def __init__(self, type_, value, pos):
        self.type = type_
        self.value = value
        self.pos = pos
    def __repr__(self):
        return f"Token({self.type},{self.value!r},{self.pos})"

def tokenize(s):
    for m in MASTER_RE.finditer(s):
        kind = m.lastgroup
        val = m.group()
        if kind == 'WS': continue
        if kind == 'ID':
            up = val.upper()
            if up in KEYWORDS:
                yield Token(up, up, m.start())
            else:
                yield Token('ID', val, m.start())
        elif kind == 'MISMATCH':
            raise SyntaxError(f'Unexpected character {val!r} at {m.start()}')
        else:
            yield Token(kind, val, m.start())
    yield Token('EOF','', len(s))

# Parser with match() and panic-mode recovery
class RDParserMatch:
    def __init__(self, tokens):
        self.tokens = list(tokens)
        self.i = 0
        self.curr = self.tokens[self.i]
        self.errors = []

    def next(self):
        self.i += 1
        if self.i < len(self.tokens):
            self.curr = self.tokens[self.i]
        else:
            self.curr = Token('EOF','', self.curr.pos if self.curr else 0)

    def error(self, message):
        msg = f"Error at pos {self.curr.pos}: {message} (got {self.curr.type}:'{self.curr.value}')"
        self.errors.append(msg)
        print(msg)

    def match(self, expected, sync_set=None):
        """Consume token if it matches expected. If not, report error and attempt recovery.
        expected: token type string or tuple/list of acceptable token types.
        sync_set: optional set of token types used for synchronization during panic-mode recovery.
        Returns True if matched, False if not (after recovery may have skipped tokens to sync point).
        """
        if isinstance(expected, str):
            expected = (expected,)
        if self.curr.type in expected:
            self.next()
            return True
        # mismatch: report error
        self.error(f"Expected {'/'.join(expected)}") 
        # panic-mode recovery: skip until we find a token in sync_set or one of expected
        if sync_set is None:
            sync_set = {'SEMI', 'EOF'}  # default sync: end of statement
        # also accept expected tokens if they appear later
        while self.curr.type not in sync_set and self.curr.type not in expected:
            self.next()
        # if found expected, consume it and continue
        if self.curr.type in expected:
            self.next()
            return True
        # otherwise, we stopped at a sync token (e.g., SEMI) and return False
        return False

    # Example: parse simple statement list with synchronization sets
    def parse_program(self):
        stmts = []
        while self.curr.type != 'EOF':
            stm = self.parse_stmt()
            stmts.append(stm)
            # ensure statement ends with SEMI; if not present, try to sync and skip to next
            if self.curr.type == 'SEMI':
                self.match('SEMI')
            else:
                # attempt to sync at SEMI or EOF
                self.match(('SEMI',), sync_set={'SEMI','EOF'})
        return stmts

    def parse_stmt(self):
        # sync sets for statements: if error inside, skip to next SEMI to continue parsing
        sync = {'SEMI','EOF'}
        if self.curr.type == 'CREATE':
            return self.parse_create(sync)
        if self.curr.type == 'INSERT':
            return self.parse_insert(sync)
        if self.curr.type == 'SELECT':
            return self.parse_select(sync)
        if self.curr.type == 'UPDATE':
            return self.parse_update(sync)
        if self.curr.type == 'DELETE':
            return self.parse_delete(sync)
        # unknown start -> skip to next semicolon
        self.error('Unexpected start of statement')
        self.match(('SEMI',), sync_set=sync)
        return ('error_stmt',)

    def parse_create(self, sync):
        self.match('CREATE', sync_set=sync)
        self.match('TABLE', sync_set=sync)
        tbl = None
        if self.match('ID', sync_set=sync):
            tbl = self.tokens[self.i-1].value
        else:
            # failed to get table name; sync will skip to SEMI likely
            return ('create', None, [])
        if not self.match('LPAREN', sync_set=sync):
            return ('create', tbl, [])
        cols = []
        # parse column list with recovery on commas
        while True:
            if self.match('ID', sync_set=sync):
                col = self.tokens[self.i-1].value
                # expect type
                if self.curr.type in ('INT','TEXT','BOOLEAN'):
                    t = self.curr.type; self.next()
                elif self.curr.type == 'VARCHAR':
                    self.next(); self.match('LPAREN', sync_set=sync)
                    if self.match('NUMBER', sync_set=sync):
                        num = self.tokens[self.i-1].value
                        self.match('RPAREN', sync_set=sync)
                        t = f'VARCHAR({num})'
                    else:
                        t = 'VARCHAR(?)'
                else:
                    # missing type, report and continue
                    self.error(f'Missing type for column {col}')
                    t = 'UNKNOWN'
                cols.append((col, t))
            else:
                break
            if self.curr.type == 'COMMA':
                self.next(); continue
            else:
                break
        if not self.match('RPAREN', sync_set=sync):
            # attempt to recover but continue
            pass
        return ('create', tbl, cols)

    def parse_insert(self, sync):
        self.match('INSERT', sync_set=sync); self.match('INTO', sync_set=sync)
        tbl = None
        if self.match('ID', sync_set=sync):
            tbl = self.tokens[self.i-1].value
        else:
            return ('insert', None, [], [])
        if not self.match('LPAREN', sync_set=sync):
            return ('insert', tbl, [], [])
        ids = []
        while True:
            if self.match('ID', sync_set=sync):
                ids.append(self.tokens[self.i-1].value)
            else:
                break
            if self.curr.type == 'COMMA':
                self.next(); continue
            else:
                break
        self.match('RPAREN', sync_set=sync)
        self.match('VALUES', sync_set=sync)
        self.match('LPAREN', sync_set=sync)
        vals = []
        while True:
            if self.curr.type == 'NUMBER':
                vals.append(('num', self.curr.value)); self.next()
            elif self.curr.type == 'STRING':
                vals.append(('str', self.curr.value)); self.next()
            elif self.curr.type in ('TRUE','FALSE','NULL'):
                vals.append((self.curr.type.lower(), self.curr.value)); self.next()
            else:
                # unexpected literal; attempt to recover by skipping to comma or RPAREN
                self.error('Expected literal in VALUES list')
                self.match(('COMMA','RPAREN'), sync_set=sync)
                if self.curr.type == 'COMMA':
                    self.next(); continue
                else:
                    break
            if self.curr.type == 'COMMA':
                self.next(); continue
            else:
                break
        self.match('RPAREN', sync_set=sync)
        return ('insert', tbl, ids, vals)

    def parse_select(self, sync):
        self.match('SELECT', sync_set=sync)
        # select list
        items = []
        if self.curr.type == 'STAR':
            self.next(); items = ['*']
        else:
            while True:
                if self.match('ID', sync_set=sync):
                    name = self.tokens[self.i-1].value
                    if self.curr.type == 'DOT':
                        self.next(); self.match('ID', sync_set=sync); name += '.' + self.tokens[self.i-1].value
                    if self.curr.type == 'AS':
                        self.next(); self.match('ID', sync_set=sync); name = (name, self.tokens[self.i-1].value)
                    items.append(name)
                else:
                    # try to parse expression as fallback (not implemented fully here)
                    break
                if self.curr.type == 'COMMA':
                    self.next(); continue
                else:
                    break
        self.match('FROM', sync_set=sync)
        tbl = None
        if self.match('ID', sync_set=sync):
            tbl = self.tokens[self.i-1].value
        where = None
        if self.curr.type == 'WHERE':
            self.next()
            where = self.parse_cond_expr(sync)
        return ('select', items, tbl, where)

    def parse_update(self, sync):
        self.match('UPDATE', sync_set=sync)
        tbl = None
        if self.match('ID', sync_set=sync):
            tbl = self.tokens[self.i-1].value
        self.match('SET', sync_set=sync)
        assigns = []
        while True:
            if self.match('ID', sync_set=sync):
                name = self.tokens[self.i-1].value
                if self.match('ASSIGN', sync_set=sync):
                    expr = self.parse_expr_simple()
                    assigns.append((name, expr))
                else:
                    # missing assignment operator
                    break
            else:
                break
            if self.curr.type == 'COMMA':
                self.next(); continue
            else:
                break
        where = None
        if self.curr.type == 'WHERE':
            self.next(); where = self.parse_cond_expr(sync)
        return ('update', tbl, assigns, where)

    def parse_delete(self, sync):
        self.match('DELETE', sync_set=sync); self.match('FROM', sync_set=sync)
        tbl = None
        if self.match('ID', sync_set=sync):
            tbl = self.tokens[self.i-1].value
        where = None
        if self.curr.type == 'WHERE':
            self.next(); where = self.parse_cond_expr(sync)
        return ('delete', tbl, where)

    # expression helpers (simple)
    def parse_expr_simple(self):
        return self.parse_expr_term()
    def parse_expr_term(self):
        node = self.parse_expr_factor()
        while self.curr.type in ('PLUS','MINUS'):
            op = self.curr.type; self.next(); rhs = self.parse_expr_factor(); node = (op, node, rhs)
        return node
    def parse_expr_factor(self):
        node = self.parse_expr_atom()
        while self.curr.type in ('TIMES','DIV'):
            op = self.curr.type; self.next(); rhs = self.parse_expr_atom(); node = (op, node, rhs)
        return node
    def parse_expr_atom(self):
        if self.curr.type == 'LPAREN':
            self.match('LPAREN'); node = self.parse_expr_simple(); self.match('RPAREN'); return node
        if self.curr.type == 'NUMBER':
            v = self.curr.value; self.next(); return ('num', v)
        if self.curr.type == 'STRING':
            v = self.curr.value; self.next(); return ('str', v)
        if self.curr.type == 'ID':
            v = self.curr.value; self.next(); return ('id', v)
        # error
        self.error('Unexpected token in expression'); self.match(('SEMI','COMMA','RPAREN'), sync_set={'SEMI','COMMA','RPAREN'})
        return ('error_expr',)

    # conditions (comparison + AND/OR)
    def parse_cond_expr(self, sync):
        left = self.parse_cond_term(sync)
        while self.curr.type == 'OR':
            self.next(); right = self.parse_cond_term(sync); left = ('or', left, right)
        return left
    def parse_cond_term(self, sync):
        left = self.parse_cond_factor(sync)
        while self.curr.type == 'AND':
            self.next(); right = self.parse_cond_factor(sync); left = ('and', left, right)
        return left
    def parse_cond_factor(self, sync):
        if self.curr.type == 'LPAREN':
            self.next(); node = self.parse_cond_expr(sync); self.match('RPAREN', sync_set=sync); return node
        # comparison
        l = self.parse_expr_simple()
        if self.curr.type in ('EQ','NEQ','LT','LE','GT','GE','ASSIGN'):
            op = self.curr.type; self.next(); r = self.parse_expr_simple(); return (op.lower(), l, r)
        self.error('Expected comparison operator'); self.match(('SEMI','COMMA','RPAREN'), sync_set=sync); return ('error_cond',)

# Example usage
if __name__ == '__main__':
    code = """
    CREATE TABLE users (id INT, name VARCHAR(100), active BOOLEAN);
    INSERT INTO users (id, name, active) VALUES (1, 'Ana', TRUE);
    SELECT id, name FROM users WHERE active = TRUE;
    -- invalid statements to test recovery
    INSERT INTO users id, name VALUES (1, 'Ana');
    UPDATE users SET = 'x' WHERE id = 2;
    DELETE FROM WHERE id = 1;
    """
    # strip comments
    lines = [ln.split('--')[0] for ln in code.splitlines()]
    code_clean = '\n'.join(lines)
    tokens = list(tokenize(code_clean))
    print('TOKENS:', tokens)
    p = RDParserMatch(tokens)
    ast = p.parse_program()
    print('\nAST:') ; pprint(ast)
    print('\nErrors:'); pprint(p.errors)
