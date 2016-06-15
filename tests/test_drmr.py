#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

import drmr.util as util


class TestMemoryParsing(unittest.TestCase):

    def setUp(self):
        self.checks = {
            '4096k': 4,
            '128': 128,
            '128m': 128,
            '4g': 4000,
            '4gB': 4000,
            '4gb': 4000,
            '1t': 1000000,
            '1Tb': 1000000,
            '1TB': 1000000,
        }

    def test_memory_parsing(self):
        for original, expected_conversion in self.checks.items():
            self.assertEqual(util.normalize_memory(original), expected_conversion)


class TestTimeParsing(unittest.TestCase):

    def setUp(self):
        self.bad_times = [
            '15:00:00:00:00',
            '15:00:',
            '',
        ]

        self.good_times = {
            ':15:00': '00:15:00',
            '00:15:00': '00:15:00',
            ':15:00:00': '15:00:00',
            '0:15:00:00': '15:00:00',
            '15:00:00': '15:00:00',
            '1d': '24:00:00',
            '1d12h': '36:00:00',
            '1d25h30m': '49:30:00',
            '1d25h90m45s': '50:30:45',
            '10': '00:10:00',
            '10:20': '00:10:20',
            '10:20:50': '10:20:50',
            '10:20:50.5': '10:20:51',
            '2-10:20:50.5': '58:20:51',
            '2:10:20:50.5': '58:20:51',
            '1d2d24h24h30s30s15': '120:01:15'
        }

    def test_bad_times(self):
        for bad_time in self.bad_times:
            with self.assertRaises(SyntaxError):
                util.parse_time(bad_time)

    def test_good_times(self):
        for original, expected_conversion in self.good_times.items():
            conversion = util.parse_time(original)
            self.assertEqual(util.make_time_string(**conversion), expected_conversion)
