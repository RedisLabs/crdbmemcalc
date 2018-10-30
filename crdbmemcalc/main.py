"""
Main module implementation.
"""
import sys
import json
import pkg_resources

import click
from jsonschema import validate

@click.command()
@click.option('--specfile', '-s', required=True, type=file,
              help='Memory calculator test spec file.')
@click.option('--redis-executable', required=False,
              default='/opt/redislabs/bin/redis-server')
@click.option('--crdt-module', required=False,
              default='/opt/redislabs/lib/crdt.so')
def cli(specfile, redis_executable, crdt_module):
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
        testspec = json.load(specfile)
    except Exception as err:
        click.echo('Error: failed to load specfile: {}'.format(err))

    try:
        validate(testspec, schema)
    except Exception as err:
        click.echo('Error: invalid testspec: {}'.format(err))
