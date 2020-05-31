# Copyright (C) 2020 Redis Labs Ltd.

# This file is part of crdbmemcalc.

# crdbmemcalc is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

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

    @classmethod
    def from_redis(cls, conn, name):
        return cls(name=name, value=conn.config_get(name).get(name))

class RedisConfig(object):
    SOCKET_PATH = '/tmp/crdbmemcalc_redis.sock'

    def __init__(self, name, executable):
        self._name = name
        self.executable = executable
        self.version = None

    def get_conn_info(self):
        return {'unix_socket_path': self.SOCKET_PATH}

    def set_version(self, version):
        self.version = version

    def get_args(self):
        return [self.executable,
                '--unixsocket', self.SOCKET_PATH]

    @property
    def name(self):
        if not self.version:
            return self._name
        return '{}-{}'.format(self._name, self.version)

class CRDBConfig(RedisConfig):
    def __init__(self, name, executable, crdtmodule):
        super(CRDBConfig, self).__init__(name, executable)
        self.crdtmodule = crdtmodule

    def get_args(self):
        return [self.executable,
                '--unixsocket', self.SOCKET_PATH,
                '--loadmodule', self.crdtmodule,
                'replica-id=1',
                'shard-id=1',
                'replicas=1:',
                'slots=16384:0-16383',
                'protocol-version=1',
                'featureset-version=1']

class Process(object):
    def __init__(self, config):
        self.config = config
        self.process = None
        self.conn = None
        self.initial_mem = None

    def start(self):
        self.process = subprocess.Popen(
            stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
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

    def configure(self, config_params):
        conn = self.get_conn()
        for param in config_params:
            conn.config_set(param.name, param.value)

    def get_active_config(self):
        PARAMS = [
            'hash-max-ziplist-entries',
            'hash-max-ziplist-value',
            'hash-max-ziplist-value',
            'list-compress-depth',
            'set-max-intset-entries',
            'zset-max-ziplist-entries',
            'zset-max-ziplist-value'
        ]

        return [ConfigParam.from_redis(self.get_conn(), name)
                for name in PARAMS]

    def stop(self):
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None

    def __del__(self):
        self.stop()
