NODE_QUERY = 'Query'           # 查询根节点，包含一个子节点（SFW或DDL/DML语句）
NODE_SFW = 'SFW'               # SELECT-FROM-WHERE 语句节点
# 关键字节点
NODE_SELECT = 'SELECT'         # SELECT 关键字节点
NODE_FROM = 'FROM'             # FROM 关键字节点
NODE_WHERE = 'WHERE'           # WHERE 关键字节点
# 关键字节点
NODE_COND = 'Cond'             # WHERE 条件表达式节点
NODE_AND = 'AND'               # AND 逻辑连接词节点
# 关键字节点
NODE_TCNAME = 'TCNAME'         # 表名或列名标识符节点
NODE_CONSTANT = 'CONSTANT'     # 常量值节点（整数或引号字符串）
NODE_SELLIST = 'SelList'       # SELECT 列列表节点
NODE_FROMLIST = 'FromList'     # FROM 表列表节点
# 关键字节点
NODE_CREATE = 'CreateStmt'     # CREATE TABLE 语句节点
NODE_INSERT = 'InsertStmt'     # INSERT INTO 语句节点
NODE_DELETE = 'DeleteStmt'     # DELETE FROM 语句节点
NODE_UPDATE = 'UpdateStmt'     # UPDATE SET 语句节点
NODE_DROP = 'DropStmt'         # DROP TABLE 语句节点
# 关键字节点
NODE_TABLE = 'TABLE'           # TABLE 关键字节点
NODE_VALUES = 'VALUES'         # VALUES 关键字节点
NODE_INTO = 'INTO'             # INTO 关键字节点
NODE_SET = 'SET'               # SET 关键字节点
# 关键字节点
NODE_FIELDDEF = 'FieldDef'     # 字段定义节点（字段名 + 类型）
NODE_FIELDDEFLIST = 'FieldDefList'  # 字段定义列表节点
NODE_VALUELIST = 'ValueList'   # 值列表节点
# 关键字节点
NODE_CHAR = 'CHAR'             # CHAR 类型关键字节点
NODE_INTEGER = 'INTEGER'       # INTEGER 类型关键字节点
NODE_LPAREN = 'LPAREN'         # 左括号节点
NODE_RPAREN = 'RPAREN'         # 右括号节点
NODE_COMMA = 'COMMA'           # 逗号分隔符节点


# 关键字节点，用于语法树验证
NODE_CHILDREN_MIN = {
    NODE_QUERY: 1,       # Query 至少需要一个子节点（语句节点）
    NODE_SFW: 4,         # SFW 最少4子节点（无WHERE），最多6子节点（有WHERE）
    NODE_SELECT: 0,      # 关键字节点，无子节点
    NODE_FROM: 0,        # 关键字节点，无子节点
    NODE_WHERE: 0,       # 关键字节点，无子节点
    NODE_COND: 2,        # Cond 至少2子节点（简单条件3子节点，AND条件3子节点）
    NODE_CREATE: 5,      # CreateStmt: TABLE + TCNAME + LPAREN + FieldDefList + RPAREN
    NODE_INSERT: 6,      # InsertStmt: INTO + TCNAME + VALUES + LPAREN + ValueList + RPAREN
    NODE_DELETE: 2,      # DeleteStmt: FROM + TCNAME
    NODE_UPDATE: 8,      # UpdateStmt: TCNAME + SET + TCNAME + = + CONSTANT + WHERE + Cond
    NODE_DROP: 2,        # DropStmt: TABLE + TCNAME
}
# 关键字节点，用于语法树验证
