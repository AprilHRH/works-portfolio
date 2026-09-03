import common_db

# the following two packages need to be installed by yourself
import ply.yacc as yacc 
import ply.lex as lex



from lex_db import tokens



# Query  : SFW | CreateStmt | InsertStmt | DeleteStmt | UpdateStmt | DropStmt
#   SWF  : SELECT SelList FROM FromList WHERE Cond
#   SWF  : SELECT SelList FROM FromList
# SelList: TCNAME COMMA SelList
# SelList: TCNAME
# SelList: STAR
# FromList:TCNAME COMMA FromList
# FromList:TCNAME
# Cond: TCNAME EQX CONSTANT
# Cond: Cond AND Cond
# CreateStmt: CREATE TABLE TCNAME LPAREN FieldDefList RPAREN
# InsertStmt: INSERT INTO TCNAME VALUES LPAREN ValueList RPAREN
# DeleteStmt: DELETE FROM TCNAME
# UpdateStmt: UPDATE TCNAME SET TCNAME EQX CONSTANT WHERE Cond
# DropStmt: DROP TABLE TCNAME
# FieldDefList: FieldDef COMMA FieldDefList | FieldDef
# FieldDef: TCNAME CHAR LPAREN CONSTANT RPAREN | TCNAME INTEGER
# ValueList: CONSTANT COMMA ValueList | CONSTANT



# check the syntax tree
# input:
#       syntax tree
# output:
#       true or falise
# 霍荣皓 递归检查语法树节点类型和最小子节点数量
def check_syn_tree(syn_tree):
    if syn_tree:
        # 检查Query节点至少有1个子节点(SFW或其他DDL/DML语句节点)
        if syn_tree.value == 'Query' and len(syn_tree.children) < 1:
            print('Error: Query node must have at least 1 child')
            return False
        # 检查SFW节点必须有4个子节点(无WHERE)或6个子节点(有WHERE)
        if syn_tree.value == 'SFW':
            if len(syn_tree.children) not in (4, 6):
                print('Error: SFW node must have 4 or 6 children')
                return False
        # 递归检查所有子节点
        if syn_tree.children:
            for child in syn_tree.children:
                if isinstance(child, common_db.Node):
                    if not check_syn_tree(child):
                        return False
    return True



#(1) construct the node for query expression
#(2) check the tree
#(3) view the data in the tree
# input:
#       
# output:
#       the root node of syntax tree
# 霍荣皓 扩展Query语法规则，支持DDL/DML语句
def p_expr_query(t):
    '''Query : SFW
             | CreateStmt
             | InsertStmt
             | DeleteStmt
             | UpdateStmt
             | DropStmt'''

    t[0]=common_db.Node('Query',[t[1]])
    common_db.global_syn_tree=t[0]
    check_syn_tree(common_db.global_syn_tree)
    common_db.show(common_db.global_syn_tree)

    return t

#(1) construct the node for WFW expression
# input:
#       
# output:
#       the nodes
def p_expr_swf(t):
    'SFW : SELECT SelList FROM FromList WHERE Cond'
    t[1]=common_db.Node('SELECT',None)
    t[3]=common_db.Node('FROM',None)
    t[5]=common_db.Node('WHERE',None)

    t[0]=common_db.Node('SFW',[t[1],t[2],t[3],t[4],t[5],t[6]])


    return t

# 霍荣皓 新增无WHERE子句的SFW规则（4个子节点）
def p_expr_swf_no_where(t):
    'SFW : SELECT SelList FROM FromList'  # 无WHERE子句的SFW，只有4个子节点
    t[1]=common_db.Node('SELECT',None)
    t[3]=common_db.Node('FROM',None)

    t[0]=common_db.Node('SFW',[t[1],t[2],t[3],t[4]])

    return t

#construct the node for select list
# input:
#       
# output:
#       the nodes

def p_expr_sellist_first(t):
    'SelList : TCNAME COMMA SelList'
    
    
    t[1]=common_db.Node('TCNAME',[t[1]])
    
    t[2]=common_db.Node(',',None)
    t[0]=common_db.Node('SelList',[t[1],t[2],t[3]])
    
    return t

#construct the node for select list expression
# input:
#       
# output:
#       the nodes
def p_expr_sellist_second(t):
    'SelList : TCNAME'

    t[1]=common_db.Node('TCNAME',[t[1]])
    t[0]=common_db.Node('SelList',[t[1]])

    return t

# 霍荣皓 新增SELECT * 语法支持
def p_expr_sellist_star(t):
    'SelList : STAR'  # 允许 SELECT * 语法
    t[1]=common_db.Node('STAR',[t[1]])
    t[0]=common_db.Node('SelList',[t[1]])

    return t


#construct the node for from expression
# input:
#       
# output:
#       the nodes
def p_expr_fromlist_first(t):
    'FromList : TCNAME COMMA FromList'
    t[1]=common_db.Node('TCNAME',[t[1]])
    t[2]=common_db.Node(',',None)
    t[0]=common_db.Node('FromList',[t[1],t[2],t[3]])
    
    return t


#(1) construct the node for from expression
# input:
#       
# output:
#       the nodes
def p_expr_fromlist_second(t):
    'FromList : TCNAME'
    t[1]=common_db.Node('TCNAME',[t[1]])
    t[0]=common_db.Node('FromList',[t[1]])    
    return t
        
#construct the node for condition expression
# input:
#       
# output:
#       the nodes
def p_expr_condition(t):
    'Cond : TCNAME EQX CONSTANT'
    t[1]=common_db.Node('TCNAME',[t[1]])
    t[2]=common_db.Node('=',None)
    t[3]=common_db.Node('CONSTANT',[t[3]])

    t[0]=common_db.Node('Cond',[t[1],t[2],t[3]])

    return t

# 霍荣皓 新增AND复合条件支持
def p_expr_condition_and(t):
    'Cond : Cond AND Cond'  # 支持 Cond AND Cond 复合条件
    t[2]=common_db.Node('AND',None)
    t[0]=common_db.Node('Cond',[t[1],t[2],t[3]])

    return t


    
# 霍荣皓 以下为DDL/DML语法规则

# construct the node for CREATE TABLE statement
# input:
#
# output:
#       the nodes
def p_expr_create(t):
    'CreateStmt : CREATE TABLE TCNAME LPAREN FieldDefList RPAREN'  # CREATE TABLE语句
    t[1]=common_db.Node('CREATE',None)
    t[2]=common_db.Node('TABLE',None)
    t[3]=common_db.Node('TCNAME',[t[3]])
    t[4]=common_db.Node('(',None)
    t[6]=common_db.Node(')',None)

    t[0]=common_db.Node('CreateStmt',[t[1],t[2],t[3],t[4],t[5],t[6]])

    return t

# construct the node for INSERT INTO statement
# input:
#
# output:
#       the nodes
def p_expr_insert(t):
    'InsertStmt : INSERT INTO TCNAME VALUES LPAREN ValueList RPAREN'  # INSERT语句
    t[1]=common_db.Node('INSERT',None)
    t[2]=common_db.Node('INTO',None)
    t[3]=common_db.Node('TCNAME',[t[3]])
    t[4]=common_db.Node('VALUES',None)
    t[5]=common_db.Node('(',None)
    t[7]=common_db.Node(')',None)

    t[0]=common_db.Node('InsertStmt',[t[1],t[2],t[3],t[4],t[5],t[6],t[7]])

    return t

# construct the node for DELETE FROM statement
# input:
#
# output:
#       the nodes
def p_expr_delete(t):
    'DeleteStmt : DELETE FROM TCNAME'  # DELETE语句
    t[1]=common_db.Node('DELETE',None)
    t[2]=common_db.Node('FROM',None)
    t[3]=common_db.Node('TCNAME',[t[3]])

    t[0]=common_db.Node('DeleteStmt',[t[1],t[2],t[3]])

    return t

# construct the node for UPDATE statement
# input:
#
# output:
#       the nodes
def p_expr_update(t):
    'UpdateStmt : UPDATE TCNAME SET TCNAME EQX CONSTANT WHERE Cond'  # UPDATE语句
    t[1]=common_db.Node('UPDATE',None)
    t[2]=common_db.Node('TCNAME',[t[2]])
    t[3]=common_db.Node('SET',None)
    t[4]=common_db.Node('TCNAME',[t[4]])
    t[5]=common_db.Node('=',None)
    t[6]=common_db.Node('CONSTANT',[t[6]])
    t[7]=common_db.Node('WHERE',None)

    t[0]=common_db.Node('UpdateStmt',[t[1],t[2],t[3],t[4],t[5],t[6],t[7],t[8]])

    return t

# construct the node for DROP TABLE statement
# input:
#
# output:
#       the nodes
def p_expr_drop(t):
    'DropStmt : DROP TABLE TCNAME'  # DROP TABLE语句
    t[1]=common_db.Node('DROP',None)
    t[2]=common_db.Node('TABLE',None)
    t[3]=common_db.Node('TCNAME',[t[3]])

    t[0]=common_db.Node('DropStmt',[t[1],t[2],t[3]])

    return t

# construct the node for FieldDefList (recursive)
# input:
#
# output:
#       the nodes
def p_expr_fielddeflist_first(t):
    'FieldDefList : FieldDef COMMA FieldDefList'  # 多个字段定义，递归展开
    t[2]=common_db.Node(',',None)
    t[0]=common_db.Node('FieldDefList',[t[1],t[2],t[3]])

    return t

def p_expr_fielddeflist_second(t):
    'FieldDefList : FieldDef'  # 单个字段定义
    t[0]=common_db.Node('FieldDefList',[t[1]])

    return t

# construct the node for FieldDef (CHAR type)
# input:
#
# output:
#       the nodes
def p_expr_fielddef_char(t):
    'FieldDef : TCNAME CHAR LPAREN CONSTANT RPAREN'  # CHAR(n)类型字段定义
    t[1]=common_db.Node('TCNAME',[t[1]])
    t[2]=common_db.Node('CHAR',None)
    t[3]=common_db.Node('(',None)
    t[4]=common_db.Node('CONSTANT',[t[4]])
    t[5]=common_db.Node(')',None)

    t[0]=common_db.Node('FieldDef',[t[1],t[2],t[3],t[4],t[5]])

    return t

# construct the node for FieldDef (INTEGER type)
# input:
#
# output:
#       the nodes
def p_expr_fielddef_integer(t):
    'FieldDef : TCNAME INTEGER'  # INTEGER类型字段定义
    t[1]=common_db.Node('TCNAME',[t[1]])
    t[2]=common_db.Node('INTEGER',None)

    t[0]=common_db.Node('FieldDef',[t[1],t[2]])

    return t

# construct the node for ValueList (recursive)
# input:
#
# output:
#       the nodes
def p_expr_valuelist_first(t):
    'ValueList : CONSTANT COMMA ValueList'  # 多个值，递归展开
    t[1]=common_db.Node('CONSTANT',[t[1]])
    t[2]=common_db.Node(',',None)
    t[0]=common_db.Node('ValueList',[t[1],t[2],t[3]])

    return t

def p_expr_valuelist_second(t):
    'ValueList : CONSTANT'  # 单个值
    t[1]=common_db.Node('CONSTANT',[t[1]])
    t[0]=common_db.Node('ValueList',[t[1]])

    return t


# for error
# input:
#
# output:
#       the error messages
def p_error(t):
# 霍荣皓 改进错误处理，增加None检查
    if t is not None and hasattr(t, 'value'):
        print ('wrong at %s' % t.value)  # 打印出错token的值
    else:
        print ('wrong input')  # token为空时输出通用错误提示


# to set the global_parser handle in common_db.py
def set_handle():    
    common_db.global_parser=yacc.yacc(write_tables=0)
    if common_db.global_parser is None:
        print ('wrong when yacc object is created')

        
    
# the following is to test
'''
# the following is to test
my_str="select f1,f2 from t1,t2 where f1=9"
my_parser=yacc.yacc(write_tables=0)# the tabl does not cache
my_parser.parse(my_str)
'''

