#
# drmr: A tool for submitting pipeline scripts to distributed resource
# managers.
#
# Copyright 2015 The Parker Lab at the University of Michigan
#
# Licensed under Version 3 of the GPL or any later version
#

from __future__ import print_function

import collections
import copy
import inspect
import logging
import os
import re
import subprocess
import uuid
import textwrap

import jinja2

import drmr
import drmr.util


class DistributedResourceManager(object):
    name = 'Base Distributed Resource Manager'
    default_job_template = ''

    def __init__(self):
        self.default_job_data = {
            'dependencies': {},
            'environment_setup': [],
        }

    def capture_process_output(self, command=[]):
        return subprocess.check_output(command, stderr=subprocess.STDOUT, universal_newlines=True)

    def validate_destination(self, destination):
        """Verifies that the given destination is valid."""
        raise NotImplementedError

    def get_method_logger(self):
        stack = inspect.getouterframes(inspect.currentframe())
        caller = stack[1][3]
        return logging.getLogger("{}.{}.{}".format(self.__module__, self.__class__.__name__, caller))

    def is_installed(self):
        """Verifies that the resource manager is installed."""
        raise NotImplementedError

    def make_control_directory(self, job_data):
        """Create the control directory for submitted jobs."""
        self.set_control_directory(job_data)
        drmr.util.makedirs(job_data['control_directory'])

    def make_job_filename(self, job_data):
        """Create a name for the job file in the control directory."""
        self.make_control_directory(job_data)
        return drmr.util.absjoin(job_data['control_directory'], job_data['job_name'] + '.' + self.name.lower())

    def make_job_template(self, job_data):
        """Format a job template, suitable for submission to the DRM."""
        template_data = self.make_job_template_data(job_data)
        template_environment = jinja2.Environment()
        return template_environment.from_string(self.default_job_template).render(**template_data)

    def make_job_template_data(self, job_data):
        """Prepare the job data for interpolation into the job file template."""
        template_data = {}
        template_data.update(copy.deepcopy(self.default_job_data))
        template_data.update(job_data)

        self.set_control_directory(template_data)
        self.set_working_directory(template_data)
        self.set_mail_events(template_data)
        self.set_job_name(template_data)
        self.set_dependencies(template_data)

        python_virtualenv = os.getenv('VIRTUAL_ENV')
        if python_virtualenv:
            template_data['environment_setup'].append('. {}/bin/activate'.format(python_virtualenv))

        return template_data

    def set_control_directory(self, job_data):
        """Add the path of the control directory to the job data."""
        control_path = drmr.util.absjoin(job_data.get('working_directory', ''), '.drmr')
        job_data['control_directory'] = control_path
        return control_path

    def set_dependencies(self, job_data):
        """Convert the map of dependency states to job IDs to the string format required by the DRM."""
        raise NotImplementedError

    def set_job_name(self, job_data):
        if 'job_name' not in job_data:
            job_data['job_name'] = uuid.uuid4()

    def set_mail_events(self, job_data):
        """Convert the list of mail events to the string format required by the DRM."""
        raise NotImplementedError

    def set_working_directory(self, job_data):
        if 'working_directory' not in job_data:
            job_data['working_directory'] = os.getcwd()

    def submit(self, job_file):
        """Submit a job file. Return the job ID."""
        raise NotImplementedError

    def submit_completion_jobs(self, job_data, job_list, mail_at_finish=False):
        """Submit two jobs: one to record success, and one just to record completion."""

        if not job_list:
            raise ValueError('You did not supply a list of job IDs to wait for.')

        common_data = copy.deepcopy(job_data)
        common_data.update({
            'walltime': '00:15:00',  # not really, but ARC suggest that it be the minimum for any job
        })
        common_data = self.make_job_template_data(common_data)

        #
        # The happy path: all jobs completed; we're done, or on to the
        # next phase. This success job ID is what dependent tasks should
        # watch.
        #
        success_commands = ['touch {control_directory}/{job_name}.success'.format(**common_data)]
        success_data = copy.deepcopy(common_data)
        success_data.update({
            'job_name': success_data['job_name'] + '.success',
            'dependencies': {'ok': job_list},
            'command': '\n'.join(success_commands),
        })

        success_job_filename = self.write_job_file(success_data)
        success_job_id = self.submit(success_job_filename)

        #
        # Whatever happened, let's record that the job is done.
        #
        finish_commands = ['touch {control_directory}/{job_name}.finished'.format(**common_data)]

        finish_data = copy.deepcopy(common_data)
        finish_data.update({
            'job_name': finish_data['job_name'] + '.finish',
            'dependencies': {'any': job_list},
            'command': '\n'.join(finish_commands)
        })

        if mail_at_finish:
            finish_data['mail_events'] = ['END', 'FAIL']

        finish_job_filename = self.write_job_file(finish_data)
        self.submit(finish_job_filename)

        return success_job_id

    def write_job_file(self, job_data):
        """Write a batch script to be submitted to the resource manager."""

        logger = self.get_method_logger()
        logger.debug('Writing job file for {}'.format(job_data))

        job_filename = self.make_job_filename(job_data)
        with open(job_filename, 'w') as job_file:
            job_file.write(self.make_job_template(job_data))

        return job_filename


class PBS(DistributedResourceManager):
    name = 'PBS'

    default_job_template = textwrap.dedent(
        """
        #!/bin/bash

        ####  PBS preamble

        #PBS -V
        #PBS -j oe
        #PBS -o {{control_directory}}
        {%- if account %}
        #PBS -A {{account}}
        {%- endif %}
        {%- if email %}
        #PBS -M {{email}}
        {%- endif %}
        {%- if mail_events %}
        #PBS -m {{mail_events}}
        {%- endif %}
        #PBS -N {{job_name}}
        {%- if dependency_list %}
        #PBS -W depend={{dependency_list}}
        {%- endif %}
        {%- if working_directory %}
        #PBS -d {{working_directory}}
        {%- endif %}
        #PBS -l nodes={{nodes|default(1)}}
        #PBS -l procs={{processors|default(1)}}
        #PBS -l pmem={{processor_memory|default('4000m')}}
        {%- if time_limit %}
        #PBS -l walltime={{time_limit}}
        {%- endif %}
        {%- if destination %}
        #PBS -q {{destination}}
        {%- endif %}
        {%- if raw_preamble %}
        {{raw_preamble}}
        {%- endif %}

        ####  End PBS preamble

        {% if notes -%}
        ####  Notes
        {{notes}}
        {%- endif %}

        {% if environment_setup -%}
        ####  Environment setup
        {% for line in environment_setup %}
        {{line}}
        {%- endfor %}
        {%- endif %}

        ####  Commands

        {{command}}


        """
    ).lstrip()

    mail_event_map = {
        'BEGIN': 'b',
        'END': 'e',
        'FAIL': 'a',
    }

    array_job_id_re = re.compile('^\S+\[.*\]')

    def is_installed(self):
        output = ''
        try:
            output = self.capture_process_output(['qmgr', '-c', 'list server'])
        except:
            pass
        return 'pbs_version = ' in output

    def set_dependencies(self, job_data):
        dependencies = job_data.get('dependencies')
        if dependencies:
            dependency_list = []
            if not isinstance(dependencies, collections.Mapping):
                raise ValueError('Job data does not contain a map under the "dependencies" key.')
            for state, job_ids in dependencies.items():
                if state not in drmr.JOB_DEPENDENCY_STATES:
                    raise ValueError('Unsupported dependency state: %s' % state)

                job_ids = [str(job_id) for job_id in job_ids]
                array_jobs = ':'.join([job_id for job_id in job_ids if self.array_job_id_re.search(job_id)])
                regular_jobs = ':'.join([job_id for job_id in job_ids if not self.array_job_id_re.search(job_id)])
                array_dependency_list = array_jobs and ('after%sarray:%s' % (state, array_jobs)) or ''
                regular_dependency_list = regular_jobs and ('after%s:%s' % (state, regular_jobs)) or ''
                dependency_list.append(','.join(l for l in [array_dependency_list, regular_dependency_list] if l))
            job_data['dependency_list'] = ','.join(dependency_list)

    def set_mail_events(self, job_data):
        if job_data.get('mail_events'):
            job_data['mail_events'] = ''.join(
                sorted(
                    self.mail_event_map[event] for event in job_data['mail_events']
                )
            )

    def submit(self, job_filename):
        if not self.is_installed():
            raise drmr.ConfigurationError('{} is not installed or not usable.'.format(self.name))

        try:
            command = ['qsub', job_filename]
            job_id = self.capture_process_output(command)
            return job_id.strip()
        except subprocess.CalledProcessError as e:
            raise drmr.SubmissionError(e.returncode, e.cmd, e.output)

    def validate_destination(self, destination):
        if not self.is_installed():
            raise drmr.ConfigurationError('{} is not installed or not usable.'.format(self.name))

        valid = False
        try:
            command = ['qstat', '-Q', '-f', destination]
            status = self.capture_process_output(command)
            if status.startswith('Queue: {}'.format(destination)):
                valid = True
        except:
            pass

        return valid


class Slurm(DistributedResourceManager):
    name = 'Slurm'

    default_job_template = textwrap.dedent(
        """
        #!/bin/bash

        ####  Slurm preamble

        #SBATCH --export=ALL
        #SBATCH --output "{{control_directory}}/{{job_name}}_%j.out"
        {%- if account %}
        #SBATCH --account={{account}}
        {%- endif %}
        {%- if email %}
        #SBATCH --mail-user={{email}}
        {%- endif %}
        {%- if mail_events %}
        #SBATCH --mail-type={{mail_events}}
        {%- endif %}
        #SBATCH --job-name={{job_name}}
        {%- if dependency_list %}
        #SBATCH --dependency={{dependency_list}}
        {%- endif %}
        {%- if working_directory %}
        #SBATCH --workdir={{working_directory}}
        {%- endif %}
        #SBATCH --nodes={{nodes|default(1)}}
        #SBATCH --ntasks={{processors|default(1)}}
        #SBATCH --mem-per-cpu={{processor_memory|default('4000m')}}
        {%- if time_limit %}
        #SBATCH --time={{time_limit}}
        {%- endif %}
        {%- if destination %}
        #SBATCH --partition={{destination}}
        {%- endif %}
        {%- if raw_preamble %}
        {{raw_preamble}}
        {%- endif %}

        ####  End Slurm preamble

        {% if notes -%}
        ####  Notes
        {{notes}}
        {%- endif %}

        {% if environment_setup -%}
        ####  Environment setup
        {% for line in environment_setup %}
        {{line}}
        {%- endfor %}
        {%- endif %}

        ####  Commands

        {{command}}


        """
    ).lstrip()

    mail_event_map = {
        'BEGIN': 'BEGIN',
        'END': 'END',
        'FAIL': 'FAIL',
    }

    def is_installed(self):
        output = ''
        try:
            output = self.capture_process_output(['scontrol', 'version'])
        except:
            pass

        return 'slurm' in output

    def set_dependencies(self, job_data):
        dependencies = job_data.get('dependencies')
        if dependencies:
            dependency_list = []
            if not isinstance(dependencies, collections.Mapping):
                raise ValueError('Job data does not contain a map under the "dependencies" key.')
            for state, job_ids in dependencies.items():
                if state not in drmr.JOB_DEPENDENCY_STATES:
                    raise ValueError('Unsupported dependency state: %s' % state)

                dependency_list.append('after%s:%s' % (state, ':'.join(str(job_id) for job_id in job_ids)))
            job_data['dependency_list'] = ','.join(dependency_list)

    def set_mail_events(self, job_data):
        if job_data.get('mail_events'):
            job_data['mail_events'] = ','.join(
                sorted(
                    self.mail_event_map[event] for event in job_data['mail_events']
                )
            )

    def submit(self, job_filename):
        if not self.is_installed():
            raise drmr.ConfigurationError('{} is not installed or not usable.'.format(self.name))

        try:
            command = ['sbatch', '--parsable', job_filename]
            job_id = self.capture_process_output(command)
            return job_id.strip().split(';')[0]
        except subprocess.CalledProcessError as e:
            raise drmr.SubmissionError(e.returncode, e.cmd, e.output)

    def validate_destination(self, destination):
        if not self.is_installed():
            raise drmr.ConfigurationError('{} is not installed or not usable.'.format(self.name))

        valid = False
        try:
            command = ['scontrol', 'show', 'partition', destination]
            status = self.capture_process_output(command)
            if status.startswith('PartitionName={}'.format(destination)):
                valid = True
        except:
            pass

        return valid
