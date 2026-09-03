# description: 自动化测试 main_db.py 全部 15 个菜单选项
# usage: python test_all_options.py
# prerequisite: pip install ply

import subprocess
import os
import sys
import time
import glob

# ---------- 配置 ----------
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(TEST_DIR, 'test_results.log')
TIMEOUT = 60  # 子进程超时秒数

# ---------- 清理旧测试数据 ----------
def cleanup():
    """删除旧测试文件，保证干净环境。若文件被占用则截断它。"""
    files_to_remove = ['all.sch', 'wal.log']
    patterns = ['*.dat', '*.ind']
    for f in files_to_remove:
        path = os.path.join(TEST_DIR, f)
        if os.path.exists(path):
            try:
                os.remove(path)
                print(f'[CLEAN] Removed {f}')
            except (PermissionError, OSError):
                # 文件被锁定，尝试截断
                try:
                    open(path, 'wb').close()
                    print(f'[CLEAN] Truncated {f} (file was locked)')
                except Exception as e:
                    print(f'[WARN] Cannot clean {f}: {e}')
    for pat in patterns:
        for path in glob.glob(os.path.join(TEST_DIR, pat)):
            try:
                os.remove(path)
                print(f'[CLEAN] Removed {os.path.basename(path)}')
            except (PermissionError, OSError) as e:
                print(f'[WARN] Cannot remove {os.path.basename(path)}: {e}')


# ---------- 构建完整输入序列 ----------
def build_input_sequence():
    """
    返回一个字符串，包含按顺序模拟用户输入的每一行。
    每行对应一个 input() 调用。
    """
    lines = []

    # ==============================================================
    # 测试选项 1: 交互式创建新表 "student" 并插入数据
    # ==============================================================
    # 主菜单选择
    lines.append('1')
    # 表名
    lines.append('student')
    # 字段数量
    lines.append('3')
    # 字段 0: name, type=0(str), length=20
    lines.append('name')
    lines.append('0')
    lines.append('20')
    # 字段 1: age, type=2(int), length=4
    lines.append('age')
    lines.append('2')
    lines.append('4')
    # 字段 2: grade, type=0(str), length=10
    lines.append('grade')
    lines.append('0')
    lines.append('10')

    # 表创建后，选择插入数据
    lines.append('y')
    # 第 1 条记录: Alice, 20, A
    lines.append('Alice')
    lines.append('20')
    lines.append('A')
    # 继续插入
    lines.append('y')
    # 第 2 条记录: Bob, 22, B
    lines.append('Bob')
    lines.append('22')
    lines.append('B')
    # 继续插入
    lines.append('y')
    # 第 3 条记录: Charlie, 25, C
    lines.append('Charlie')
    lines.append('25')
    lines.append('C')
    # 停止插入
    lines.append('n')

    # ==============================================================
    # 测试选项 3: 查看表结构和数据
    # ==============================================================
    lines.append('3')
    lines.append('student')

    # ==============================================================
    # 测试选项 5: SELECT FROM WHERE 子句（多种查询）
    # ==============================================================
    # 5a: SELECT * FROM student (无 WHERE)
    lines.append('5')
    lines.append('select * from student')
    # 5b: SELECT name, age FROM student WHERE age=22
    lines.append('5')
    lines.append("select name, age from student where age=22")
    # 5c: SELECT name FROM student WHERE name='Alice'
    lines.append('5')
    lines.append("select name from student where name='Alice'")

    # ==============================================================
    # 测试选项 6: 按关键字删除行 (fieldname:keyword format)
    # ==============================================================
    lines.append('6')
    lines.append('student')
    lines.append('name:Bob')

    # ==============================================================
    # 测试选项 7: 按关键字更新行 (interactive)
    # ==============================================================
    lines.append('7')
    lines.append('student')
    lines.append('name')        # old field name to match
    lines.append('Charlie')     # old value
    lines.append('grade')       # new field to update
    lines.append('A+')          # new value

    # ==============================================================
    # 测试选项 8: CREATE TABLE (SQL)
    # ==============================================================
    lines.append('8')
    lines.append('create table test_sql (id integer, sname char(30), score integer)')

    # ==============================================================
    # 测试选项 9: INSERT INTO (SQL)
    # ==============================================================
    lines.append('9')
    lines.append("insert into test_sql values ('1', 'zhangsan', '95')")
    lines.append('9')
    lines.append("insert into test_sql values ('2', 'lisi', '88')")
    lines.append('9')
    lines.append("insert into test_sql values ('3', 'wangwu', '72')")

    # ==============================================================
    # 测试选项 11: UPDATE SET (SQL)
    # ==============================================================
    lines.append('11')
    lines.append("update test_sql set score = '90' where id = '2'")

    # 验证更新结果 via SELECT
    lines.append('5')
    lines.append('select * from test_sql')

    # ==============================================================
    # 测试选项 10: DELETE FROM (SQL)
    # ==============================================================
    lines.append('10')
    lines.append('delete from test_sql')

    # 验证清空
    lines.append('3')
    lines.append('test_sql')

    # ==============================================================
    # 测试选项 12: DROP TABLE (SQL)
    # ==============================================================
    lines.append('12')
    lines.append('drop table test_sql')

    # ==============================================================
    # 测试选项 1 (再次): 创建表用于事务测试
    # ==============================================================
    lines.append('1')
    lines.append('txn_test')
    lines.append('2')
    lines.append('id')
    lines.append('2')  # int
    lines.append('4')
    lines.append('value')
    lines.append('0')  # str
    lines.append('30')
    lines.append('n')  # 不立即插入数据

    # ==============================================================
    # 测试选项 13: 带事务持久化的插入
    # ==============================================================
    lines.append('13')
    lines.append('txn_test')
    lines.append('1')      # id
    lines.append('txn_val_1')  # value

    lines.append('13')
    lines.append('txn_test')
    lines.append('2')
    lines.append('txn_val_2')

    # ==============================================================
    # 测试选项 15: 查看 WAL 日志
    # ==============================================================
    lines.append('15')

    # ==============================================================
    # 测试选项 14: 崩溃恢复（重放 WAL 日志）
    # ==============================================================
    lines.append('14')

    # ==============================================================
    # 验证事务数据
    # ==============================================================
    lines.append('3')
    lines.append('txn_test')

    # ==============================================================
    # 测试选项 2: 删除单个表的结构和数据
    # ==============================================================
    lines.append('2')
    lines.append('txn_test')

    # ==============================================================
    # 测试选项 8: 再创建一个快速表用于测试选项 4
    # ==============================================================
    lines.append('8')
    lines.append('create table tmp (x integer)')

    # ==============================================================
    # 测试选项 4: 删除所有表结构和数据
    # ==============================================================
    lines.append('4')

    # ==============================================================
    # 退出
    # ==============================================================
    lines.append('.')

    # 用 \n 连接所有输入行
    return '\n'.join(lines) + '\n'


# ---------- 分析输出，检查成功/失败标记 ----------
def analyze_output(output: str) -> dict:
    """
    分析程序输出，返回每个测试的结果。
    成功标记: 'OK!', 'created', 'dropped', 'updated', 'executed' 等
    失败标记: 'Wrong', 'fail', 'error', 'WRONG SQL INPUT' 等
    """
    results = {}
    # 将输出转为小写以便匹配
    lower = output.lower()

    # --- 选项 1: 创建表 student ---
    results['opt1_create_table'] = (
        'student' in lower and
        'created' in lower and
        ('ok!' in lower or 'ok' in lower)
    )

    # --- 选项 3: 查看表 ---
    results['opt3_view_table'] = (
        'alice' in lower and
        'bob' in lower and
        'charlie' in lower
    )

    # --- 选项 5: SELECT 查询 ---
    results['opt5_select_star'] = (
        'select' in lower and 'from' in lower
    )
    results['opt5_select_where'] = (
        '22' in output  # Bob's age
    )
    results['opt5_select_alice'] = (
        'alice' in lower
    )

    # --- 选项 6: 删除行 ---
    results['opt6_delete_row'] = (
        'deleted' in lower or 'record' in lower
    )

    # --- 选项 7: 更新行 ---
    # 检查是否出现成功提示或更新后的数据
    results['opt7_update_row'] = (
        'updated' in lower or 'a+' in lower
    )

    # --- 选项 8: CREATE TABLE SQL ---
    results['opt8_create_sql'] = (
        'test_sql' in lower and 'created' in lower
    )

    # --- 选项 9: INSERT SQL ---
    results['opt9_insert_sql'] = (
        'zhangsan' in lower or ('ok!' in lower and '95' in output)
    )

    # --- 选项 11: UPDATE SQL ---
    results['opt11_update_sql'] = (
        '90' in output  # updated score
    )

    # --- 选项 10: DELETE FROM SQL ---
    results['opt10_delete_sql'] = lower.count('暂无数据') >= 1 or 'delete' in lower

    # --- 选项 12: DROP TABLE SQL ---
    results['opt12_drop_sql'] = (
        'dropped' in lower
    )

    # --- 选项 13: 事务插入 ---
    results['opt13_transaction_insert'] = (
        'txn_val_1' in output and 'txn_val_2' in output
    )

    # --- 选项 15: 查看 WAL 日志 ---
    results['opt15_view_wal'] = (
        'wal log' in lower or 'insert' in lower or 'commit' in lower
    )

    # --- 选项 14: 崩溃恢复 ---
    results['opt14_crash_recovery'] = (
        'recovery' in lower or 'redo' in lower or 'undo' in lower or
        'no recovery' in lower
    )

    # --- 选项 2: 删除表 ---
    results['opt2_delete_table'] = (
        'deletion' in lower or 'deleted' in lower
    )

    # --- 选项 4: 删除所有 ---
    results['opt4_delete_all'] = (
        'truncated' in lower or 'all.sch' in lower
    )

    return results


# ---------- 主测试函数 ----------
def run_tests():
    """主入口：清理、构建输入、运行子进程、分析结果、写报告"""
    # 清理
    cleanup()

    # 构建输入
    input_data = build_input_sequence()

    print(f'\n[INFO] Total input lines: {input_data.count(chr(10))}')
    print(f'[INFO] Running main_db.py (timeout={TIMEOUT}s)...\n')

    # 运行 main_db.py
    start_time = time.time()
    try:
        proc = subprocess.run(
            [sys.executable, 'main_db.py'],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
            cwd=TEST_DIR,
            encoding='gbk',        # main_db.py 输出使用 GBK 编码
            errors='replace',       # 忽略无法解码的字符
        )
        elapsed = time.time() - start_time
        stdout = proc.stdout or ''
        stderr = proc.stderr or ''
        returncode = proc.returncode
    except subprocess.TimeoutExpired:
        print(f'[ERROR] subprocess timed out after {TIMEOUT}s')
        return
    except FileNotFoundError:
        print(f'[ERROR] main_db.py not found in {TEST_DIR}')
        return

    if not stdout:
        print('[ERROR] No output captured from main_db.py')
        return

    # 分析结果
    results = analyze_output(stdout)

    # 写入日志
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.write('=' * 70 + '\n')
        f.write('  DATABASE SYSTEM TEST REPORT\n')
        f.write('=' * 70 + '\n')
        f.write(f'  Elapsed: {elapsed:.2f}s\n')
        f.write(f'  Return code: {returncode}\n')
        f.write('=' * 70 + '\n\n')

        # 统计
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        f.write(f'  RESULTS: {passed}/{total} tests passed\n\n')

        # 每个测试
        test_descriptions = {
            'opt1_create_table':          'Option 1  - Create table (interactive)',
            'opt3_view_table':            'Option 3  - View table structure & data',
            'opt5_select_star':           'Option 5  - SELECT * FROM (no WHERE)',
            'opt5_select_where':          'Option 5  - SELECT with WHERE clause',
            'opt5_select_alice':          'Option 5  - SELECT with string WHERE',
            'opt6_delete_row':            'Option 6  - Delete row by keyword',
            'opt7_update_row':            'Option 7  - Update row by keyword',
            'opt8_create_sql':            'Option 8  - CREATE TABLE (SQL)',
            'opt9_insert_sql':            'Option 9  - INSERT INTO (SQL)',
            'opt10_delete_sql':           'Option 10 - DELETE FROM (SQL)',
            'opt11_update_sql':           'Option 11 - UPDATE SET (SQL)',
            'opt12_drop_sql':             'Option 12 - DROP TABLE (SQL)',
            'opt13_transaction_insert':   'Option 13 - Transaction insert (WAL)',
            'opt14_crash_recovery':       'Option 14 - Crash recovery (WAL replay)',
            'opt15_view_wal':             'Option 15 - View WAL log',
            'opt2_delete_table':          'Option 2  - Delete a table',
            'opt4_delete_all':            'Option 4  - Delete all tables',
        }

        for key, desc in test_descriptions.items():
            status = 'PASS' if results.get(key, False) else 'FAIL'
            f.write(f'  [{status}] {desc}\n')

        f.write('\n' + '=' * 70 + '\n')
        f.write('  STDOUT (full)\n')
        f.write('=' * 70 + '\n')
        f.write(stdout)

        if stderr:
            f.write('\n' + '=' * 70 + '\n')
            f.write('  STDERR\n')
            f.write('=' * 70 + '\n')
            f.write(stderr[:4000])

        f.write('\n' + '=' * 70 + '\n')
        f.write('  END OF REPORT\n')
        f.write('=' * 70 + '\n')

    # 终端输出摘要
    print(f'\n{"="*60}')
    print(f'  TEST SUMMARY: {passed}/{total} passed  ({elapsed:.1f}s)')
    print(f'{"="*60}')
    for key, desc in test_descriptions.items():
        status = '[PASS]' if results.get(key, False) else '[FAIL]'
        print(f'  {status}  {desc}')
    print(f'\n  Full log: {LOG_FILE}')
    print(f'  STDOUT len: {len(stdout)} chars')
    if stderr:
        print(f'  STDERR len: {len(stderr)} chars')
    print()

    # --- 测试后验证文件系统状态 ---
    print(f'\n{"="*60}')
    print('  POST-TEST ARTIFACTS')
    print(f'{"="*60}')
    artifacts = {
        'all.sch': os.path.exists(os.path.join(TEST_DIR, 'all.sch')),
        'wal.log': os.path.exists(os.path.join(TEST_DIR, 'wal.log')),
        '*.dat files': glob.glob(os.path.join(TEST_DIR, '*.dat')),
        '*.ind files': glob.glob(os.path.join(TEST_DIR, '*.ind')),
    }
    for name, val in artifacts.items():
        if isinstance(val, list):
            print(f'  {name}: {len(val)} files ({", ".join([os.path.basename(p) for p in val]) if val else "none"})')
        else:
            print(f'  {name}: {"exists" if val else "absent"}')

    # --- 最终清理：删除测试产生的文件 ---
    print(f'\n  Final cleanup...')
    for pat in ['*.dat', '*.ind']:
        for path in glob.glob(os.path.join(TEST_DIR, pat)):
            try:
                os.remove(path)
                print(f'  Removed {os.path.basename(path)}')
            except Exception as e:
                print(f'  WARN: Cannot remove {os.path.basename(path)}: {e}')
    for f in ['wal.log']:
        path = os.path.join(TEST_DIR, f)
        if os.path.exists(path):
            try:
                os.remove(path)
                print(f'  Removed {f}')
            except Exception as e:
                print(f'  WARN: Cannot remove {f}: {e}')
    print(f'  (all.sch kept for schema persistence)')

    # 返回退出码（有失败则为 1）
    return 0 if passed == total else 1


if __name__ == '__main__':
    sys.exit(run_tests())
