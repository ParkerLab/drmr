#
# drmr: A tool for submitting pipeline scripts to distributed resource
# managers.
#
# Copyright 2015 Stephen Parker
#
# Licensed under Version 3 of the GPL or any later version
#


import json
import logging
import os

import drmr.drm.PBS
import drmr.drm.Slurm
import drmr.exceptions


RESOURCE_MANAGERS = {
    'PBS': drmr.drm.PBS.PBS,
    'Slurm': drmr.drm.Slurm.Slurm,
}


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
    raise drmr.exceptions.ConfigurationError('Unrecognized resource manager "{}"'.format(name))


def guess_resource_manager():
    """Try to determine the resource manager in use."""

    logger = logging.getLogger("{}.{}".format(__name__, guess_resource_manager.__name__))

    available_resource_managers = get_available_resource_managers()
    if available_resource_managers:
        logger.debug('Available resource managers: {}'.format(available_resource_managers))
        if len(available_resource_managers) > 1:
            raise drmr.exceptions.ConfigurationError('Multiple resource managers are available: {}'.format(available_resource_managers))
        return available_resource_managers[0]
    else:
        raise drmr.exceptions.ConfigurationError('No recognized resource manager found.')


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
        except drmr.exceptions.ConfigurationError as e:
            available_resource_managers = get_available_resource_managers()
            raise drmr.exceptions.ConfigurationError("""Could not determine your resource manager.\n{}\nPlease specify the one you're using in your ~/.drmrc under "resource_manager", e.g.:\n\n{{"resource_manager": "{}"}}\n""".format(e, available_resource_managers and available_resource_managers[0] or 'Slurm'))
    return config
