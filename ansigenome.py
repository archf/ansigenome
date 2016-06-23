#!/usr/bin/env python3

import os
import sys

import importlib
import argparse

# import ansigenome.constants as c
# import ansigenome.ui as ui
# import ansigenome.test_helpers as th
# import ansigenome.utils as utils

# from ansigenome.config import Config
# from ansigenome.init import Init
# from ansigenome.run import Run
# from ansigenome.scan import Scan

def execute_run(args, options, config, parser):
    """
    Execute the run action.
    """
    if options.command is None:
        parser.print_help()
        sys.exit()

    check_roles_path(args, parser)
    Run(args, options, config)

def execute_init(args, options, config, parser):
    """
    Execute the init action.
    """
    if len(args) == 0:
        parser.print_help()
        sys.exit()

    Init(args, options, config)

def check_roles_path(args, parser):
    """
    Use the default role path or the user supplied roles path.
    """
    found_path = False

    if len(args) == 0:
        roles_path = os.path.join(os.getcwd(), "playbooks", "roles")

        if os.path.exists(roles_path):
            found_path = True

        if not found_path:
            roles_path = os.getcwd()
            found_path = True
    else:
        roles_path = os.path.abspath(args[0])

    if not os.path.exists(roles_path):
        ui.error(c.MESSAGES["path_missing"], roles_path)
        sys.exit(1)

    if len(args) == 0:
        # there are no args, so add it at as the first arg
        args.append(roles_path)
    else:
        # replace the old argument with the new one
        args[0] = roles_path

def load_config():
    """
    Load properties from the yaml file.
    """
    default_config_path = os.path.join(c.CONFIG_DEFAULT_PATH, c.CONFIG_FILE)
    pwd_config_path = os.path.join(os.getcwd(), c.CONFIG_FILE)
    found_config = False

    if os.path.exists(pwd_config_path):
        this_config = pwd_config_path
        found_config = True
    elif not found_config and os.path.exists(default_config_path):
        this_config = default_config_path
    else:
        # There are no configs at all, so let's help the user make one.
        Config([], {}, {})
        sys.exit(0)

    return (utils.yaml_load(this_config, err_quit=True), this_config)

def load_test_config():
    """
    Load the test config when running tests.
    """
    test_path = os.path.join(c.TEST_PATH, c.CONFIG_FILE)
    th.create_ansigenome_config(test_path)

    return (utils.yaml_load(test_path, err_quit=True), test_path)

def validate_config(config, path):
    """
    Enforce that certain keys exist in the config.
    """
    config_keys = utils.keys_in_dict(config, "", [])
    default_config_keys = utils.keys_in_dict(c.CONFIG_DEFAULTS, "", [])
    missing_keys = []

    for key in default_config_keys:
        if key not in config_keys:
            missing_keys.append(key)

    if missing_keys:
        merge_missing_config_keys(config, missing_keys, path)

def merge_missing_config_keys(config, missing_keys, path):
    """
    Add any missing config keys to the config.
    """
    ui.warn(c.MESSAGES["config_upgraded"])
    ui.ok(missing_keys)
    print()

    config = utils.yaml_load(path)

    # merge in empty keys, then add the real keys.
    merged_config = dict(config.items() + c.CONFIG_DEFAULTS.items())
    merged_config.update(config)

    utils.write_config(path, merged_config)

def is_role(path):
    """
    Determine if a path is an ansible role.
    """
    seems_legit = False
    for folder in c.ANSIBLE_FOLDERS:
        if os.path.exists(os.path.join(path, folder)):
            seems_legit = True

    return seems_legit

def run_subcommand(args):
# def run_subcommand(args, options, config, parser):
    """
    lazy import and run subcommand
    """
    if args.verbose:
        # print(vars(args))
        print('loading module' + args.cmd_name)
    print(args)

    from ansilib import args.cmd_name
    # importlib.import_module(args.cmd_name, '.')

def main():
    # create parser objects
    parser = argparse.ArgumentParser()

    # top level parser options
    parser.add_argument("-v", "--verbose", help="increase output verbosity",
                         action="store_true")

    # todo: read version form file
    parser.add_argument('-V', action='version', version='%(prog)s 2.0')

    parser.add_argument("-o", "-w", dest="out_file",
                        help="output file path (export and config subcommands)")

    # default fct to invoke
    parser.set_defaults(fct=run_subcommand)
    """"
    from the manual (see https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.add_subparsers)
    The add_subparsers() method is normally called with no arguments and
    returns a special action object. This object has a single method,
    add_parser(), which takes a command name and any ArgumentParser constructor
    arguments, and returns an ArgumentParser object that can be modified as
    usual.
    """

    ########################################
    # adding subparsers for each subcommands
    ########################################

    # store the name of the subparser under 'cmd_name' for later usage
    subparsers = parser.add_subparsers(dest='cmd_name')

    # config
    parser_config = subparsers.add_parser('config',
      help='create a necessary config file to make ansigenome work')
    parser_config.add_argument('-o', dest='OUT_FILE', help='output file')

    # scan
    parser_scan = subparsers.add_parser('scan',
      help='scan a path containing Ansible roles and report back useful stats')

    # gendoc
    parser_gendoc = subparsers.add_parser('gendoc',
      help='generate a README from the meta file for each role')
    parser_gendoc.add_argument('-f', '--format', dest='format', default='rst',
                               help='output formats: rst | md')

    parser_gemeta = subparsers.add_parser('genmeta',
          help='augment existing meta files to be compatible with Ansigenome')

    parser_export = subparsers.add_parser('export',
          help='export roles to a dependency graph, requirements file and more')
    parser_export.add_argument('-f', '--format', dest='format',
                               help='dot | png | yml | txt | yml')

    parser_export.add_argument('-s', dest='SIZE', help='(dot | png) image size')
    parser_export.add_argument('-d', dest='DPI', default='130',
                               type=int, help='(dot | png) image DPI')

    parser_export.add_argument('-t', '--type', dest='type',
                               help='export type (graph | reqs | dump)' )

    parser_export.add_argument('-g',
                              help="send custom flags to the graphviz command")
    parser_export.add_argument("-r", "--read-version", dest="read_version",
                                help="read in the version from a VERSION file")

    # init
    parser_init = subparsers.add_parser('init',
                      help='init new roles with a custom meta file and tests')

    parser_init.add_argument("-c", "--galaxy-categories",
                             dest="galaxy_categories",
                             help="comma separated string of galaxy categories")

    # run
    parser_run = subparsers.add_parser('run',
                    help="run shell commands inside of each role's directory")

    parser_run.add_argument('-m', '--command', dest='command',
                          help="execute this shell command on each role")

    # parser_run.set_defaults(func=run_subcommand)
#     if action in ("scan", "gendoc", "genmeta", "export", "run"):
#         parser.add_option("-l", "--limit", dest="limit",
#                           help="comma separated string of roles to white list")

    args = parser.parse_args()

#     version = utils.get_version(os.path.join(c.PACKAGE_RESOURCE,
#                                              os.pardir, os.pardir, "VERSION"))

#     OptionParser.format_epilog = lambda self, formatter: self.epilog
#     parser = OptionParser(usage=usage, epilog=epilog,
#                           version="%prog {0}".format(version))

#     if not action and "--version" not in sys.argv:
#         parser.print_help()
#         sys.exit()

    args.fct(args)
    sys.exit()
    print(vars(args))
    print(args)
    print('vars')
    locals
    print(locals)

    print()
    print('now will invoke func')
    print(args.func)

    print('parser')
    print(vars(parser_init))

    # if action != "config":
    #     config = validate_config(config, config_path)

    # # reload the config
    # reloaded_config = utils.yaml_load(config_path)

    # args = utils.stripped_args(args)

    # if 1:
    #     fn = globals()["execute_%s" % action]
    #     fn(args, options, reloaded_config, parser)

if __name__ == "__main__":
    main()
