"""
Start and stop the Redis process.
"""

from __future__ import absolute_import
import subprocess
import time

import redis

class Process(object):
    def __init__(self, executable):
        self.executable = executable
        self.process = None

    def start(self):
        self.process = subprocess.Popen(
            executable=self.executable,
            args=[self.executable,
                  '--unixsocket', '/tmp/redis.sock'])
        time.sleep(0.5)

    def get_conn(self):
        return redis.Redis(unix_socket_path='/tmp/redis.sock')

    def stop(self):
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None

    def __del__(self):
        self.stop()
