#
# drmr: A tool for submitting pipeline scripts to distributed resource
# managers.
#
# Copyright 2015 Stephen Parker
#
# Licensed under Version 3 of the GPL or any later version
#

from __future__ import print_function

import collections
import logging
import os
import re
import subprocess
import time
import textwrap

import lxml.objectify

import drmr
import drmr.drm.base
import drmr.util


class PBS(drmr.drm.base.DistributedResourceManager):
    name = 'PBS'

    default_job_template = textwrap.dedent(
        """
        #!/bin/bash

        ####  PBS preamble

        #PBS -V
        #PBS -j oe
        #PBS -o {{control_directory}}
        {% if account %}
        # account={{account}}
        #PBS -A {{account}}
        {% endif %}
        {% if email %}
        # email={{email}}
        #PBS -M {{email}}
        {% endif %}
        {% if mail_event_string %}
        #PBS -m {{mail_event_string}}
        {% endif %}
        #PBS -N {{job_name}}
        {% if dependencies %}
        #PBS -W depend={{resource_manager.make_dependency_string(dependencies)}}
        {% endif %}
        {% if working_directory %}
        #PBS -d {{working_directory}}
        {% endif %}
        {% if nodes %}
        #PBS -l nodes={{nodes}}:ppn={{processors|default(1)}}{% if node_properties %}:{{':'.join(node_properties.split(','))}}{% endif %}

        {% else %}
        #PBS -l ncpus={{processors|default(1)}}
        {% endif %}
        {% if memory %}
        #PBS -l mem={{memory|default('4000')}}mb
        {% else %}
        #PBS -l pmem={{processor_memory|default('4000')}}mb
        {% endif %}
        {% if time_limit %}
        #PBS -l walltime={{time_limit}}
        {% endif %}
        {% if destination %}
        #PBS -q {{destination}}
        {% endif %}
        {% if array_controls %}
        #PBS -t {{array_controls['array_index_min']|default(1)}}-{{array_controls['array_index_max']|default(1)}}{% if array_controls['array_concurrent_jobs'] %}%{{array_controls['array_concurrent_jobs']}}{% endif %}
        {% endif %}
        {% if raw_preamble %}
        {{raw_preamble}}
        {% endif %}


        ####  End PBS preamble

        {% if notes %}
        ####  Notes
        {{notes}}
        {% endif %}

        {% if environment_setup %}
        ####  Environment setup
        {% for line in environment_setup %}
        {{line}}
        {% endfor %}
        {% endif %}

        ####  Commands

        {{command}}


        """
    ).lstrip()

    default_array_command_template = textwrap.dedent(
        """
        if [ "$PBS_ARRAYID" = "{{index}}" ]; then
            {{command}}
        fi
        """
    )

    job_dependency_states = [
        'any',
        'notok',
        'ok',
        'start',
    ]

    mail_event_map = {
        'BEGIN': 'b',
        'END': 'e',
        'FAIL': 'a',
    }

    array_job_id_re = re.compile('^\S+\[.*\]')

    def delete_jobs(self, job_ids=None, job_name=None, job_owner=None, dry_run=False):
        logger = self.get_method_logger()

        if job_ids is None:
            job_ids = []

        targets = set(job_ids)
        targets.update(self.get_active_job_ids(job_ids, job_name, job_owner))

        if targets:
            if dry_run:
                logger.info(self.explain_job_deletion(targets, job_name, job_owner, dry_run))
            else:
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(self.explain_job_deletion(targets, job_name, job_owner, dry_run))
                for target in sorted(targets):
                    command = ['qdel', target]
                    try:
                        subprocess.check_call(command)
                    except subprocess.CalledProcessError as e:
                        raise drmr.exceptions.DeletionError(e.returncode, e.cmd, e.output, [target])
                    time.sleep(0.25)  # PBS is frail

    def get_active_job_ids(self, job_ids=None, job_name=None, job_owner=None):
        logger = self.get_method_logger()

        if job_ids is None:
            job_ids = []

        jobs = set([])

        command = ['qstat', '-t', '-x']

        qstat = lxml.objectify.fromstring(self.capture_process_output(command))
        for job in qstat.findall('Job'):
            if job.job_state not in ['E', 'H', 'Q', 'R', 'T', 'W']:
                continue

            if job_name and job_name not in job.Job_Name.text:
                continue

            if job_ids and job.Job_Id.text not in job_ids:
                continue

            owner = job.Job_Owner.text.split('@')[0]
            if job_owner and job_owner != owner:
                continue

            jobs.add(job.Job_Id.text)

        if jobs:
            logger.debug('Found {} active jobs'.format(len(jobs)))
        else:
            logger.debug('No active jobs found.')

        return jobs

    def is_installed(self):
        output = ''
        try:
            output = self.capture_process_output(['qmgr', '-c', 'list server'])
        except:
            pass
        return 'pbs_version = ' in output

    def write_cancel_script(self, job_data, job_ids):
        logger = self.get_method_logger()
        logger.debug('Writing canceller script for {}'.format(job_data))

        self.set_control_directory(job_data)
        filename = drmr.util.absjoin(job_data['control_directory'], job_data['job_name'])
        if not os.path.exists(job_data['control_directory']):
            os.makedirs(job_data['control_directory'])
        with open(filename, 'w') as canceller:
            canceller.write('#!/bin/sh\n\n')
            for job_id in job_ids:
                canceller.write('qdel %s; sleep 0.25\n' % job_id)
            os.chmod(filename, 0o755)

    def make_dependency_string(self, dependencies):
        dependency_string = ''
        if dependencies:
            dependency_list = []
            if not isinstance(dependencies, collections.Mapping):
                raise ValueError('Job data does not contain a map under the "dependencies" key.')
            for state, job_ids in dependencies.items():
                if state not in self.job_dependency_states:
                    raise ValueError('Unsupported dependency state: %s' % state)

                job_ids = [str(job_id) for job_id in job_ids]
                array_jobs = ':'.join([job_id for job_id in job_ids if self.array_job_id_re.search(job_id)])
                regular_jobs = ':'.join([job_id for job_id in job_ids if not self.array_job_id_re.search(job_id)])
                array_dependency_list = array_jobs and ('after%sarray:%s' % (state, array_jobs)) or ''
                regular_dependency_list = regular_jobs and ('after%s:%s' % (state, regular_jobs)) or ''
                dependency_list.append(','.join(l for l in [array_dependency_list, regular_dependency_list] if l))
            dependency_string = ','.join(dependency_list)
        return dependency_string

    def set_mail_event_string(self, job_data):
        if job_data.get('mail_events'):
            job_data['mail_event_string'] = ''.join(
                sorted(
                    self.mail_event_map[event] for event in job_data['mail_events']
                )
            )

    def submit(self, job_filename, hold=False):
        if not self.is_installed():
            raise drmr.exceptions.ConfigurationError('{} is not installed or not usable.'.format(self.name))

        try:
            command = ['qsub', job_filename]
            if hold:
                command.insert(1, '-h')
            job_id = self.capture_process_output(command)
            return job_id.strip()
        except subprocess.CalledProcessError as e:
            raise drmr.exceptions.SubmissionError(e.returncode, e.cmd, e.output)

    def validate_destination(self, destination):
        if not self.is_installed():
            raise drmr.exceptions.ConfigurationError('{} is not installed or not usable.'.format(self.name))

        valid = False
        try:
            command = ['qstat', '-Q', '-f', destination]
            status = self.capture_process_output(command)
            if status.startswith('Queue: {}'.format(destination)):
                valid = True
        except:
            pass

        return valid
