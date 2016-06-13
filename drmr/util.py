#
# drmr: A tool for submitting pipeline scripts to distributed resource
# managers.
#
# Copyright 2015 Stephen Parker
#
# Licensed under Version 3 of the GPL or any later version
#


import copy
import decimal
import os
import re


MEMORY = re.compile('^([0-9]+)(?:([gkmt])b?)?$', re.IGNORECASE)

# First, let me apologize for you having to spend part of your life
# trying to parse this nasty regular expression.
#
# Now that that's out of the way: most of the hideousness is the two
# lookahead expressions that make sure we only extract days and hours
# if the rest of the time is present.
TIME = re.compile(
    '\A(?:(?:(?P<days>\d+(?:\.\d+)*)?[-:])(?=(?:\d+(?:\.\d+)?)(?::\d+(?:\.\d+)?)(?::(?:\d+(?:\.\d+)?))))?'
    '(?:(?P<hours>\d+(?:\.\d+)*)?:(?=(?:\d+(?:\.\d+)?)(?::(?:\d+(?:\.\d+)?))))?'
    '(?P<minutes>\d+(?:\.\d+)?)'
    '(?::(?P<seconds>\d+(?:\.\d+)?))?\Z'
)

FLOAT_PATTERN = '\d+(?:\.\d+)*'

DAYS = re.compile('(' + FLOAT_PATTERN + ')d')
HOURS = re.compile('(' + FLOAT_PATTERN + ')h')
MINUTES = re.compile('(' + FLOAT_PATTERN + ')m')
SECONDS = re.compile('(' + FLOAT_PATTERN + ')(?:s|\Z)')
TIME_UNITS = re.compile('(' + FLOAT_PATTERN + ')[dhms\Z]')

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
        elif unit == 'k':
            amount //= 1000
        elif unit == 't':
            amount *= 1000 * 1000

    return amount


def tally_time_units(regex, time_string):
    occurrences = regex.findall(time_string)
    return sum(occurrence and float(occurrence) or 0.0 for occurrence in occurrences)


def parse_time(time_string):
    m = TIME.match(time_string)
    if m:
        return {k: v and float(v) or 0.0 for k, v in m.groupdict().items()}

    if TIME_UNITS.search(time_string) is None:
        raise SyntaxError('Could not find a time in "{}"'.format(time_string))

    result = {
        'days': tally_time_units(DAYS, time_string),
        'hours': tally_time_units(HOURS, time_string),
        'minutes': tally_time_units(MINUTES, time_string),
        'seconds': tally_time_units(SECONDS, time_string)
    }

    if sum(result.values()) <= 0:
        raise ValueError('Could not parse a positive time value from "{}'.format(time_string))

    return result


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

    Raises SyntaxError if the input cannot be parsed.
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


def merge_mappings(*mappings):
    merged_mapping = copy.deepcopy(mappings[0])
    for mapping in mappings[1:]:
        merged_mapping.update(mapping)
    return merged_mapping
