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
import logging
import os
import subprocess

import drmr.drm


class ConfigurationError(EnvironmentError):
    pass


class SubmissionError(subprocess.CalledProcessError):
    pass


RESOURCE_MANAGERS = {
    'PBS': drmr.drm.PBS,
    'Slurm': drmr.drm.Slurm,
}

MAIL_EVENTS = [
    'BEGIN',
    'END',
    'FAIL',
]

JOB_DEPENDENCY_STATES = [
    'any',
    'notok',
    'ok',
    'start',
]

JOB_DIRECTIVES = {
    'account': 'The account to which the job will be billed.',
    'array_control': 'A dictionary of integer values for keys array_index_min, array_index_max, and array_concurrent_jobs.',
    'dependencies': 'A map of states ({}) to lists of job IDs which must end in the specified state.'.format(JOB_DEPENDENCY_STATES),
    'destination': 'The execution environment (queue, partition, etc.) for the job.',
    'environment_setup': 'Additional commands to execute to prepare the job environment.',
    'mail_events': 'A list of job events ({}) that will trigger email notifications.'.format(MAIL_EVENTS),
    'job_name': 'A name for the job.',
    'memory': 'The amount of memory required on any one node.',
    'nodes': 'The number of nodes required for the job.',
    'processors': 'The number of cores required on each node.',
    'processor_memory': 'The amount of memory required per processor.',
    'email': """The submitter's email address, for notifications.""",
    'time_limit': 'The maximum amount of time the DRM should allow the job, in HH:MM:SS format.',
    'working_directory': 'The directory where the job should be run.',
}


def load_configuration(config={}, file=None):
    """Loads a drmr config in JSON format.

    If a configuration dictionary is supplied, only the parameters for
    which it lacks values will be updated. So you can for example
    parse command line arguments, put them in a dictionary, and
    backfill it from the user config file.

    If file is not specified, it defaults to ~/.drmrc.

    """

    logger = logging.getLogger("{}.{}".format(__name__, load_configuration.__name__))

    if not file:
        file = os.path.expanduser('~/.drmrc')
    if os.path.exists(file):
        with open(file) as rc:
            rc = json.load(rc)
        for k, v in rc.items():
            if not config.get(k):
                config[k] = rc[k]

    if 'resource_manager' not in config:
        try:
            config['resource_manager'] = guess_resource_manager()
            logger.debug("""No resource manager configured, so I'm going with the one I found, {}.""".format(config['resource_manager']))
        except ConfigurationError as e:
            available_resource_managers = get_available_resource_managers()
            raise ConfigurationError("""Could not determine your resource manager.\n{}\nPlease specify the one you're using in your ~/.drmrc under "resource_manager", e.g.:\n\n{{"resource_manager": "{}"}}\n""".format(e, available_resource_managers and available_resource_managers[0] or 'Slurm'))
    return config


def get_available_resource_managers():
    available_resource_managers = []
    for name, rm in RESOURCE_MANAGERS.items():
        if rm().is_installed():
            available_resource_managers.append(name)
    return available_resource_managers


def get_resource_manager(name):
    """Given the name of a resource manager, return an instance of it."""
    if name in RESOURCE_MANAGERS:
        return RESOURCE_MANAGERS[name]()
    raise KeyError('Unrecognized resource manager "{}"'.format(name))


def guess_resource_manager():
    """Try to determine the resource manager in use."""

    logger = logging.getLogger("{}.{}".format(__name__, guess_resource_manager.__name__))

    available_resource_managers = get_available_resource_managers()
    if available_resource_managers:
        logger.debug('Available resource managers: {}'.format(available_resource_managers))
        if len(available_resource_managers) > 1:
            raise ConfigurationError('Multiple resource managers are available: {}'.format(available_resource_managers))
        return available_resource_managers[0]
    else:
        raise ConfigurationError('No recognized resource manager found.')
