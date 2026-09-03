import struct
import os
import datetime

# WAL日志记录格式常量定义：日志类型、记录结构、文件路径

# Log record format (560 bytes total):
#   log_type       int (4 bytes)   0=开始事务, 1=插入操作, 2=更新操作, 3=提交事务, 4=中止事务
#   transaction_id int (4 bytes)
#   table_name     char[20] (20 bytes)
#   before_image   char[256] (256 bytes)
#   after_image    char[256] (256 bytes)
#   timestamp      char[20] (20 bytes)

LOG_TYPE_BEGIN = 0
LOG_TYPE_INSERT = 1
LOG_TYPE_UPDATE = 2
LOG_TYPE_COMMIT = 3
LOG_TYPE_ABORT = 4

LOG_RECORD_SIZE = 4 + 4 + 20 + 256 + 256 + 20  # 560字节

LOG_FILE = 'wal.log'


# WAL辅助函数：记录的序列化与反序列化
def serialize_record(record):
    """
    Serialize a record tuple to a fixed-width string for WAL logging.
    Input:
        record: tuple of field values (bytes, int, str, etc.)
    Output:
        str of exactly 256 bytes (space-padded)
    """
    parts = []
    for val in record:
        if isinstance(val, bytes):
            parts.append(val.decode('utf-8').strip())
        else:
            parts.append(str(val))
    result = '|'.join(parts)
    if len(result) > 256:
        result = result[:256]
    else:
        result = result + ' ' * (256 - len(result))
    return result


def deserialize_record(data):
    """
    Deserialize a 256-byte string back to a list of field values.
    Input:
        data: str, space-padded serialized record
    Output:
        list of str field values (stripped)
    """
    stripped = data.strip()
    if not stripped:
        return []
    return [v.strip() for v in stripped.split('|')]


def serialize_table_name(name):
    """
    Serialize a table name to exactly 20 bytes.
    Input:
        name: str or bytes, the table name
    Output:
        str of exactly 20 bytes (space-padded)
    """
    if isinstance(name, bytes):
        name = name.decode('utf-8').strip()
    name = str(name).strip()
    if len(name) > 20:
        name = name[:20]
    else:
        name = name + ' ' * (20 - len(name))
    return name


def make_timestamp():
    """Return a 20-byte timestamp string."""
    ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if len(ts) < 20:
        ts = ts + ' ' * (20 - len(ts))
    return ts[:20]


# 事务管理器类：实现WAL预写日志，支持事务的提交、中止与崩溃恢复
class TransactionManager(object):
    """
    Manages transaction durability via Write-Ahead Logging (WAL).
    Implements Commit Rule (after-image to disk before commit) and
    WAL Rule (before-image to log before writing after-image to DB).
    """

# 构造函数：初始化事务管理器，打开/创建wal.log，加载已提交事务ID
    def __init__(self):
        """
        Initialize the transaction manager.
        Opens/creates wal.log and loads committed transaction IDs.
        """
        self.active_transactions = {}
        self.committed_transactions = set()
        self._next_txn_id = 1

        if os.path.exists(LOG_FILE):
            self._load_committed()
        else:
            open(LOG_FILE, 'wb+').close()

# 开始新事务：分配事务ID，注册活动事务，写入BEGIN日志
    def begin_transaction(self):
        """
        Start a new transaction.
        Input: none
        Output: int, the new transaction ID
        Algorithm:
            1. Allocate next transaction ID.
            2. Register in active_transactions with status='active'.
            3. Write BEGIN log record to wal.log.
        """
        txn_id = self._next_txn_id
        self._next_txn_id += 1
        self.active_transactions[txn_id] = {'status': 'active', 'operations': []}
        self._write_log(LOG_TYPE_BEGIN, txn_id, '', '', '')
        return txn_id

# 记录INSERT操作到WAL日志：前映像为空（插入前没有旧数据）
    def log_insert(self, txn_id, table_name, after_image):
        """
        Record an INSERT operation in the WAL log.
        Before image is empty (noting existed before).
        Input:
            txn_id: int, the transaction ID
            table_name: str or bytes, the affected table
            after_image: str, the serialized new record
        """
        if txn_id not in self.active_transactions:
            return
        self.active_transactions[txn_id]['operations'].append(
            ('INSERT', table_name, '', after_image))
        self._write_log(LOG_TYPE_INSERT, txn_id, table_name, '', after_image)

# 记录UPDATE操作到WAL日志：遵循WAL规则，前映像先于后映像写入日志
    def log_update(self, txn_id, table_name, before_image, after_image):
        """
        Record an UPDATE operation in the WAL log.
        WAL Rule: before_image is written to log BEFORE after_image goes to DB.
        Input:
            txn_id: int, the transaction ID
            table_name: str or bytes, the affected table
            before_image: str, serialized old record
            after_image: str, serialized new record
        """
        if txn_id not in self.active_transactions:
            return
        self.active_transactions[txn_id]['operations'].append(
            ('UPDATE', table_name, before_image, after_image))
        self._write_log(LOG_TYPE_UPDATE, txn_id, table_name,
                        before_image, after_image)

# 提交事务：写入COMMIT日志，移入已提交集，fsync确保持久化
    def commit(self, txn_id):
        """
        Commit a transaction: write COMMIT log, move to committed set, fsync.
        Commit Rule: after-image already in .dat file; COMMIT log makes it durable.
        Input:
            txn_id: int, the transaction ID to commit
        Output: True on success
        """
        if txn_id not in self.active_transactions:
            return False
        self._write_log(LOG_TYPE_COMMIT, txn_id, '', '', '')
        self.committed_transactions.add(txn_id)
        del self.active_transactions[txn_id]
        self._fsync()
        return True

# 中止事务：写入ABORT日志，实际UNDO操作在recover()中处理
    def abort(self, txn_id):
        """
        Abort (rollback) a transaction.
        Writes ABORT log. The actual UNDO is handled during recover().
        Input:
            txn_id: int, the transaction ID to abort
        """
        if txn_id not in self.active_transactions:
            return False
        self._write_log(LOG_TYPE_ABORT, txn_id, '', '', '')
        del self.active_transactions[txn_id]
        self._fsync()
        return True

# 崩溃恢复：重放WAL日志，已提交事务REDO，未提交事务UNDO
    def recover(self):
        """
        Crash recovery: replay the WAL log.
        - REDO: re-apply all operations from committed transactions.
        - UNDO: skip operations from uncommitted/aborted transactions.
        Input: none
        Output:
            list of (txn_id, action) tuples describing recovery actions taken
        Algorithm:
            1. Read wal.log from beginning.
            2. Track which transactions committed (COMMIT record found).
            3. Track which transactions aborted (ABORT record found).
            4. Replay: for each INSERT/UPDATE record:
               - If the transaction committed: REDO the operation
                 (ensure the after-image is in the .dat file).
               - If the transaction did NOT commit: UNDO
                 (ensure the before-image is restored).
            5. Return the list of recovery actions.
        """
        actions = []
        if not os.path.exists(LOG_FILE):
            return actions

        # First pass: determine transaction outcomes
        committed = set()
        aborted = set()
        all_records = []

        with open(LOG_FILE, 'rb') as f:
            while True:
                buf = f.read(LOG_RECORD_SIZE)
                if len(buf) < LOG_RECORD_SIZE:
                    break
                log_type, txn_id, table_name, before_img, after_img, ts = \
                    struct.unpack_from('!ii20s256s256s20s', buf, 0)
                table_name = table_name.decode('utf-8').strip()
                before_img = before_img.decode('utf-8')
                after_img = after_img.decode('utf-8')
                ts = ts.decode('utf-8').strip()

                rec = (log_type, txn_id, table_name, before_img, after_img, ts)
                all_records.append(rec)

                if log_type == LOG_TYPE_COMMIT:
                    committed.add(txn_id)
                elif log_type == LOG_TYPE_ABORT:
                    aborted.add(txn_id)

        # Second pass: REDO / UNDO
        for log_type, txn_id, table_name, before_img, after_img, ts in all_records:
            if log_type == LOG_TYPE_INSERT:
                if txn_id in committed and txn_id not in aborted:
                    # REDO: ensure after-image is written
                    actions.append((txn_id, 'REDO INSERT into ' + table_name))
                    self._redo_insert(table_name, after_img)
                elif txn_id not in committed:
                    # UNDO: remove the after-image if it was written
                    actions.append((txn_id, 'UNDO INSERT from ' + table_name))
                    self._undo_insert(table_name, after_img)

            elif log_type == LOG_TYPE_UPDATE:
                if txn_id in committed and txn_id not in aborted:
                    # REDO: ensure after-image is applied
                    actions.append((txn_id, 'REDO UPDATE on ' + table_name))
                    self._redo_update(table_name, before_img, after_img)
                elif txn_id not in committed:
                    # UNDO: restore before-image
                    actions.append((txn_id, 'UNDO UPDATE on ' + table_name))
                    self._undo_update(table_name, before_img, after_img)

        return actions

# REDO/UNDO内部辅助方法：实现崩溃恢复中的重做与撤销操作
    def _redo_insert(self, table_name, after_image):
        """
        REDO an INSERT: idempotently write the after-image record to .dat.
        Checks if record already exists before inserting.
        """
        try:
            import storage_db
            vals = deserialize_record(after_image)
            if not vals:
                return
            tn = table_name.encode('utf-8') if isinstance(table_name, str) else table_name
            sobj = storage_db.Storage(tn)
            # Check for duplicate
            exists = False
            for rec in sobj.getRecord():
                rec_vals = []
                for v in rec:
                    if isinstance(v, bytes):
                        rec_vals.append(v.decode('utf-8').strip())
                    else:
                        rec_vals.append(str(v))
                if rec_vals == [str(v) for v in vals]:
                    exists = True
                    break
            if not exists:
                sobj.insert_record(vals)
            del sobj
        except Exception as e:
            print('REDO INSERT error: ' + str(e))

    def _undo_insert(self, table_name, after_image):
        """
        UNDO an INSERT: delete the record matching the after-image.
        Gracefully handles case where record was never written.
        """
        try:
            import storage_db
            tn = table_name.encode('utf-8') if isinstance(table_name, str) else table_name
            sobj = storage_db.Storage(tn)
            vals = deserialize_record(after_image)
            if vals and sobj.field_name_list:
                cond_field = sobj.field_name_list[0][0]
                if isinstance(cond_field, bytes):
                    cond_field = cond_field.decode('utf-8').strip()
                # Try to delete — may fail if record was never written (graceful)
                try:
                    sobj.delete_record(cond_field, vals[0])
                except:
                    pass  # Record may not exist, that's fine for UNDO
                del sobj
        except Exception as e:
            print('UNDO INSERT error: ' + str(e))

    def _redo_update(self, table_name, before_image, after_image):
        """REDO an UPDATE: apply the after-image."""
        try:
            import storage_db
            tn = table_name.encode('utf-8') if isinstance(table_name, str) else table_name
            sobj = storage_db.Storage(tn)
            before_vals = deserialize_record(before_image)
            after_vals = deserialize_record(after_image)
            if before_vals and after_vals and len(before_vals) > 0:
                flist = sobj.field_name_list
                changed = -1
                for i in range(min(len(before_vals), len(after_vals))):
                    if before_vals[i] != after_vals[i]:
                        changed = i
                        break
                if changed >= 0 and flist:
                    fn = flist[changed][0]
                    if isinstance(fn, bytes):
                        fn = fn.decode('utf-8').strip()
                    first_fn = flist[0][0]
                    if isinstance(first_fn, bytes):
                        first_fn = first_fn.decode('utf-8').strip()
                    sobj.update_record(first_fn, before_vals[0], fn, after_vals[changed])
                del sobj
        except Exception as e:
            print('REDO UPDATE error: ' + str(e))

    def _undo_update(self, table_name, before_image, after_image):
        """UNDO an UPDATE: restore the before-image."""
        try:
            import storage_db
            tn = table_name.encode('utf-8') if isinstance(table_name, str) else table_name
            sobj = storage_db.Storage(tn)
            before_vals = deserialize_record(before_image)
            after_vals = deserialize_record(after_image)
            if before_vals and after_vals and len(before_vals) > 0:
                flist = sobj.field_name_list
                changed = -1
                for i in range(min(len(before_vals), len(after_vals))):
                    if before_vals[i] != after_vals[i]:
                        changed = i
                        break
                if changed >= 0 and flist:
                    fn = flist[changed][0]
                    if isinstance(fn, bytes):
                        fn = fn.decode('utf-8').strip()
                    first_fn = flist[0][0]
                    if isinstance(first_fn, bytes):
                        first_fn = first_fn.decode('utf-8').strip()
                    sobj.update_record(first_fn, after_vals[0], fn, before_vals[changed])
                del sobj
        except Exception as e:
            print('UNDO UPDATE error: ' + str(e))

# 写入日志记录：将事务操作序列化为560字节固定格式写入wal.log
    def _write_log(self, log_type, txn_id, table_name, before_image, after_image):
        """
        Write a log record to wal.log.
        Input:
            log_type: int (0-4)
            txn_id: int
            table_name: str
            before_image: str (256 bytes max)
            after_image: str (256 bytes max)
        """
        tn = serialize_table_name(table_name)
        bi = before_image if isinstance(before_image, str) else str(before_image)
        ai = after_image if isinstance(after_image, str) else str(after_image)
        bi = bi[:256].ljust(256)
        ai = ai[:256].ljust(256)
        ts = make_timestamp()

        buf = struct.pack('!ii20s256s256s20s',
                          log_type, txn_id,
                          tn.encode('utf-8'),
                          bi.encode('utf-8'),
                          ai.encode('utf-8'),
                          ts.encode('utf-8'))

        with open(LOG_FILE, 'ab') as f:
            f.write(buf)
            f.flush()

# 加载已提交事务ID集合：从wal.log中扫描所有COMMIT记录，确定下一个可用事务ID
    def _load_committed(self):
        """
        Load the set of committed transaction IDs from wal.log.
        Also determine the next available transaction ID.
        """
        if not os.path.exists(LOG_FILE):
            return
        max_txn = 0
        with open(LOG_FILE, 'rb') as f:
            while True:
                buf = f.read(LOG_RECORD_SIZE)
                if len(buf) < LOG_RECORD_SIZE:
                    break
                log_type, txn_id = struct.unpack_from('!ii', buf, 0)
                max_txn = max(max_txn, txn_id)
                if log_type == LOG_TYPE_COMMIT:
                    self.committed_transactions.add(txn_id)
        self._next_txn_id = max_txn + 1

# 强制刷盘：调用os.fsync确保WAL日志写入物理磁盘
    def _fsync(self):
        """Force WAL log to disk (fsync)."""
        try:
            with open(LOG_FILE, 'rb+') as f:
                os.fsync(f.fileno())
        except:
            pass

# 查看日志：以可读格式返回wal.log中的所有日志记录
    def view_log(self):
        """
        Read and return all log records in human-readable format.
        Input: none
        Output: list of dicts, each describing a log record
        """
        records = []
        if not os.path.exists(LOG_FILE):
            return records
        type_names = {0: 'BEGIN', 1: 'INSERT', 2: 'UPDATE', 3: 'COMMIT', 4: 'ABORT'}
        with open(LOG_FILE, 'rb') as f:
            while True:
                buf = f.read(LOG_RECORD_SIZE)
                if len(buf) < LOG_RECORD_SIZE:
                    break
                log_type, txn_id, table_name, before_img, after_img, ts = \
                    struct.unpack_from('!ii20s256s256s20s', buf, 0)
                records.append({
                    'type': type_names.get(log_type, 'UNKNOWN'),
                    'txn_id': txn_id,
                    'table': table_name.decode('utf-8').strip(),
                    'before': before_img.decode('utf-8').strip()[:60],
                    'after': after_img.decode('utf-8').strip()[:60],
                    'timestamp': ts.decode('utf-8').strip(),
                })
        return records


