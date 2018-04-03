from __future__ import print_function

import json
import time
import sqlite3
import threading
import traceback

import requests

import docker_helper


_database_path = docker_helper.read_configuration(
    'REPLAY_DATABASE', '/var/config/webhooks/replay', 'webhooks-replay.db'
)

_schedule_condition = threading.Condition()
_shutdown = [False]


def initialize():
    _initialize_schema()

    thread = threading.Thread(target=_schedule)
    thread.setDaemon(True)
    thread.start()


def shutdown():
    _shutdown[:] = [True]

    with _schedule_condition:
        _schedule_condition.notify()


def _schedule():
    from server import Server

    # wait for server initialization
    while not Server.http_port:
        time.sleep(1)

    while not _shutdown[0]:
        # wait for the next task or until notified
        with _schedule_condition:
            _schedule_condition.wait(timeout=_until_next_scheduled())

        _next = _next_scheduled()

        if not _next:
            continue

        _id, _path, _method, _headers, _body, _time = _next

        if _time > time.time():
            continue

        print('Replaying request on %s' % _path)

        try:
            url = 'http://localhost:%d%s' % (Server.http_port, _path)
            requests.request(
                method=_method, url=url,
                headers=json.loads(_headers), json=json.loads(_body)
            )

        except Exception:
            traceback.print_exc()

        finally:
            with read_write_db() as db:
                db.execute('DELETE FROM requests WHERE id = :id', {'id': _id})
                db.commit()


def _next_scheduled():
    with read_only_db() as db:
        return db.execute('''
          SELECT id, path, method, headers, body, next
          FROM requests
          ORDER BY next ASC
          LIMIT 1
        ''').fetchone()


def _until_next_scheduled():
    _next = _next_scheduled()
    if _next:
        _, _, _, _, _, scheduled_time = _next
        return max(0.1, scheduled_time - time.time())


def replay(path, method, headers, body, at):
    print('Replay requested on %s' % path)

    headers = {
        key: value for key, value in headers.items()
    }

    with read_write_db() as db:
        db.execute('''
          INSERT INTO requests (path, method, headers, body, next)
          VALUES (:path, :method, :headers, :body, :at)
        ''', {
            'path': path,
            'method': method,
            'headers': json.dumps(headers),
            'body': json.dumps(body),
            'at': at
        })
        db.commit()

    with _schedule_condition:
        _schedule_condition.notify()


class _DatabaseContext(object):
    write_lock = threading.RLock()

    def __init__(self, path, read_only=True):
        self.path = path
        self.read_only = read_only

    def __enter__(self):
        if not self.read_only:
            self.write_lock.acquire()

        try:
            self.connection = sqlite3.connect(self.path)
            return self.connection

        except Exception:
            if not self.read_only:
                self.write_lock.release()

            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.connection.close()

        finally:
            if not self.read_only:
                self.write_lock.release()


def read_only_db(path=_database_path):
    return _DatabaseContext(path, read_only=True)


def read_write_db(path=_database_path):
    return _DatabaseContext(path, read_only=False)


def _initialize_schema():
    with read_write_db() as db:
        cursor = db.cursor()

        cursor.execute('''
          CREATE TABLE IF NOT EXISTS requests (
            id      INTEGER PRIMARY KEY,
            path    TEXT,
            method  TEXT,
            headers TEXT,
            body    TEXT,
            next    TIMESTAMP
          )
        ''')

        cursor.execute('''
          CREATE INDEX IF NOT EXISTS idx_next_date ON requests(next ASC)
        ''')
