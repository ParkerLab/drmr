# -*- coding: utf-8 -*-

"""
Utilities for parsing POSIX scripts for creation of drmr jobs.
"""

import logging
import re

import drmr


# A subset of drmr.JOB_DIRECTIVES, omitting those that don't make sense in a script, and adding 'default'.
JOB_DIRECTIVES = {
    "account": "The account to which the job will be billed.",
    "default": "Use the resource manager's default job parameters.",
    "destination": "The execution environment (queue, partition, etc.) for the job.",
    "mail_events": "A comma-separated list of job events ({}) that will trigger email notifications.".format(drmr.MAIL_EVENTS),
    "job_name": "A name for the job.",
    "nodes": "The number of nodes required for the job.",
    "processors": "The number of cores on each node required for the job.",
    "processor_memory": "The number of memory required for the job, per processor.",
    "email": "The submitter's email address, for notifications.",
    "time_limit": "The maximum amount of time the DRM should allow the job, in HH:MM:SS format.",
    "working_directory": "The directory where the job should be run.",
}

COMMENT_RE = re.compile('(?P<comment>#.*)$')
CONTINUATION_RE = re.compile('\\\s*$')
DIRECTIVES = ['job', 'wait']
DIRECTIVE_RE = re.compile('^#\s*drmr:(?P<directive>job|wait)(\s(?P<args>.*))*')
EMPTY_RE = re.compile('^\s*$')


def is_empty(line):
    """Return True if the line contains nothing more than whitespace."""
    return (not line) or EMPTY_RE.match(line)


def is_comment(line):
    """Return True if the line starts with a shell comment marker (#)."""
    return line.startswith('#')


def is_continued(line):
    """Return true if the line ends with a backslash (and possibly whitespace)."""
    return CONTINUATION_RE.search(line)


def is_directive(line):
    return DIRECTIVE_RE.search(line)


def parse_directive(line):
    """Parse a drmr directive from the line, returning a tuple of the directive and its arguments."""
    logger = logging.getLogger('drmr.script.parse_directive')
    directive = args = None
    match = DIRECTIVE_RE.match(line)
    if match:
        directive = match.group('directive')
        args = match.group('args')
        logger.debug('directive: {}, args: {}'.format(directive, args))
        if args:
            arg_keys = [arg.split('=')[0] for arg in args.split()]
            for arg in arg_keys:
                if arg not in JOB_DIRECTIVES:
                    raise NotImplementedError('Unrecognized job directive {} in {}'.format(arg, line))

    return (directive, args)


def is_boring(line):
    """Return True if the line is empty or a comment that does not contain a directive."""
    return is_empty(line) or (is_comment(line) and not is_directive(line))


def parse_script(script):
    """Parse a POSIX script for submission."""
    lines = [l.strip() for l in script.splitlines() if not is_boring(l)]

    commands = ''
    for line in lines:
        if is_continued(line):
            commands += CONTINUATION_RE.sub('', line)
            continue
        else:
            commands += line + '\n'

    return commands.splitlines()
