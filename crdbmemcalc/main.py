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
Main module implementation.
"""
import sys
import json
import pkg_resources

import click
from jsonschema import validate

from crdbmemcalc.spec import Spec
from crdbmemcalc.redis import Process, RedisConfig, CRDBConfig
from crdbmemcalc.runner import Report, DatasetRunner

@click.command()
@click.option('--specfile', '-s', required=True, type=click.File(),
              help='Memory calculator test spec file.')
@click.option('--redis-executable', required=False,
              default='/opt/redislabs/bin/redis-server-5.0')
@click.option('--crdt-module', required=False,
              default='/opt/redislabs/lib/redis/5.0/crdt.so')
@click.option('--key-factor', required=False, type=int, default=100,
              help='Factor to apply on number of keys')

def cli(specfile, redis_executable, crdt_module, key_factor):
    """
    Run memory calculation to compare a Redis dataset with an equivalent
    CRDB dataset.
    """

    schema_file = pkg_resources.resource_filename(
        'crdbmemcalc', 'schema/testspec_schema.json')
    try:
        schema = json.load(open(schema_file))
    except Exception as err:
        click.echo('Error: failed to load schema: {}: {}'.format(
            schema_file, err))
        sys.exit(1)

    try:
        spec_data = json.load(specfile)
    except Exception as err:
        click.echo('Error: failed to load specfile: {}'.format(err))

    try:
        validate(spec_data, schema)
    except Exception as err:
        click.echo('Error: invalid testspec: {}'.format(err))
        sys.exit(1)

    spec = Spec.from_json(spec_data)
    report = Report()

    configs = [
        RedisConfig('Redis', executable=redis_executable),
        CRDBConfig('CRDB', executable=redis_executable,
                   crdtmodule=crdt_module)
    ]

    for dataset in spec.datasets:
        DatasetRunner(dataset, configs, key_factor).run(report)
    click.echo(report.generate())
