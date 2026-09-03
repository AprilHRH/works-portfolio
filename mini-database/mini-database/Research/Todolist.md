# 数据库系统实现 — 项目待完善清单

---

## 一、项目概览

| 文件 | 作用 | 状态 |
|------|------|------|
| common_db.py | 全局常量、Node 类、树遍历函数 | ✅ 无需完善 |
| head_db.py | 主存模式结构 Header 类 | ❌ 有 Bug |
| schema_db.py | 模式文件管理（all.sch 读写、CRUD） | ⚠️ 部分修复（持久化已修复 ✅） |
| storage_db.py | 数据文件存储（.dat 二进制格式） | ❌ 有 Bug / ⚠️ 有缺失 |
| mega_storage.py | 文本存储演示（.txt 格式） | ✅ 无需完善 |
| lex_db.py | 词法分析（SQL → Token） | ⚠️ 有缺失 |
| parser_db.py | 语法分析（Token → AST） | ❌ 有 Bug / ⚠️ 有缺失 |
| query_plan_db.py | 查询计划（AST → 逻辑计划 → 执行） | ❌ 有 Bug |
| index_db.py | B 树索引 | ❌ 有 Bug / ⚠️ 有缺失 |
| test_db.py | 测试模块 | ⚠️ 有缺失 |
| main_db.py | 主控入口（7 个菜单分支） | ⚠️ 有缺失 |
| node_db.py | 语法树节点定义（实验 2 要求） | ❌ 缺失文件 |

---

## 二、完善项明细（按文件分组）

### 文件：common_db.py

**状态：✅ 无需完善**

理由：该文件定义的全局变量（`global_lexer`、`global_parser`、`global_syn_tree`、`global_logical_tree`）、`Node` 类（第 19-26 行）和 `show()` 树遍历函数（第 33-44 行）均功能完整。`show()` 函数能正确处理 Node 对象和叶子层字符串，无待完善标记，无逻辑错误。

---

### 文件：head_db.py

#### 完善项 1：`showTables()` 对 dict 类型按数字索引访问
- 位置：第 51 行
- 标记：无（隐藏 Bug）
- 当前状态：`self.tableFields` 是 dict（键为表名），但 `showTables()` 使用 `self.tableFields[i]` 按数字索引访问
- 应实现功能：应通过表名字符串键访问，如 `self.tableFields[self.tableNames[i][0].strip()]`
- 涉及实验：实验 1

---

### 文件：schema_db.py

#### 完善项 1：`viewTableStructure()` 方法未实现
- 位置：第 95-105 行
- 标记：第 105 行 `# to be inserted here`
- 当前状态：方法体只有一条 print 语句和一段被注释掉的代码。注释掉的代码本身也有 Bug（`self.headObj.tableFields[i]` 对 dict 按索引访问、Python 2 语法 `print '|'.join(...)`）
- 应实现功能：根据输入的表名 `table_name`，在 `self.headObj.tableNames` 中查找匹配项，从 `self.headObj.tableFields` 中获取字段列表，格式化输出字段名、类型和长度
- 涉及实验：实验 1

#### 完善项 2：`WriteBuff()` 对 dict 按数字索引访问
- 位置：第 339 行
- 标记：无（隐藏 Bug）
- 当前状态：`self.headObj.tableFields[idx][idj]` — `tableFields` 是 dict，键为 `tableName.strip()`（bytes），不能用数字索引 `idx` 访问
- 应实现功能：改为 `self.headObj.tableFields[self.headObj.tableNames[idx][0].strip()][idj]`
- 涉及实验：实验 1

#### 完善项 3：`fillTableName()` 编码混用与缺少返回值
- 位置：第 63-66 行
- 标记：无（隐藏 Bug）
- 当前状态：
  - 第 65 行：`(' ' * ...).encode('utf-8') + tableName.strip()` — 若 `tableName` 为 str，则 bytes + str 会抛出 TypeError
  - 当 `len(tableName.strip()) >= MAX_TABLE_NAME_LEN` 时函数无返回值（隐式返回 None）
- 应实现功能：统一编码处理，补齐 else 分支的 return，返回填充后的 bytes 类型表名
- 涉及实验：实验 1

#### 完善项 4：`appendTable()` 中 `filledFieldName` 可能未绑定
- 位置：第 258-265 行
- 标记：无（隐藏 Bug）
- 当前状态：若 `len(fieldName.strip()) >= 10`，`filledFieldName` 不会被赋值，但第 264 行和 265 行仍引用它，导致 `NameError`
- 应实现功能：添加 else 分支处理 `len >= 10` 的情况，确保 `filledFieldName` 始终有定义
- 涉及实验：实验 1

#### 完善项 5：`appendTable()` 中字段名填充使用了错误的常量
- 位置：第 262 行
- 标记：无（隐藏 Bug）
- 当前状态：填充字段名时使用 `MAX_FIELD_LEN`（=18，对应 10s+4+4）而非 `MAX_FIELD_NAME_LEN`（=10），导致 `filledFieldName` 长度为 18 而非预期的 10，与 `struct.pack_into('!10sii', ...)` 的格式不匹配
- 应实现功能：将 `MAX_FIELD_LEN` 改为 `MAX_FIELD_NAME_LEN`
- 涉及实验：实验 1
- 状态：✅ 已修复（2026-06-13）

#### 完善项 6：数据持久化失效 — 元数据头不更新 + 无恢复逻辑
- 位置：第 131-145 行（`_update_metahead` 新增）、第 150-159 行（`__init__` 修改）
- 标记：`<!-- : 持久化修复 -->`
- 当前状态：`__del__` 是唯一更新 `isStored` 的地方，Python `__del__` 不保证被调用（异常退出/Ctrl+C/崩溃）；`__init__` 中对 `isStored=False` 直接创建空 Header，忽略已存在的有效表条目；`open('rb+')` 要求文件已存在，首次运行会崩溃
- 已实现功能：
  1. 新增 `_update_metahead()` 方法，在 `appendTable()`、`delete_table_schema()`、`deleteAll()` 每次 Schema 修改后立即将元数据头写入磁盘
  2. `__init__` 新增恢复逻辑：当 `isStored=False` 时扫描 TableNameHead 区域（偏移 12-1811），检测有效条目（`tnum>0 && tnum<=5 && tpos>=1812`），若发现则恢复并立即调用 `_update_metahead()` 修正
  3. `__init__` 新增文件创建：若 `all.sch` 不存在则先用 `wb+` 创建再用 `rb+` 打开
- 涉及实验：实验 1
- 状态：✅ 已修复（2026-06-14）

---

### 文件：storage_db.py

#### 完善项 1：缺少 `getfilenamelist()` 方法
- 位置：全局（被 query_plan_db.py 第 214、222、228 行调用）
- 标记：无（方法被外部调用但未定义）
- 当前状态：`Storage` 类有 `getFieldList()` 方法（第 340-341 行）返回 `self.field_name_list`，但 `query_plan_db.py` 调用的是 `getfilenamelist()`
- 应实现功能：添加 `getfilenamelist()` 方法，返回与 `getFieldList()` 相同的数据结构 `[(field_name, field_type, field_length), ...]`，或统一命名为 `getfilenamelist()`
- 涉及实验：实验 1、实验 2

#### 完善项 2：缺少 DELETE 和 UPDATE 记录的方法
- 位置：全局
- 标记：无（main_db.py choice 6/7 需要调用但方法不存在）
- 当前状态：`Storage` 类有 `insert_record()` 和 `delete_table_data()`（删除整个表文件），但没有 `delete_record()` 和 `update_record()` 方法
- 应实现功能：
  - `delete_record(condition_field, condition_value)`：按条件删除记录
  - `update_record(condition_field, condition_value, new_field, new_value)`：按条件更新记录
- 涉及实验：实验 1

#### 完善项 3：编码混用风险
- 位置：第 83、85、87、90 行
- 标记：无（隐藏 Bug）
- 当前状态：`tablename + '.dat'.encode('utf-8')` — 若 `tablename` 为 str，str + bytes 抛出 TypeError。虽然 main_db.py 中已预先 `.encode('utf-8')`，但模块本身应健壮处理
- 应实现功能：在方法开头统一将 `tablename` 转为 bytes 或 str
- 涉及实验：实验 1

---

### 文件：mega_storage.py

**状态：✅ 无需完善**

理由：该文件是第 1 章的文本存储演示模块，使用 ASCII 文本格式（`.txt`），功能完整：`insert_record()`、`view_all()`、`del_one_record()`、`update_record()`、`delete_table_data()` 均已实现。不参与主程序流程（main_db.py 只引用 storage_db.py 的二进制存储），无需修改。

---

### 文件：lex_db.py

#### 完善项 1：缺少选做 SQL 关键字 Token
- 位置：第 13 行
- 标记：无（功能缺失）
- 当前状态：仅定义了 `SELECT, FROM, WHERE, AND, TCNAME, EQX, COMMA, CONSTANT, SPACE` 共 9 个 Token，缺少 `CREATE, INSERT, INTO, VALUES, UPDATE, SET, DELETE, DROP, TABLE` 等关键字
- 应实现功能：为实验 2 选做部分（CREATE/INSERT/UPDATE/DELETE/DROP）添加对应的 Token 定义和词法规则
- 涉及实验：实验 2（选做）

#### 完善项 2：`t_error()` 函数冗余
- 位置：第 55-64 行
- 标记：无（代码质量问题）
- 当前状态：使用嵌套 try/except/else 打印三次相同的 `'wrong'`，逻辑混乱。且 `lex.LexError` 引用方式可能有误（应为实例属性检查）
- 应实现功能：简化为直接打印错误信息并跳过非法字符 `t.lexer.skip(1)`
- 涉及实验：实验 2

---

### 文件：parser_db.py

#### 完善项 1：`check_syn_tree()` 函数体为空
- 位置：第 41-43 行
- 标记：无（功能缺失）
- 当前状态：函数体仅 `pass`，不对语法树做任何合法性校验
- 应实现功能：遍历语法树检查节点结构是否完整（如 Query 必须有 SFW 子节点，SFW 必须有 6 个子节点等）
- 涉及实验：实验 2

#### 完善项 2：缺少 AND 条件支持
- 位置：第 29 行注释 / 全局
- 标记：无（功能缺失）
- 当前状态：`Cond` 语法规则仅支持 `TCNAME EQX CONSTANT` 单一条件。不支持 `Cond AND Cond` 复合条件
- 应实现功能：添加递归条件规则，如：
  ```
  Cond : TCNAME EQX CONSTANT
  Cond : Cond AND Cond
  ```
  使解析器能处理 `WHERE f1='xx' AND f2=5` 这样的 SQL
- 涉及实验：实验 2

#### 完善项 3：`p_error()` 可能引用未定义属性
- 位置：第 174-175 行
- 标记：无（潜在 Bug）
- 当前状态：`print('wrong at %s' % t.value)` — 在某些解析错误场景下，`t` 可能为 None 或无 `.value` 属性，导致 AttributeError
- 应实现功能：添加 `if t is not None and hasattr(t, 'value')` 判断
- 涉及实验：实验 2

#### 完善项 4：缺少选做 SQL 语法规则
- 位置：全局
- 标记：无（功能缺失）
- 当前状态：仅定义了 `Query : SFW` 规则，无 CREATE / INSERT / UPDATE / DELETE / DROP 语法规则
- 应实现功能：参考实验 2 选做 SQL 示例，添加对应的语法产生式及其 AST 构建函数
- 涉及实验：实验 2（选做）

---

### 文件：query_plan_db.py

#### 完善项 1：调用不存在的 `getfilenamelist()` 方法
- 位置：第 214、222、228 行
- 标记：无（运行时错误）
- 当前状态：代码调用 `a_1.getfilenamelist()`，但 `storage_db.Storage` 类中该方法不存在（只有 `getFieldList()`）
- 应实现功能：在 `storage_db.py` 的 `Storage` 类中添加 `getfilenamelist()` 方法，或将其改为已存在的 `getFieldList()`
- 涉及实验：实验 1、实验 2

#### 完善项 2：`excute_tree()` 内部函数命名拼写错误
- 位置：第 166 行
- 标记：无（代码质量问题）
- 当前状态：`def excute_tree():` — "excute" 应为 "execute"
- 应实现功能：修正为 `def execute_tree():`
- 涉及实验：实验 2

#### 完善项 3：内部 `show()` 函数与外层 `show()` 命名冲突
- 位置：第 171 行 vs common_db.py 第 33 行
- 标记：无（代码质量问题）
- 当前状态：`excute_tree()` 内重新定义了 `show(node_obj, idx, dict_)`，与外层 `common_db.show()` 同名，增加维护难度
- 应实现功能：重命名为 `collect_nodes()` 或 `traverse_tree()` 等语义更明确的名称
- 涉及实验：实验 2

---

### 文件：index_db.py

#### 完善项 1：`__init__()` 中查看所有索引条目未实现
- 位置：第 90-91 行
- 标记：第 91 行 `# to be inserted here`
- 当前状态：注释后无代码，读取索引文件后未在控制台输出已有索引条目
- 应实现功能：读取 block 0 获取根节点指针，从根节点遍历 B 树，输出所有 key 和对应指针
- 涉及实验：实验 1

#### 完善项 2：`create_index()` 方法体为空
- 位置：第 116-119 行
- 标记：第 119 行 `# to be inserted here`
- 当前状态：仅打印一行提示，方法体为空
- 应实现功能：接收索引字段名 `index_field`，遍历数据文件所有记录，提取该字段值，为每条记录调用 `insert_index_entry()` 插入 B 树
- 涉及实验：实验 1

#### 完善项 3：`get_next_block_ptr()` 始终返回 -1
- 位置：第 130-132 行
- 标记：无（功能缺失）
- 当前状态：方法体仅 `ret_value=-1; return ret_value`，不执行任何查找逻辑
- 应实现功能：在 `index_key_list` 中二分查找 `current_value` 应落入的区间，返回对应的子节点 block_id
- 涉及实验：实验 1

#### 完善项 4：内部节点遍历使用了空的 key_list/ptr_list
- 位置：第 242-251 行
- 标记：无（逻辑 Bug）
- 当前状态：代码将 key/ptr 读入 `internal_key_list` 和 `internal_ptr_list`，但调用 `get_next_block_ptr(field_value, key_list, ptr_list)` 时传入的是空列表 `key_list` 和 `ptr_list`（第 240-241 行初始化为 `[]`，第 247 行只向 `ptr_list` 追加了 `last_ptr`）
- 应实现功能：将参数改为正确的列表名，如 `self.get_next_block_ptr(field_value, internal_key_list, ptr_list)`
- 涉及实验：实验 1

#### 完善项 5：叶子节点分裂未实现
- 位置：第 295-296 行
- 标记：无（功能缺失）
- 当前状态：仅 `print("the leaf node is full, we should split")`，未实际执行分裂
- 应实现功能：当叶子节点 key 数达到 `MAX_NUM_OF_KEYS` 时，将节点分裂为两个，将中间 key 提升到父节点（若父节点也满则递归分裂）
- 涉及实验：实验 1

#### 完善项 6：模块级测试代码在 import 时执行
- 位置：第 319-320 行
- 标记：无（代码质量问题 / 潜在 Bug）
- 当前状态：`index_obj=Index('all'); index_obj.insert_index_entry('a',4,1)` 在模块顶层执行，任何 `import index_db` 都会触发文件创建
- 应实现功能：将测试代码放入 `if __name__ == '__main__':` 保护块中
- 涉及实验：实验 1

#### 完善项 7：`insert_index_entry()` 条件判断 `field_value.strip()` 可能失败
- 位置：第 181 行
- 标记：无（潜在 Bug）
- 当前状态：`if len(field_value.strip())>0 and ...` — 若 `field_value` 为 int 类型（字段类型为 integer 时），`.strip()` 会抛出 AttributeError
- 应实现功能：先将 `field_value` 统一转为字符串后再调用 `.strip()`
- 涉及实验：实验 1

---

### 文件：test_db.py

#### 完善项 1：缺乏系统化测试
- 位置：全局
- 标记：无（功能缺失）
- 当前状态：仅包含一个测试 dict 操作的 `test_dict()` 函数，与数据库系统核心功能无关
- 应实现功能：编写覆盖所有模块的单元测试，至少包括：Storage CRUD、Schema 管理、Lex 解析、Parser 构建 AST、Query Plan 执行、B 树索引操作
- 涉及实验：实验 1、实验 2、实验 3

---

### 文件：main_db.py

#### 完善项 1：Choice 6（按关键字删除一行）未实现
- 位置：第 161-167 行
- 标记：第 165 行 `# to the students: to be inserted here, delete the line from data files`
- 当前状态：获取了 `table_name` 和 `field_name:keyword`，但未执行任何删除操作
- 应实现功能：
  1. 解析 `field_name:keyword` 格式
  2. 创建 `storage_db.Storage(table_name)` 对象
  3. 调用删除方法（需先在 storage_db.py 中实现）删除匹配记录
  4. 输出操作结果
- 涉及实验：实验 1

#### 完善项 2：Choice 7（按关键字更新一行）未实现
- 位置：第 169-176 行
- 标记：第 174 行 `# to the students: to be inserted here, update the line according to the user input`
- 当前状态：获取了 `table_name`、`field_name`、`field_name_value`，但未执行任何更新操作
- 应实现功能：
  1. 创建 `storage_db.Storage(table_name)` 对象
  2. 调用更新方法（需先在 storage_db.py 中实现）将旧值替换为新值
  3. 输出操作结果
- 涉及实验：实验 1

#### 完善项 3：Choice 1 插入逻辑不完善
- 位置：第 61 行
- 标记：第 61 行 `# to the students: The following needs to be further implemented (many lines can be added)`
- 当前状态：每次只插入一条记录后即返回菜单。且首次创建表时（`tableName not in schema` 分支）跳过了插入数据的步骤
- 应实现功能：支持循环插入多条记录（如输入空行退出），且修复首次建表后无数据插入的问题
- 涉及实验：实验 1

#### 完善项 5：`reload(query_plan_db)` 被注释
- 位置：第 152 行（被注释）
- 标记：readme.txt 第 39 行明确说明"选择5reload注释掉了，未实现"
- 当前状态：Python 3 中 `reload()` 已移至 `importlib.reload()`
- 应实现功能：如需支持热更新查询计划模块，使用 `from importlib import reload; reload(query_plan_db)`
- 涉及实验：实验 2

---

### 文件：node_db.py（缺失）

#### 完善项 1：整个模块缺失
- 位置：N/A（文件不存在）
- 标记：实验 2 文档明确要求完善 `node_db.py`（定义语法树节点）
- 当前状态：语法树节点定义直接写在 `common_db.py` 的 `Node` 类中，缺少独立的节点类型定义模块
- 应实现功能：创建 `node_db.py`，定义各类 AST 节点的数据类（如 `SelectNode`、`FromNode`、`WhereNode`、`ConditionNode` 等），使语法树构建更加结构化
- 涉及实验：实验 2

---

## 三、实验 3（事务持久性）相关

> 实验 3 的所有内容均未实现，属于全新开发。

| 完善项 | 描述 | 涉及文件 |
|--------|------|----------|
| 日志文件机制 | 创建日志文件记录前像（Before Image）和后像（After Image） | 新模块（如 log_db.py） |
| 活动事务表 | 记录当前未提交事务的状态 | 新模块或扩展现有模块 |
| 提交事务表 | 记录已提交事务 | 新模块或扩展现有模块 |
| Commit Rule | 后像在事务提交前写入非易失存储 | storage_db.py |
| WAL 规则 | 后像写入数据库前，前像先写入日志 | storage_db.py |
| 崩溃恢复 | 重启时读取日志，重做已提交事务 | 新模块或 main_db.py |
| INSERT 事务化 | INSERT 操作加上日志记录 | storage_db.py |
| UPDATE 事务化（可选） | UPDATE 操作加上日志记录 | storage_db.py |

---

## 四、汇总统计

| 类别 | 数量 |
|------|------|
| 待完善标记（#to the students / #to be inserted here） | 9 处 |
| 逻辑 Bug（dict 按索引访问、变量未绑定、方法不存在等） | 10 处 |
| 功能缺失（方法空壳、分支未实现） | 8 处 |
| 缺失模块/文件 | 1 个（node_db.py） |
| 实验 3 全新开发项 | 8 项 |
| **合计待处理项** | **36 项** |
