#
# drmr: A tool for submitting pipeline scripts to distributed resource
# managers.
#
# Copyright 2015 The Parker Lab at the University of Michigan
#
# Licensed under Version 3 of the GPL or any later version
#

from __future__ import print_function

import copy
import os
import subprocess
import uuid
import textwrap

import jinja2

import drmr


class DistributedResourceManager(object):
    name = "Base Distributed Resource Manager"
    default_job_template = ''

    def __init__(self):
        self.default_directives = {
            'environment_setup': [],
        }

    def make_control_directory(self, directives):
        control_path = absjoin(directives.get('working_directory', ''), '.drmr')
        makedirs(control_path)
        directives['control_directory'] = control_path
        return control_path

    def make_job_filename(self, directives):
        control_directory = self.make_control_directory(directives)
        return absjoin(control_directory, directives['name'] + '.' + self.name)

    def make_job_template(self, directives):
        """Format a job template, suitable for submission to the DRM."""
        job_data = {}
        job_data.update(copy.deepcopy(self.default_directives))
        job_data.update(directives)

        self.set_dependencies(job_data)
        self.set_mail_events(job_data)
        self.set_name(job_data)
        self.set_working_directory(job_data)

        python_virtualenv = os.getenv('VIRTUAL_ENV')
        if python_virtualenv:
            job_data['environment_setup'].append('. {}/bin/activate'.format(python_virtualenv))

        template_environment = jinja2.Environment()
        return template_environment.from_string(self.default_job_template).render(**job_data)

    def set_dependencies(self, job_data):
        """Convert the list of dependencies to the string format required by the DRM."""
        raise NotImplementedError

    def set_mail_events(self, job_data):
        """Convert the list of mail events to the string format required by the DRM."""
        raise NotImplementedError

    def set_name(self, job_data):
        if 'name' not in job_data:
            job_data['name'] = uuid.uuid4()

    def set_working_directory(self, job_data):
        if 'working_directory' not in job_data:
            job_data['working_directory'] = os.getcwd()

    def submit(self, job_file):
        """
        Submit a job file. Return the job ID.
        """
        raise NotImplementedError

    def write_job_file(self, directives):
        job_filename = self.make_job_filename(directives)
        with open(job_filename, 'w') as job_file:
            job_file.write(self.make_job_template(directives))
        return job_filename


class PBS(DistributedResourceManager):
    name = "pbs"

    default_job_template = textwrap.dedent(
        """
        #!/bin/bash

        ####  PBS preamble

        #PBS -V
        #PBS -j oe
        #PBS -o {{control_directory}}
        {%- if account %}
        #PBS -A {{account}}
        {% endif -%}
        {%- if email %}
        #PBS -M {{email}}
        {% endif -%}
        {%- if mail_events %}
        #PBS -m {{mail_events}}
        {% endif -%}
        #PBS -N {{name}}
        {%- if dependencies %}
        #PBS -W afterok:{{dependencies}}
        {% endif -%}
        {%- if working_directory %}
        #PBS -d {{working_directory}}
        {% endif -%}
        #PBS -l nodes={{nodes|default(1)}}
        #PBS -l procs={{processors|default(1)}}
        #PBS -l pmem={{processor_memory|default("4000m")}}
        {%- if time_limit %}
        #PBS -l walltime={{time_limit}}
        {% endif -%}
        {%- if destination %}
        #PBS -q {{destination}}
        {% endif -%}
        {{raw_preamble}}

        ####  End PBS preamble

        {{notes}}

        {%- for line in environment_setup %}
        {{line}}
        {% endfor -%}
        {{command}}

        """
    ).lstrip()

    mail_event_map = {
        'BEGIN': 'b',
        'END': 'e',
        'FAIL': 'a',
    }

    def set_dependencies(self, job_data):
        if job_data.get('dependencies'):
            job_data['dependencies'] = ':'.join(job_data['dependencies'])

    def set_mail_events(self, job_data):
        if job_data.get('mail_events'):
            job_data['mail_events'] = ''.join(
                sorted(
                    self.mail_event_map[event] for event in job_data['mail_events']
                )
            )

    def submit(self, job_filename):
        try:
            command = ['qsub', job_filename]
            job_id = subprocess.check_output(command, stderr=subprocess.STDOUT, universal_newlines=True)
            return job_id.strip()
        except subprocess.CalledProcessError as e:
            raise drmr.SubmissionError(e.returncode, e.cmd, e.output)


class Slurm(DistributedResourceManager):
    name = "slurm"

    default_job_template = textwrap.dedent(
        """
        #!/bin/bash

        ####  Slurm preamble

        #SBATCH --export=ALL
        #SBATCH --output "{{control_directory}}/{{name}}_%j.out"
        {% if account %}#SBATCH --account={{account}}{% endif -%}
        {% if email %}#SBATCH --mail-user={{email}}{% endif -%}
        {% if mail_events %}#SBATCH --mail-type={{mail_events}}{% endif -%}
        #SBATCH --job-name={{name}}
        {% if dependencies %}#SBATCH --dependencies afterok:{{dependencies}}{% endif -%}
        {% if working_directory %}#SBATCH --workdir={{working_directory}}{% endif -%}
        #SBATCH --nodes={{nodes|default(1)}}
        #SBATCH --ntasks={{processors|default(1)}}
        #SBATCH --mem-per-cpu={{processor_memory|default("4000m")}}
        {% if time_limit %}#SBATCH --time={{time_limit}}{% endif -%}
        {% if destination %}#SBATCH --partition={{destination}}{% endif -%}
        {{raw_preamble}}

        ####  End Slurm preamble

        {{notes}}

        {%- for line in environment_setup %}
        {{line}}
        {% endfor -%}

        {{command}}

        """
    ).lstrip()

    mail_event_map = {
        'BEGIN': 'BEGIN',
        'END': 'END',
        'FAIL': 'FAIL',
    }

    def set_dependencies(self, job_data):
        if job_data.get('dependencies'):
            job_data['dependencies'] = ':'.join(job_data['dependencies'])

    def set_mail_events(self, job_data):
        if job_data.get('mail_events'):
            job_data['mail_events'] = ','.join(
                sorted(
                    self.mail_event_map[event] for event in job_data['mail_events']
                )
            )

    def submit(self, job_filename):
        try:
            command = ['sbatch', '--parsable', job_filename]
            job_id = subprocess.check_output(command, stderr=subprocess.STDOUT, universal_newlines=True)
            return job_id.strip().split(';')[0]
        except subprocess.CalledProcessError as e:
            raise drmr.SubmissionError(e.returncode, e.cmd, e.output)


def makedirs(*paths):
    """Creates each path given.

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
