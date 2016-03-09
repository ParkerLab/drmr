#
# drmr: A tool for submitting pipeline scripts to distributed resource
# managers.
#
# Copyright 2015 The Parker Lab at the University of Michigan
#
# Licensed under Version 3 of the GPL or any later version
#


import decimal
import os
import re


MEMORY = re.compile('^([0-9]+)(?:([gmt])b?)?$', re.IGNORECASE)

TIME = re.compile(
    '\A(?:(?P<hours>\d+(?:\.\d+)*)*:(?=(?:\d+(?:\.\d+)*)(?::(?:\d+(?:\.\d+)*))))*'
    '(?P<minutes>\d+(?:\.\d+)*)'
    '(?::(?P<seconds>\d+(?:\.\d+)*))*\Z'
)

TIME_WITH_DAYS = re.compile(
    '\A(?P<days>\d+(?:\.\d+)*)-'
    '(?:(?:(?P<hours>\d+(?:\.\d+)*)'
    '(?::(?P<minutes>\d+(?:\.\d+)*)'
    '(?::(?P<seconds>\d+(?:\.\d+)*)*)*)*))*\Z'
)

FLOAT_PATTERN = '\d+(?:\.\d+)*'

DAYS = re.compile('(' + FLOAT_PATTERN + ')d')
HOURS = re.compile('(' + FLOAT_PATTERN + ')h')
MINUTES = re.compile('(' + FLOAT_PATTERN + ')m')
SECONDS = re.compile('(' + FLOAT_PATTERN + ')s?\Z')


def normalize_memory(memory):
    """
    Normalizes a string describing an amount of memory.

    Returns the equivalent in megabytes, or the original value if it
    can't be parsed.
    """

    amount = memory

    match = MEMORY.match(memory)
    if match:
        amount, unit = match.groups('')
        amount = int(amount)
        unit = unit.lower()
        if unit == 'g':
            amount *= 1000
        elif unit == 't':
            amount *= 1000 * 1000

    return amount


def tally_time_units(regex, time_string):
    occurrences = regex.findall(time_string)
    return sum(occurrence and float(occurrence) or 0.0 for occurrence in occurrences)


def parse_time(time):
    m = TIME_WITH_DAYS.match(time)
    if m:
        return {k: v and float(v) or 0.0 for k, v in m.groupdict().items()}

    m = TIME.match(time)
    if m:
        return {k: v and float(v) or 0.0 for k, v in m.groupdict().items()}

    return {
        'days': tally_time_units(DAYS, time),
        'hours': tally_time_units(HOURS, time),
        'minutes': tally_time_units(MINUTES, time),
        'seconds': tally_time_units(SECONDS, time)
    }


def make_time_string(days=0, hours=0, minutes=0, seconds=0):
    total_seconds = (
        (days * 24 * 60 * 60) +
        (hours * 60 * 60) +
        (minutes * 60) +
        seconds
    )
    hours = total_seconds // (60 * 60)
    total_seconds -= hours * 60.0 * 60.0
    minutes = total_seconds // 60
    total_seconds -= minutes * 60.0
    seconds = total_seconds

    hours = decimal.Decimal(hours).quantize(decimal.Decimal('1.'), decimal.ROUND_UP)
    minutes = decimal.Decimal(minutes).quantize(decimal.Decimal('1.'), decimal.ROUND_UP)
    seconds = decimal.Decimal(seconds).quantize(decimal.Decimal('1.'), decimal.ROUND_UP)
    return '{:02f}:{:02f}:{:02f}'.format(hours, minutes, seconds)


def normalize_time(time):
    """
    Normalizes a string describing a duration.

    Accepts seconds up through days, e.g.:

    "18d 1.99h 2min 3.5seconds"

    If the input can be parsed, returns a string containing whole
    integers in the format hours:minutes:seconds.

    Otherwise returns the input.
    """

    return make_time_string(**parse_time(time))


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
