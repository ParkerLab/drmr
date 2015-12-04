#
# drmr: A tool for submitting pipeline scripts to distributed resource
# managers.
#
# Copyright 2015 The Parker Lab at the University of Michigan
#
# Licensed under Version 3 of the GPL or any later version
#


import os


def makedirs(*paths):
    """
    Creates each path given.

    An exception will be raised if any path exists and is not a directory.
    """
    for path in paths:
        if os.path.lexists(path):
            if not os.path.isdir(path):
                raise ValueError('Path exists but is not a directory: %s' % path)
        else:
            os.makedirs(path)


def absjoin(*paths):
    """Simple combination of os.path.abspath and os.path.join."""
    return os.path.abspath(os.path.join(*paths))
