=====
Usage
=====

Configuration
=============

The first thing you'll want to do is configure drmr for your local
workload manager, by running ``drmrc``. As long as you only have one
workload manager installed, it should be able to detect it and create
a reasonable configuration.

If you have a default account or destination (Slurm partition or PBS
queue) you want to use for jobs that don't specify one, you can add
that to the configuration. See :ref:`drmrc` in the :ref:`command_reference`
section below for details.

Writing and submitting scripts
==============================

Once you've configured drmr, you're ready to write and submit a drmr
script. Try putting this script in a file called `hello`::

  echo "hello world"

Then run ``drmr hello``. Almost nothing will happen. You should just
see a number printed before the shell prompt comes back. This is the
job ID of a success job, which drmr submits at the end of every
script. You can monitor that job ID to see when your jobs finish.

The `hello` script has probably finished by the time you've read this
far. The only indication will be a new directory named `.drmr`. In
there you'll find a surprising number of files for a simple "hello
world" example. The signal-to-noise ratio does improve as your scripts
grow in size. The contents of `.drmr` should look something like
this::

  $ ls -1 .drmr
  hello.1_174.out
  hello.1.slurm
  hello.cancel
  hello.finish_176.out
  hello.finished
  hello.finish.slurm
  hello.success
  hello.success_175.out
  hello.success.slurm

All of them start with `hello`, the job name derived automatically
from your drmr script's filename. We could have explicitly set the job
name instead, by submitting the script with drmr's ``--job-name``
option.

The file `hello.1.slurm` contains the actual job script. The name
consists of the job prefix `hello`, the job number of the command in
the drmr script (`1`), and a suffix indicating the DRM in use
(`.slurm`, because I'm using Slurm for this example). The job script
looks like this::

    #!/bin/bash

    ####  Slurm preamble

    #SBATCH --export=ALL
    #SBATCH --job-name=hello.1
    #SBATCH --cpus-per-task=1
    #SBATCH --mem-per-cpu=4000
    #SBATCH --output "/home/john/tmp/.drmr/hello.1_%j.out"
    #SBATCH --workdir=/home/john/tmp


    ####  End Slurm preamble


    ####  Environment setup
    . /home/john/.virtualenvs/drmr/bin/activate

    ####  Commands

    echo "hello world"

It's pretty much what you'd write to submit any Slurm job. If you're
using PBS, it will have a `.pbs` extension, and contain a PBS-specific
preamble.

You'll notice that the last line is the command from your `hello`
script.

In between is a nicety for Python users: if you have a virtual
environment active when you submit a script, it will be activated
before running your commands.

Each job script's standard output and error will be in a file named
after the job, containing its DRM job ID. Here it's `hello.1_174.out`,
and it contains::

  hello world

Usually, your drmr scripts will contain commands explicitly
redirecting their standard output to files, and you'll only refer to
these default output files when jobs fail.

The rest of the files are drmr housekeeping: there's a script to
cancel all the jobs (`hello.cancel`), completion jobs
(`hello.finish.slurm` and `hello.success.slurm`) and their output
files, and finally a couple of marker files: `hello.finished` and
`hello.success`. That last one is what you want to see: if the
`.success` file exists, all of your drmr script's jobs completed
successfully. If you see the `.finished` file, but not `.success`,
something went wrong.

A more complete example is included in the output of ``drmr --help``,
which you can read under :ref:`drmr` below. See also the real-world
scripts under :ref:`examples`.

.. _command_reference:

Command reference
=================

.. _drmrc:

drmrc
-----

Creates the drmr configuration file, `.drmrc`.

Help is available by running ``drmrc --help``::

    usage: drmrc [-h] [-a ACCOUNT] [-d DESTINATION] [-o]
                          [-r RESOURCE_MANAGER]

    Generate a drmr configuration file for your local environment.

    optional arguments:
      -h, --help            show this help message and exit
      -a ACCOUNT, --account ACCOUNT
                            The account to which jobs will be charged by default.
      -d DESTINATION, --destination DESTINATION
                            The default queue/partition in which to run jobs.
      -o, --overwrite       Overwrite any existing configuration file.
      -r RESOURCE_MANAGER, --resource-manager RESOURCE_MANAGER
                            If you have more than one resource manager available,
                            you can specify it.

.. _drmr:

drmr
----

Submits a pipeline script to a distributed resource manager. By
default all the pipeline's commands are run concurrently, but you can
indicate dependencies by adding ``# drmr:wait`` directives between
jobs. Whenever a wait directive is encountered, the pipeline will wait
for all prior jobs to complete before continuing.

You may also specify job parameters, like CPU or memory requirements,
time limits, etc. in ``# drmr:job`` directives.

You can get help, including a full example, by running ``drmr --help``::

    usage: drmr [-h] [-a ACCOUNT] [-d DESTINATION] [--debug] [-j JOB_NAME]
                [-f FROM_LABEL] [--mail-at-finish] [--mail-on-error]
                [--start-held] [-t TO_LABEL] [-w WAIT_LIST]
                input

    Submit a drmr script to a distributed resource manager.

    positional arguments:
      input                 The file containing commands to submit. Use "-" for
                            stdin.

    optional arguments:
      -h, --help            show this help message and exit
      -a ACCOUNT, --account ACCOUNT
                            The account to be billed for the jobs.
      -d DESTINATION, --destination DESTINATION
                            The queue/partition in which to run the jobs.
      --debug               Turn on debug-level logging.
      -j JOB_NAME, --job-name JOB_NAME
                            The job name.
      -f FROM_LABEL, --from-label FROM_LABEL
                            Ignore script lines before the given label.
      --mail-at-finish      Send mail when all jobs are finished.
      --mail-on-error       Send mail if any job fails.
      --start-held          Submit a held job at the start of the pipeline, which
                            must be released to start execution.
      -t TO_LABEL, --to-label TO_LABEL
                            Ignore script lines after the given label.
      -w WAIT_LIST, --wait-list WAIT_LIST
                            A colon-separated list of job IDs that must complete
                            before any of this script's jobs are started.

    Supported resource managers are:

      Slurm
      PBS

    drmr will read configuration from your ~/.drmrc, which must be
    valid JSON. You can specify your resource manager and default
    values for any job parameters listed below.

    Directives
    ==========

    Your script can specify job control directives in special
    comments starting with "drmr:".

    # drmr:wait

      Drmr by default runs all the script's commands
      concurrently. The wait directive tells drmr to wait for
      any jobs started since the last wait directive, or the
      beginning of the script, to complete successfully.

    # drmr:label

      Labels let you selectively run sections of your script: you can
      restart from a label with --from-label, running everything after
      it, or just the commands before the label given with --to-label.

    # drmr:job

      You can customize the following job parameters:

      time_limit: The maximum amount of time the DRM should allow the job: "12:30:00" or "12h30m".
      working_directory: The directory where the job should be run.
      processor_memory: The amount of memory required per processor.
      node_properties: A comma-separated list of properties each node must have.
      account: The account to which the job will be billed.
      processors: The number of cores required on each node.
      default: Use the resource manager's default job parameters.
      destination: The execution environment (queue, partition, etc.) for the job.
      job_name: A name for the job.
      memory: The amount of memory required on any one node.
      nodes: The number of nodes required for the job.
      email: The submitter's email address, for notifications.

      Whatever you specify will apply to all jobs after the directive.

      To revert to default parameters, use:

      # drmr:job default

      To request 4 CPUs, 8GB of memory per processor, and a
      limit of 12 hours of execution time on one node:

      # drmr:job nodes=1 processors=4 processor_memory=8000 time_limit=12:00:00

    Example
    =======

    A complete example script follows:

    #!/bin/bash

    #
    # Example drmr script. It can be run as a normal shell script, or
    # submitted to a resource manager with the drmr command.
    #

    #
    # You can just write commands as you would in any script. Their output
    # will be captured in files by the resource manager.
    #
    echo thing1

    #
    # You can only use flow control within a command; drmr's parser is not
    # smart enough to deal with conditionals, or create jobs for each
    # iteration of a for loop, or anything like that.
    #
    # You can do this, but it will just all happen in a single job:
    #
    for i in $(seq 1 4); do echo thing${i}; done

    #
    # Comments are OK.
    #
    echo thing2  # even trailing comments

    #
    # Line continuations are OK.
    #
    echo thing1 \
         thing2 \
         thing3

    #
    # Pipes are OK.
    #
    echo funicular berry harvester | wc -w

    #
    # The drmr wait directive makes subsequent tasks depend on the
    # successful completion of all jobs since the last wait directive or
    # the start of the script.
    #

    # drmr:wait
    echo "And proud we are of all of them."

    #
    # You can specify job parameters:
    #

    # drmr:job nodes=1 processors=4 processor_memory=8000 time_limit=12:00:00
    echo "I got mine but I want more."

    #
    # And revert to the defaults defined by drmr or the resource manager.
    #

    # drmr:job default
    echo "This job feels so normal."

    # drmr:wait
    # drmr:job time_limit=00:15:00
    echo "All done!"

    # And finally, a job is automatically submitted to wait on all the
    # other jobs and report success or failure of the entire script.
    # Its job ID will be printed.

.. _drmrarray:

drmrarray
---------

If you have hundreds or thousands of tasks that don't depend on each
other, you can make life easier for yourself and your DRM by
submitting them in a job array with `drmrarray`. Both Slurm and PBS
cope better with lots of jobs if they're part of an array, and it's
definitely easier to make sense of the DRM's status output when it
doesn't contain hundreds or thousands of lines.

With `drmrarray`, job parameters can only be specified once, at the
top of the script, and will apply to all jobs in the array. And of
course you cannot define dependencies. You can, however, run whatever
program you like on each line of the script you feed to drmrarray.

You can get help, including a full example, by running ``drmrarray --help``::

    usage: drmrarray [-h] [-a ACCOUNT] [-d DESTINATION] [--debug] [-f]
                     [-j JOB_NAME] [--mail-at-finish] [--mail-on-error]
                     [-s SLOT_LIMIT] [-w WAIT_LIST]
                     input

    Submit a drmr script to a distributed resource manager as a job array.

    positional arguments:
      input                 The file containing commands to submit. Use "-" for
                            stdin.

    optional arguments:
      -h, --help            show this help message and exit
      -a ACCOUNT, --account ACCOUNT
                            The account to be billed for the jobs.
      -d DESTINATION, --destination DESTINATION
                            The queue/partition in which to run the jobs.
      --debug               Turn on debug-level logging.
      -f, --finish-jobs     If specified, two extra jobs will be queued after the
                            main array, to indicate success and completion.
      -j JOB_NAME, --job-name JOB_NAME
                            The job name.
      --mail-at-finish      Send mail when all jobs are finished.
      --mail-on-error       Send mail if any job fails.
      -s SLOT_LIMIT, --slot-limit SLOT_LIMIT
                            The number of jobs that will be run concurrently when
                            the job is started, or 'all' (the default).
      -w WAIT_LIST, --wait-list WAIT_LIST
                            A colon-separated list of job IDs that must complete
                            before any of this script's jobs are started.

    Supported resource managers are:

      Slurm
      PBS

    drmrarray will read configuration from your ~/.drmrc, which must be valid
    JSON. You can specify your resource manager and default values for any job
    parameters listed below.

    Directives
    ==========

    Your script can specify job parameters in special comments starting
    with "drmr:job".

    # drmr:job

      You can customize the following job parameters:

      time_limit: The maximum amount of time the DRM should allow the job: "12:30:00" or "12h30m".
      working_directory: The directory where the job should be run.
      processor_memory: The amount of memory required per processor.
      node_properties: A comma-separated list of properties each node must have.
      account: The account to which the job will be billed.
      processors: The number of cores required on each node.
      default: Use the resource manager's default job parameters.
      destination: The execution environment (queue, partition, etc.) for the job.
      job_name: A name for the job.
      memory: The amount of memory required on any one node.
      nodes: The number of nodes required for the job.
      email: The submitter's email address, for notifications.

      Whatever you specify will apply to all jobs after the directive.

      To revert to default parameters, use:

      # drmr:job default

      To request 4 CPUs, 8GB of memory per processor, and a
      limit of 12 hours of execution time on one node:

      # drmr:job nodes=1 processors=4 processor_memory=8000 time_limit=12:00:00

.. _drmrm:

drmrm
-----

A drmr script can generate a lot of jobs. Deleting them with the DRM
tools (e.g. qdel, scancel) can be cumbersome, so drmrm tries to make
it easier. Help is available by running ``drmrm --help`` ::

    usage: drmrm [-h] [--debug] [-n] [-j JOB_NAME] [-u USER] [job_id [job_id ...]]

    Remove jobs from a distributed resource manager.

    positional arguments:
      job_id                A job ID to remove.

    optional arguments:
      -h, --help            show this help message and exit
      --debug               Turn on debug-level logging.
      -n, --dry-run         Just print jobs that would be removed, without
                            actually removing them.
      -j JOB_NAME, --job-name JOB_NAME
                            Remove only jobs whose names contain this string.
      -u USER, --user USER  Remove only jobs belonging to this user.
