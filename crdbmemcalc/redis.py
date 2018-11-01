"""
Start and stop the Redis process.
"""

from __future__ import absolute_import
import subprocess
import time
from functools import wraps

import redis

class ConfigParam(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value

    @classmethod
    def from_json(cls, obj):
        return cls(name=obj['name'], value=obj['value'])

class RedisConfig(object):
    SOCKET_PATH = '/tmp/crdbmemcalc_redis.sock'

    def __init__(self, executable):
        self.executable = executable

    def get_conn_info(self):
        return {'unix_socket_path': self.SOCKET_PATH}

    def get_args(self):
        return [self.executable,
                '--unixsocket', self.SOCKET_PATH]

class CRDBConfig(RedisConfig):
    def __init__(self, executable, crdtmodule):
        super(CRDBConfig, self).__init__(executable)
        self.crdtmodule = crdtmodule

    def get_args(self):
        return [self.executable,
                '--unixsocket', self.SOCKET_PATH,
                '--loadmodule', self.crdtmodule,
                'replica_id=1',
                'replicas=1:',
                'slots=16384:0-16383']

class Process(object):
    def __init__(self, config):
        self.config = config
        self.process = None
        self.conn = None
        self.initial_mem = None

    def start(self):
        self.process = subprocess.Popen(
            executable=self.config.executable,
            args=self.config.get_args())
        self.ping()

    def ping(self, retries=20, interval=0.2):
        while retries:
            try:
                return self.get_conn().ping()
            except redis.ConnectionError:
                retries -= 1
                if not retries:
                    raise
                time.sleep(interval)

    def used_memory(self):
        return self.get_conn().info('memory').get('used_memory')

    def get_conn(self, retries=10, interval=0.1):
        if self.conn:
            return self.conn

        while retries:
            try:
                self.conn = redis.Redis(**self.config.get_conn_info())
                self.conn.ping()
                return self.conn
            except redis.ConnectionError:
                retries -= 1
                if retries:
                    time.sleep(interval)
                else:
                    raise

    def stop(self):
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None

    def __del__(self):
        self.stop()
