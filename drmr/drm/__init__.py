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
import sys
import time
import uuid
import textwrap

import jinja2
import lxml.objectify

import drmr
import drmr.util


class DistributedResourceManager(object):
    name = 'Base Distributed Resource Manager'
    default_job_template = ''
    default_array_command_template = textwrap.dedent(
        """
        if [ "$THE_DRM_ARRAY_JOB_INDEX_ID" = "{index}" ]; then
            {command}
        fi
        """
    )

    def __init__(self):
        self.default_job_data = {
            'dependencies': {},
            'environment_setup': [],
        }

    def capture_process_output(self, command=[]):
        return subprocess.check_output(command, stderr=subprocess.STDOUT, universal_newlines=True)

    def delete_jobs(self, job_ids=[], job_name=None, job_owner=None, dry_run=False):
        raise NotImplementedError

    def explain_job_deletion(self, job_ids=[], job_name=None, job_owner=None, dry_run=False):
        msg = (dry_run and 'Would delete ' or 'Deleting ') + 'jobs belonging to ' + job_owner
        if job_ids:
            msg += ' whose IDs are in this list: {}'.format(job_ids)
        if job_name:
            if job_ids:
                msg += ' or'
            msg += ' whose names match "' + job_name + '"'
        return msg

    def get_active_job_ids(self, job_name=None, job_owner=None):
        """
        Get a list of ids of jobs that are running, or might be in the future.
        """
        raise NotImplementedError

    def get_method_logger(self):
        stack = inspect.getouterframes(inspect.currentframe())
        caller = stack[1][3]
        return logging.getLogger("{}.{}.{}".format(self.__module__, self.__class__.__name__, caller))

    def is_installed(self):
        """Verifies that the resource manager is installed."""
        raise NotImplementedError

    def make_cancel_script(self, job_data, job_ids):
        raise NotImplementedError

    def make_control_directory(self, job_data):
        """Create the control directory for submitted jobs."""
        self.set_control_directory(job_data)
        drmr.util.makedirs(job_data['control_directory'])

    def make_job_filename(self, job_data):
        """Create a name for the job file in the control directory."""
        self.make_control_directory(job_data)
        return drmr.util.absjoin(job_data['control_directory'], job_data['job_name'] + '.' + self.name.lower())

    def make_array_command(self, command_data):
        template_environment = jinja2.Environment()
        return template_environment.from_string(self.default_array_command_template).render(**command_data)

    def make_job_script(self, job_data):
        """Format a job template, suitable for submission to the DRM."""
        template_data = self.make_job_script_data(job_data)
        template_environment = jinja2.Environment(trim_blocks=True, lstrip_blocks=True)
        return template_environment.from_string(self.default_job_template).render(**template_data)

    def make_job_script_data(self, job_data):
        """Prepare the job data for interpolation into the job file template."""
        template_data = {}
        template_data.update(copy.deepcopy(self.default_job_data))
        template_data.update(job_data)
        template_data['resource_manager'] = self

        self.set_control_directory(template_data)
        self.set_working_directory(template_data)
        self.set_mail_event_string(template_data)
        self.set_job_name(template_data)

        python_virtualenv = os.getenv('VIRTUAL_ENV')
        if python_virtualenv:
            template_data['environment_setup'].append('. {}/bin/activate'.format(python_virtualenv))

        return template_data

    def set_control_directory(self, job_data):
        """Add the path of the control directory to the job data."""
        control_path = drmr.util.absjoin(job_data.get('working_directory', os.getcwd()), '.drmr')
        job_data['control_directory'] = control_path
        return control_path

    def make_dependency_string(self, state, job_id):
        """Convert a dependency states and job ID to the dependency string format required by the DRM."""
        raise NotImplementedError

    def set_job_name(self, job_data):
        if 'job_name' not in job_data:
            job_data['job_name'] = uuid.uuid4()

    def set_mail_event_string(self, job_data):
        """Convert the list of mail events to the string format required by the DRM."""
        raise NotImplementedError

    def set_working_directory(self, job_data):
        if 'working_directory' not in job_data:
            job_data['working_directory'] = os.getcwd()

    def submit(self, job_file, hold=False):
        """Submit a job file. Return the job ID."""
        raise NotImplementedError

    def submit_completion_jobs(self, job_data, job_list, mail_at_finish=False):
        """Submit two jobs: one to record success, and one just to record completion."""

        if not job_list:
            raise ValueError('You did not supply a list of job IDs to wait for.')

        common_data = copy.deepcopy(job_data)
        self.set_control_directory(common_data)

        #
        # The happy path: all jobs completed; we're done, or on to the
        # next phase. This success job ID is what dependent tasks should
        # watch.
        #
        success_data = copy.deepcopy(common_data)
        success_commands = ['touch {control_directory}/{job_name}.success'.format(**success_data)]
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
        finish_data = copy.deepcopy(common_data)
        finish_commands = ['touch {control_directory}/{job_name}.finished'.format(**finish_data)]
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

    def validate_destination(self, destination):
        """Verifies that the given destination is valid."""
        raise NotImplementedError

    def write_job_file(self, job_data):
        """Write a batch script to be submitted to the resource manager."""

        logger = self.get_method_logger()
        logger.debug('Writing job file for {}'.format(job_data))

        job_filename = self.make_job_filename(job_data)
        with open(job_filename, 'w') as job_file:
            job_file.write(self.make_job_script(job_data))

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
        #PBS -l nodes={{nodes}}:ppn={{processors|default(1)}}
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

    mail_event_map = {
        'BEGIN': 'b',
        'END': 'e',
        'FAIL': 'a',
    }

    array_job_id_re = re.compile('^\S+\[.*\]')

    def delete_jobs(self, job_ids=[], job_name=None, job_owner=None, dry_run=False):
        logger = self.get_method_logger()

        targets = set(job_ids)
        targets.update(self.get_active_job_ids(job_ids, job_name, job_owner))

        if targets:
            if dry_run:
                logger.info(self.explain_job_deletion(job_ids, job_name, job_owner, dry_run))
            else:
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(self.explain_job_deletion(job_ids, job_name, job_owner, dry_run))
                for target in sorted(targets):
                    command = ['qdel', target]
                    try:
                        subprocess.check_call(command)
                    except subprocess.CalledProcessError as e:
                        raise drmr.DeletionError(e.returncode, e.cmd, e.output, [target])
                    time.sleep(0.25)  # PBS is frail

    def get_active_job_ids(self, job_ids=[], job_name=None, job_owner=None):
        jobs = set([])

        command = ['qstat', '-t', '-x']

        qstat = lxml.objectify.fromstring(self.capture_process_output(command))
        for job in qstat.findall('Job'):
            if job.job_state not in ['E', 'H', 'Q', 'R', 'T', 'W']:
                continue

            if job_name and job_name not in job.Job_Name.text:
                print('job name {} != {}'.format(job_name, job.Job_Name.text), file=sys.stderr)
                continue

            if job_ids and job.Job_Id.text not in job_ids:
                print('job id no good {}'.format(job.Job_Id.text), file=sys.stderr)
                continue

            owner = job.Job_Owner.text.split('@')[0]
            if job_owner and job_owner != owner:
                continue

            jobs.add(job.Job_Id.text)

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
                if state not in drmr.JOB_DEPENDENCY_STATES:
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
            raise drmr.ConfigurationError('{} is not installed or not usable.'.format(self.name))

        try:
            command = ['qsub', job_filename]
            if hold:
                command.insert(1, '-h')
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
        #SBATCH --job-name={{job_name}}
        {% if nodes %}
        #SBATCH --nodes={{nodes}}
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

    def delete_jobs(self, job_ids=[], job_name=None, job_owner=None, dry_run=False):
        logger = self.get_method_logger()

        targets = set(job_ids)
        targets.update(self.get_active_job_ids(job_ids, job_name, job_owner))

        if targets:
            if dry_run:
                logger.info(self.explain_job_deletion(job_ids, job_name, job_owner, dry_run))
            else:
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(self.explain_job_deletion(job_ids, job_name, job_owner, dry_run))
                command = ['scancel'] + list(targets)
                try:
                    subprocess.check_call(command)
                except subprocess.CalledProcessError as e:
                    raise drmr.DeletionError(e.returncode, e.cmd, e.output, targets)

    def get_active_job_ids(self, job_ids=[], job_name=None, job_owner=None):
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

                if job_name and job_name != name:
                    continue

                if job_ids and job_id not in job_ids:
                    continue

                jobs.add(job_id)

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
                if state not in drmr.JOB_DEPENDENCY_STATES:
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
            raise drmr.ConfigurationError('{} is not installed or not usable.'.format(self.name))

        try:
            command = ['sbatch', '--parsable', job_filename]
            if hold:
                command.insert(1, '--hold')

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
