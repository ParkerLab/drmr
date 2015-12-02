# -*- coding: utf-8 -*-

"""
Utilities for parsing POSIX scripts for creation of drmr jobs.
"""

import re


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
    directive = args = None
    match = DIRECTIVE_RE.match(line)
    if match:
        directive = match.group('directive')
        args = match.group('args')
        arg_keys = [arg.split('=')[0] for arg in args]
        for arg in arg_keys:
            if arg not in drmr.JOB_DIRECTIVES:
                raise NotImplementedError('Unrecognized job directive {}'.format(arg))

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
