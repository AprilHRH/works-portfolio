import struct
import sys
import ctypes
import os

import head_db  # the main memory structure of table schema
import schema_db  # the module to process table schema
import storage_db  # the module to process the storage of instance

import query_plan_db  # for SQL clause of which data is stored in binary format
import lex_db  # for lex, where data is stored in binary format
import parser_db  # for yacc, where ddata is tored in binary format
import common_db  # the global variables, functions, constants in the program
import query_plan_db  # construct the query plan and execute it

# 扩展提示字符串，增加DDL/DML和事务选项
PROMPT_STR = 'Input your choice  \n1:add a new table structure and data \n2:delete a table structure and data\
\n3:view a table structure and data \n4:delete all tables and data \n5:select from where clause\
\n6:delete a row according to field keyword \n7:update a row according to field keyword \
\n8:create table (SQL) \n9:insert into (SQL) \n10:delete from (SQL) \n11:update set (SQL) \
\n12:drop table (SQL) \n13:insert with transaction durability \n14:crash recovery (replay WAL log) \
\n15:view WAL log \n. to quit):\n'


# DDL/DML语句处理函数，根据AST节点类型执行对应操作
def process_ddl_dml(schemaObj):
    """处理DDL/DML语句，根据语法树节点类型调用相应操作"""
    stmt = common_db.global_syn_tree.children[0]  # 取Query的第一个子节点
    stmt_type = stmt.value  # 语句类型：SFW, CreateStmt, InsertStmt, DeleteStmt, UpdateStmt, DropStmt

    if stmt_type == 'CreateStmt':  # CREATE TABLE SQL
        # CreateStmt子节点: [CREATE, TABLE, TCNAME, LPAREN, FieldDefList, RPAREN], TCNAME在索引2, FieldDefList在索引4
        table_name = stmt.children[2].children[0]  # TCNAME节点
        if isinstance(table_name, str):
            table_name = table_name.encode('utf-8')
        field_def_list = stmt.children[4]  # FieldDefList节点
        field_defs = []
        _collect_field_defs(field_def_list, field_defs)  # 递归收集字段定义
        # 直接创建.dat文件写入block 0（非交互式）
        dat_path = table_name.strip() + b'.dat'
        fh = open(dat_path, 'wb+')
        buf = ctypes.create_string_buffer(common_db.BLOCK_SIZE)
        struct.pack_into('!iii', buf, 0, 0, 0, len(field_defs))
        pos = struct.calcsize('!iii')
        for fn, ft, fl in field_defs:
            if isinstance(fn, str): fn = fn.encode('utf-8')
            if len(fn.strip()) < 10:
                fn = (' ' * (10 - len(fn.strip()))).encode('utf-8') + fn.strip()
            struct.pack_into('!10sii', buf, pos, fn, int(ft), int(fl))
            pos += struct.calcsize('!10sii')
        fh.seek(0); fh.write(buf); fh.close()
        schemaObj.appendTable(table_name, field_defs)
        print('Table ' + table_name.decode('utf-8').strip() + ' created.')
        return True

    elif stmt_type == 'InsertStmt':  # INSERT INTO SQL
        # InsertStmt子节点: [INSERT, INTO, TCNAME, VALUES, LPAREN, ValueList, RPAREN], TCNAME在索引2, ValueList在索引5
        table_name = stmt.children[2].children[0]
        if isinstance(table_name, str):
            table_name = table_name.encode('utf-8')
        value_list = stmt.children[5]
        values = []
        _collect_values(value_list, values)
        dataObj = storage_db.Storage(table_name)
        ok = dataObj.insert_record(values)
        del dataObj
        return ok

    elif stmt_type == 'DeleteStmt':  # DELETE FROM SQL
        # DeleteStmt子节点: [DELETE, FROM, TCNAME], TCNAME在索引2
        table_name = stmt.children[2].children[0]
        if isinstance(table_name, str):
            table_name = table_name.encode('utf-8')
        dataObj = storage_db.Storage(table_name)
        # 清空记录列表并重写空文件（保留表结构）
        dataObj.record_list = []
        dataObj.record_Position = []
        dataObj.data_block_num = 0
        dataObj.f_handle.seek(0); dataObj.f_handle.truncate(0)
        buf = ctypes.create_string_buffer(common_db.BLOCK_SIZE)
        struct.pack_into('!iii', buf, 0, 0, 0, int(dataObj.num_of_fields))
        pos = struct.calcsize('!iii')
        for fn, ft, fl in dataObj.field_name_list:
            if isinstance(fn, str): fn = fn.encode('utf-8')
            struct.pack_into('!10sii', buf, pos, fn, int(ft), int(fl))
            pos += struct.calcsize('!10sii')
        dataObj.f_handle.write(buf); dataObj.f_handle.flush()
        del dataObj
        return True

    elif stmt_type == 'UpdateStmt':  # UPDATE SET SQL
        # UpdateStmt子节点: [UPDATE, TCNAME表名, SET, TCNAME字段, =, CONSTANT值, WHERE, Cond]
        table_name = stmt.children[1].children[0]  # TCNAME表名在索引1
        if isinstance(table_name, str):
            table_name = table_name.encode('utf-8')
        set_field = stmt.children[3].children[0]  # TCNAME字段在索引3
        if isinstance(set_field, bytes):
            set_field = set_field.decode('utf-8')
        set_value = str(stmt.children[5].children[0]).strip("'")  # CONSTANT在索引5
        cond_node = stmt.children[7]  # Cond在索引7
        cond_field = cond_node.children[0].children[0]  # WHERE条件字段(TCNAME)
        if isinstance(cond_field, bytes):
            cond_field = cond_field.decode('utf-8')
        cond_value = str(cond_node.children[2].children[0]).strip("'")  # WHERE条件值(CONSTANT)
        dataObj = storage_db.Storage(table_name)
        ok = dataObj.update_record(cond_field, cond_value, set_field, set_value)
        del dataObj
        return ok

    elif stmt_type == 'DropStmt':  # DROP TABLE SQL
        # DropStmt子节点: [DROP, TABLE, TCNAME], TCNAME在索引2
        table_name = stmt.children[2].children[0]
        if isinstance(table_name, str):
            table_name = table_name.encode('utf-8')
        schemaObj.delete_table_schema(table_name)
        # 直接删除.dat文件
        dat_path = table_name.strip() + b'.dat'
        if os.path.exists(dat_path):
            os.remove(dat_path)
        print('Table ' + table_name.decode('utf-8').strip() + ' dropped.')
        return True


# 递归收集FieldDef列表，提取字段名、类型和长度
def _collect_field_defs(node, result):
    """递归遍历FieldDefList节点，提取字段定义(field_name, field_type, field_length)"""
    if node.value == 'FieldDefList':
        for child in node.children:
            _collect_field_defs(child, result)
    elif node.value == 'FieldDef':
        field_name = node.children[0].children[0]  # TCNAME
        if len(node.children) == 5:  # CHAR(n)类型
            field_len = node.children[3].children[0]  # CONSTANT 长度
            result.append((field_name, 0, int(field_len)))  # type=0 -> str
        elif len(node.children) == 2:  # INTEGER类型
            result.append((field_name, 2, 4))  # type=2 -> int, 默认长度4


# 递归收集ValueList中的常量值
def _collect_values(node, result):
    """递归遍历ValueList节点，提取常量值列表"""
    if node.value == 'ValueList':
        for child in node.children:
            _collect_values(child, result)
    elif node.value == 'CONSTANT':
        v = str(node.children[0]).strip("'")
        result.append(v)


# the main loop, which needs further implementation

def main():
    # main loops for the whole program
    print('main function begins to execute')

    # The instance data of table is stored in binary format, which corresponds to chapter 2-8 of textbook

    schemaObj = schema_db.Schema()  # to create a schema object, which contains the schema of all tables
    dataObj = None
    choice = input(PROMPT_STR)

    while True:

        if choice == '1':  # add a new table and lines of data
            tableName = input('please enter your new table name:')
            if isinstance(tableName, str):
                tableName = tableName.encode('utf-8')
            #  tableName not in all.sch
            insertFieldList = []
            if tableName.strip() not in schemaObj.get_table_name_list():
                # Create a new table
                dataObj = storage_db.Storage(tableName)

                insertFieldList = dataObj.getFieldList()

                schemaObj.appendTable(tableName, insertFieldList)  # add the table structure

# 创建表后交互式询问是否插入数据
                choice2 = input('Table created. Insert data now? (y/n):')
                while choice2.lower() == 'y':  # 循环插入记录，输入.停止
                    record = []
                    Field_List = dataObj.getFieldList()
                    for x in Field_List:
                        s = 'Input field name is: ' + str(x[0].strip()) + '  field type is: ' + str(x[1]) + \
                            ' field maximum length is: ' + str(x[2]) + '\n'
                        val = input(s)
                        if val == '.':
                            break
                        record.append(val)
                    if val == '.':
                        break
                    if dataObj.insert_record(record):
                        print('OK!')
                    else:
                        print('Wrong input!')
                    choice2 = input('Continue inserting? (y/n):')
                del dataObj
            else:
                dataObj = storage_db.Storage(tableName)

# 已存在表时循环插入数据
                while True:  # 循环插入记录
                    record = []
                    Field_List = dataObj.getFieldList()
                    for x in Field_List:
                        s = 'Input field name is: ' + str(x[0].strip()) + '  field type is: ' + str(x[1]) + \
                            ' field maximum length is: ' + str(x[2]) + '\n'
                        val = input(s)
                        if val == '.':
                            break
                        record.append(val)
                    if val == '.':
                        break
                    if dataObj.insert_record(record):  # add a row
                        print('OK!')
                    else:
                        print('Wrong input!')
                    cont = input('Continue inserting? (y/n):')
                    if cont.lower() != 'y':
                        break

                del dataObj

            choice = input(PROMPT_STR)





        elif choice == '2':  # delete a table from schema file and data file

            table_name = input('please input the name of the table to be deleted:')
            if isinstance(table_name,str):
                table_name=table_name.encode('utf-8')
            if schemaObj.find_table(table_name.strip()):
                if schemaObj.delete_table_schema(
                        table_name):  # delete the schema from the schema file
                    dataObj = storage_db.Storage(table_name)  # create an object for the data of table
                    dataObj.delete_table_data(table_name.strip())  # delete table content from the table file
                    del dataObj

                else:
                    print('the deletion from schema file fail')


            else:
                print('there is no table '.encode('utf-8') + table_name + ' in the schema file'.encode('utf-8'))


            choice = input(PROMPT_STR)



        elif choice == '3':  # view the table structure and all the data

            print(schemaObj.headObj.tableNames)
            table_name = input('please input the name of the table to be displayed:')
            if isinstance(table_name,str):
                table_name=table_name.encode('utf-8')
            if table_name.strip():
                if schemaObj.find_table(table_name.strip()):
                    schemaObj.viewTableStructure(table_name)  # to be implemented

# 检查.dat数据文件是否存在，不存在则提示无数据
                    if isinstance(table_name, bytes):
                        dat_path = table_name.strip() + '.dat'.encode('utf-8')
                    else:
                        dat_path = table_name.strip() + '.dat'
                    if not os.path.exists(dat_path):
                        print('表中暂无数据（数据文件不存在）')  # 数据文件不存在，只读模式无需创建
                    else:
                        dataObj = storage_db.Storage(table_name, readonly=True)  # 只读模式打开
                        dataObj.show_table_data()  # view all the data of the table
                        del dataObj
                else:
                    print('table name is None')

            choice = input(PROMPT_STR)



        elif choice == '4':  # delete all the table structures and their data
            table_name_list = list(schemaObj.get_table_name_list())
            # to be inserted here -> to delete from data files
            for i in range(len(table_name_list)):
                table_name = table_name_list[i]
                table_name.strip()

                if table_name:
                    stObj = storage_db.Storage(table_name)
                    stObj.delete_table_data(table_name.strip())  # delete table data
                    del stObj

            schemaObj.deleteAll()  # delete schema from schema file

            choice = input(PROMPT_STR)


        elif choice == '5':  # process SELECT FROM WHERE clause
            print('#        Your Query is to SQL QUERY                  #')
            sql_str = input('please enter the select from where clause:')
            lex_db.set_lex_handle()  # to set the global_lexer in common_db.py
            parser_db.set_handle()  # to set the global_parser in common_db.py

            try:
                common_db.global_syn_tree = common_db.global_parser.parse(sql_str.strip(),
                                                                          lexer=common_db.global_lexer)  # construct the global_syn_tree
# 判断语句类型：SFW走逻辑查询计划，否则走DDL/DML处理
                stmt_type = common_db.global_syn_tree.children[0].value  # 检查Query的子节点类型
                if stmt_type == 'SFW':  # SELECT FROM WHERE查询走逻辑树
                    query_plan_db.construct_logical_tree()
                    query_plan_db.execute_logical_tree()
                else:  # DDL/DML语句走process_ddl_dml处理
                    process_ddl_dml(schemaObj)
            except:
                print('WRONG SQL INPUT!')
            print('#----------------------------------------------------#')
            choice = input(PROMPT_STR)


        elif choice == '6':  # delete a line of data from the storage file given the keyword

            table_name = input('please input the name of the table to be deleted from:')
            field_name = input('please input the field name and the corresponding keyword (fieldname:keyword):')
# 解析 fieldname:keyword 格式并调用delete_record删除记录
            if isinstance(table_name, str):
                table_name = table_name.encode('utf-8')
            if ':' in field_name:  # 按冒号分隔字段名和关键字值
                parts = field_name.split(':', 1)
                fname = parts[0].strip()  # 字段名
                keyword = parts[1].strip()  # 关键字值
                dataObj = storage_db.Storage(table_name)
                dataObj.delete_record(fname, keyword)  # 删除匹配记录
                print('Record deleted.')
                del dataObj
            else:
                print('Wrong format! Use fieldname:keyword')

            choice = input(PROMPT_STR)

        elif choice == '7':  # update a line of data given the keyword

            table_name = input('please input the name of the table:')
            field_name = input('please input the field name:')
            field_name_value = input('please input the old value of the field:')
# 提示输入新字段名和新值并调用update_record更新记录
            if isinstance(table_name, str):
                table_name = table_name.encode('utf-8')
            new_field_name = input('please input the new field name to update:')  # 要更新的字段名
            new_field_value = input('please input the new value of the field:')  # 新值
            dataObj = storage_db.Storage(table_name)
            if dataObj.update_record(field_name, field_name_value, new_field_name, new_field_value):  # 更新记录
                print('Record updated.')
            else:
                print('Update failed.')
            del dataObj

            choice = input(PROMPT_STR)


# 新增选项8-15：DDL/DML SQL语句和事务操作
        elif choice == '8':  # CREATE TABLE SQL
            sql_str = input('please enter CREATE TABLE statement:')
            lex_db.set_lex_handle()
            parser_db.set_handle()
            try:
                common_db.global_syn_tree = common_db.global_parser.parse(sql_str.strip(),
                                                                          lexer=common_db.global_lexer)
                if common_db.global_syn_tree.children[0].value == 'CreateStmt':  # 确认是CREATE语句
                    process_ddl_dml(schemaObj)
                else:
                    print('Not a CREATE TABLE statement')
            except:
                print('WRONG SQL INPUT!')
            choice = input(PROMPT_STR)

        elif choice == '9':  # INSERT INTO SQL
            sql_str = input('please enter INSERT INTO statement:')
            lex_db.set_lex_handle()
            parser_db.set_handle()
            try:
                common_db.global_syn_tree = common_db.global_parser.parse(sql_str.strip(),
                                                                          lexer=common_db.global_lexer)
                if common_db.global_syn_tree.children[0].value == 'InsertStmt':  # 确认是INSERT语句
                    process_ddl_dml(schemaObj)
                else:
                    print('Not an INSERT INTO statement')
            except:
                print('WRONG SQL INPUT!')
            choice = input(PROMPT_STR)

        elif choice == '10':  # DELETE FROM SQL
            sql_str = input('please enter DELETE FROM statement:')
            lex_db.set_lex_handle()
            parser_db.set_handle()
            try:
                common_db.global_syn_tree = common_db.global_parser.parse(sql_str.strip(),
                                                                          lexer=common_db.global_lexer)
                if common_db.global_syn_tree.children[0].value == 'DeleteStmt':  # 确认是DELETE语句
                    process_ddl_dml(schemaObj)
                else:
                    print('Not a DELETE FROM statement')
            except:
                print('WRONG SQL INPUT!')
            choice = input(PROMPT_STR)

        elif choice == '11':  # UPDATE SET SQL
            sql_str = input('please enter UPDATE SET statement:')
            lex_db.set_lex_handle()
            parser_db.set_handle()
            try:
                common_db.global_syn_tree = common_db.global_parser.parse(sql_str.strip(),
                                                                          lexer=common_db.global_lexer)
                if common_db.global_syn_tree.children[0].value == 'UpdateStmt':  # 确认是UPDATE语句
                    process_ddl_dml(schemaObj)
                else:
                    print('Not an UPDATE SET statement')
            except:
                print('WRONG SQL INPUT!')
            choice = input(PROMPT_STR)

        elif choice == '12':  # DROP TABLE SQL
            sql_str = input('please enter DROP TABLE statement:')
            lex_db.set_lex_handle()
            parser_db.set_handle()
            try:
                common_db.global_syn_tree = common_db.global_parser.parse(sql_str.strip(),
                                                                          lexer=common_db.global_lexer)
                if common_db.global_syn_tree.children[0].value == 'DropStmt':  # 确认是DROP语句
                    process_ddl_dml(schemaObj)
                else:
                    print('Not a DROP TABLE statement')
            except:
                print('WRONG SQL INPUT!')
            choice = input(PROMPT_STR)

        elif choice == '13':  # insert with transaction durability
            table_name = input('please enter the table name for transactional insert:')
            if isinstance(table_name, str):
                table_name = table_name.encode('utf-8')
            dataObj = storage_db.Storage(table_name, use_transaction=True)  # 启用事务
            record = []
            Field_List = dataObj.getFieldList()
            for x in Field_List:
                s = 'Input field name is: ' + str(x[0].strip()) + '  field type is: ' + str(x[1]) + \
                    ' field maximum length is: ' + str(x[2]) + '\n'
                record.append(input(s))
            if dataObj.insert_record(record):
                print('OK! (with transaction)')
            else:
                print('Wrong input!')
            del dataObj
            choice = input(PROMPT_STR)

        elif choice == '14':  # crash recovery (replay WAL log)
            import transaction_db
            tm = transaction_db.TransactionManager()
            actions = tm.recover()  # 回放WAL日志执行崩溃恢复
            if actions:
                print('Crash recovery actions:')
                for action in actions:
                    print('  ' + str(action))
            else:
                print('No recovery actions needed (WAL log empty or not found).')
            choice = input(PROMPT_STR)

        elif choice == '15':  # view WAL log
            import transaction_db
            tm = transaction_db.TransactionManager()
            records = tm.view_log()  # 查看WAL日志内容
            if records:
                print('WAL Log records:')
                for rec in records:
                    print('  Type: ' + rec['type'] + ', TxnID: ' + str(rec['txn_id']) +
                          ', Table: ' + rec['table'] + ', Time: ' + rec['timestamp'])
            else:
                print('WAL log is empty or not found.')
            choice = input(PROMPT_STR)

        elif choice == '.':
            print('main loop finishies')
            del schemaObj
            break

    print('main loop finish!')


if __name__ == '__main__':
    main()
