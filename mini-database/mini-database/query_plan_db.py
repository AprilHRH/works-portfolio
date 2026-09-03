import common_db
import storage_db
import itertools
    

# to import the syntax tree, which is defined in parser_db.py

class parseNode:
    def __init__(self):
        self.sel_list=[]
        self.from_list=[]
        self.where_list=[]

    def get_sel_list(self):
        return self.sel_list

    def get_from_list(self):
        return self.from_list

    def get_where_list(self):
        return self.where_list

    def update_sel_list(self,self_list):
        self.sel_list = self_list

    def update_from_list(self, from_list):
        self.from_list = from_list

    def update_where_list(self,where_list):
        self.where_list = where_list


# Author: Shuting Guo shutingnjupt@gmail.com
# to extract data from gloal variable syn_tree
# output:
#       sel_list
#       from_list
#       where_list
def extract_sfw_data():
    print('extract_sfw_data begins to execute')
# 将 syn_tree 改为直接引用 common_db.global_syn_tree
    if common_db.global_syn_tree is None:
        print ('wrong')
    else:
        #common_db.show(common_db.global_syn_tree)
        PN = parseNode()
        destruct(common_db.global_syn_tree,PN)
        return PN.get_sel_list(),PN.get_from_list(),PN.get_where_list()

# Author: Shuting Guo shutingnjupt@gmail.com
# Query  : SFW
#   SFW  : SELECT SelList FROM FromList WHERE Condition
# SelList: TCNAME COMMA SelList
# SelList: TCNAME
#
# FromList:TCNAME COMMA FromList
# FromList:TCNAME
# Condition: TCNAME EQX CONSTANT

def destruct(nodeobj,PN):
    if isinstance(nodeobj, common_db.Node):  # it is a Node object
        if nodeobj.children:
            if nodeobj.value == 'SelList':
                tmpList=[]
                show(nodeobj,tmpList)
                PN.update_sel_list(tmpList)
            elif nodeobj.value == 'FromList':
                tmpList = []
                show(nodeobj, tmpList)
                PN.update_from_list(tmpList)
            elif nodeobj.value == 'Cond':
                tmpList = []
                show(nodeobj, tmpList)
                PN.update_where_list(tmpList)
            else:
                for i in range(len(nodeobj.children)):
                    destruct(nodeobj.children[i],PN)

def show(nodeobj,tmpList):
    if isinstance(nodeobj,common_db.Node):
        if not nodeobj.children:
            tmpList.append(nodeobj.value)
        else:
            for i in range(len(nodeobj.children)):
                show(nodeobj.children[i],tmpList)
    if isinstance(nodeobj,str):
        tmpList.append(nodeobj)


#input:
#       from_list
#output:
#       a tree
        
def construct_from_node(from_list):
    if from_list:        
        if len(from_list)==1:
            temp_node=common_db.Node(from_list[0],None)
            return common_db.Node('X',[temp_node])
        elif len(from_list)==2:
            temp_node_first=common_db.Node(from_list[0],None)
            temp_node_second=common_db.Node(from_list[1],None)
            
            return common_db.Node('X',[temp_node_first,temp_node_second])       
            
        elif len(from_list)>2:
            
            right_node=common_db.Node(from_list[len(from_list)-1],None)
            
            return common_db.Node('X',[construct_from_node(from_list[0:len(from_list)-1]),right_node])

#input:
#       where_list
#       from_node
#output:
#       a tree
def construct_where_node(from_node,where_list):
    if from_node and len(where_list)>0:
       return common_db.Node('Filter',[from_node],where_list)
    elif from_node and len(where_list)==0:# there is no where clause
        return from_node


#input:
#       sel_list
#       wf_node
#output:
#       a tree
def construct_select_node(wf_node,sel_list):
    if wf_node and len(sel_list)>0:
        return common_db.Node('Proj',[wf_node],sel_list)

# Author: Shuting Guo shutingnjupt@gmail.com
# to execute the query plan and return the result
# input
#       global logical tree

def execute_logical_tree():
    if common_db.global_logical_tree:
        def excute_tree():

            idx = 0
            dict_ = {}

            def show(node_obj, idx, dict_):
                if isinstance(node_obj, common_db.Node):  # it is a Node object
                    dict_.setdefault(idx, [])
                    dict_[idx].append(node_obj.value)
                    if node_obj.var:
                        dict_[idx][-1] = tuple((dict_[idx][-1], node_obj.var))
                    if node_obj.children:
                        for i in range(len(node_obj.children)):
                            show(node_obj.children[i], idx + 1, dict_)

            show(common_db.global_logical_tree, idx, dict_)
            idx = sorted(dict_.keys(), reverse=True)[0]

            def GetFilterParam(tableName_Order, current_field, param):
                # print tableName_Order,current_field
# bytes→str规范化处理，防止bytes类型导致比对失败
                if isinstance(param, bytes):
                    param = param.decode('utf-8').strip()  # bytes解码为str
                if isinstance(param, str):
                    param = param.strip()
                tableName_Order = [tn.decode('utf-8').strip() if isinstance(tn, bytes) else tn for tn in tableName_Order]  # tableName_Order元素bytes转str
                if '.' in param:
                    # 点号表示法：table.field
                    tableName = param.split('.')[0]
                    FieldName = param.split('.')[1]
                    if tableName in tableName_Order:
                        TableIndex = tableName_Order.index(tableName)
                    else:
                        return 0, 0, 0, False
                else:
                    # 无点号：搜索所有表找到第一个匹配的字段
                    FieldName = param
                    found = False
                    for ti in range(len(tableName_Order)):
                        # 规范化该表的字段名列表
                        tmp = []
                        for x in current_field[ti]:
                            fname = x[0]
                            if isinstance(fname, bytes):
                                fname = fname.decode('utf-8').strip()
                            else:
                                fname = str(fname).strip()
                            tmp.append(fname)
                        if FieldName in tmp:
                            TableIndex = ti
                            FieldIndex = tmp.index(FieldName)
                            FieldType = current_field[TableIndex][FieldIndex][1]
                            return TableIndex, FieldIndex, FieldType, True
                    return 0, 0, 0, False
                # 点号表示法：在指定表中查找字段
                FieldName = FieldName.strip() if isinstance(FieldName, str) else FieldName
                tmp = []
                for x in current_field[TableIndex]:
                    fname = x[0]
                    if isinstance(fname, bytes):
                        fname = fname.decode('utf-8').strip()
                    else:
                        fname = str(fname).strip()
                    tmp.append(fname)
                if FieldName in tmp:
                    FieldIndex = tmp.index(FieldName)
                    FieldType = current_field[TableIndex][FieldIndex][1]
                    return TableIndex, FieldIndex, FieldType, True
                else:
                    return 0, 0, 0, False

            current_field = []
            current_list =[]
            #print dict_
            while (idx >= 0):
                if idx == sorted(dict_.keys(), reverse=True)[0]:
                    if len(dict_[idx]) > 1:
                        a_1 = storage_db.Storage(dict_[idx][0])
                        a_2 = storage_db.Storage(dict_[idx][1])
                        current_list = []
                        tableName_Order = [dict_[idx][0], dict_[idx][1]]
# getfilenamelist()改为getFieldList()
                        current_field = [a_1.getFieldList(), a_2.getFieldList()]  # 使用getFieldList()
                        for x in itertools.product(a_1.getRecord(), a_2.getRecord()):
                            current_list.append(list(x))
                    else:
                        a_1 = storage_db.Storage(dict_[idx][0])
                        current_list = a_1.getRecord()

                        tableName_Order = [dict_[idx][0]]
# getfilenamelist()改为getFieldList()
                        current_field = [a_1.getFieldList()]  # 使用getFieldList()
                        #print current_list

                elif 'X' in dict_[idx] and len(dict_[idx]) > 1:
                    a_2 = storage_db.Storage(dict_[idx][1])
                    tableName_Order.append(dict_[idx][1])
# getfilenamelist()改为getFieldList()
                    current_field.append(a_2.getFieldList())  # 使用getFieldList()
                    tmp_List = current_list[:]
                    current_list = []
                    for x in itertools.product(tmp_List, a_2.getRecord()):
                        current_list.append(list((x[0][0], x[0][1], x[1])))

                elif 'X' not in dict_[idx]:
                    if 'Filter' in dict_[idx][0]:
# AND复合条件支持：将FilterChoice按AND标记拆分为多个条件，依次过滤
                        FilterChoice = dict_[idx][0][1]
                        # 拆分AND复合条件
                        if isinstance(FilterChoice, tuple) and 'AND' in FilterChoice:
                            filter_conditions = []
                            current_cond = []
                            for elem in FilterChoice:
                                if elem == 'AND':
                                    if current_cond:
                                        filter_conditions.append(tuple(current_cond))
                                        current_cond = []
                                else:
                                    current_cond.append(elem)
                            if current_cond:
                                filter_conditions.append(tuple(current_cond))
                        else:
                            filter_conditions = [FilterChoice]  # 单条件也用列表统一处理
                        # 对每个条件依次过滤
                        for filter_cond in filter_conditions:
                            TableIndex, FieldIndex, FieldType, isTrue = GetFilterParam(tableName_Order, current_field,
                                                                                       filter_cond[0])
                            if not isTrue:
                                return [], [], False
                            else:
                                if FieldType == 2:
                                    FilterParam = int(filter_cond[2].strip() if isinstance(filter_cond[2], str) else filter_cond[2])
                                elif FieldType == 3:
                                    FilterParam = bool(filter_cond[2].strip() if isinstance(filter_cond[2], str) else filter_cond[2])
                                else:
                                    FilterParam = filter_cond[2].strip() if isinstance(filter_cond[2], str) else filter_cond[2]
                                #print FilterParam
                            tmp_List = current_list[:]
                            current_list = []
                            for tmpRecord in tmp_List:
                                if len(current_field) == 1:
                                    ans = tmpRecord[FieldIndex]
                                else:
                                    ans = tmpRecord[TableIndex][FieldIndex]
                                if FieldType == 0 or FieldType == 1:
# bytes数据规范化处理
                                    if isinstance(ans, bytes):
                                        ans = ans.decode('utf-8').strip()  # bytes解码为str
                                    else:
                                        ans = str(ans).strip()  # 统一str处理
# FilterParam bytes规范化，确保比对正确
                                cmp_param = FilterParam
                                if isinstance(FilterParam, bytes):
                                    cmp_param = FilterParam.decode('utf-8').strip()  # bytes解码比较
                                if cmp_param == ans:
                                    current_list.append(tmpRecord)
# AND复合条件过滤结束

                    if 'Proj' in dict_[idx][0]:
# SELECT * 支持：若投影列表含'*'则展开为所有表的所有字段
                        proj_list = dict_[idx][0][1]
                        if '*' in proj_list:
                            SelIndexList = []
                            for ti, tbl in enumerate(tableName_Order):
                                for fi in range(len(current_field[ti])):
                                    SelIndexList.append((ti, fi))  # 添加全部字段
                        else:
                            SelIndexList = []
                            for i in range(len(proj_list)):
                                TableIndex, FieldIndex, FieldType, isTrue = GetFilterParam(tableName_Order, current_field,
                                                                                           proj_list[i])
                                if not isTrue:
                                    return [], [], False
                                SelIndexList.append((TableIndex, FieldIndex))
# SELECT * 结束
                        tmp_List = current_list[:]
                        current_list = []
                        # print SelIndexList,current_field
                        for tmpRecord in tmp_List:
                            # print tmpRecord
                            if len(current_field) == 1:
                                tmp = []
                                for x in list(map(lambda x: x[1], SelIndexList)):
                                    tmp.append(tmpRecord[x])
                                current_list.append(tmp)
                            else:
                                tmp = []
                                for x in SelIndexList:
                                    tmp.append(tmpRecord[x[0]][x[1]])
                                current_list.append(tmp)
                        outPutField = []
                        for xi in SelIndexList:
# 规范化字段名输出
                            tn = tableName_Order[xi[0]]
                            tn = tn.strip() if isinstance(tn, str) else (tn.decode('utf-8').strip() if isinstance(tn, bytes) else tn)  # bytes/str规范化
                            fn = current_field[xi[0]][xi[1]][0]
                            fn = fn.strip() if isinstance(fn, str) else (fn.decode('utf-8').strip() if isinstance(fn, bytes) else fn)  # bytes/str规范化
                            outPutField.append(tn + '.' + fn)
                        return outPutField, current_list, True
                idx -= 1

        outPutField, current_list, isRight = excute_tree()

        if isRight:
            print (outPutField)
            for record in current_list:
                print (record)
        else:
            print ('WRONG SQL INPUT!')
    else:
        print ('there is no query plan tree for the execution')

# Author: Shuting Guo shutingnjupt@gmail.com
# to construct a logical query plan tree
# output:
#       global_logical_tree
def construct_logical_tree():
# 将 syn_tree 改为直接引用 common_db.global_syn_tree
    if common_db.global_syn_tree:
        sel_list,from_list,where_list=extract_sfw_data()
        sel_list=[i for i in sel_list if i!=',']
        from_list=[i for i in from_list if i!=',']
        where_list=tuple(where_list)
        #print sel_list,from_list,where_list

        from_node = construct_from_node(from_list)
        where_node = construct_where_node(from_node, where_list)
        common_db.global_logical_tree = construct_select_node(where_node, sel_list)

        #if common_db.global_logical_tree:
        #    common_db.show(common_db.global_logical_tree)


    else:
        print ('there is no data in the syntax tree in the construct_logical_tree')


'''
# the following is to test the code
from_list1=['a','b','c','d','e','f','g']
tree_from=construct_from_node(from_list1)
where_list1=[('x.c','=','y.c'),('z','=','w')]
tree_where=construct_where_node(tree_from,where_list1)
sel_list1=['f1','f2']
syn_tree=construct_select_node(tree_where,sel_list1)
print extract_sfw_data()
'''


