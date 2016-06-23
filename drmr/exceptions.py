#
# drmr: A tool for submitting pipeline scripts to distributed resource
# managers.
#
# Copyright 2015 Stephen Parker
#
# Licensed under Version 3 of the GPL or any later version
#


import subprocess


class ConfigurationError(EnvironmentError):
    pass


class ControlError(subprocess.CalledProcessError):
    """
    Base exception for job control commands: submit, delete, alter.
    """

    action = ''

    def __init__(self, returncode, cmd, output=None, job_ids=None):
        self.returncode = returncode
        self.cmd = cmd
        self.output = output
        self.job_ids = job_ids or []

    def __str__(self):
        job_list = self.job_ids and ' job{} {}'.format(len(self.job_ids) > 1 and 's' or '', ', '.join(self.job_ids))
        return "Error {}{}: '{}' returned non-zero exit status {:d}".format(
            self.action and 'trying to ' + self.action,
            job_list,
            ' '.join(self.cmd),
            self.returncode
        )


class DeletionError(ControlError):
    action = 'delete'


class SubmissionError(ControlError):
    action = 'submit'
