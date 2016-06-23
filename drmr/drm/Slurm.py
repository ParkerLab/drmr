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
import subprocess
import textwrap

import drmr
import drmr.drm.base
import drmr.util


class Slurm(drmr.drm.base.DistributedResourceManager):
    name = 'Slurm'

    default_job_template = textwrap.dedent(
        """
        #!/bin/bash

        ####  Slurm preamble

        #SBATCH --export=ALL
        #SBATCH --job-name={{job_name}}
        {% if nodes %}
        #SBATCH --nodes={{nodes}}
        {% endif %}
        {% if node_properties %}
        #SBATCH --constraint="{{'&'.join(node_properties.split(','))}}"
        {% endif %}
        #SBATCH --cpus-per-task={{processors|default(1)}}
        {% if memory %}
        #SBATCH --mem={{memory|default('4000')}}
        {% else %}
        #SBATCH --mem-per-cpu={{processor_memory|default('4000')}}
        {% endif %}
        {% if time_limit %}
        #SBATCH --time={{time_limit}}
        {% endif %}
        {% if array_controls %}
        #SBATCH --output "{{control_directory}}/{{job_name}}_%A_%a_%j.out"
        {% else %}
        #SBATCH --output "{{control_directory}}/{{job_name}}_%j.out"
        {% endif %}
        {% if account %}
        #SBATCH --account={{account}}
        {% endif %}
        {% if destination %}
        #SBATCH --partition={{destination}}
        {% endif %}
        {% if email %}
        #SBATCH --mail-user={{email}}
        {% endif %}
        {% if mail_event_string %}
        #SBATCH --mail-type={{mail_event_string}}
        {% endif %}
        {% if dependencies %}
        #SBATCH --dependency={{resource_manager.make_dependency_string(dependencies)}}
        {% endif %}
        {% if working_directory %}
        #SBATCH --workdir={{working_directory}}
        {% endif %}
        {% if array_controls %}
        #SBATCH --array {{array_controls['array_index_min']|default(1)}}-{{array_controls['array_index_max']|default(1)}}{% if array_controls['array_concurrent_jobs'] %}%{{array_controls['array_concurrent_jobs']}}{% endif %}
        {% endif %}
        {% if raw_preamble %}
        {{raw_preamble}}
        {% endif %}


        ####  End Slurm preamble

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
        if [ "$SLURM_ARRAY_TASK_ID" = "{{index}}" ]; then
            {{command}}
        fi
        """
    )

    job_dependency_states = [
        'any',
        'notok',
        'ok',
    ]

    job_state_map = {
        'any': 'any',
        'notok': 'notok',
        'ok': 'ok',
        'start': '',
    }

    mail_event_map = {
        'BEGIN': 'BEGIN',
        'END': 'END',
        'FAIL': 'FAIL',
    }

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
                command = ['scancel'] + list(targets)
                try:
                    subprocess.check_call(command)
                except subprocess.CalledProcessError as e:
                    raise drmr.exceptions.DeletionError(e.returncode, e.cmd, e.output, targets)

    def get_active_job_ids(self, job_ids=None, job_name=None, job_owner=None):
        logger = self.get_method_logger()

        if job_ids is None:
            job_ids = []

        jobs = set([])

        command = [
            'squeue',
            '-r',
            '--format=%A,%j,%u',
            '--states=CONFIGURING,COMPLETING,PENDING,PREEMPTED,RUNNING,SUSPENDED'
        ]

        squeue_lines = self.capture_process_output(command).splitlines()
        if 1 < len(squeue_lines):
            squeue_lines = set(squeue_lines[1:])
            for job in squeue_lines:
                job_id, name, owner = job.split(',')
                if job_owner and owner != job_owner:
                    continue

                if job_name and job_name not in name:
                    continue

                if job_ids and job_id not in job_ids:
                    continue

                jobs.add(job_id)

        if jobs:
            logger.debug('Found {} active jobs'.format(len(jobs)))
        else:
            logger.debug('No active jobs found.')

        return jobs

    def is_installed(self):
        output = ''
        try:
            output = self.capture_process_output(['scontrol', 'version'])
        except:
            pass

        return 'slurm' in output

    def write_cancel_script(self, job_data, job_ids):
        logger = self.get_method_logger()
        logger.debug('Writing canceller script for {}'.format(job_data))

        self.set_control_directory(job_data)
        filename = drmr.util.absjoin(job_data['control_directory'], job_data['job_name'])
        if not os.path.exists(job_data['control_directory']):
            os.makedirs(job_data['control_directory'])
        with open(filename, 'w') as canceller:
            canceller.write('#!/bin/sh\n\n')
            for job in job_ids:
                canceller.write('scancel %s\n' % job)
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

                dependency_list.append('after%s:%s' % (state, ':'.join(str(job_id) for job_id in job_ids)))
            dependency_string = ','.join(dependency_list)

        return dependency_string

    def set_mail_event_string(self, job_data):
        if job_data.get('mail_events'):
            job_data['mail_event_string'] = ','.join(
                sorted(
                    self.mail_event_map[event] for event in job_data['mail_events']
                )
            )

    def submit(self, job_filename, hold=False):
        if not self.is_installed():
            raise drmr.exceptions.ConfigurationError('{} is not installed or not usable.'.format(self.name))

        try:
            command = ['sbatch', '--parsable', job_filename]
            if hold:
                command.insert(1, '--hold')

            job_id = self.capture_process_output(command)
            return job_id.strip().split(';')[0]
        except subprocess.CalledProcessError as e:
            raise drmr.exceptions.SubmissionError(e.returncode, e.cmd, e.output)

    def validate_destination(self, destination):
        if not self.is_installed():
            raise drmr.exceptions.ConfigurationError('{} is not installed or not usable.'.format(self.name))

        valid = False
        try:
            command = ['scontrol', 'show', 'partition', destination]
            status = self.capture_process_output(command)
            if status.startswith('PartitionName={}'.format(destination)):
                valid = True
        except:
            pass

        return valid
