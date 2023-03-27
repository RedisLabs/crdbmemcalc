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

from setuptools import setup, find_packages
setup(
    name='crdbmemcalc',
    version='1.0.0',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'crdbmemcalc': ['schema/testspec_schema.json']
    },
    install_requires=[
        'jsonschema==2.6.0',
        'click==7.0',
        'humanize==0.5.1',
        'redis==4.5.3',
        'tabulate==0.8.2'
    ],
    entry_points='''
        [console_scripts]
        crdbmemcalc=crdbmemcalc.main:cli
    '''
)

