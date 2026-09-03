import ctypes
import os       #   新增os模块，用于文件检测与重命名
import struct
import head_db # it is main memory structure for the table schema





#the following is metaHead structure,which is 12 bytes
"""
isStored    # whether there is data in the all.sch
tableNum    # how many tables
offset      # where the free area begins for body.
"""
META_HEAD_SIZE=12                                           #the First part in the schema file


#the following is the structure of tableNameHead
"""
tablename|numofFeilds|beginOffsetInBody|....|tablename|numofFeilds|beginOffsetInBody|
10 bytes |4 bytes    |4 bytes
"""
MAX_TABLE_NAME_LEN=10                                       # the maximum length of table name
MAX_TABLE_NUM=100                                           # the maximum number of tables in the all.sch
TABLE_NAME_ENTRY_LEN=MAX_TABLE_NAME_LEN+4+4                 # the length of one table name entry
TABLE_NAME_HEAD_SIZE=MAX_TABLE_NUM*TABLE_NAME_ENTRY_LEN     # the SECOND part in the schema file



# the following is for body, which stores the field information of each table and the field information is as follows
"""
field_name   # it is a string
field_type   # it is an integer, 0->str,1->varstr,2->int,3->bool
field_length # it is an integer
"""
MAX_FIELD_NAME_LEN=10                                       # the maximum length of field name
MAX_FIELD_LEN=10+4+4                                         #  the maximum length of one field
MAX_NUM_OF_FIELD_PER_TABLE=5                                # the maximum number of fields in one table
FIELD_ENTRY_SIZE_PER_TABLE=MAX_FIELD_LEN*MAX_NUM_OF_FIELD_PER_TABLE
MAX_FIELD_SECTION_SIZE=FIELD_ENTRY_SIZE_PER_TABLE*MAX_TABLE_NUM #the THIRD part in the schema file



BODY_BEGIN_INDEX=META_HEAD_SIZE+TABLE_NAME_HEAD_SIZE            # Intitially, where the field name, type and length are stored


# the table name is padded if its lenght is smaller than MAX_TABLE_NAME_WHEN
# input:
#       tableName: the table name
# 重写fillTableName：支持bytes/str，左填充加截断
def fillTableName(tableName): # 将表名填充或截断至10字节
    # 处理bytes输入：解码为字符串
    if isinstance(tableName, bytes):
        tableName = tableName.decode('utf-8')
    # 去除两端空白字符
    tableName = tableName.strip()
    if len(tableName) < MAX_TABLE_NAME_LEN:
        # 左侧填充空格至10字符长度
        tableName = ' ' * (MAX_TABLE_NAME_LEN - len(tableName)) + tableName
    else:
        # 超过10字符则截断
        tableName = tableName[:MAX_TABLE_NAME_LEN]
    return tableName.encode('utf-8')  # 返回bytes


class Schema(object):
    '''
    Schema class
    '''

    fileName = 'all.sch'  # the schema file name
    count = 0  # there should be only one object in the program

    @staticmethod
    def how_many():  # give the count of instances
        return Schema.count


    def viewTableNames(self):  # to list all the table names in the all.sch

        print ('viewtablenames begin to execute')
        # to be inserted here
        for i in self.headObj.tableNames:
            print ('Table name is     ', i[0])
        print ('execute Done!')

    # to show the schema of given table
    # input
    #       table_name
# 实现viewTableStructure：查询并打印表结构
    def viewTableStructure(self, table_name):
        print('the structure of table '.encode('utf-8')+table_name+' is as follows:'.encode('utf-8'))
        # 去除表名两端空格作为字典键
        key = table_name.strip()
        # 在字段字典中查找表名（保持bytes类型与存储的key一致）
        if key in self.headObj.tableFields:
            fields = self.headObj.tableFields[key]
            # 遍历并打印每个字段的名称、类型、长度
            for f in fields:
                fname = f[0].strip() if isinstance(f[0], bytes) else f[0].strip()
                print('field name: {}, type: {}, length: {}'.format(fname, f[1], f[2]))
            return fields
        else:
            print('table not found')
            return None

# 新增_update_metahead：立即将metaHead写入all.sch
    def _update_metahead(self):
        """将内存中的metaHead(isStored,lenOfTableNum,offsetOfBody)立即写入all.sch文件"""
        buf = ctypes.create_string_buffer(META_HEAD_SIZE)
        struct.pack_into('!?ii', buf, 0, self.headObj.isStored, self.headObj.lenOfTableNum, self.headObj.offsetOfBody)
        self.fileObj.seek(0)       # 定位到文件开头
        self.fileObj.write(buf)    # 写入metaHead
        self.fileObj.flush()       # 刷新到磁盘

# 新增_discover_dat_files：自动发现并恢复孤立的.dat文件
    def _discover_dat_files(self):
        """扫描当前目录下所有.dat文件，将不在schema中的表恢复"""
        import glob
        discovered = 0
        # 获取schema中已有的表名集合
        known = set()
        for tn in self.headObj.tableNames:
            name = tn[0].strip()
            if isinstance(name, bytes):
                name = name.decode('utf-8')
            known.add(name)
        for datfile in glob.glob('*.dat'):
            tname = os.path.splitext(datfile)[0]  # 去除.dat后缀
            if tname in known:
                continue  # 已记录，跳过
            try:
                with open(datfile, 'rb') as f:
                    # 读block 0头部：header(!iii) = 12 bytes
                    hdr = f.read(12)
                    if len(hdr) < 12:
                        continue
                    cols, rows, flen = struct.unpack('!iii', hdr)
                if cols <= 0 or cols > MAX_NUM_OF_FIELD_PER_TABLE:
                    continue
                fields = []
                # 读字段条目
                with open(datfile, 'rb') as f:
                    f.seek(12)
                    for _ in range(cols):
                        entry = f.read(MAX_FIELD_LEN)
                        if len(entry) < MAX_FIELD_LEN:
                            break
                        fn, ft, fl = struct.unpack_from('!10sii', entry, 0)
                        fields.append((fn, ft, fl))
                if len(fields) != cols:
                    continue
                # 调用appendTable将发现的表加入schema
                self.appendTable(tname, fields)
                discovered += 1
                # 若tname被截断，将.dat文件重命名为schema中的完整名
                actualName = self.headObj.tableNames[-1][0]
                if isinstance(actualName, bytes):
                    actualName = actualName.decode('utf-8').strip()
                else:
                    actualName = actualName.strip()
                if actualName != tname:
                    try:
                        os.rename(datfile, actualName + '.dat')
                    except Exception:
                        pass
            except Exception:
                continue
        return discovered

    # constructor of the class
# 修改__init__：自动创建文件/恢复数据/规范化文件名
    def __init__(self):
        print ('__init__ of Schema')

        print ('schema fileName is ' + Schema.fileName)
        # 若schema文件不存在则创建
        if not os.path.exists(Schema.fileName):
            open(Schema.fileName, 'wb+').close()
        self.fileObj = open(Schema.fileName, 'rb+')  # in binary format

        # read all data from schema file
        bufLen = META_HEAD_SIZE + TABLE_NAME_HEAD_SIZE + MAX_FIELD_SECTION_SIZE  # the length of metahead, table name entries and feildName sections
        buf = ctypes.create_string_buffer(bufLen)
        buf = self.fileObj.read(bufLen)

        #the following is to print the content of the buffer
        buf.strip()
        if len(buf) == 0:  # for the first time, there is nothing in the schema file
            self.body_begin_index = BODY_BEGIN_INDEX
            buf = struct.pack('!?ii', False, 0, self.body_begin_index)  # is_stored, tablenum,offset

            self.fileObj.seek(0)
            self.fileObj.write(buf)
            self.fileObj.flush()

            # the following is to create a main memory structure for the schema

            tableNameList = []
            fieldNameList = {}  # it is a dictionary
            nameList = []
            fieldsList = {}
            self.headObj = head_db.Header(nameList, fieldsList,False, 0, self.body_begin_index)

            print ('metaHead of schema has been written to all.sch and the Header ojbect created')

        else:  # there is something in the schema file


            print ("there is something  in the all.sch")
            # in the following ? denotes bool type and  i denotes int type
            isStored, tempTableNum, tempOffset = struct.unpack_from('!?ii', buf, 0)   #link:https://docs.python.org/2/library/struct.html

            print ("tableNum in schema file is ", tempTableNum)
            print ("isStored in schema file is ", isStored)
            print ("offset of body in schema  file is ", tempOffset)

            Schema.body_begin_index = tempOffset
            nameList=[]
            fieldsList={}
             # it is a dictionary

            if isStored == False:  # only the meta head exists, but there is no table information in the schema file
# ：即使isStored为False，也扫描tableNameHead和body二进制数据恢复表
                recovered = 0
                for i in range(MAX_TABLE_NUM):
                    pos = META_HEAD_SIZE + i * TABLE_NAME_ENTRY_LEN
                    if pos + TABLE_NAME_ENTRY_LEN > len(buf):  # 缓冲区不够大，停止扫描
                        break
                    tn, = struct.unpack_from('!10s', buf, pos)
                    tnum, = struct.unpack_from('!i', buf, pos + 10)
                    tpos, = struct.unpack_from('!i', buf, pos + 10 + struct.calcsize('i'))
                    # 校验数据有效性：字段数>0且偏移量合理
                    if tnum > 0 and tnum <= MAX_NUM_OF_FIELD_PER_TABLE and tpos >= BODY_BEGIN_INDEX:
                        fields = []
                        for j in range(tnum):
                            if tpos + (j + 1) * MAX_FIELD_LEN > len(buf):  # 防止越界
                                break
                            tfn, tft, tfl = struct.unpack_from('!10sii', buf, tpos + j * MAX_FIELD_LEN)
                            fields.append((tfn, tft, tfl))
                        if len(fields) == tnum:
                            nameList.append((tn.strip(), tnum, tpos))
                            fieldsList[tn.strip()] = fields
                            recovered += 1
                if recovered > 0:
                    print(" recovered {} tables from binary data".format(recovered))
                    tempTableNum = recovered
                    tempOffset = BODY_BEGIN_INDEX
                    for (nm, nf, po) in nameList:
                        tempOffset = max(tempOffset, po + nf * MAX_FIELD_LEN)
                    self.headObj = head_db.Header(nameList, fieldsList, True, tempTableNum, tempOffset)
                    # 恢复后写入metaHead
                    self._update_metahead()
                else:
                    self.headObj = head_db.Header(nameList, fieldsList, False, 0, BODY_BEGIN_INDEX)
                print ("there is no table in the file")

            else:  # there is information of some tables

                print( "there is at least one table in the schema file ")

                # the following is to fetch the tableNameHead from the buffer
                for i in range(tempTableNum):
                    # fetch the table name in tableNameHead
                    tempName, = struct.unpack_from('!10s', buf,
                                                   META_HEAD_SIZE + i * TABLE_NAME_ENTRY_LEN)  # Note: '!' means no memory alignment
                    print ("tablename is ", tempName)

                    # fetch the number of fields in the table in tableNameHead
                    tempNum, = struct.unpack_from('!i', buf, META_HEAD_SIZE + i * TABLE_NAME_ENTRY_LEN + 10)
                    print ('number of fields of table ', tempName, ' is ', tempNum)

                    # fetch the offset where field names are stored in the body
                    tempPos, = struct.unpack_from('!i', buf,
                                                  META_HEAD_SIZE + i * TABLE_NAME_ENTRY_LEN + 10 + struct.calcsize('i'))
                    print ("tempPos in body is ", tempPos)

                    tempNameMix = (tempName.strip(), tempNum, tempPos)
                    nameList.append(tempNameMix)  # It is a triple

                    # the following is to fetch field information from body section and each field is  (fieldname,fieldtype,fieldlength)
                    if tempNum > 0: # the number of fields is greater than 0
                        fields = []  # it is a list
                        for j in range(tempNum):
                            tempFieldName,tempFieldType,tempFieldLength = struct.unpack_from('!10sii',
                                                                                             buf, tempPos + j * MAX_FIELD_LEN)


                            print ('field name is ', tempFieldName.strip())

                            print ('field type is', tempFieldType)

                            print ('filed length is', tempFieldLength)

                            tempFieldTuple=(tempFieldName,tempFieldType,tempFieldLength)

                            fields.append(tempFieldTuple)


                        fieldsList[tempName.strip()]=fields

                # the main memory structure for schema is constructed

                self.headObj = head_db.Header(nameList, fieldsList, True, tempTableNum, tempOffset)

        # :load finished, discover orphan .dat files and recover
        discovered = self._discover_dat_files()
        print(" discovered {} orphan .dat files".format(discovered))
        # :normalize .dat filenames to match schema table names
        import glob as _glob
        for tn in self.headObj.tableNames:
            sname = tn[0].strip()
            if isinstance(sname, bytes):
                sname = sname.decode('utf-8')
            for df in _glob.glob(sname + '*.dat'):
                expected = sname + '.dat'
                if df != expected:
                    try:
                        os.rename(df, expected)
                    except Exception:
                        pass

    # destructor of the class
    def __del__(self):  # write the metahead information in head object to file

        print ("__del__ of class Schema begins to execute")

        buf = ctypes.create_string_buffer(12)

        struct.pack_into('!?ii', buf, 0, self.headObj.isStored, self.headObj.lenOfTableNum, self.headObj.offsetOfBody)
        self.fileObj.seek(0)
        self.fileObj.write(buf)
        self.fileObj.flush()
        self.fileObj.close()

    # delete all the contents in the schema file
# 修改deleteAll：截断后立即更新metaHead
    def deleteAll(self):
        self.headObj.tableFields=[]
        self.headObj.tableNames=[]
        self.fileObj.seek(0)
        self.fileObj.truncate(0)
        self.headObj.isStored = False
        self.headObj.lenOfTableNum = 0
        self.headObj.offsetOfBody = self.body_begin_index
        self.fileObj.flush()
        self._update_metahead()  # :write metahead right after truncate
        print ("all.sch file has been truncated")

    # insert a table schema to the schema file
    # input:
    #       tablename: the table to be added
    #       fieldList: the field information list and each element is a tuple(fieldname,fieldtype,fieldlength)
# 修改appendTable：捕获strip结果/字段bytes处理/立即写metaHead
    def appendTable(self, tableName, fieldList):  # it modify the tableNameHead and body of all.sch
        print ("appendTable begins to execute")
        tableName = tableName.strip()  # 捕获strip结果

        if len(tableName) == 0 or len(tableName) > 10 or len(fieldList)==0:
            print ('tablename is invalid or field list is invalid')
        else:

            fieldNum = len(fieldList)

            print ("the following is to write the fields to body in all.sch")
            fieldBuff = ctypes.create_string_buffer(MAX_FIELD_LEN * len(fieldList))
            beginIndex = 0
            for i in range(len(fieldList)):
                (fieldName,fieldType,fieldLength)=fieldList[i]
# ：fieldName为str时编码为bytes
                if isinstance(fieldName, str):
                    fieldName = fieldName.encode('utf-8')
# ：正确处理字段名的strip和左填充
                fname_stripped = fieldName.strip()
                if len(fname_stripped) < MAX_FIELD_NAME_LEN:
                    filledFieldName = b' ' * (MAX_FIELD_NAME_LEN - len(fname_stripped)) + fname_stripped
                else:
                    filledFieldName = fname_stripped[:MAX_FIELD_NAME_LEN]
                struct.pack_into('!10sii', fieldBuff, beginIndex, filledFieldName,int(fieldType),int(fieldLength))

                beginIndex = beginIndex + MAX_FIELD_LEN

            writePos = self.headObj.offsetOfBody

            self.fileObj.seek(writePos)
            self.fileObj.write(fieldBuff)
            self.fileObj.flush()

            # self.headObj.offsetOfBody=self.headObj.offsetBody+fieldNum*MAX_FIELD_LEN

            print ("the following is to write table name entry to tableNameHead in all.sch")
            filledTableName = fillTableName(tableName)
            if isinstance(filledTableName, str):
                filledTableName = filledTableName.encode('utf-8')
            nameBuf = struct.pack('!10sii', filledTableName, fieldNum, self.headObj.offsetOfBody)

            self.fileObj.seek(META_HEAD_SIZE + self.headObj.lenOfTableNum * TABLE_NAME_ENTRY_LEN)
            nameContent = (tableName.strip(), fieldNum, self.headObj.offsetOfBody)

            self.fileObj.write(nameBuf)
            self.fileObj.flush()

            print ("to modify the header structure in main memory")
            self.headObj.isStored = True
            self.headObj.lenOfTableNum += 1
            self.headObj.offsetOfBody += fieldNum * MAX_FIELD_LEN
            self.headObj.tableNames.append(nameContent)
            # fieldTuple = tuple(fieldList)
            self.headObj.tableFields[tableName.strip()]=fieldList
# ：修改内存结构后立即写入metaHead
            self._update_metahead()

    # to determine whether the table named table_name exist, depending on the main memory structures
    # input
    #       table_name
    # output
    #       true or false
    def find_table(self, table_name):
        Tables = list(map(lambda x: x[0].strip(), self.headObj.tableNames))
        if table_name.strip() in Tables:
            return True
        else:
            return False



        
    # to write the main memory information into the schema file
    # input
    #
    # output
    #       True or False
# 修改WriteBuff：表名与字段名的bytes/str兼容处理
    def WriteBuff(self):
        bufLen = META_HEAD_SIZE + TABLE_NAME_HEAD_SIZE + MAX_FIELD_SECTION_SIZE  # the length of metahead, table name entries and feildName sections
        buf = ctypes.create_string_buffer(bufLen)
        struct.pack_into('!?ii', buf, 0, self.headObj.isStored, self.headObj.lenOfTableNum, self.headObj.offsetOfBody)
        #isStored, tempTableNum, tempOffset = struct.unpack_from('!?ii', buf,0)  # link:https://docs.python.org/2/library/struct.html
        #print isStored,tempTableNum,tempOffset
        for idx in range(len(self.headObj.tableNames)):
            tmp_tableName = self.headObj.tableNames[idx][0]
# ：bytes解码为str再处理
            if isinstance(tmp_tableName, bytes):
                tmp_tableName = tmp_tableName.decode('utf-8')
            tmp_tableName = tmp_tableName.strip()
            if len(tmp_tableName) < 10:
                tmp_tableName = ' ' * (10 - len(tmp_tableName)) + tmp_tableName
            tmp_tableName = tmp_tableName.encode('utf-8')  # 编码回bytes

            # write (tablename,numberoffields,offsetinbody) to buffer
            struct.pack_into('!10sii', buf, META_HEAD_SIZE + idx * TABLE_NAME_ENTRY_LEN, tmp_tableName,
                             self.headObj.tableNames[idx][1],self.headObj.tableNames[idx][2])

            # write the field information of each table into the buffer
            for idj in range(self.headObj.tableNames[idx][1]):
# ：通过表名key（而非整数索引）访问dict
                table_key = self.headObj.tableNames[idx][0].strip()
                (tempFieldName,tempFieldType,tempFieldLength)=self.headObj.tableFields[table_key][idj]
# ：字段名为str时编码为bytes
                if isinstance(tempFieldName, str):
                    tempFieldName = tempFieldName.encode('utf-8')
                struct.pack_into('!10sii',buf,self.headObj.tableNames[idx][2]+idj*MAX_FIELD_LEN,
                                tempFieldName,tempFieldType,tempFieldLength)
        self.fileObj.seek(0)
        self.fileObj.write(buf)
        self.fileObj.flush()

    # to delete the schema of a table from the schema file
    # input
    #       table_name: the table to be deleted
    # output
    #       True or False
# 修改delete_table_schema：Py3兼容list(zip)/list(map) + 更新metaHead
    def delete_table_schema(self, table_name):
        # 删除所有匹配的表名条目（处理重复情况）
        key = table_name.strip()
        self.headObj.tableNames = [t for t in self.headObj.tableNames if t[0].strip() != key]
        self.headObj.tableFields.pop(key, None)
        self.headObj.lenOfTableNum = len(self.headObj.tableNames)

        if self.headObj.lenOfTableNum > 0: # there is at least one table after the deletion
            name_list = list(map(lambda x: x[0], self.headObj.tableNames))  # :list() compat Py3
            field_num_per_table = list(map(lambda x: x[1], self.headObj.tableNames))  # :list() compat Py3
            table_offset= list(map(lambda x: x[2], self.headObj.tableNames))

            table_offset[0] = BODY_BEGIN_INDEX
            for idx in range(1,len(table_offset)):
                table_offset[idx] = table_offset[idx-1] + field_num_per_table[idx-1]*MAX_FIELD_LEN

            self.headObj.tableNames=list(zip(name_list,field_num_per_table,table_offset))  # :list(zip) compat Py3
            self.headObj.offsetOfBody=self.headObj.tableNames[-1][2]+self.headObj.tableNames[-1][1]*MAX_FIELD_LEN
            self.WriteBuff()

        else:# there is no table after the deletion
            print (False)
            self.headObj.offsetOfBody = BODY_BEGIN_INDEX
            self.headObj.isStored = False
            self._update_metahead()  # :update metahead when no tables remain
        return True

    # to return the list of all the table names
    # input
    # output
    #       table_name_list: the returned list of table names
    def get_table_name_list(self):
        return map(lambda x:x[0],self.headObj.tableNames)
