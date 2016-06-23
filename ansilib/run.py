import os

import constants as c
import ui as ui
import utils
import sys

class Run(object):
    def __init__(self, args, options, config):
        self.roles_path = args[0]
        self.options = options
        self.config = config
        self.command = options.command

        self.execute_command()

    def execute_command(self):
        """
        Execute the shell command.
        """
        stderr = ""
        roles_count = 0
        for role in utils.roles_dict(self.roles_path):
            self.command = self.command.replace("%role_name", role)
            (_, err) = utils.capture_shell("cd {0} && {1}".
                                           format(os.path.join(
                                                  self.roles_path, role),
                                                  self.command))

            stderr = err
            roles_count += 1

        if roles_count == 0:
            ui.warn(c.MESSAGES["empty_roles_path"], roles_path)
            sys.exit()

        if len(stderr) > 0:
            ui.error(c.MESSAGES["run_error"], stderr[:-1])
        else:
            if not self.config["options_quiet"]:
                ui.ok(c.MESSAGES["run_success"].replace(
                    "%role_count", str(roles_count)), self.options.command)
