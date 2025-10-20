// CRUD.g4 - Gramática ANTLR4 del Punto 2 
grammar CRUD;

program: stmt* EOF ;

stmt
    : create_stmt ';'
    | insert_stmt ';'
    | select_stmt ';'
    | update_stmt ';'
    | delete_stmt ';'
    ;

create_stmt: CREATE TABLE ID '(' column_list ')' ;
column_list: column_def (',' column_def)* ;
column_def: ID type_spec ;
type_spec: INT | VARCHAR '(' NUMBER ')' | TEXT | BOOLEAN ;

insert_stmt: INSERT INTO ID '(' id_list ')' VALUES '(' value_list ')' ;
id_list: ID (',' ID)* ;
value_list: literal (',' literal)* ;
literal: NUMBER | STRING | NULL | TRUE | FALSE ;

select_stmt: SELECT select_list FROM ID opt_where ;
select_list: STAR | select_item (',' select_item)* ;
select_item: ID ('.' ID)? (AS ID)? | expr (AS ID)? ;

update_stmt: UPDATE ID SET assign_list opt_where ;
assign_list: assign (',' assign)* ;
assign: ID ASSIGN expr ;

delete_stmt: DELETE FROM ID opt_where ;

opt_where: /* vacío */ | WHERE cond_expr ;
cond_expr: cond_term (OR cond_term)* ;
cond_term: cond_factor (AND cond_factor)* ;
cond_factor: '(' cond_expr ')' | comparison ;
comparison: expr comp_op expr ;
comp_op: EQ | NEQ | LT | LE | GT | GE ;

expr: term ((PLUS | MINUS) term)* ;
term: factor ((TIMES | DIV) factor)* ;
factor: LPAREN expr RPAREN | ID | NUMBER | STRING ;

//////////////////////////////////////////////////////////
// Reglas léxicas

CREATE : 'CREATE' ;
TABLE  : 'TABLE' ;
INSERT : 'INSERT' ;
INTO   : 'INTO' ;
VALUES : 'VALUES' ;
SELECT : 'SELECT' ;
FROM   : 'FROM' ;
WHERE  : 'WHERE' ;
UPDATE : 'UPDATE' ;
SET    : 'SET' ;
DELETE : 'DELETE' ;
AS     : 'AS' ;

INT : 'INT' ;
VARCHAR : 'VARCHAR' ;
TEXT : 'TEXT' ;
BOOLEAN : 'BOOLEAN' ;

TRUE : 'TRUE' ;
FALSE: 'FALSE' ;
NULL : 'NULL' ;

STAR   : '*' ;
SEMI   : ';' ;
COMMA  : ',' ;
LPAREN : '(' ;
RPAREN : ')' ;
DOT    : '.' ;

PLUS   : '+' ;
MINUS  : '-' ;
TIMES  : '*' ;
DIV    : '/' ;

EQ  : '==' ;
NEQ : '!=' ;
LT  : '<' ;
LE  : '<=' ;
GT  : '>' ;
GE  : '>=' ;

AND : 'AND' ;
OR  : 'OR' ;

ASSIGN : '=' ;

NUMBER : [0-9]+ ;
STRING : '\'' (~'\'')* '\'' ;
ID : [a-zA-Z_] [a-zA-Z_0-9]* ;

WS : [ \t\r\n]+ -> skip ;
COMMENT: '--' ~[\r\n]* -> skip ;
