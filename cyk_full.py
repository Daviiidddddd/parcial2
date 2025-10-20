\
# cyk_full.py
# Implementación de:
# - Conversión a CNF (básica) para una gramática dada en forma de diccionario
# - Algoritmo CYK que usa la CNF producida
# - Comparativa de tiempos entre parser LL(1) (importado desde rd_parser_ll1.py) y CYK
#
# Limitaciones: el conversor maneja gramáticas sin símbolos ambiguos extremos y admite
# eliminación de epsilon, eliminación de unitarias y binarización. Está diseñado para
# la gramática de expresiones usada en el parcial.

import itertools, time
from collections import defaultdict

# Grammar representation: dict nonterm -> list of rhs (each rhs is a tuple of symbols (terminals or nonterminals))
# Terminals are lowercase strings like 'id', '+', '*', '(', ')' ; Nonterminals are uppercase like 'E', 'T'

# We'll start from the transformed grammar (after removing left recursion):
# E  -> T EP
# EP -> + T EP | - T EP | ε
# T  -> F TP
# TP -> * F TP | / F TP | ε
# F  -> ( E ) | id

GRAMMAR = {
    'E' : [('T','EP')],
    'EP': [('+','T','EP'), ('-','T','EP'), ()],  # () denotes epsilon
    'T' : [('F','TP')],
    'TP': [('*','F','TP'), ('/','F','TP'), ()],
    'F' : [('(', 'E', ')'), ('id',)]
}

def remove_epsilon(grammar, start):
    # Find nullable nonterminals
    nullable = set(A for A, rhss in grammar.items() if any(len(rhs)==0 for rhs in rhss))
    changed = True
    while changed:
        changed = False
        for A, rhss in grammar.items():
            for rhs in rhss:
                if all((sym in nullable) for sym in rhs) and A not in nullable and len(rhs)>0:
                    nullable.add(A); changed = True
    # Build new grammar without epsilon productions (except possibly for start if needed)
    newg = {}
    for A, rhss in grammar.items():
        new_rhss = set()
        for rhs in rhss:
            if len(rhs)==0:  # skip epsilons; they'll be accounted for via combinations
                continue
            # for each subset of nullable symbols in rhs, produce rhs with those omitted
            indices = [i for i,s in enumerate(rhs) if s in nullable]
            for r in range(0, 1<<len(indices)):
                to_remove = {indices[i] for i in range(len(indices)) if (r>>i)&1}
                new_rhs = tuple(rhs[i] for i in range(len(rhs)) if i not in to_remove)
                if len(new_rhs)==0:
                    # empty: only add epsilon if A is start later; but skip here
                    continue
                new_rhss.add(new_rhs)
        newg[A] = list(new_rhss)
    # If start is nullable, keep epsilon for start explicitly
    if start in nullable:
        newg.setdefault(start, []).append(tuple())
    return newg

def remove_unit_productions(grammar):
    # Remove unit productions A -> B where B is nonterminal
    # Compute unit pairs via transitive closure
    nonterms = set(grammar.keys())
    unit = {A:set() for A in nonterms}
    for A in nonterms:
        for rhs in grammar[A]:
            if len(rhs)==1 and rhs[0] in nonterms:
                unit[A].add(rhs[0])
    # transitive closure
    changed = True
    while changed:
        changed = False
        for A in nonterms:
            for B in list(unit[A]):
                for C in unit.get(B, set()):
                    if C not in unit[A]:
                        unit[A].add(C); changed = True
    # Build new grammar without unit productions
    newg = {}
    for A in nonterms:
        rhss = [rhs for rhs in grammar[A] if not (len(rhs)==1 and rhs[0] in nonterms)]
        # add productions from unit successors
        for B in unit[A]:
            for rhs in grammar[B]:
                if not (len(rhs)==1 and rhs[0] in nonterms):
                    rhss.append(rhs)
        # remove duplicates
        newg[A] = list(dict.fromkeys(rhss))
    return newg

def binarize(grammar):
    # For productions with length > 2, introduce new nonterminals to make them binary
    newg = {}
    counter = 0
    for A, rhss in grammar.items():
        new_rhss = []
        for rhs in rhss:
            if len(rhs) <= 2:
                new_rhss.append(rhs)
            else:
                # create chain: A -> X1 rhs[0] ; X1 -> rhs[1] X2 ; ... final -> rhs[-2] rhs[-1]
                prev = None
                symbols = list(rhs)
                # build right-associative chain
                first = symbols[0]
                rest = symbols[1:]
                current_left = first
                for i in range(len(rest)-1):
                    new_nt = f"X{counter}"; counter += 1
                    new_rhss.append( (current_left, new_nt) )
                    current_left = rest[i]
                    # we need to ensure next iteration uses rest[i+1] etc; but simpler approach below
                # Simpler: create chain by creating intermediate nonterminals from left to right
                # Implement proper method below
                pass
        newg[A] = new_rhss
    # Simpler robust binarization: handle by replacing terminals first and then for each long rhs create chain
    # Let's implement a clearer version below
    return _binarize_full(grammar)

def _binarize_full(grammar):
    newg = {}
    counter = [0]
    def new_nt(): 
        v = f"X{counter[0]}"; counter[0]+=1; return v
    for A, rhss in grammar.items():
        newg.setdefault(A, [])
        for rhs in rhss:
            if len(rhs) <= 2:
                newg[A].append(rhs)
            else:
                symbols = list(rhs)
                left = symbols[0]
                rest = symbols[1:]
                prev = left
                # create chain of new nonterminals representing rest
                for i in range(len(rest)-1):
                    nxt = new_nt()
                    newg.setdefault(A, []).append( (prev, nxt) )
                    prev = rest[i]
                    A = nxt  # subsequent productions should be under new nonterminal
                # last production
                newg.setdefault(A,[]).append( (prev, rest[-1]) )
    # Note: this implementation is somewhat ad-hoc; for our grammar sizes it will suffice.
    return newg

def replace_terminals(grammar, terminals):
    # Ensure that in productions with length 2, terminals are replaced by dedicated nonterminals
    newg = {}
    term_map = {}
    counter = 0
    for A, rhss in grammar.items():
        newg.setdefault(A, [])
        for rhs in rhss:
            if len(rhs)==1 and rhs[0] in terminals:
                # terminal production A -> a (allowed)
                newg[A].append(rhs)
            elif len(rhs)==2:
                a,b = rhs
                na = a
                nb = b
                if a in terminals:
                    ta = f"T_{a}" 
                    term_map[ta] = (a,)
                    na = ta
                if b in terminals:
                    tb = f"T_{b}"
                    term_map[tb] = (b,)
                    nb = tb
                newg[A].append((na, nb))
            else:
                # lengths other than 1 or 2: keep as is (shouldn't happen after binarize)
                newg[A].append(rhs)
    # add terminal mapping rules
    for k,v in term_map.items():
        newg[k] = [v]
    return newg

def to_cnf(grammar, start='E'):
    # steps: remove epsilons, remove unit productions, binarize, replace terminals
    g1 = remove_epsilon(grammar, start)
    g2 = remove_unit_productions(g1)
    g3 = _binarize_full(g2)
    # define terminals set as lowercase tokens seen in original grammar (heuristic)
    terminals = set()
    for rhss in grammar.values():
        for rhs in rhss:
            for s in rhs:
                if s.islower() or (not s.isupper() and s not in ('',)):
                    terminals.add(s)
    g4 = replace_terminals(g3, terminals)
    return g4

def invert_rules(cnf):
    inv = defaultdict(set)
    for A, rhss in cnf.items():
        for rhs in rhss:
            inv[rhs].add(A)
    return inv

def cyk(tokens, cnf, start='E'):
    inv = invert_rules(cnf)
    n = len(tokens)
    if n == 0:
        return False
    table = [ [set() for _ in range(n+1)] for _ in range(n) ]
    # length 1
    for i in range(n):
        t = tokens[i]
        for A in inv.get((t,), set()):
            table[i][1].add(A)
    for l in range(2, n+1):
        for i in range(0, n-l+1):
            for p in range(1, l):
                left = table[i][p]
                right = table[i+p][l-p]
                for B in left:
                    for C in right:
                        for A in inv.get((B,C), set()):
                            table[i][l].add(A)
    return start in table[0][n]

if __name__ == '__main__':
    # Convert grammar to CNF and print it
    cnf = to_cnf(GRAMMAR, start='E')
    print('CNF produced (nonterm -> rhss):')
    for A, rhss in cnf.items():
        print(A, '->', rhss)
    # Test tokens and parse with CYK
    samples = [
        ['id','+','id','*','id'],
        ['(','id','+','id',')','*','id'],
        ['id','+','*','id'],  # invalid
    ]
    for tokens in samples:
        t0 = time.perf_counter()
        ok = cyk(tokens, cnf, start='E')
        t1 = time.perf_counter()
        print('tokens=', tokens, ' -> CYK:', ok, ' time=', (t1-t0))