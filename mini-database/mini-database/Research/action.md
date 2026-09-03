#   

## 一、新增文件（5个）

| 文件名 | 功能描述 |
|--------|----------|
| `node_db.py` | AST节点类型常量定义，包含所有SQL语句节点类型及最小子节点数验证映射 |
| `transaction_db.py` | WAL（预写日志）事务管理器，实现事务的BEGIN/INSERT/UPDATE/COMMIT/ABORT及崩溃恢复（REDO/UNDO） |
| `run_test.py` | 实验一自动化测试：表创建、数据插入、查询、删除、更新功能验证 |
| `run_test2.py` | 实验二SQL解析测试：DDL/DML语句及SELECT查询功能验证 |
| `run_test3.py` | 实验三崩溃恢复测试：WAL事务持久化的三种崩溃恢复场景验证 |

---

## 二、原有文件修改对照表

### 1. common_db.py

---

### 2. head_db.py
**修改内容**：
| 行号 | 修改类型 | 描述 |
|------|----------|------|
| 51 | Bug修复 | `showTables()`中访问tableFields字典，从`self.tableFields[i]`（错误：整数索引访问字典）改为`self.tableFields[self.tableNames[i][0].strip()]`（正确：按表名key访问） |

---

### 3. index_db.py
**修改内容**：无实际代码变更

---

### 4. lex_db.py

**修改内容**：
| 行号 | 修改类型 | 描述 |
|------|----------|------|
| 13 | 扩展 | tokens元组新增14个token：STAR, SEMICOLON, CREATE, TABLE, INSERT, INTO, VALUES, UPDATE, SET, DELETE, DROP, LPAREN, RPAREN, CHAR, INTEGER |
| 37-99 | 新增 | 新增14个token匹配函数：t_STAR(`\*`), t_SEMICOLON(`;`), t_CREATE, t_TABLE, t_INSERT, t_INTO, t_VALUES, t_UPDATE, t_SET, t_DELETE, t_DROP, t_CHAR, t_INTEGER, t_LPAREN(`\(`), t_RPAREN(`\)`) |
| 112 | 修改 | t_CONSTANT正则从`\d+\|\'\w+\'`改为`\d+\|\'[^\']*\'`，支持含非单词字符的字符串 |
| 126 | 修改 | t_error简化：移除try/except/else结构，改为直接`print('wrong character: %s' % t.value[0]); t.lexer.skip(1)` |

---

### 5. parser_db.py
**修改内容**：
| 行号 | 修改类型 | 描述 |
|------|----------|------|
| 41-69 | 重写 | `check_syn_tree()`从空壳`pass`改为完整递归验证：Query≥1子节点，SFW为4或6子节点，递归检查所有子节点 |
| 83-93 | 扩展 | `p_expr_query`从`'Query : SFW'`扩展为`'Query : SFW \| CreateStmt \| InsertStmt \| DeleteStmt \| UpdateStmt \| DropStmt'` |
| 113-122 | 新增 | `p_expr_swf_no_where`规则：支持无WHERE子句的SELECT |
| 158-165 | 新增 | `p_expr_sellist_star`规则：支持`SELECT *` |
| 214-221 | 新增 | `p_expr_condition_and`规则：支持`Cond AND Cond`复合条件 |
| 225-398 | 新增 | 11个DDL/DML语法规则函数：CreateStmt, InsertStmt, DeleteStmt, UpdateStmt, DropStmt, FieldDefList(2条), FieldDef(2条), ValueList(2条) |
| 407-413 | 修改 | `p_error`增加None检查和hasattr防护 |

---

### 6. query_plan_db.py
**修改内容**：
| 行号 | 修改类型 | 描述 |
|------|----------|------|
| 21 | 删除 | 移除`from common_db import global_syn_tree as syn_tree`，改为使用`common_db.global_syn_tree`直接引用 |
| 58-64 | 修改 | `extract_sfw_data()`和`construct_logical_tree()`中的`syn_tree`引用改为`common_db.global_syn_tree` |
| 184-224 | 重写 | `GetFilterParam()`增加bytes→str规范化处理：参数含`.`时支持`table.field`格式，单表时直接匹配字段名，字段名比较使用`str.strip()` |
| 261-307 | 新增 | Filter部分新增AND复合条件支持：按AND拆分FilterChoice为独立条件元组，逐个循环应用过滤 |
| 311-348 | 新增 | Proj部分新增`SELECT *`支持：检测`*`后展开为所有表的所有字段索引 |
| 214/228/251 | 修改 | `getfilenamelist()`调用统一改为`getFieldList()` |
| 299-304 | 新增 | 过滤值比较时增加bytes/str规范化处理 |

---

### 7. schema_db.py
**修改内容**（已有详细的标记）：
| 行号 | 修改类型 | 描述 |
|------|----------|------|
| 14 | 新增 | `import os` |
| 65-79 | 重写 | `fillTableName()`：增加bytes/str兼容、左空格补齐到10字节、超长截断 |
| 108-126 | 重写 | `viewTableStructure()`：从空壳改为通过dict查找并打印字段信息 |
| 128-136 | 新增 | `_update_metahead()`：立即将isStored/lenOfTableNum/offsetOfBody写入all.sch |
| 138-192 | 新增 | `_discover_dat_files()`：自动发现孤儿.dat文件并注册到schema |
| 197-346 | 重写 | `__init__`：增加文件不存在时的创建、崩溃恢复扫描、自动发现.dat、文件名规范化 |
| 386-444 | 修改 | `appendTable()`：捕获strip结果、field packing增加bytes/str处理、立即_update_metahead |
| 366-378 | 修改 | `deleteAll()`：增加立即_update_metahead |
| 470-502 | 修改 | `WriteBuff()`：增加bytes/str兼容处理 |
| 511-549 | 修改 | `delete_table_schema()`：Python3兼容(zip→list(zip), map→list(map))、增加_update_metahead |

---

### 8. storage_db.py
**修改内容**：
| 行号 | 修改类型 | 描述 |
|------|----------|------|
| 76 | 修改 | `__init__()`签名增加`use_transaction=False, readonly=False`参数 |
| 77-81 | 新增 | tablename的str→bytes编码和strip处理 |
| 86-91 | 新增 | 事务支持：条件导入transaction_db并初始化TransactionManager |
| 94-100 | 新增 | readonly模式（文件不存在）：设置空字段列表并返回 |
| 108-115 | 新增 | readonly模式：以`'rb'`只读方式打开文件 |
| 123 | 修改 | 移除`self.dir_buf.strip()`（bytes的strip存在问题） |
| 128-133 | 新增 | readonly模式（空文件）：设置空字段并返回 |
| 230-232 | 新增 | `self.has_data`标志，记录是否成功从磁盘加载数据 |
| 342-348 | 新增 | `show_table_data()`增加空数据保护，打印"表中暂无数据" |
| 386-394 | 新增 | `getfilenamelist()`方法，返回字段列表 |
| 397-492 | 新增 | `delete_record(condition_field, condition_value)`完整实现 |
| 495-582 | 新增 | `update_record(condition_field, condition_value, new_field, new_value)`完整实现 |
| 644-668 | 新增 | `insert_record_with_txn()`：带WAL事务持久化的插入 |
| 670-732 | 新增 | `update_record_with_txn()`：带WAL事务持久化的更新 |
| 748-764 | 新增 | `_serialize_txn_record()`：记录序列化为WAL格式字符串 |

---

### 9. main_db.py
**修改内容**：
| 行号 | 修改类型 | 描述 |
|------|----------|------|
| 25-30 | 扩展 | PROMPT_STR从7个选项扩展到15个（增加SQL DDL/DML 8-12和事务操作13-15） |
| 34-115 | 新增 | `process_ddl_dml(schemaObj)`函数：处理CreateStmt/InsertStmt/DeleteStmt/UpdateStmt/DropStmt |
| 173-217 | 修改 | Choice 1：新建表后询问是否插入数据（y/n循环），已有表增加while循环支持多条插入 |
| 261-276 | 修改 | Choice 3：增加.dat文件存在性检查，使用readonly模式打开 |
| 306-313 | 修改 | Choice 5：根据语句类型分发到SFW逻辑树执行或process_ddl_dml |
| 324-336 | 重写 | Choice 6：从空壳改为解析fieldname:keyword格式并调用delete_record |
| 346-357 | 重写 | Choice 7：从空壳改为增加new_field_name/new_field_value输入并调用update_record |
| 362-480 | 新增 | Choices 8-15：CREATE TABLE / INSERT / DELETE / UPDATE / DROP SQL操作及事务插入、崩溃恢复、WAL日志查看 |

---

### 10. mega_storage.py
---

### 11. test_db.py
---

## 三、修改类型统计

| 修改类型 | 数量 | 涉及文件 |
|----------|------|----------|
| Bug修复 | 2 | head_db.py(showTables字典访问), storage_db.py(bytes的strip处理) |
| 函数重写 | 6 | parser_db.py(check_syn_tree), schema_db.py(fillTableName, viewTableStructure, __init__, delete_table_schema), query_plan_db.py(GetFilterParam) |
| 新增功能/方法 | 25+ | lex_db(14 token规则), parser_db(11+语法规则), storage_db(delete_record, update_record, insert/update_with_txn等), schema_db(_update_metahead, _discover_dat_files), main_db(process_ddl_dml, choices 8-15), query_plan_db(AND/STAR支持) |
| 接口扩展 | 4 | storage_db.__init__增加参数, main_db PROMPT_STR扩展, lex_db tokens扩展, parser_db p_expr_query扩展 |
| Python3兼容 | 2 | schema_db(zip→list(zip)), query_plan_db(map→list(map)) |
| Bytes/Str兼容 | 多处 | schema_db, storage_db, query_plan_db, main_db, lex_db |

---

## 四、新增文件代码量统计

| 文件名 | 行数 | 主要新增内容 |
|--------|------|-------------|
| node_db.py | ~57 | AST节点类型常量 + NODE_CHILDREN_MIN验证映射 |
| transaction_db.py | ~460 | TransactionManager完整实现(WAL日志记录、事务管理、崩溃恢复REDO/UNDO) |
| run_test.py | ~280 | 实验一：9个自动化测试用例 |
| run_test2.py | ~200 | 实验二：SQL解析与执行测试 |
| run_test3.py | ~180 | 实验三：WAL崩溃恢复三种场景测试 |

---

