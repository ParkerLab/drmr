#
# drmr: A tool for submitting pipeline scripts to distributed resource
# managers.
#
# Copyright 2015 Stephen Parker
#
# Licensed under Version 3 of the GPL or any later version
#

from __future__ import print_function

import copy
import inspect
import logging
import os
import subprocess
import uuid
import textwrap

import jinja2

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
        msg = (dry_run and 'Would delete' or 'Deleting') + (job_ids and ' these' or '') + ' jobs belonging to ' + job_owner
        if job_name:
            msg += ' whose names match "' + job_name + '"'

        if job_ids:
            msg += ': [{}]'.format(', '.join(sorted(job_ids)))

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
        template_data = drmr.util.merge_mappings(self.default_job_data, job_data, {'resource_manager': self})

        self.set_control_directory(template_data)
        self.set_working_directory(template_data)
        self.set_mail_event_string(template_data)
        self.set_job_name(template_data)
        self.normalize_memory(template_data)
        self.normalize_time_limit(template_data)

        python_virtualenv = os.getenv('VIRTUAL_ENV')
        if python_virtualenv:
            template_data['environment_setup'].append('. {}/bin/activate'.format(python_virtualenv))

        return template_data

    def normalize_memory(self, job_data):
        """
        Normalize the amount of memory requested to megabytes.
        """

        memory = job_data.get('memory')
        if not memory:
            return

        job_data['memory'] = drmr.util.normalize_memory(memory)

    def normalize_time_limit(self, job_data):
        """
        Normalize the time limit requested to hours:minutes:seconds.
        """

        time_limit = job_data.get('time_limit')
        if not time_limit:
            return

        job_data['time_limit'] = drmr.util.normalize_time(time_limit)

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
        success_data = drmr.util.merge_mappings(
            common_data,
            {
                'job_name': common_data['job_name'] + '.success',
                'time_limit': '00:15:00',
                'processors': '1',
                'processor_memory': '1000',
                'memory': '1000',
                'dependencies': {'ok': job_list},
                'command': 'touch {control_directory}/{job_name}.success'.format(**common_data),
            }
        )

        success_job_filename = self.write_job_file(success_data)
        success_job_id = self.submit(success_job_filename)

        #
        # Whatever happened, let's record that the job is done.
        #
        finish_data = drmr.util.merge_mappings(
            common_data,
            {
                'job_name': common_data['job_name'] + '.finish',
                'time_limit': '00:15:00',
                'processors': '1',
                'processor_memory': '1000',
                'memory': '1000',
                'dependencies': {'any': job_list},
                'command': 'touch {control_directory}/{job_name}.finished'.format(**common_data),
            }
        )

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
