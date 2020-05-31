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

from collections import OrderedDict

from click import echo
from tabulate import tabulate

from crdbmemcalc.redis import Process

class Report(object):
    def __init__(self):
        self.results = []

    def add(self, result):
        self.results.append(result)

    def config_names(self):
        return set([r.config.name for r in self.results])

    def dataset_names(self):
        return set([r.dataset.name for r in self.results])

    def results_map(self):
        return {r.dataset.name: {rr.config.name: rr
                                 for rr in self.results
                                 if rr.dataset.name == r.dataset.name}
                for r in self.results}

    def datasets(self):
        return set([r.dataset for r in self.results])

    def generate_mem_summary(self):
        table = []
        for k, v in sorted(self.results_map().iteritems()):
            line = [k] + [v[name].mem_usage for name in self.config_names()]
            min_mem = min([r.mem_usage for r in v.values()])
            max_mem = max([r.mem_usage for r in v.values()])
            line += ['+{}'.format((max_mem - min_mem) * 100 / min_mem)]
            table += [line]
        return tabulate(table, headers=[''] + list(self.config_names()) +
                        ['%'])

    def generate_dataset_config(self, dataset):
        ret = '\nDATASET CONFIGURATION\n -- {}\n\n'.format(dataset.name)
        ret += 'Keys:\n'
        for key in dataset.keys:
            ret += '{}\n'.format(str(key))
        ret += '\nRedis Configuration:\n'
        table = []
        set_params = {param.name: param.value
                      for param in dataset.config_params}
        dataset_results = self.results_map()[dataset.name]
        all_params = set([])
        for result in dataset_results.itervalues():
            for param in result.active_config:
                all_params.add(param)
        for param in all_params:
            line = [param]
            line.append(set_params.get(param, ''))
            for config in self.config_names():
                line.append(dataset_results[config].active_config[param])
            table.append(line)

        ret += tabulate(table, headers=[''] + ['(Configured)'] +
                        ['{} (Actual)'.format(name)
                         for name in self.config_names()])
        ret += '\n'
        return ret

    def generate(self):
        r = ''
        for dataset in self.datasets():
            r += self.generate_dataset_config(dataset)

        r += '\n\nMEMORY USAGE SUMMARY\n'
        r += self.generate_mem_summary()
        r += '\n'

        return r

class RunResult(object):
    def __init__(self, dataset, config, version, mem_usage, active_config):
        self.dataset = dataset
        self.config = config
        self.mem_usage = mem_usage
        self.version = version
        self.active_config = {
            p.name: p.value for p in active_config}

class DatasetRunner(object):
    def __init__(self, dataset, configs, key_factor):
        self.dataset = dataset;
        self.configs = configs
        self.key_factor = key_factor

    def run(self, report):
        echo('** Dataset: {} ...'.format(self.dataset.name), nl=False)
        for config in self.configs:
            echo(' [{}]'.format(config.name), nl=False)

            redis = Process(config)
            redis.start()
            redis.configure(self.dataset.config_params)

            version = redis.get_conn().info().get('redis_version')
            config.set_version(version)

            mem_start = redis.used_memory()
            pipeline = redis.get_conn().pipeline(transaction=False)
            self.dataset.create(pipeline, self.key_factor)
            pipeline.execute()
            mem_end = redis.used_memory()
            active_config = redis.get_active_config()

            redis.stop()
            report.add(RunResult(
                self.dataset, config, version, mem_end - mem_start,
                active_config))
        echo('')

