# crdbmemcalc

This is a tool that makes it easier to calculate the Redis Enterprise
Active-Active (CRDT) overhead for a specified dataset.

Datasets are specified using a custom JSON-based spec file which describes
various aspects of the dataset, such as:

* Types of keys
* Length of key name
* Length of values
* Similar attributes of sub-elements (e.g. hash fields, list/set elements,
  etc.)

The tool then spins up a Redis process, populates it with the synthetic dataset
and produces a report comparing Redis and Redis CRDT memory usage.

## Getting Started

As the `crdbmemcalc` tool requires access to `redis-server` and `crdt.so`
binaries, it is best to deploy it on a test Redis Enterprise cluster node.

First, clone the repository and install it, run the following commands:

    # Clone
    git clone https://github.com/redislabs/crdbmemcalc
    cd crdbmemcalc
    python setup.py install

You can confirm the installation is successful by running:

    crdbmemcalc --help

Next, you can run `crdbmemcalc` using the default sample spec file provided:

    crdbmemcalc -s testspec.json

## What is reported?

The reports includes a section for every dataset described in the specfile. For
example:

```
DATASET CONFIGURATION
 -- Sorted Sets: large sorted sets, short elements

Keys:
Key Type             : sorted_set
Length               : 20
# Of Elements        : 500
Element Length       : 20


Redis Configuration:
                          (Configured)      CRDB-5.0.9 (Actual)    Redis-5.0.9 (Actual)
------------------------  --------------  ---------------------  ----------------------
set-max-intset-entries                                      512                     512
list-compress-depth                                           0                       0
zset-max-ziplist-value                                       64                      64
hash-max-ziplist-value                                       64                      64
hash-max-ziplist-entries                                    512                     512
zset-max-ziplist-entries                                    128                     128
```

The section begins with a description of the keys that make up the dataset, as
specified in the spec file.

Next, it describes Redis configuration parameters that may affect the dataset in
memory.

At the bottom of the report you can find the memory used by each of the datasets
in Redis and Redis CRDT:

```
                                                  CRDB-5.0.9    Redis-5.0.9      %
----------------------------------------------  ------------  -------------  -----
Hashes: large hashes, short keys and values          4111480        2465024    +66
Lists: long lists, short elements                   13661024        1144224  +1093
Lists: short lists, short elements                    605024          65824   +819
Sets: large sets, short elements                     4435424        2826624    +56
Sets: small sets, short elements                      224224         151424    +48
Sorted Sets: large sorted sets, short elements       8797816        5248768    +67
Sorted Sets: small sorted sets, short elements        143480          58624   +144
Strings: short keys and values                         21880          11424    +91
Strings: short keys, 1K values                        145880         135424     +7
```

## Creating a spec file

The spec file is a JSON document that describes datasets that are generated and
tested.

The `datasets` field contains an array of dataset objects, each identified by a
name and a list of keys. For example:

```json
{
    "datasets": [
        { 
            "name": "Strings: short keys and values",
            "keys": [ ... ],
        },
        { 
            "name": "Strings: short keys, 1K values",
            "keys": [ ... ],
        }
    ]
}
```

The `keys` dataset field describes a list of dataset keys. Each dataset key is
described by a name, a key name length, type and value. It is possible to create
datasets with different key specifications. For example:

```json
        { 
            "name": "Sets: small sets, short elements",
            "keys": [
              {
                "length": 20,
                "value": {
                    "type": "set",
                    "elements_num": 20,
                    "element_length": 20
                }
              }
          ]
        }
```

Each `dataset` object may also contain a `redis_config_params` object which
includes specific Redis configuration parameters to apply.

