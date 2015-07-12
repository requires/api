# -*- coding: utf-8 -*-
import sys


def column_length(requirements, title, key):
    l = lambda r: len(key(r))
    if not requirements:
        return len(title)
    return max(len(title), l(max(requirements, key=l)))


def draw(requirements, stream=sys.stdout):
    t_name = 'Package'
    t_specs = 'Requirement'
    t_latest_version = 'Latest'
    t_status = 'Status'
    l_name = column_length(requirements, t_name, lambda r: r['package']['name'])
    l_specs = column_length(requirements, t_specs, lambda r: r['specs'])
    l_latest_version = column_length(requirements, t_latest_version, lambda r: r['latest']['version'])
    l_status = column_length(requirements, t_status, lambda r: r['status'])
    string_format = '%%-%ds  %%-%ds  %%-%ds  %%-%ds\n' % (l_name, l_specs, l_latest_version, l_status)
    separator = string_format % (l_name * '=', l_specs * '=', l_latest_version * '=', l_status * '=')
    stream.write(separator)
    stream.write(string_format % (t_name, t_specs, t_latest_version, t_status))
    stream.write(separator)
    if requirements:
        for r in requirements:
            stream.write(string_format % (r['package']['name'], r['specs'], r['latest']['version'], r['status']))
    else:
        stream.write(string_format % ('-', '-', '-', '-'))
    stream.write(separator)
