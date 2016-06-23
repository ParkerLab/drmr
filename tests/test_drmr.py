#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import json
import os
import shutil
import tempfile
import unittest

import drmr.config
import drmr.util


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
            self.assertEqual(drmr.util.normalize_memory(original), expected_conversion)


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
                drmr.util.parse_time(bad_time)

    def test_good_times(self):
        for original, expected_conversion in self.good_times.items():
            conversion = drmr.util.parse_time(original)
            self.assertEqual(drmr.util.make_time_string(**conversion), expected_conversion)


class TestPBS(unittest.TestCase):

    def setUp(self):
        self.oldcwd = os.getcwd()
        self.tmpdir = tempfile.mkdtemp(prefix='drmrconfigtest')
        os.chdir(self.tmpdir)

        # stash the current PATH and replace it with our temp directory, so PBS commands can't be found
        self.oldpath = os.environ['PATH']
        os.environ['PATH'] = self.tmpdir

    def tearDown(self):
        shutil.rmtree(self.tmpdir)
        os.environ['PATH'] = self.oldpath
        os.chdir(self.oldcwd)

    def testPBS(self):
        drmrc = os.path.join(self.tmpdir, '.drmrc')
        try:
            config = drmr.config.load_configuration(file=drmrc)
        except drmr.exceptions.ConfigurationError:
            pass  # good, caught non-existent file

        drmrc_content = {
            'account': 'notthere',
            'destination': 'notthere',
            'resource_manager': 'PBS'
        }
        json.dump(drmrc_content, open(drmrc, 'w'), indent=2, sort_keys=True)
        config = drmr.config.load_configuration(file=drmrc)
        resource_manager = drmr.config.get_resource_manager(config['resource_manager'])

        self.assertFalse(resource_manager.is_installed())

        qmgr_content = '#!/bin/sh\necho "pbs_version = fake"\n'
        with open('qmgr', 'w') as qmgr:
            qmgr.write(qmgr_content)
        os.chmod('qmgr', 0755)
        self.assertTrue(resource_manager.is_installed())

        try:
            resource_manager.submit('qmgr')
        except OSError:
            pass  # good, qsub not found

        qsub_content = '#!/bin/sh\necho "1"\n'
        with open('qsub', 'w') as qsub:
            qsub.write(qsub_content)
        os.chmod('qsub', 0755)

        job_id = resource_manager.submit('qmgr')

        try:
            resource_manager.delete_jobs([2])
        except OSError:
            pass  # right, qdel doesn't exist

        qdel_content = '#!/bin/sh\n[[ $1 = "1" ]] || exit 1\n'
        with open('qdel', 'w') as qdel:
            qdel.write(qdel_content)
        os.chmod('qdel', 0755)

        qstat_content = '#!/bin/sh\necho "<Data><Job><Job_Id>1</Job_Id><job_name>test</job_name><job_state>Q</job_state><Job_Owner>test_owner</Job_Owner></Job></Data>"\n'
        with open('qstat', 'w') as qstat:
            qstat.write(qstat_content)
        os.chmod('qstat', 0755)

        try:
            resource_manager.delete_jobs(["2"])
        except drmr.exceptions.DeletionError:
            pass  # right, job 2 is invalid

        resource_manager.delete_jobs([job_id])


class TestSlurm(unittest.TestCase):

    def setUp(self):
        self.oldcwd = os.getcwd()
        self.tmpdir = tempfile.mkdtemp(prefix='drmrconfigtest')
        os.chdir(self.tmpdir)

        # stash the current PATH and replace it with our temp directory, so Slurm commands can't be found
        self.oldpath = os.environ['PATH']
        os.environ['PATH'] = self.tmpdir

    def tearDown(self):
        # shutil.rmtree(self.tmpdir)
        os.environ['PATH'] = self.oldpath
        os.chdir(self.oldcwd)

    def testSlurm(self):
        drmrc = os.path.join(self.tmpdir, '.drmrc')
        try:
            config = drmr.config.load_configuration(file=drmrc)
        except drmr.exceptions.ConfigurationError:
            pass  # good, caught non-existent file

        drmrc_content = {
            'account': 'noslurm',
            'destination': 'noslurm',
            'resource_manager': 'Slurm'
        }
        json.dump(drmrc_content, open(drmrc, 'w'), indent=2, sort_keys=True)
        config = drmr.config.load_configuration(file=drmrc)
        resource_manager = drmr.config.get_resource_manager(config['resource_manager'])

        self.assertFalse(resource_manager.is_installed())

        print('CURRENT DIRECTORY: ' + os.getcwd())
        print('PATH: ' + os.environ['PATH'])
        scontrol_content = '#!/bin/sh\necho "slurm something something"\n'
        with open('scontrol', 'w') as scontrol:
            scontrol.write(scontrol_content)
        os.chmod('scontrol', 0755)
        self.assertTrue(resource_manager.is_installed())

        try:
            resource_manager.submit('scontrol')
        except OSError:
            pass  # good, sbatch not found

        sbatch_content = '#!/bin/sh\necho "1"\n'
        with open('sbatch', 'w') as sbatch:
            sbatch.write(sbatch_content)
        os.chmod('sbatch', 0755)

        job_id = resource_manager.submit('scontrol')

        try:
            resource_manager.delete_jobs([2])
        except OSError:
            pass  # right, scancel doesn't exist

        scancel_content = '#!/bin/sh\n[[ $1 = "1" ]] || exit 1\n'
        with open('scancel', 'w') as scancel:
            scancel.write(scancel_content)
        os.chmod('scancel', 0755)

        squeue_content = '#!/bin/sh\necho "1,test_job.1,test_owner"\n'
        with open('squeue', 'w') as squeue:
            squeue.write(squeue_content)
        os.chmod('squeue', 0755)

        try:
            resource_manager.delete_jobs(["2"])
        except drmr.exceptions.DeletionError:
            pass  # right, job 2 is invalid

        resource_manager.delete_jobs([job_id])
