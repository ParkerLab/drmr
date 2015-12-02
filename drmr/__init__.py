#
# drmr: A tool for submitting pipeline scripts to distributed resource
# managers.
#
# Copyright 2015 The Parker Lab at the University of Michigan
#
# Licensed under Version 3 of the GPL or any later version
#


__author__ = 'The Parker Lab'
__email__ = 'parkerlab-software@umich.edu'
__version__ = '0.1.0'


import json
import os
import subprocess

import drmr.drm


class SubmissionError(subprocess.CalledProcessError):
    pass


MAIL_EVENTS = [
    'BEGIN',
    'END',
    'FAIL',
]


JOB_DIRECTIVES = {
    "account": "The account to which the job will be billed.",
    "dependencies": "A list of job IDs which must complete successfully before this job is run.",
    "destination": "The execution environment (queue, partition, etc.) for the job.",
    "environment_setup": "Additional commands to execute to prepare the job environment.",
    "mail_events": "A list of job events (from the set {}) that will trigger email notifications.".format(MAIL_EVENTS),
    "name": "A name for the job.",
    "nodes": "The number of nodes required for the job.",
    "processors": "The number of cores on each node required for the job.",
    "processor_memory": "The number of memory required for the job, per processor.",
    "email": "The submitter's email address, for notifications.",
    "time_limit": "The maximum amount of time the DRM should allow the job, in HH:MM:SS format.",
    "working_directory": "The directory where the job should be run.",
}


RESOURCE_MANAGERS = {
    'slurm': drmr.drm.Slurm,
    'pbs': drmr.drm.PBS,
}


def load_configuration(config={}, file=None):
    """Loads a drmr config in JSON format.

    If a configuration dictionary is supplied, only the parameters for
    which it lacks values will be updated. So you can for example
    parse command line arguments, put them in a dictionary, and
    backfill it from the user config file.

    If file is not specified, it defaults to ~/.drmrc.

    """

    if not file:
        file = os.path.expanduser("~/.drmrc")
    if os.path.exists(file):
        with open(file) as rc:
            rc = json.load(rc)
        for k, v in rc.items():
            if not config.get(k):
                config[k] = rc[k]
    return config


def get_resource_manager(name):
    if name in RESOURCE_MANAGERS:
        return RESOURCE_MANAGERS[name]()
    raise KeyError('Unrecognized resource manager "{}"'.format(name))
