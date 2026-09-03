import ply.lex as lex
import common_db

# 扩展token列表以支持DDL/DML语句解析
tokens=('SELECT','FROM','WHERE','AND','TCNAME','EQX','COMMA','CONSTANT','SPACE',
        'STAR','SEMICOLON',
        'CREATE','TABLE','INSERT','INTO','VALUES',
        'UPDATE','SET','DELETE','DROP',
        'LPAREN','RPAREN',
        'CHAR','INTEGER')

# the following is to defining rules for each token
def t_SELECT(t):
    r'select'
    return t

def t_FROM(t):
    r'from'
    return t

def t_WHERE(t):
    r'where'
    return t

def t_AND(t):
    r'and'
    return t

# DDL/DML关键字和符号的token规则
def t_STAR(t):
    r'\*'
    return t

def t_SEMICOLON(t):
    r';'
    pass

def t_CREATE(t):
    r'create'
    return t

def t_TABLE(t):
    r'table'
    return t

def t_INSERT(t):
    r'insert'
    return t

def t_INTO(t):
    r'into'
    return t

def t_VALUES(t):
    r'values'
    return t

def t_UPDATE(t):
    r'update'
    return t

def t_SET(t):
    r'set'
    return t

def t_DELETE(t):
    r'delete'
    return t

def t_DROP(t):
    r'drop'
    return t

def t_CHAR(t):
    r'char'
    return t

def t_INTEGER(t):
    r'integer'
    return t

def t_LPAREN(t):
    r'\('
    return t

def t_RPAREN(t):
    r'\)'
    return t

def t_TCNAME(t):
    r'[A-Z_a-z]\w*'
    return t
def t_COMMA(t):
    r','
    return t

def t_EQX(t):
    r'[=]'
    return t

# 修改正则以支持字符串中的非单词字符
def t_CONSTANT(t):
    r'\d+|\'[^\']*\''
    return t

def t_SPACE(t):
    r'\s+'
    pass

# to cope with the error

# 简化错误处理逻辑
def t_error(t):
    print('wrong character: %s' % t.value[0])
    t.lexer.skip(1)

        
# to set the global_lexer in common_db.py
def set_lex_handle():
    common_db.global_lexer=lex.lex()
    if common_db.global_lexer is None:
        print ('wrong when the global_lex is created')



'''
def test():
    my_lexer=lex.lex()
    my_lexer.input("select f1,f2 from GOOD where f1='xx' and f2=5 ")
    while True:
        temp_tok=my_lexer.token()
        if temp_tok is None:
            break
        print temp_tok


test()
'''
