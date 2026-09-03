from common_db import BLOCK_SIZE

# structure of block_0, which stores the meta information and field information
# block_id                                # 0
# number_of_dat_blocks                    # at first it is 0 because there is no data in the table
# number_of_fields or number_of_records   # the total number of fields for the table


# the data type is as follows
# 0->str,1->varstr,2->int,3->bool


# structure of data block, whose block id begins with 1
# block_id       
# number of records
# record_0_offset         # it is a pointer to the data of record
# record_1_offset
# ...
# record_n_offset
# ....
# free space
# ...
# record_n
# ...
# record_1
# record_0

# structre of one record
# pointer                     #offset of table schema in block id 0
# length of record            # including record head and record content
# time stamp of last update  # for example,1999-08-22
# field_0_value
# field_1_value
# ...
# field_n_value


import struct
import os
import ctypes


# the class can store table data into files
# functions include insert, delete and update

class Storage(object):

    # constructor of the class
    # input:
    #       tablename
    def __init__(self, tablename, use_transaction=False, readonly=False):
# 添加事务支持和只读模式参数
        # print "__init__ of ",Storage.__name__,"begins to execute"
        if isinstance(tablename, str):  # 统一编码为bytes
            tablename = tablename.encode('utf-8')
        tablename = tablename.strip()

        self.record_list = []
        self.record_Position = []
# 事务管理器和数据状态标志
        self.tm = None
        if use_transaction:
            import transaction_db
            self.tm = transaction_db.TransactionManager()
        self.has_data = False  # 标记表中是否有数据

# 只读模式：文件不存在时设置空字段并返回
        if not os.path.exists(tablename + '.dat'.encode('utf-8')):  # the file corresponding to the table does not exist
            if readonly:
                self.field_name_list = []  # 只读模式下直接设为空
                self.num_of_fields = 0
                self.open = False
                return
            print('table file '.encode('utf-8') + tablename + '.dat does not exists'.encode('utf-8'))
            self.f_handle = open(tablename + '.dat'.encode('utf-8'), 'wb+')
            self.f_handle.close()
            self.open = False
            print(tablename + '.dat has been created'.encode('utf-8'))

# 只读模式：文件存在时以只读方式打开
        if readonly:
            self.f_handle = open(tablename + '.dat'.encode('utf-8'), 'rb')
            self.open = True
        else:
            self.f_handle = open(tablename + '.dat'.encode('utf-8'), 'rb+')
            self.open = True
        print('table file '.encode('utf-8') + tablename + '.dat has been opened'.encode('utf-8'))
        self.open = True

        self.dir_buf = ctypes.create_string_buffer(BLOCK_SIZE)
        self.f_handle.seek(0)
        self.dir_buf = self.f_handle.read(BLOCK_SIZE)

        # remove .strip() on bytes buffer (original had buffer on bytes which is problematic)
        my_len = len(self.dir_buf)
        self.field_name_list = []
        beginIndex = 0

# 只读模式：文件为空时设置空字段并返回
        if my_len == 0:  # there is no data in the block 0, we should write meta data into the block 0
            if readonly:
                self.field_name_list = []  # 只读模式下直接设为空
                self.num_of_fields = 0
                return
            if isinstance(tablename, bytes):
                self.num_of_fields = input(
                    "please input the number of feilds in table " + tablename.decode('utf-8') + ":")
            else:
                self.num_of_fields = input(
                    "please input the number of feilds in table " + tablename + ":")
            if int(self.num_of_fields) > 0:

                self.dir_buf = ctypes.create_string_buffer(BLOCK_SIZE)
                self.block_id = 0
                self.data_block_num = 0
                struct.pack_into('!iii', self.dir_buf, beginIndex, 0, 0,
                                 int(self.num_of_fields))  # block_id,number_of_data_blocks,number_of_fields

                beginIndex = beginIndex + struct.calcsize('!iii')

                # the following is to write the field name,field type and field length into the buffer in turn
                for i in range(int(self.num_of_fields)):
                    field_name = input("please input the name of field " + str(i) + " :")

                    if len(field_name) < 10:
                        field_name = ' ' * (10 - len(field_name.strip())) + field_name

                    while True:
                        field_type = input(
                            "please input the type of field(0-> str; 1-> varstr; 2-> int; 3-> boolean) " + str(
                                i) + " :")
                        if int(field_type) in [0, 1, 2, 3]:
                            break

                    # to need further modification here
                    field_length = input("please input the length of field " + str(i) + " :")
                    temp_tuple = (field_name, int(field_type), int(field_length))
                    self.field_name_list.append(temp_tuple)
                    if isinstance(field_name, str):
                        field_name = field_name.encode('utf-8')

                    struct.pack_into('!10sii', self.dir_buf, beginIndex, field_name, int(field_type),
                                     int(field_length))
                    beginIndex = beginIndex + struct.calcsize('!10sii')

                self.f_handle.seek(0)
                self.f_handle.write(self.dir_buf)
                self.f_handle.flush()

        else:  # there is something in the file

            self.block_id, self.data_block_num, self.num_of_fields = struct.unpack_from('!iii', self.dir_buf, 0)

            print('number of fields is ', self.num_of_fields)
            print('data_block_num', self.data_block_num)
            beginIndex = struct.calcsize('!iii')

            # the followins is to read field name, field type and field length into main memory structures
            for i in range(self.num_of_fields):
                field_name, field_type, field_length = struct.unpack_from('!10sii', self.dir_buf,
                                                                          beginIndex + i * struct.calcsize(
                                                                              '!10sii'))  # i means no memory alignment

                temp_tuple = (field_name, field_type, field_length)
                self.field_name_list.append(temp_tuple)
                print("the " + str(i) + "th field information (field name,field type,field length) is ", temp_tuple)
        # print self.field_name_list
        record_head_len = struct.calcsize('!ii10s')
        record_content_len = sum(map(lambda x: x[2], self.field_name_list))
        # print record_content_len

        Flag = 1
        while Flag <= self.data_block_num:
            self.f_handle.seek(BLOCK_SIZE * Flag)
            self.active_data_buf = self.f_handle.read(BLOCK_SIZE)
            self.block_id, self.Number_of_Records = struct.unpack_from('!ii', self.active_data_buf, 0)
            print('Block_ID=%s,   Contains %s data' % (self.block_id, self.Number_of_Records))
            # There exists record
            if self.Number_of_Records > 0:
                for i in range(self.Number_of_Records):
                    self.record_Position.append((Flag, i))
                    offset = \
                        struct.unpack_from('!i', self.active_data_buf,
                                           struct.calcsize('!ii') + i * struct.calcsize('!i'))[
                            0]
                    record = struct.unpack_from('!' + str(record_content_len) + 's', self.active_data_buf,
                                                offset + record_head_len)[0]
                    tmp = 0
                    tmpList = []
                    for field in self.field_name_list:
                        t = record[tmp:tmp + field[2]].strip()
                        tmp = tmp + field[2]
                        if field[1] == 2:
                            t = int(t)
                        if field[1] == 3:
                            t = bool(t)
                        tmpList.append(t)
                    self.record_list.append(tuple(tmpList))
            Flag += 1
# 设置数据存在标志
        if self.field_name_list:
            self.has_data = True  # 标记表中有数据

    # return the record list of the table
    # input:
    #
    def getRecord(self):
        return self.record_list

    # to insert a record into table
    # param insert_record: list
    # return: True or False
    def insert_record(self, insert_record):

        # example: ['xuyidan','23','123456']

        # step 1 : to check the insert_record is True or False

        tmpRecord = []
        for idx in range(len(self.field_name_list)):
            insert_record[idx] = insert_record[idx].strip()
            if self.field_name_list[idx][1] == 0 or self.field_name_list[idx][1] == 1:
                if len(insert_record[idx]) > self.field_name_list[idx][2]:
                    return False
                tmpRecord.append(insert_record[idx])
            if self.field_name_list[idx][1] == 2:
                try:
                    tmpRecord.append(int(insert_record[idx]))
                except:
                    return False
            if self.field_name_list[idx][1] == 3:
                try:
                    tmpRecord.append(bool(insert_record[idx]))
                except:
                    return False
            insert_record[idx] = ' ' * (self.field_name_list[idx][2] - len(insert_record[idx])) + insert_record[idx]

        # step2: Add tmpRecord to record_list ; change insert_record into inputstr
        inputstr = ''.join(insert_record)

        self.record_list.append(tuple(tmpRecord))

        # Step3: To calculate MaxNum in each Data Blocks
        record_content_len = len(inputstr)
        record_head_len = struct.calcsize('!ii10s')
        record_len = record_head_len + record_content_len
        MAX_RECORD_NUM = (BLOCK_SIZE - struct.calcsize('!i') - struct.calcsize('!ii')) / (
                record_len + struct.calcsize('!i'))

        # Step4: To calculate new record Position
        if not len(self.record_Position):
            self.data_block_num += 1
            self.record_Position.append((1, 0))
        else:
            last_Position = self.record_Position[-1]
            if last_Position[1] == MAX_RECORD_NUM - 1:
                self.record_Position.append((last_Position[0] + 1, 0))
                self.data_block_num += 1
            else:
                self.record_Position.append((last_Position[0], last_Position[1] + 1))

        last_Position = self.record_Position[-1]

        # Step5: Write new record into file xxx.dat
        # update data_block_num
        self.f_handle.seek(0)
        self.buf = ctypes.create_string_buffer(struct.calcsize('!ii'))
        struct.pack_into('!ii', self.buf, 0, 0, self.data_block_num)
        self.f_handle.write(self.buf)
        self.f_handle.flush()

        # update data block head
        self.f_handle.seek(BLOCK_SIZE * last_Position[0])
        self.buf = ctypes.create_string_buffer(struct.calcsize('!ii'))
        struct.pack_into('!ii', self.buf, 0, last_Position[0], last_Position[1] + 1)
        self.f_handle.write(self.buf)
        self.f_handle.flush()

        # update data offset
        offset = struct.calcsize('!ii') + last_Position[1] * struct.calcsize('!i')
        beginIndex = BLOCK_SIZE - (last_Position[1] + 1) * record_len
        self.f_handle.seek(BLOCK_SIZE * last_Position[0] + offset)
        self.buf = ctypes.create_string_buffer(struct.calcsize('!i'))
        struct.pack_into('!i', self.buf, 0, beginIndex)
        self.f_handle.write(self.buf)
        self.f_handle.flush()

        # update data
        record_schema_address = struct.calcsize('!iii')
        update_time = '2016-11-16'  # update time
        self.f_handle.seek(BLOCK_SIZE * last_Position[0] + beginIndex)
        self.buf = ctypes.create_string_buffer(record_len)
        struct.pack_into('!ii10s', self.buf, 0, record_schema_address, record_content_len, update_time.encode('utf-8'))
        struct.pack_into('!' + str(record_content_len) + 's', self.buf, record_head_len, inputstr.encode('utf-8'))
        self.f_handle.write(self.buf.raw)
        self.f_handle.flush()

        return True

    # show the data structure and its data
    # input:
    #       t

    def show_table_data(self):
# 空表检查
        if not self.field_name_list:
            print("表中暂无数据")  # 表无字段定义
            return
        if not self.record_list:
            print("表中暂无数据")  # 表无记录
            return
        print('|    '.join(map(lambda x: x[0].decode('utf-8').strip(), self.field_name_list)))  # show the structure

        # the following is to show the data of the table
        for record in self.record_list:
            print(record)

    # to delete  the data file
    # input
    #       table name
    # output
    #       True or False
    def delete_table_data(self, tableName):

        # step 1: identify whether the file is still open
        if self.open == True:
            self.f_handle.close()
            self.open = False

        # step 2: remove the file from os   
        tableName.strip()
        if os.path.exists(tableName + '.dat'.encode('utf-8')):
            os.remove(tableName + '.dat'.encode('utf-8'))

        return True

    # get the list of field information, each element of which is (field name, field type, field length)
    # input:
    #       

    def getFieldList(self):
        return self.field_name_list

# 新增方法：返回字段名列表（同getFieldList）
    # get the list of field names
    # input:
    #
    def getfilenamelist(self):
        """返回字段名列表，功能同getFieldList"""
        return self.field_name_list

# 新增方法：按条件删除记录
    # to delete records matching condition_field == condition_value
    # param condition_field: str or bytes, the field name to match
    # param condition_value: str, the value to match
    # return: True if records were deleted, False otherwise
    def delete_record(self, condition_field, condition_value):
        """删除所有满足 condition_field == condition_value 的记录，重写.dat文件"""
        # 查找条件字段索引
        cond_idx = -1
        for i, field_tuple in enumerate(self.field_name_list):
            fn = field_tuple[0]
            if isinstance(fn, bytes):
                fn = fn.decode('utf-8').strip()
            if isinstance(condition_field, bytes):
                condition_field = condition_field.decode('utf-8').strip()
            if fn == condition_field:
                cond_idx = i
                break
        if cond_idx == -1:
            return False  # 找不到条件字段

        # 过滤record_list，保留不匹配的记录
        new_record_list = []
        deleted_count = 0
        for rec in self.record_list:
            rec_val = rec[cond_idx]
            if isinstance(rec_val, bytes):
                rec_val = rec_val.decode('utf-8').strip()
            rec_val = str(rec_val)
            if rec_val == str(condition_value):
                deleted_count += 1
            else:
                new_record_list.append(rec)

        if deleted_count == 0:
            return False  # 没有记录被删除

        # 更新内存中的record_list和record_Position
        self.record_list = new_record_list
        # 重新构建record_Position（记录可能分散在不同块）
        new_positions = []
        record_head_len = struct.calcsize('!ii10s')
        record_content_len = sum(map(lambda x: x[2], self.field_name_list))
        record_len = record_head_len + record_content_len
        MAX_RECORD_NUM = (BLOCK_SIZE - struct.calcsize('!i') - struct.calcsize('!ii')) // (
                record_len + struct.calcsize('!i'))
        block_num = 1
        pos_in_block = 0
        for _ in self.record_list:
            new_positions.append((block_num, pos_in_block))
            pos_in_block += 1
            if pos_in_block >= MAX_RECORD_NUM:
                block_num += 1
                pos_in_block = 0

        # 重写整个.dat文件
        self.data_block_num = block_num
        self.f_handle.seek(0)
        self.f_handle.truncate(0)  # 清空文件

        # 重写block 0头部
        self.dir_buf = ctypes.create_string_buffer(BLOCK_SIZE)
        beginIndex = 0
        struct.pack_into('!iii', self.dir_buf, beginIndex, 0, 0,
                         int(self.num_of_fields))
        beginIndex += struct.calcsize('!iii')
        for field_tuple in self.field_name_list:
            fn = field_tuple[0]
            if isinstance(fn, str):
                fn = fn.encode('utf-8')
            struct.pack_into('!10sii', self.dir_buf, beginIndex,
                             fn, int(field_tuple[1]), int(field_tuple[2]))
            beginIndex += struct.calcsize('!10sii')
        self.f_handle.write(self.dir_buf)
        self.f_handle.flush()

        # 重新插入所有保留的记录
        self.record_Position = []
        self.data_block_num = 0
        for rec in self.record_list:
            rec_strs = []
            tmpList = []
            for idx, field_tuple in enumerate(self.field_name_list):
                val = rec[idx]
                if isinstance(val, bytes):
                    val = val.decode('utf-8').strip()
                s = str(val).strip()
                # Pad ALL fields to their fixed length (int/bool too)
                s = ' ' * (field_tuple[2] - len(s)) + s
                rec_strs.append(s)
                if field_tuple[1] == 0 or field_tuple[1] == 1:
                    val = s
                tmpList.append(val)
            self._rewrite_insert(rec_strs, rec)
        return True

# 新增方法：按条件更新记录
    # to update records matching condition_field == condition_value
    # by setting new_field = new_value
    # param condition_field: str or bytes, the field name to match
    # param condition_value: str, the value to match
    # param new_field: str or bytes, the field name to update
    # param new_value: str, the new value to set
    # return: True if records were updated, False otherwise
    def update_record(self, condition_field, condition_value, new_field, new_value):
        """更新所有满足 condition_field == condition_value 的记录，设置 new_field = new_value"""
        # 查找条件字段索引和新字段索引
        cond_idx = -1
        new_idx = -1
        for i, field_tuple in enumerate(self.field_name_list):
            fn = field_tuple[0]
            if isinstance(fn, bytes):
                fn = fn.decode('utf-8').strip()
            if isinstance(condition_field, bytes):
                condition_field = condition_field.decode('utf-8').strip()
            if isinstance(new_field, bytes):
                new_field = new_field.decode('utf-8').strip()
            if fn == condition_field:
                cond_idx = i
            if fn == new_field:
                new_idx = i
        if cond_idx == -1 or new_idx == -1:
            return False  # 找不到字段

        updated_count = 0
        # 遍历记录，更新匹配的记录
        for i, rec in enumerate(self.record_list):
            rec_val = rec[cond_idx]
            if isinstance(rec_val, bytes):
                rec_val = rec_val.decode('utf-8').strip()
            rec_val = str(rec_val)
            if rec_val == str(condition_value):
                # 构建更新后的记录tuple
                new_rec_list = list(rec)
                new_val = str(new_value)
                if self.field_name_list[new_idx][1] == 2:  # int类型
                    new_val = int(new_value)
                elif self.field_name_list[new_idx][1] == 3:  # bool类型
                    new_val = bool(new_value)
                new_rec_list[new_idx] = new_val
                self.record_list[i] = tuple(new_rec_list)
                updated_count += 1

        if updated_count == 0:
            return False  # 没有记录被更新

        # 重写整个.dat文件以反映更新
        self.f_handle.seek(0)
        self.f_handle.truncate(0)  # 清空文件

        # 重写block 0头部
        self.dir_buf = ctypes.create_string_buffer(BLOCK_SIZE)
        beginIndex = 0
        struct.pack_into('!iii', self.dir_buf, beginIndex, 0, 0,
                         int(self.num_of_fields))
        beginIndex += struct.calcsize('!iii')
        for field_tuple in self.field_name_list:
            fn = field_tuple[0]
            if isinstance(fn, str):
                fn = fn.encode('utf-8')
            struct.pack_into('!10sii', self.dir_buf, beginIndex,
                             fn, int(field_tuple[1]), int(field_tuple[2]))
            beginIndex += struct.calcsize('!10sii')
        self.f_handle.write(self.dir_buf)
        self.f_handle.flush()

        # 重新插入所有记录
        self.record_Position = []
        self.data_block_num = 0
        for rec in self.record_list:
            rec_strs = []
            for idx, field_tuple in enumerate(self.field_name_list):
                val = rec[idx]
                if isinstance(val, bytes):
                    val = val.decode('utf-8').strip()
                s = str(val).strip()
                # Pad ALL fields to their fixed length
                s = ' ' * (field_tuple[2] - len(s)) + s
                rec_strs.append(s)
            self._rewrite_insert(rec_strs, rec)
        return True

# 内部辅助方法：向.dat文件写入一条记录
    def _rewrite_insert(self, insert_record_strs, insert_record_tuple):
        """
        内部辅助方法：将一条记录写入.dat文件（不重复校验，不添加self.record_list）。
        用于delete_record和update_record的重写逻辑。
        """
        inputstr = ''.join(insert_record_strs)
        record_content_len = len(inputstr)
        record_head_len = struct.calcsize('!ii10s')
        record_len = record_head_len + record_content_len
        MAX_RECORD_NUM = (BLOCK_SIZE - struct.calcsize('!i') - struct.calcsize('!ii')) // (
                record_len + struct.calcsize('!i'))

        if not len(self.record_Position):
            self.data_block_num += 1
            self.record_Position.append((1, 0))
        else:
            last_Position = self.record_Position[-1]
            if last_Position[1] == MAX_RECORD_NUM - 1:
                self.record_Position.append((last_Position[0] + 1, 0))
                self.data_block_num += 1
            else:
                self.record_Position.append((last_Position[0], last_Position[1] + 1))

        last_Position = self.record_Position[-1]

        # 更新data_block_num
        self.f_handle.seek(0)
        self.buf = ctypes.create_string_buffer(struct.calcsize('!ii'))
        struct.pack_into('!ii', self.buf, 0, 0, self.data_block_num)
        self.f_handle.write(self.buf)
        self.f_handle.flush()

        # 更新block头部
        self.f_handle.seek(BLOCK_SIZE * last_Position[0])
        self.buf = ctypes.create_string_buffer(struct.calcsize('!ii'))
        struct.pack_into('!ii', self.buf, 0, last_Position[0], last_Position[1] + 1)
        self.f_handle.write(self.buf)
        self.f_handle.flush()

        # 更新offset
        offset = struct.calcsize('!ii') + last_Position[1] * struct.calcsize('!i')
        beginIdx = BLOCK_SIZE - (last_Position[1] + 1) * record_len
        self.f_handle.seek(BLOCK_SIZE * last_Position[0] + offset)
        self.buf = ctypes.create_string_buffer(struct.calcsize('!i'))
        struct.pack_into('!i', self.buf, 0, beginIdx)
        self.f_handle.write(self.buf)
        self.f_handle.flush()

        # 写记录数据
        record_schema_address = struct.calcsize('!iii')
        update_time = '2016-11-16'
        self.f_handle.seek(BLOCK_SIZE * last_Position[0] + beginIdx)
        self.buf = ctypes.create_string_buffer(record_len)
        struct.pack_into('!ii10s', self.buf, 0, record_schema_address, record_content_len, update_time.encode('utf-8'))
        struct.pack_into('!' + str(record_content_len) + 's', self.buf, record_head_len, inputstr.encode('utf-8'))
        self.f_handle.write(self.buf.raw)
        self.f_handle.flush()

# 新增方法：带WAL事务持久化的插入操作
    # to insert a record with WAL transaction durability
    # param insert_record: list of field values
    # return: True if committed, False if aborted
    def insert_record_with_txn(self, insert_record):
        """带WAL事务持久化的插入操作"""
        if self.tm is None:
            return False  # 未启用事务
        # 序列化后像（after-image）
        after_img = _serialize_txn_record(insert_record)
        # 获取表名
        import os
        table_name = os.path.splitext(os.path.basename(self.f_handle.name))[0]
        # 开始事务、记录插入日志
        txn_id = self.tm.begin_transaction()
        self.tm.log_insert(txn_id, table_name, after_img)
        # 执行实际插入
        result = self.insert_record(insert_record)
        if result:
            self.tm.commit(txn_id)  # 提交
        else:
            self.tm.abort(txn_id)  # 回滚
        return result

# 新增方法：带WAL事务持久化的更新操作
    # to update records with WAL transaction durability
    # param condition_field: str or bytes, the field name to match
    # param condition_value: str, the value to match
    # param new_field: str or bytes, the field name to update
    # param new_value: str, the new value to set
    # return: True if committed, False if aborted
    def update_record_with_txn(self, condition_field, condition_value, new_field, new_value):
        """带WAL事务持久化的更新操作"""
        if self.tm is None:
            return False  # 未启用事务
        # 查找匹配的记录，构建前后像
        cond_idx = -1
        new_idx = -1
        for i, field_tuple in enumerate(self.field_name_list):
            fn = field_tuple[0]
            if isinstance(fn, bytes):
                fn = fn.decode('utf-8').strip()
            if isinstance(condition_field, bytes):
                condition_field = condition_field.decode('utf-8').strip()
            if isinstance(new_field, bytes):
                new_field = new_field.decode('utf-8').strip()
            if fn == condition_field:
                cond_idx = i
            if fn == new_field:
                new_idx = i
        if cond_idx == -1 or new_idx == -1:
            return False

        import os
        table_name = os.path.splitext(os.path.basename(self.f_handle.name))[0]
        all_success = True
        for rec in self.record_list:
            rec_val = rec[cond_idx]
            if isinstance(rec_val, bytes):
                rec_val = rec_val.decode('utf-8').strip()
            rec_val = str(rec_val)
            if rec_val == str(condition_value):
                # 构建前后像
                before_img = _serialize_txn_record(rec)
                updated_rec = list(rec)
                new_val = str(new_value)
                if self.field_name_list[new_idx][1] == 2:
                    new_val = int(new_value)
                elif self.field_name_list[new_idx][1] == 3:
                    new_val = bool(new_value)
                updated_rec[new_idx] = new_val
                after_img = _serialize_txn_record(tuple(updated_rec))
                # 开始事务并记录更新日志
                txn_id = self.tm.begin_transaction()
                self.tm.log_update(txn_id, table_name, before_img, after_img)
                # 执行实际更新
                result = self.update_record(condition_field, condition_value, new_field, new_value)
                if result:
                    self.tm.commit(txn_id)
                else:
                    self.tm.abort(txn_id)
                    all_success = False
        return all_success

    # destructor
    def __del__(self):  # write the metahead information in head object to file
        if self.open == True:
            # 只读模式不写入，直接关闭
            if hasattr(self, 'f_handle') and self.f_handle and not self.f_handle.closed:
                try:
                    self.f_handle.seek(0)
                    self.buf = ctypes.create_string_buffer(struct.calcsize('!ii'))
                    struct.pack_into('!ii', self.buf, 0, 0, self.data_block_num)
                    self.f_handle.write(self.buf)
                    self.f_handle.flush()
                except (IOError, OSError, AttributeError):
                    pass
                finally:
                    self.f_handle.close()


# 模块级辅助函数：序列化记录为WAL日志格式
def _serialize_txn_record(record):
    """
    将记录元组序列化为 '|'.join(parts) 格式的字符串，用于WAL事务日志。
    Input:
        record: tuple of field values (bytes, int, str, etc.)
    Output:
        str, pipe-separated field values
    """
    parts = []
    for val in record:
        if isinstance(val, bytes):
            parts.append(val.decode('utf-8').strip())  # bytes解码为str
        else:
            parts.append(str(val))  # 转换为字符串
    return '|'.join(parts)  # 用管道符连接
