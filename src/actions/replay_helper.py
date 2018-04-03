import sqlite3
import threading


_write_lock = threading.RLock()


def replay(request):
    pass


def read_only_db(path):
    class ReadOnlyContext(object):
        def __enter__(self):
            self.connection = sqlite3.connect(path)
            return self.connection

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.connection.close()

    return ReadOnlyContext()


def read_write_db(path):
    class ReadWriteContext(object):  # TODO duplication, could merge RO/RW
        def __enter__(self):
            _write_lock.acquire()

            try:
                self.connection = sqlite3.connect(path)
                return self.connection

            except:
                _write_lock.release()
                raise

        def __exit__(self, *args, **kwargs):
            try:
                self.connection.close()

            finally:
                _write_lock.release()

    return ReadWriteContext()

