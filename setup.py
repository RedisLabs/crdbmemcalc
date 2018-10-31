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
        'redis==2.10.6'
    ],
    entry_points='''
        [console_scripts]
        crdbmemcalc=crdbmemcalc.main:cli
    '''
)

