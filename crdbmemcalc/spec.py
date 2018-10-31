"""
Test spec execution implementation.
"""
import random
import string
from abc import abstractmethod

def make_random_string(length):
    return ''.join(random.choice(string.ascii_letters + string.digits)
                   for _ in range(length))

class Value(object):
    @abstractmethod
    def create(self, conn, key):
        pass

    @classmethod
    def from_json(cls, obj):
        return cls(**obj)

class StringValue(Value):
    def __init__(self, length):
        self.length = length

    def create(self, conn, key):
        conn.set(key, make_random_string(self.length))

    def __repr__(self):
        return '<StringValue length={}>'.format(self.length)

class MultiValue(Value):
    def __init__(self, elements_num, element_length):
        self.elements_num = elements_num
        self.element_length = element_length

class SetValue(MultiValue):
    def create(self, conn, key):
        for _ in range(self.elements_num):
            conn.sadd(key, make_random_string(self.element_length))

class SortedSetValue(MultiValue):
    def create(self, conn, key):
        for _ in range(self.elements_num):
            conn.zadd(key, make_random_string(self.element_length))

class ListValue(MultiValue):
    def create(self, conn, key):
        for _ in range(self.elements_num):
            conn.lpush(key, make_random_string(self.element_length))

class HashValue(Value):
    def __init__(self, elements_num, element_key_length, element_length):
        self.elements_num = elements_num
        self.element_key_length = element_key_length
        self.element_length = element_length

    def create(self, conn, key):
        for _ in range(self.elements_num):
            conn.hset(key, make_random_string(self.element_key_length),
                      make_random_string(self.element_length))

VALUE_CLASSES = {
    'string': StringValue,
    'set': SetValue,
    'sorted_set': SortedSetValue,
    'hash': HashValue,
    'list': ListValue
}

def create_value_from_json(obj):
    value_obj = obj.copy()
    value_type = value_obj.pop('type')
    if not value_type in VALUE_CLASSES:
        raise ValueError('Invalid type "{}"'.format(value_type))
    return VALUE_CLASSES[value_type].from_json(value_obj)

class Key(object):
    def __init__(self, name, length, value):
        self.name = name
        self.length = length
        self.value = value

    def create(self, conn):
        key = make_random_string(self.length)
        self.value.create(conn, key)

    @classmethod
    def from_json(cls, obj):
        return cls(name=obj['name'], length=obj['length'],
                   value=create_value_from_json(obj['value']))

    def __repr__(self):
        return '<Key name={} length={} value={}>'.format(
            self.name, self.length, repr(self.value))

class Dataset(object):
    def __init__(self, keys):
        self.keys = keys

    def create(self, conn, key_factor):
        for k in self.keys:
            for _ in range(key_factor):
                k.create(conn)

    @classmethod
    def from_json(cls, obj):
        return cls(keys=[Key.from_json(k) for k in obj['keys']])

    def __repr__(self):
        return '<Dataset keys=[{}]>'.format(
            ','.join([repr(k) for k in self.keys]))


class Spec(object):
    def __init__(self, datasets):
        self.datasets = datasets

    def create(self, conn, key_factor):
        for dataset in self.datasets:
            dataset.create(conn, key_factor)

    @classmethod
    def from_json(cls, obj):
        return cls(datasets=[Dataset.from_json(d) for d in obj['datasets']])
